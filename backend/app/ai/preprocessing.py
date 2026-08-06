from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.ai.config import (
    IMAGE_SIZE,
    SUPPORTED_IMAGE_TYPES,
)


class ImagePreprocessor:

    # =====================================================
    # LOAD FROM FILE
    # =====================================================

    def load_file(
        self,
        image_path: str,
    ) -> np.ndarray:

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(image_path)

        if path.suffix.lower() not in SUPPORTED_IMAGE_TYPES:
            raise ValueError("Unsupported image.")

        image = cv2.imread(str(path))

        if image is None:
            raise ValueError("Unable to read image.")

        return image

    # =====================================================
    # LOAD FROM BYTES
    # =====================================================

    def load_bytes(
        self,
        image_bytes: bytes,
    ) -> np.ndarray:

        np_buffer = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )

        image = cv2.imdecode(
            np_buffer,
            cv2.IMREAD_COLOR,
        )

        if image is None:
            raise ValueError("Invalid image bytes.")

        return image

    # =====================================================
    # RGB
    # =====================================================

    def to_rgb(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

    # =====================================================
    # RESIZE
    # =====================================================

    def resize(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        return cv2.resize(
            image,
            (IMAGE_SIZE, IMAGE_SIZE),
        )

    # =====================================================
    # COMPLETE
    # =====================================================

    def preprocess(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        image = self.to_rgb(image)

        image = self.resize(image)

        return image


preprocessor = ImagePreprocessor()