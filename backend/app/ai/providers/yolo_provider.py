from __future__ import annotations

from ultralytics.engine.results import Results

from app.ai.config import (
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    MAX_DETECTIONS,
)

from app.ai.model_loader import (
    model_loader,
)


class YOLOProvider:

    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = model_loader.get_model()
        return self._model

    # =====================================================
    # SINGLE IMAGE
    # =====================================================

    def predict(
        self,
        image,
    ) -> Results:

        result = self.model.predict(

            source=image,

            conf=CONFIDENCE_THRESHOLD,

            iou=IOU_THRESHOLD,

            max_det=MAX_DETECTIONS,

            verbose=False,

        )

        return result[0]

    # =====================================================
    # BATCH
    # =====================================================

    def predict_batch(
        self,
        images,
    ):

        return self.model.predict(

            source=images,

            conf=CONFIDENCE_THRESHOLD,

            iou=IOU_THRESHOLD,

            verbose=False,

        )


yolo_provider = YOLOProvider()