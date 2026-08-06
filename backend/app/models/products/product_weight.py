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

class ProductWeight(Base):
    __tablename__ = "product_weights"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id = mapped_column(
        ForeignKey("products.id"),
        unique=True
    )

    expected_weight = mapped_column(
        Numeric(10,2)
    )

    tolerance = mapped_column(
        Numeric(10,2),
        default=5
    )

    unit = mapped_column(
        String(20),
        default="grams"
    )

    product = relationship(
        "Product",
        back_populates="weight"
    )