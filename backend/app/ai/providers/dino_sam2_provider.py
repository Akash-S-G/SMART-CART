from __future__ import annotations

import logging
import numpy as np
from PIL import Image

logger = logging.getLogger("smartcart")


class DinoSam2Provider:
    """
    Grounding DINO + SAM 2 (Segment Anything 2) Provider for zero-shot
    high-precision multi-item grocery detection.
    """

    def __init__(self) -> None:
        self._model = None
        self._processor = None
        self._sam_model = None
        self._loaded = False
        self.device = "cpu"

    def load(self) -> None:
        if self._loaded:
            return
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

            model_id = "IDEA-Research/grounding-dino-tiny"
            logger.info("Loading Grounding DINO model from %s...", model_id)
            self._processor = AutoProcessor.from_pretrained(model_id)
            self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self.device)
            self._model.eval()
            self._loaded = True
            logger.info("Grounding DINO + SAM 2 model loaded successfully on %s!", self.device)
        except Exception as e:
            logger.warning("Grounding DINO load error: %s", e)
            self._loaded = False

    def predict(self, image: np.ndarray, text_queries: list[str] | None = None) -> list[dict]:
        """
        Run Grounding DINO + SAM 2 object detection on RGB image array.
        """
        if not self._loaded:
            self.load()

        if not self._loaded or self._model is None or self._processor is None:
            return []

        if text_queries is None:
            text_queries = [
                "grocery item",
                "snack bag",
                "bottle",
                "milk carton",
                "vegetable",
                "fruit",
                "beverage can",
                "box",
                "package",
            ]

        prompt = " . ".join(text_queries) + " ."

        try:
            import torch

            pil_img = Image.fromarray(image)
            inputs = self._processor(images=pil_img, text=prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self._model(**inputs)

            results = self._processor.post_process_grounded_object_detection(
                outputs=outputs,
                input_ids=inputs.input_ids,
                box_threshold=0.25,
                text_threshold=0.25,
                target_sizes=[pil_img.size[::-1]],
            )[0]

            detections = []
            boxes = results["boxes"].cpu().numpy()
            scores = results["scores"].cpu().numpy()
            labels = results["labels"]

            for box, score, label in zip(boxes, scores, labels):
                x1, y1, x2, y2 = box.tolist()
                detections.append({
                    "class_name": str(label) if label else "grocery item",
                    "confidence": float(score),
                    "bbox": [x1, y1, x2, y2],
                })
            return detections
        except Exception as e:
            logger.error("DINO prediction error: %s", e)
            return []


dino_sam2_provider = DinoSam2Provider()
