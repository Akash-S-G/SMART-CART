from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
# ==========================================================
# ORDER ITEM
# ==========================================================

class OrderItemResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    product_id: UUID

    product_name: str

    sku: str

    quantity: int

    unit_price: Decimal

    total_price: Decimal


# ==========================================================
# ORDER SUMMARY
# ==========================================================

class OrderSummary(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    order_number: str

    status: OrderStatus

    total_amount: Decimal

    created_at: datetime


# ==========================================================
# COMPLETE ORDER
# ==========================================================

class OrderResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    order_number: str

    status: OrderStatus

    subtotal: Decimal

    discount: Decimal

    tax: Decimal

    total_amount: Decimal

    created_at: datetime

    items: list[OrderItemResponse]


# ==========================================================
# CHECKOUT RESPONSE
# ==========================================================

class CheckoutResponse(BaseModel):

    order: OrderResponse

    message: str = "Checkout completed successfully."


# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

class UpdateOrderStatusRequest(BaseModel):

    status: OrderStatus


# ==========================================================
# CANCEL ORDER
# ==========================================================

class CancelOrderResponse(BaseModel):

    message: str


# ==========================================================
# ORDER LIST
# ==========================================================

class OrderListResponse(BaseModel):

    items: list[OrderSummary]

    page: int

    page_size: int

    total_items: int

    total_pages: int