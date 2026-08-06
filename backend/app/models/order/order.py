import uuid
from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "confirmed",
            "paid",
            "processing",
            "shipped",
            "delivered",
            "completed",
            "cancelled",
            "refunded",
            name="order_status",
            create_constraint=False,
        ),
        default="pending",
        nullable=False,
    )

    # Shipping / tracking info
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_delivery: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    subtotal: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    discount: Mapped[float] = mapped_column(
        Numeric(10,2),
        default=0
    )

    tax: Mapped[float] = mapped_column(
        Numeric(10,2),
        default=0
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="orders"
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )