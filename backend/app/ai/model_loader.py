from __future__ import annotations

from pathlib import Path
from threading import Lock

from ultralytics import YOLO

from app.ai.config import MODEL_PATH


class ModelLoader:
    """
    Singleton responsible for loading and serving
    the YOLO model.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):

        if cls._instance is None:

            with cls._lock:

                if cls._instance is None:
                    cls._instance = super().__new__(cls)

                    cls._instance._model = None
                    cls._instance._loaded = False

        return cls._instance

    # =====================================================
    # LOAD MODEL
    # =====================================================

    def load(self):

        if self._loaded:
            return

        if not Path(MODEL_PATH).exists():
            raise FileNotFoundError(
                f"YOLO model not found: {MODEL_PATH}"
            )

        self._model = YOLO(str(MODEL_PATH))

        self._loaded = True

    # =====================================================
    # GET MODEL
    # =====================================================

    def get_model(self) -> YOLO:

        if not self._loaded:
            self.load()

        return self._model

    # =====================================================
    # STATUS
    # =====================================================

    def is_loaded(self) -> bool:

        return self._loaded

    # =====================================================
    # WARMUP
    # =====================================================

    def warmup(self):

        model = self.get_model()

        model.predict(
            source="https://ultralytics.com/images/bus.jpg",
            verbose=False,
        )


model_loader = ModelLoader()