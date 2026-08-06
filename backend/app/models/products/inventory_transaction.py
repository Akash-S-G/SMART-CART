import uuid
from enum import Enum

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SqlEnum,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class InventoryTransactionType(str, Enum):
    RESTOCK = "restock"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    inventory_id: Mapped[str] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        SqlEnum(InventoryTransactionType),
        nullable=False
    )

    quantity_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    quantity_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    quantity_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    reference_type: Mapped[str | None] = mapped_column(
        String(50)
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(36)
    )

    remarks: Mapped[str | None] = mapped_column(
        String(255)
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    inventory = relationship(
        "Inventory",
        back_populates="transactions"
    )

    product = relationship(
        "Product",
        back_populates="inventory_transactions"
    )