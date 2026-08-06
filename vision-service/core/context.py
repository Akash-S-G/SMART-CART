from dataclasses import dataclass
from typing import Optional, Any
import time

@dataclass
class Detection:
    bbox: list[float]  # [x1, y1, x2, y2]
    confidence: float
    class_name: str

@dataclass
class RecognitionContext:
    image: Any  # PIL Image or numpy array representing the cropped product
    detection: Detection
    timestamp: float = time.time()
    camera_id: Optional[str] = None
    cart_id: Optional[str] = None
    track_id: Optional[str] = None  # For temporal tracking across frames
