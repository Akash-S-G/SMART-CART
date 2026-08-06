import uuid
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from sqlalchemy import Numeric

class ProductPrice(Base):
    __tablename__ = "product_prices"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id = mapped_column(
        ForeignKey("products.id"),
        unique=True
    )

    price = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    gst_percentage = mapped_column(
        Numeric(5,2),
        default=0
    )

    discount_percentage = mapped_column(
        Numeric(5,2),
        default=0
    )

    product = relationship(
        "Product",
        back_populates="price"
    )