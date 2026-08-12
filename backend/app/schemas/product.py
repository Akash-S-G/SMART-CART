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
    barcode: str | None = Field(default=None, max_length=50)
    price: float | None = Field(default=None, ge=0.0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    # Image handling: if image_url is provided the product image is replaced with it.
    image_url: str | None = None


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
        raw_images = getattr(data, "images", None)
        if raw_images:
            if isinstance(raw_images, (list, tuple, set)):
                for item in raw_images:
                    if hasattr(item, "image_url") and item.image_url:
                        images_val.append(str(item.image_url))
                    elif isinstance(item, str) and item:
                        images_val.append(item)
            elif isinstance(raw_images, dict):
                if raw_images.get("thumbnail"):
                    images_val.append(str(raw_images["thumbnail"]))
                if isinstance(raw_images.get("gallery"), list):
                    for g in raw_images["gallery"]:
                        if isinstance(g, str) and g:
                            images_val.append(g)

        if not images_val and meta.get("images"):
            raw_meta = meta.get("images")
            if isinstance(raw_meta, (list, tuple, set)):
                for item in raw_meta:
                    if isinstance(item, str) and item:
                        images_val.append(item)
            elif isinstance(raw_meta, dict):
                if raw_meta.get("thumbnail"):
                    images_val.append(str(raw_meta["thumbnail"]))
                if isinstance(raw_meta.get("gallery"), list):
                    for g in raw_meta["gallery"]:
                        if isinstance(g, str) and g:
                            images_val.append(g)
            elif isinstance(raw_meta, str):
                images_val.append(raw_meta)

        if not images_val:
            name_lower = (getattr(data, "name", "") or "").lower()
            cat_name = ""
            if getattr(data, "category", None) and hasattr(data.category, "name"):
                cat_name = (data.category.name or "").lower()

            if any(k in name_lower for k in ['parle', 'biscuit', 'cookie', 'marie', 'good day', 'oreo', 'monaco', '50-50', 'crackjack']):
                images_val = ["https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['kitkat', 'dairy milk', 'chocolate', 'munch', 'perk', 'snickers', '5 star', 'silk', 'bournville']):
                images_val = ["https://images.unsplash.com/photo-1511381939415-e44015466834?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['milk', 'butter', 'cheese', 'paneer', 'curd', 'dahi', 'ghee', 'cream']) or 'dairy' in cat_name:
                images_val = ["https://images.unsplash.com/photo-1563636619-e9143da7973b?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['apple', 'banana', 'orange', 'mango', 'grapes', 'strawberry', 'pomegranate']) or 'fruit' in cat_name:
                images_val = ["https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['tomato', 'potato', 'onion', 'carrot', 'cucumber', 'spinach', 'chilli']) or 'veg' in cat_name:
                images_val = ["https://images.unsplash.com/photo-1597362925123-77861d3fbac7?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['juice', 'coke', 'pepsi', 'sprite', 'fanta', 'thums', 'water', 'soda', 'tea', 'coffee']) or 'beverage' in cat_name or 'drink' in cat_name:
                images_val = ["https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=600&auto=format&fit=crop&q=80"]
            elif any(k in name_lower for k in ['chips', 'kurkure', 'lays', 'bingo', 'namkeen', 'bhujia', 'snack']) or 'snack' in cat_name:
                images_val = ["https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600&auto=format&fit=crop&q=80"]
            else:
                images_val = ["https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&auto=format&fit=crop&q=80"]

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


class BarcodeResponse(BaseModel):
    barcode: str
    image: str  # data URI (SVG) of the rendered barcode


class BulkUploadResult(BaseModel):
    created: int
    failed: int
    errors: list[str]
