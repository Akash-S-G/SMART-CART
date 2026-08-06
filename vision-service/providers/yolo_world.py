from typing import List, Any
from interfaces.detector import DetectorInterface
from core.context import Detection
from core.models import ProviderMetadata
from ultralytics import YOLOWorld
from PIL import Image
import numpy as np

class YOLOWorldDetector(DetectorInterface):
    def __init__(self, model_size: str = "yolov8s-worldv2.pt", confidence: float = 0.25):
        # YOLO automatically downloads the weights if they don't exist
        from ultralytics import YOLO
        if "world" in model_size:
            self.model = YOLOWorld(model_size)
            self.model.set_classes(["product", "package", "bottle", "box"])
        else:
            self.model = YOLO(model_size)
        self.confidence = confidence

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name="yolo-world", version="8.x", capabilities={"classes": ["product", "package", "bottle", "box"]})
        
    def detect_batch(self, images: List[Any]) -> List[List[Detection]]:
        # Run batch inference
        results = self.model(images, conf=self.confidence, verbose=False)
        
        batch_detections = []
        for result in results:
            frame_detections = []
            
            # Extract bounding boxes
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes[i].xyxy[0].cpu().numpy().tolist() # [x1, y1, x2, y2]
                conf = float(boxes[i].conf[0].cpu().numpy())
                cls_id = int(boxes[i].cls[0].cpu().numpy())
                cls_name = self.model.names[cls_id]
                
                det = Detection(bbox=box, confidence=conf, class_name=cls_name)
                frame_detections.append(det)
                
            batch_detections.append(frame_detections)
            
        return batch_detections
