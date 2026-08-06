import uuid
from sqlalchemy import (
    String,
    Integer,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    cart_id: Mapped[str] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    total_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    cart = relationship(
        "Cart",
        back_populates="items"
    )

    product = relationship(
    "Product",
    back_populates="cart_items"
    )