from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime


class CreateReviewRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)
    title: str | None = None
    body: str = Field(..., min_length=5)


class ReviewResponse(BaseModel):
    id: str
    product_id: str
    user_name: str | None
    rating: float
    title: str | None
    body: str
    verified_purchase: bool
    helpful_count: int
    review_date: datetime
    is_generated: bool

    class Config:
        from_attributes = True
