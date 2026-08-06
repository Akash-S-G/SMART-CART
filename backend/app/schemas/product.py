import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=50)
    barcode: str | None = Field(default=None, max_length=50)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    category_id: str = Field(min_length=1)
    initial_stock: int = Field(default=0, ge=0)
    price: float = Field(default=0.0, ge=0.0)
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    brand: str | None = Field(default=None, max_length=100)
    category_id: str | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    barcode: str | None
    name: str
    description: str | None
    brand: str | None
    category_id: str
    is_active: bool
    price: float | None = None
    compare_at_price: float | None = None
    stock: int | None = None
    rating: float | None = None
    review_count: int | None = None
    images: list[str] | None = None
    tags: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def serialize_product(cls, data):
        if not hasattr(data, "id"):
            return data

        price_val = None
        compare_at_price_val = None
        if getattr(data, "price", None):
            price_val = float(data.price.price)
            if getattr(data.price, "discount_percentage", None) and data.price.discount_percentage > 0:
                original = price_val / (1 - float(data.price.discount_percentage) / 100)
                compare_at_price_val = round(original, 2)

        stock_val = None
        if getattr(data, "inventory", None):
            stock_val = data.inventory.quantity

        meta = getattr(data, "metadata_", {}) or {}
        rating_val = meta.get("rating", 4.5)
        review_count_val = meta.get("review_count", 150)
        tags_val = meta.get("tags", [])

        images_val = []
        if getattr(data, "images", None):
            images_val = [img.image_url for img in data.images if img.image_url]
        if not images_val:
            images_val = meta.get("images", [])

        return {
            "id": data.id,
            "sku": data.sku,
            "barcode": data.barcode,
            "name": data.name,
            "description": data.description,
            "brand": data.brand,
            "category_id": data.category_id,
            "is_active": data.is_active,
            "price": price_val,
            "compare_at_price": compare_at_price_val,
            "stock": stock_val,
            "rating": rating_val,
            "review_count": review_count_val,
            "images": images_val,
            "tags": tags_val,
        }


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)
