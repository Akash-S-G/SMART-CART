from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.models.user.users import User
from app.models.products.wishlist import Wishlist
from app.models.products.product import Product
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

@router.get("", response_model=list[ProductResponse])
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()
    products = [item.product for item in items if item.product]
    return products

@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).first()

    if not existing:
        item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.add(item)
        db.commit()

    return {"message": "Added to wishlist", "product_id": product_id}

@router.delete("/{product_id}")
def remove_from_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": "Removed from wishlist", "product_id": product_id}
