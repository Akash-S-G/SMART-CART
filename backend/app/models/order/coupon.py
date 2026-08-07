from sqlalchemy import Column, String, Float, Boolean, DateTime, func
import uuid
from app.db.base import Base

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    discount_percentage = Column(Float, nullable=False)
    max_discount = Column(Float, nullable=True)
    min_order_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
