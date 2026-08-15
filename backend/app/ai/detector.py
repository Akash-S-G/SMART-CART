from __future__ import annotations

import numpy as np

from app.ai.preprocessing import preprocessor
from app.ai.providers.dino_sam2_provider import dino_sam2_provider
from app.ai.providers.yolo_provider import yolo_provider
from app.ai.schemas import Detection


class Detector:

    def detect(
        self,
        image: np.ndarray,
    ) -> list[Detection]:

        image = preprocessor.preprocess(image)

        # 1. Primary: Grounding DINO + SAM 2 zero-shot multi-item detector
        dino_results = dino_sam2_provider.predict(image)
        if dino_results:
            detections = []
            for idx, d in enumerate(dino_results):
                detections.append(
                    Detection(
                        class_id=idx,
                        class_name=d["class_name"],
                        confidence=d["confidence"],
                        bbox=d["bbox"],
                    )
                )
            return detections

        # 2. Fallback: YOLO provider
        result = yolo_provider.predict(image)
        detections = []
        if hasattr(result, "boxes") and result.boxes is not None:
            for box in result.boxes:
                cls = int(box.cls.item())
                detections.append(
                    Detection(
                        class_id=cls,
                        class_name=result.names[cls],
                        confidence=float(box.conf.item()),
                        bbox=box.xyxy[0].tolist(),
                    )
                )

        return detections


detector = Detector()