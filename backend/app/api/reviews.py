from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.db.session import get_db
from app.models.products.review import Review
from app.models.products.product import Product
from app.models.order.order import Order
from app.models.order.order_item import OrderItem
from app.models.user.users import User
from app.schemas.review import CreateReviewRequest, ReviewResponse

router = APIRouter(prefix="/products", tags=["Reviews"])


def _get_product_or_404(product_id: str, db: Session) -> Product:
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/{product_id}/reviews
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/{product_id}/reviews",
    response_model=list[ReviewResponse],
)
def list_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    _get_product_or_404(product_id, db)
    skip = (page - 1) * page_size
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.helpful_count.desc(), Review.review_date.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    return reviews


# ─────────────────────────────────────────────────────────────────────────────
# POST /products/{product_id}/reviews
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    product_id: str,
    body: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_product_or_404(product_id, db)

    # Check for verified purchase — user ordered this product
    verified = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == str(current_user.id),
            OrderItem.product_id == product_id,
            Order.status.in_(["paid", "completed", "delivered"]),
        )
        .first()
    ) is not None

    # Derive display name from profile or username
    display_name = current_user.username
    if hasattr(current_user, "profile") and current_user.profile:
        fn = current_user.profile.first_name or ""
        ln = current_user.profile.last_name or ""
        full = f"{fn} {ln}".strip()
        if full:
            display_name = full

    review = Review(
        id=str(uuid.uuid4()),
        product_id=product_id,
        user_name=display_name,
        rating=body.rating,
        title=body.title,
        body=body.body,
        is_generated=False,
        verified_purchase=verified,
        helpful_count=0,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ─────────────────────────────────────────────────────────────────────────────
# POST /products/{product_id}/reviews/{review_id}/helpful
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/{product_id}/reviews/{review_id}/helpful",
    response_model=ReviewResponse,
)
def mark_helpful(
    product_id: str,
    review_id: str,
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.product_id == product_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.helpful_count = (review.helpful_count or 0) + 1
    db.commit()
    db.refresh(review)
    return review
