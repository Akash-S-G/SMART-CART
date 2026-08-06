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
class Category(Base):
    __tablename__ = "categories"

    id = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description = mapped_column(Text)

    products = relationship(
        "Product",
        back_populates="category"
    )