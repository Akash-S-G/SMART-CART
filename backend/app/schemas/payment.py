from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ============================================================
# ENUMS
# ============================================================

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    WALLET = "wallet"
    NET_BANKING = "net_banking"
    RAZORPAY = "razorpay"
    STRIPE = "stripe"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# ============================================================
# CREATE PAYMENT
# ============================================================

class CreatePaymentRequest(BaseModel):

    order_id: UUID

    payment_method: PaymentMethod


# ============================================================
# VERIFY PAYMENT
# ============================================================

class VerifyPaymentRequest(BaseModel):

    transaction_id: str


# ============================================================
# REFUND
# ============================================================

class RefundRequest(BaseModel):

    reason: str | None = None


# ============================================================
# PAYMENT SUMMARY
# ============================================================

class PaymentSummary(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID

    transaction_id: str

    amount: Decimal

    status: PaymentStatus

    created_at: datetime


# ============================================================
# PAYMENT LIST
# ============================================================
class PaymentListResponse(BaseModel):

    items: list[PaymentSummary]

    page: int

    page_size: int

    total_items: int

    total_pages: int

    
class PaymentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    order_id: UUID

    user_id: UUID

    transaction_id: str

    gateway_reference: str | None = None

    payment_method: PaymentMethod

    status: PaymentStatus

    currency: str

    amount: Decimal

    created_at: datetime

# ============================================================
# REFUND RESPONSE
# ============================================================

class RefundResponse(BaseModel):

    message: str

    payment: PaymentResponse