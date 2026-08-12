from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
    File,
)

import uuid

from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.dependencies import (
    get_current_admin,
    get_current_user,
)

from app.db.session import get_db

from app.models.user.users import User

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryResponse,
    BarcodeResponse,
    BulkUploadResult,
)

from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    try:

        product = service.create_product(request)

        return product

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
@router.get(
    "/categories",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
):
    from app.models.products.categories import Category
    return db.query(Category).all()


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=500),
    category_id: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort: str | None = Query(None, description="price_asc | price_desc | rating_desc | name_asc"),
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    return service.list_products(
        skip=skip,
        limit=limit,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
    )

@router.get(
    "/search/",
    response_model=list[ProductResponse],
)
def search_products(
    keyword: str,
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    return service.search_products(keyword)

@router.get(
    "/generate-barcode",
    response_model=BarcodeResponse,
)
def generate_barcode_endpoint(
    existing: str | None = Query(None, description="Reuse/validate an existing barcode if valid"),
    db: Session = Depends(get_db),
):
    """Generate (or validate) a retail barcode and return an SVG preview."""
    from app.core.barcode_util import generate_barcode, render_barcode_svg

    value = generate_barcode(existing)
    return BarcodeResponse(barcode=value, image=render_barcode_svg(value))


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):

    service = ProductService(db)

    try:

        return service.get_product(product_id)

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "/upload-image",
    response_model=dict,
)
async def upload_product_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Upload a product image (multipart) to Cloudinary and return the URL."""
    from app.services.cloudinary_service import cloudinary_service

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    image_url = None
    if cloudinary_service.is_configured:
        image_url = cloudinary_service.upload_image(contents, folder="products")
    else:
        # Fallback: store under backend/static/uploads and serve via /static.
        import os
        from app.core.config import settings
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
        fname = f"{uuid.uuid4().hex}{ext}"
        with open(os.path.join(upload_dir, fname), "wb") as f:
            f.write(contents)
        image_url = f"/static/uploads/{fname}"

    if not image_url:
        raise HTTPException(status_code=502, detail="Image upload failed.")
    return {"image_url": image_url}


@router.post(
    "/bulk",
    response_model=BulkUploadResult,
)
async def bulk_create_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Bulk-create products from a CSV (columns match ProductCreate + image_url)."""
    import csv
    import io

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    text = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"name", "sku", "category_id"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must include columns: {sorted(required)} (got {reader.fieldnames}).",
        )

    service = ProductService(db)
    created = 0
    failed = 0
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            payload = ProductCreate(
                name=(row.get("name") or "").strip(),
                sku=(row.get("sku") or "").strip(),
                barcode=(row.get("barcode") or "").strip() or None,
                description=(row.get("description") or "").strip() or None,
                brand=(row.get("brand") or "").strip() or None,
                category_id=(row.get("category_id") or "").strip(),
                initial_stock=int(row.get("initial_stock") or 0) or 0,
                price=float(row.get("price") or 0) or 0.0,
                image_url=(row.get("image_url") or "").strip() or None,
            )
            service.create_product(payload)
            created += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            errors.append(f"row {i}: {exc}")

    return BulkUploadResult(created=created, failed=failed, errors=errors[:20])


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: str,
    request: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    try:

        return service.update_product(
            product_id,
            request,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):

    service = ProductService(db)

    service.delete_product(product_id)


class RestockRequest(BaseModel):
    quantity: int

@router.post(
    "/{product_id}/restock",
    response_model=ProductResponse,
)
def restock_product(
    product_id: str,
    request: RestockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    from app.models.products.inventory import Inventory
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        inv = Inventory(product_id=product_id, quantity=request.quantity)
        db.add(inv)
    else:
        inv.quantity += request.quantity
    db.commit()
    service = ProductService(db)
    return service.get_product(product_id)



