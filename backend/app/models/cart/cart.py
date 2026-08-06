import uuid
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,          # One active cart per user
        index=True,
    )

    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0
    )

    discount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0
    )

    tax: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0
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
        back_populates="cart"
    )

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )