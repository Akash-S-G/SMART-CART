import uuid
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Review(Base):
    """Customer review for a product.

    Real reviews are only stored when sourced from a legally-reusable dataset
    (is_generated=False). When none is available, the seeder generates realistic
    synthetic reviews and marks them is_generated=True so they are never mistaken
    for genuine customer feedback.
    """

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id"),
        index=True,
        nullable=False,
    )

    # Display name of the reviewer (synthetic handles for generated reviews).
    user_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    rating: Mapped[float] = mapped_column(Float, nullable=False)

    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    body: Mapped[str] = mapped_column(Text, nullable=False)

    is_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)

    helpful_count: Mapped[int] = mapped_column(Integer, default=0)

    review_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product = relationship("Product", back_populates="reviews")
