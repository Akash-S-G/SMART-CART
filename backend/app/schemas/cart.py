from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==========================================================
# REQUESTS
# ==========================================================

class AddToCartRequest(BaseModel):

    product_id: UUID

    quantity: int = Field(
        default=1,
        ge=1,
    )


class UpdateCartRequest(BaseModel):

    quantity: int = Field(
        ge=1,
    )


# ==========================================================
# CART ITEM
# ==========================================================

class CartItemResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    product_id: UUID
    product_name: str
    sku: str
    image_url: str | None = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    available_stock: int

    @model_validator(mode="before")
    @classmethod
    def resolve_attributes(cls, data):
        if isinstance(data, dict):
            return data
        product = getattr(data, "product", None)
        inventory = getattr(product, "inventory", None) if product else None
        image_url = None
        if product and getattr(product, "images", None):
            imgs = product.images
            if isinstance(imgs, (list, tuple, set)) and len(imgs) > 0:
                primary_img = next((img for img in imgs if getattr(img, "is_primary", False)), None)
                if not primary_img:
                    primary_img = imgs[0]
                if hasattr(primary_img, "image_url"):
                    image_url = primary_img.image_url
                elif isinstance(primary_img, str):
                    image_url = primary_img
            elif isinstance(imgs, dict):
                image_url = imgs.get("thumbnail") or (imgs.get("gallery")[0] if isinstance(imgs.get("gallery"), list) and imgs["gallery"] else None)
        return {
            "id": data.id,
            "product_id": data.product_id,
            "product_name": product.name if product else "Unknown Product",
            "sku": product.sku if product else "N/A",
            "image_url": image_url,
            "quantity": data.quantity,
            "unit_price": data.unit_price,
            "total_price": data.total_price,
            "available_stock": inventory.quantity if inventory else 0,
        }


# ==========================================================
# CART SUMMARY
# ==========================================================

class CartSummary(BaseModel):

    subtotal: Decimal

    discount: Decimal

    tax: Decimal

    total_amount: Decimal

    total_items: int

    total_quantity: int


# ==========================================================
# CART RESPONSE
# ==========================================================

class CartResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    user_id: UUID
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse]
    summary: CartSummary

    @model_validator(mode="before")
    @classmethod
    def resolve_summary(cls, data):
        if isinstance(data, dict):
            return data
        
        items = getattr(data, "items", []) or []
        total_items = len(items)
        total_quantity = sum(item.quantity for item in items)
        
        summary = {
            "subtotal": data.subtotal,
            "discount": data.discount,
            "tax": data.tax,
            "total_amount": data.total_amount,
            "total_items": total_items,
            "total_quantity": total_quantity,
        }
        
        return {
            "id": data.id,
            "user_id": data.user_id,
            "status": "active",
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "items": items,
            "summary": summary,
        }


# ==========================================================
# MESSAGE RESPONSE
# ==========================================================

class MessageResponse(BaseModel):

    message: str