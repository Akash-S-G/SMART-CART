from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional

from app.db.session import get_db
from app.auth.dependencies import get_current_admin
from app.models.user.users import User
from app.models.products.inventory import Inventory
from app.models.products.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.models.products.product import Product
from app.models.products.product_price import ProductPrice
from app.repositories.inventory_repository import InventoryRepository
from app.websocket.events import emit_inventory_updated

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---------- Schemas ----------
class InventoryResponse(BaseModel):
    product_id: str
    inventory_id: str
    product_name: str
    sku: str
    barcode: str | None
    quantity: int
    reorder_level: int | None
    max_capacity: int | None
    location: str | None
    price: float | None
    status: str  # optimal | low | out

class InventoryUpdateRequest(BaseModel):
    reorder_level: Optional[int] = Field(default=None, ge=0)
    max_capacity: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=0, description="Direct set quantity (admin override)")

class InventoryAdjustRequest(BaseModel):
    quantity_change: int = Field(description="Positive for inbound, negative for outbound (non-zero)")
    transaction_type: InventoryTransactionType = Field(default=InventoryTransactionType.ADJUSTMENT)
    remarks: Optional[str] = Field(default=None, max_length=255)
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None

class TransactionResponse(BaseModel):
    id: str
    product_id: str
    inventory_id: str
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference_type: str | None
    remarks: str | None
    created_at: str | None

def _status_for(qty: int, reorder: int | None) -> str:
    if qty == 0:
        return "out"
    threshold = reorder if reorder is not None else 20
    if qty < threshold:
        return "low"
    return "optimal"

def _to_response(inv: Inventory) -> InventoryResponse:
    prod = inv.product
    price_val = float(prod.price.price) if getattr(prod, "price", None) else None
    return InventoryResponse(
        product_id=str(prod.id),
        inventory_id=str(inv.id),
        product_name=prod.name,
        sku=prod.sku,
        barcode=prod.barcode,
        quantity=inv.quantity or 0,
        reorder_level=inv.reorder_level,
        max_capacity=inv.max_capacity,
        location=inv.location,
        price=price_val,
        status=_status_for(inv.quantity or 0, inv.reorder_level),
    )


# ---------- Endpoints ----------
@router.get("", response_model=list[InventoryResponse])
def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    low_stock: bool = Query(False, description="Only low/out stock"),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    q = db.query(Inventory).join(Product, Inventory.product_id == Product.id).options(
        joinedload(Inventory.product).joinedload(Product.price)
    )
    if search:
        q = q.filter(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))
    rows = q.offset(skip).limit(limit).all()
    # ensure product relationship loaded for price fallback
    # if product.price not eager, fetch separately via joinedload above
    result = [_to_response(r) for r in rows]
    if low_stock:
        result = [r for r in result if r.status in ("low", "out")]
    return result


@router.get("/valuation")
def inventory_valuation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    rows = db.query(Inventory, ProductPrice.price).join(Product, Inventory.product_id == Product.id).outerjoin(ProductPrice, ProductPrice.product_id == Product.id).all()
    total_units = sum((inv.quantity or 0) for inv, _ in rows)
    total_value = sum(float(price or 0) * (inv.quantity or 0) for inv, price in rows)
    low = sum(1 for inv, _ in rows if 0 < (inv.quantity or 0) < (inv.reorder_level or 20))
    out = sum(1 for inv, _ in rows if (inv.quantity or 0) == 0)
    return {
        "total_skus": len(rows),
        "total_units": total_units,
        "total_valuation": round(total_value, 2),
        "low_stock_count": low,
        "out_of_stock_count": out,
    }


@router.get("/low-stock", response_model=list[InventoryResponse])
def low_stock_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    rows = db.query(Inventory).options(joinedload(Inventory.product).joinedload(Product.price)).all()
    result = [_to_response(r) for r in rows if _status_for(r.quantity or 0, r.reorder_level) in ("low", "out")]
    return result


@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).options(joinedload(Inventory.product).joinedload(Product.price)).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return _to_response(inv)


