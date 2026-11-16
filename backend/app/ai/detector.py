from __future__ import annotations

import logging
import numpy as np

from app.ai.preprocessing import preprocessor
from app.ai.providers.dino_sam2_provider import dino_sam2_provider
from app.ai.providers.yolo_provider import yolo_provider
from app.ai.schemas import Detection

logger = logging.getLogger("smartcart")


class Detector:
    """
    Detection pipeline — priority order:

    1. best.pt (custom YOLO with 718 SmartCart-specific product classes)
       → Returns exact product names as class labels → matcher does direct lookup.

    2. Grounding DINO (zero-shot) used ONLY as a bounding-box provider
       when best.pt finds nothing.  DINO labels are IGNORED for matching —
       the detection_service runs OCR on each DINO crop and matches via text.

    This avoids the previous failure where DINO generic labels
    ('milk carton', 'vegetable') fuzzy-matched the wrong DB products.
    """

    def detect(
        self,
        image: np.ndarray,
    ) -> list[Detection]:

        image = preprocessor.preprocess(image)

        # ── 1. Primary: custom best.pt (718 specific SmartCart product classes) ──
        yolo_result = yolo_provider.predict(image)
        yolo_detections: list[Detection] = []
        if yolo_result is not None and hasattr(yolo_result, "boxes") and yolo_result.boxes is not None:
            for box in yolo_result.boxes:
                cls = int(box.cls.item())
                conf = float(box.conf.item())
                yolo_detections.append(
                    Detection(
                        class_id=cls,
                        class_name=yolo_result.names[cls],
                        confidence=conf,
                        bbox=box.xyxy[0].tolist(),
                    )
                )

        if yolo_detections:
            logger.info("[Detector] best.pt found %d detection(s) — using YOLO results.", len(yolo_detections))
            return yolo_detections

        # ── 2. Fallback: Grounding DINO for bounding-box discovery ──────────────
        # Note: DINO class labels are intentionally generic.
        # detection_service will run OCR on each crop and match via text — the
        # DINO label is only used as a last-resort display label, not for DB matching.
        logger.info("[Detector] best.pt found 0 detections — falling back to Grounding DINO for bounding boxes.")
        dino_results = dino_sam2_provider.predict(image)
        if dino_results:
            detections = []
            for idx, d in enumerate(dino_results):
                detections.append(
                    Detection(
                        class_id=idx,
                        # Mark label so detection_service knows to skip YOLO-class matching
                        class_name="__dino__:" + d["class_name"],
                        confidence=d["confidence"],
                        bbox=d["bbox"],
                    )
                )
            logger.info("[Detector] Grounding DINO found %d bounding box(es).", len(detections))
            return detections

        logger.info("[Detector] No detections from either provider.")
        return []


detector = Detector()
