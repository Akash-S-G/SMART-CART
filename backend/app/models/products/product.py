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


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    barcode: Mapped[str | None] = mapped_column(
        String(50),
        unique=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    description: Mapped[str | None] = mapped_column(Text)

    brand: Mapped[str | None] = mapped_column(String(100))

    category_id: Mapped[str] = mapped_column(
        ForeignKey("categories.id")
    )

    unit = mapped_column(
        String(20),
        default="piece"
    )

    is_active = mapped_column(
        Boolean,
        default=True
    )

    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    category = relationship("Category", back_populates="products")

    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False
    )

    price = relationship(
        "ProductPrice",
        back_populates="product",
        uselist=False
    )

    weight = relationship(
        "ProductWeight",
        back_populates="product",
        uselist=False
    )

    detection = relationship(
        "ProductDetection",
        back_populates="product",
        uselist=False
    )
    cart_items = relationship(
    "CartItem",
    back_populates="product"
    )

    order_items = relationship(
    "OrderItem",
    back_populates="product"
    )

    inventory_transactions = relationship(
    "InventoryTransaction",
    back_populates="product"
    )

    reviews = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan"
    )


from app.models.products.categories import Category  # noqa: E402,F401
from app.models.products.product_image import ProductImage  # noqa: E402,F401
from app.models.products.inventory import Inventory  # noqa: E402,F401
from app.models.products.product_price import ProductPrice  # noqa: E402,F401
from app.models.products.product_weight import ProductWeight  # noqa: E402,F401
from app.models.products.prodcut_detection import ProductDetection  # noqa: E402,F401
from app.models.cart.cart_item import CartItem  # noqa: E402,F401
from app.models.order.order_item import OrderItem  # noqa: E402,F401
from app.models.products.inventory_transaction import InventoryTransaction  # noqa: E402,F401
from app.models.products.review import Review  # noqa: E402,F401
