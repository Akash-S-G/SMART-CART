from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# REQUEST
# ============================================================

class DetectionRequest(BaseModel):
    """
    Used when frontend sends an image path.
    """

    image_path: str


# ============================================================
# SINGLE DETECTION
# ============================================================

class Detection(BaseModel):

    class_name: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    bbox: list[float]

    class_id: int


# ============================================================
# PRODUCT MATCH
from app.schemas.product import ProductResponse

class DetectionBox(BaseModel):
    label: str
    confidence: float
    x: float
    y: float
    width: float
    height: float

# ============================================================
# DETECTION RESULT
# ============================================================

class DetectionResult(BaseModel):
    request_id: str
    object_type: str
    confidence: float
    bbox: DetectionBox | None = None
    matched_product: ProductResponse | None = None


# ============================================================
# DETECTION RESPONSE
# ============================================================

class DetectionResponse(BaseModel):

    detections: list[DetectionResult]

    inference_time_ms: float

    image_width: int

    image_height: int


# ============================================================
# CART ADD RESPONSE
# ============================================================

class AddDetectedProductResponse(BaseModel):

    success: bool

    message: str

    product: ProductMatch | None = None


# ============================================================
# HEALTH
# ============================================================

class AIHealthResponse(BaseModel):

    model_loaded: bool

    device: str

    model_name: str