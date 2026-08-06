import asyncio
from typing import Dict, Any, List
from plugins.annotators.base_annotator import BaseAnnotator, AnnotationResult

class GroundingDinoAnnotator(BaseAnnotator):
    """Grounding DINO open-vocabulary detector mock/stub plugin."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.default_confidence = self.config.get("default_confidence", 0.85)

    async def annotate(self, image_path: str, prompt: str) -> List[AnnotationResult]:
        """Simulates bounding box detection around the center of the image."""
        print(f"[GroundingDINO] Running inference on {image_path} with prompt '{prompt}'...")
        # Simulate slight network/GPU processing delay
        await asyncio.sleep(0.1)
        
        # Return a mock bounding box around the center
        return [
            {
                "label": prompt,
                "bbox": [0.5, 0.5, 0.8, 0.8], # Center x, Center y, Width, Height
                "confidence": self.default_confidence
            }
        ]
