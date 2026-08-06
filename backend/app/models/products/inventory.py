import uuid
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id = mapped_column(
        ForeignKey("products.id"),
        unique=True
    )

    quantity = mapped_column(Integer)

    reorder_level = mapped_column(Integer)

    max_capacity = mapped_column(Integer)

    location = mapped_column(String(100))

    product = relationship(
        "Product",
        back_populates="inventory"
    )

    transactions = relationship(
    "InventoryTransaction",
    back_populates="inventory",
    cascade="all, delete-orphan"
    )