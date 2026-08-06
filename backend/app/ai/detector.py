from __future__ import annotations

import numpy as np

from ultralytics.engine.results import Results

from app.ai.preprocessing import preprocessor
from app.ai.providers.yolo_provider import yolo_provider
from app.ai.schemas import Detection


class Detector:

    def detect(
        self,
        image: np.ndarray,
    ) -> list[Detection]:

        image = preprocessor.preprocess(image)

        result: Results = yolo_provider.predict(image)

        detections = []

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