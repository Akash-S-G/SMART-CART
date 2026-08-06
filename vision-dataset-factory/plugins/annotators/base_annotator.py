from abc import ABC, abstractmethod
from typing import Dict, Any, List, TypedDict

class AnnotationResult(TypedDict):
    label: str
    bbox: List[float] # [x_center, y_center, width, height] normalized
    confidence: float

class BaseAnnotator(ABC):
    """Abstract base class for all pluggable annotation engines."""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    async def annotate(self, image_path: str, prompt: str) -> List[AnnotationResult]:
        """Perform object detection/segmentation on the given image path.
        
        Args:
            image_path: Absolute local path to the image.
            prompt: Text prompt for open-vocabulary detection (e.g. "product box", "coca cola").
            
        Returns:
            A list of AnnotationResult dictionaries containing label, bounding box, and confidence.
        """
        pass
