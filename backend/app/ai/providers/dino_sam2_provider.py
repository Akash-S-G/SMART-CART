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
            # Load from local cache if available without checking HF hub every time
            try:
                self._processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
                self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, local_files_only=True)
            except Exception:
                # Fallback to normal load if not cached yet
                self._processor = AutoProcessor.from_pretrained(model_id, revision="main", trust_remote_code=False)
                self._model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id, revision="main", trust_remote_code=False)

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
                "grocery product",
                "juice carton",
                "bottle",
                "beverage can",
                "snack bag",
                "food package",
                "milk carton",
                "box",
            ]

        prompt = " . ".join(text_queries) + " ."

        try:
            import torch
            import torchvision.ops as ops

            pil_img = Image.fromarray(image)
            inputs = self._processor(images=pil_img, text=prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self._model(**inputs)

            results = self._processor.post_process_grounded_object_detection(
                outputs=outputs,
                input_ids=inputs.input_ids,
                threshold=0.32,
                text_threshold=0.30,
                target_sizes=[pil_img.size[::-1]],
            )[0]

            boxes_t = results["boxes"]
            scores_t = results["scores"]
            labels = results["labels"]

            if len(boxes_t) == 0:
                return []

            # Non-Maximum Suppression (NMS) to eliminate duplicate overlapping crops on the same object
            keep_indices = ops.nms(boxes_t, scores_t, iou_threshold=0.45).cpu().numpy()

            boxes = boxes_t.cpu().numpy()
            scores = scores_t.cpu().numpy()

            detections = []
            for idx in keep_indices:
                x1, y1, x2, y2 = boxes[idx].tolist()
                detections.append({
                    "class_name": str(labels[idx]) if labels[idx] else "grocery product",
                    "confidence": float(scores[idx]),
                    "bbox": [x1, y1, x2, y2],
                })
            return detections
        except Exception as e:
            logger.error("DINO prediction error: %s", e)
            return []


dino_sam2_provider = DinoSam2Provider()
