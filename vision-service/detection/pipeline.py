from typing import List, Any
from interfaces.detector import DetectorInterface
from core.context import RecognitionContext

class DetectionPipeline:
    def __init__(self, detector: DetectorInterface):
        self.detector = detector

    def process_batch(self, images: List[Any], camera_id: str = None) -> List[List[RecognitionContext]]:
        """
        Runs the batch detector and wraps each detection in a RecognitionContext.
        """
        batch_detections = self.detector.detect_batch(images)
        
        batch_contexts = []
        for img, detections in zip(images, batch_detections):
            contexts = []
            for det in detections:
                # In reality, we'd crop the image based on det.bbox here
                cropped_img = img  # Mock crop
                ctx = RecognitionContext(
                    image=cropped_img,
                    detection=det,
                    camera_id=camera_id
                )
                contexts.append(ctx)
            batch_contexts.append(contexts)
            
        return batch_contexts