@router.get("/{product_id}/transactions", response_model=list[TransactionResponse])
def get_transactions(
    product_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    repo = InventoryRepository(db)
    txs = repo.get_transactions(product_id)[:limit]
    return [
        TransactionResponse(
            id=str(t.id),
            product_id=str(t.product_id),
            inventory_id=str(t.inventory_id),
            transaction_type=t.transaction_type.value if hasattr(t.transaction_type, "value") else str(t.transaction_type),
            quantity_change=t.quantity_change,
            quantity_before=t.quantity_before,
            quantity_after=t.quantity_after,
            reference_type=t.reference_type,
            remarks=t.remarks,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in txs
    ]


@router.patch("/{product_id}", response_model=InventoryResponse)
def update_inventory_thresholds(
    product_id: str,
    body: InventoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        # auto-create if missing
        inv = Inventory(product_id=product_id, quantity=body.quantity or 0, reorder_level=body.reorder_level, max_capacity=body.max_capacity, location=body.location)
        db.add(inv)
        db.commit()
        db.refresh(inv)
    else:
        if body.reorder_level is not None:
            inv.reorder_level = body.reorder_level
        if body.max_capacity is not None:
            inv.max_capacity = body.max_capacity
        if body.location is not None:
            inv.location = body.location
        if body.quantity is not None:
            before = inv.quantity or 0
            inv.quantity = body.quantity
            db.commit()
            db.refresh(inv)
            # record adjustment if quantity changed via direct set
            if before != inv.quantity:
                repo = InventoryRepository(db)
                repo.record_transaction(
                    inventory_id=inv.id,
                    product_id=product_id,
                    transaction_type=InventoryTransactionType.ADJUSTMENT,
                    quantity_change=inv.quantity - before,
                    quantity_before=before,
                    quantity_after=inv.quantity,
                )
                # remarks via separate update
                # we write remarks as transaction remarks not stored here; skip
        if body.quantity is None:
            db.commit()
            db.refresh(inv)
    # reload with product
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).options(joinedload(Inventory.product).joinedload(Product.price)).first()
    response = _to_response(inv)
    emit_inventory_updated(
        product_id=response.product_id,
        sku=response.sku,
        quantity=response.quantity,
        status=response.status,
        reorder_level=response.reorder_level,
        actor_id=str(current_user.id),
    )
    return response


@router.post("/{product_id}/adjust", response_model=InventoryResponse)
def adjust_inventory(
    product_id: str,
    body: InventoryAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    if body.quantity_change == 0:
        raise HTTPException(status_code=400, detail="quantity_change cannot be 0")
    repo = InventoryRepository(db)
    inv = repo.get_by_product(product_id)
    if not inv:
        # create with 0 then adjust
        inv = Inventory(product_id=product_id, quantity=0)
        db.add(inv)
        db.commit()
        db.refresh(inv)
    before = inv.quantity or 0
    after = before + body.quantity_change
    if after < 0:
        raise HTTPException(status_code=400, detail=f"Insufficient stock: {before} available, cannot deduct {abs(body.quantity_change)}")
    if inv.max_capacity and after > inv.max_capacity:
        raise HTTPException(status_code=400, detail=f"Exceeds max capacity {inv.max_capacity}")
    inv.quantity = after
    db.commit()
    db.refresh(inv)
    repo.record_transaction(
        inventory_id=inv.id,
        product_id=product_id,
        transaction_type=body.transaction_type,
        quantity_change=body.quantity_change,
        quantity_before=before,
        quantity_after=after,
    )
    # patch remarks/reference if provided (last tx)
    if body.remarks or body.reference_type:
        last_tx = db.query(InventoryTransaction).filter(InventoryTransaction.inventory_id == inv.id).order_by(InventoryTransaction.created_at.desc()).first()
        if last_tx:
            if body.remarks:
                last_tx.remarks = body.remarks
            if body.reference_type:
                last_tx.reference_type = body.reference_type
            if body.reference_id:
                last_tx.reference_id = body.reference_id
            db.commit()
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).options(joinedload(Inventory.product).joinedload(Product.price)).first()
    response = _to_response(inv)
    emit_inventory_updated(
        product_id=response.product_id,
        sku=response.sku,
        quantity=response.quantity,
        status=response.status,
        reorder_level=response.reorder_level,
        actor_id=str(current_user.id),
        transaction_type=body.transaction_type.value if hasattr(body.transaction_type, "value") else str(body.transaction_type),
    )
    return response
