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
class ProductImage(Base):
    __tablename__ = "product_images"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    product_id = mapped_column(
        ForeignKey("products.id")
    )

    image_url = mapped_column(Text)

    image_type = mapped_column(
        String(30),
        default="training"
    )

    is_primary = mapped_column(
        Boolean,
        default=False
    )

    # Content hash (sha256 hex) of the image bytes. Used to guarantee the same
    # image is never stored twice for a product (de-duplication across runs).
    content_hash = mapped_column(
        String(64),
        nullable=True,
        index=True
    )

    product = relationship(
        "Product",
        back_populates="images"
    )