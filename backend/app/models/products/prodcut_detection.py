import uuid
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
class ProductDetection(Base):
    __tablename__ = "product_detection"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id = mapped_column(
        ForeignKey("products.id"),
        unique=True
    )

    model_name = mapped_column(
        String(100)
    )

    class_name = mapped_column(
        String(100)
    )

    confidence_threshold = mapped_column(
        Numeric(5,2),
        default=0.80
    )

    embeddings = mapped_column(JSON)

    product = relationship(
        "Product",
        back_populates="detection"
    )
