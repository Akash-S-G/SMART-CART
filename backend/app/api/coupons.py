from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.order.coupon import Coupon

router = APIRouter(prefix="/coupons", tags=["Coupons"])

class CouponValidateRequest(BaseModel):
    code: str
    order_amount: float = 0.0

class CouponValidateResponse(BaseModel):
    code: str
    discount_percentage: float
    discount_amount: float
    message: str

# Pre-seeded default coupons
DEFAULT_COUPONS = {
    "SMART10": {"discount_percentage": 10.0, "max_discount": 500.0, "min_order_amount": 200.0},
    "WELCOME20": {"discount_percentage": 20.0, "max_discount": 1000.0, "min_order_amount": 500.0},
    "FREESHIP": {"discount_percentage": 100.0, "max_discount": 100.0, "min_order_amount": 0.0},
}

@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon(
    request: CouponValidateRequest,
    db: Session = Depends(get_db),
):
    code_upper = request.code.strip().upper()
    coupon = db.query(Coupon).filter(Coupon.code == code_upper, Coupon.is_active == True).first()

    if not coupon and code_upper in DEFAULT_COUPONS:
        c_info = DEFAULT_COUPONS[code_upper]
        coupon = Coupon(
            code=code_upper,
            discount_percentage=c_info["discount_percentage"],
            max_discount=c_info["max_discount"],
            min_order_amount=c_info["min_order_amount"],
            is_active=True
        )
        db.add(coupon)
        db.commit()
        db.refresh(coupon)

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired promo code."
        )

    if request.order_amount < coupon.min_order_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order amount must be at least ₹{coupon.min_order_amount:.2f} for this coupon."
        )

    raw_discount = (request.order_amount * coupon.discount_percentage) / 100.0
    discount_amount = min(raw_discount, coupon.max_discount) if coupon.max_discount else raw_discount

    return CouponValidateResponse(
        code=coupon.code,
        discount_percentage=coupon.discount_percentage,
        discount_amount=round(discount_amount, 2),
        message=f"Promo code '{coupon.code}' applied successfully!"
    )
