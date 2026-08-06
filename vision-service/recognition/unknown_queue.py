import os
import json
import uuid
from typing import List
from core.context import RecognitionContext
from core.models import ProductCandidate

class UnknownProductQueue:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        
    def enqueue(self, context: RecognitionContext, candidates: List[ProductCandidate]):
        """
        Saves the crop and context metadata for manual review and later dataset training.
        """
        item_id = uuid.uuid4().hex
        
        # Save image (mocked as text save if not real image)
        img_path = os.path.join(self.storage_path, f"{item_id}.jpg")
        with open(img_path, "w") as f:
            f.write(str(context.image))
            
        # Save metadata
        meta = {
            "timestamp": context.timestamp,
            "camera_id": context.camera_id,
            "bbox": context.detection.bbox,
            "candidates": [c.model_dump() for c in candidates]
        }
        
        meta_path = os.path.join(self.storage_path, f"{item_id}.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f)
