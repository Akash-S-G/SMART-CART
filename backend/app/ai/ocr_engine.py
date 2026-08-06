"""
OCR Engine — wraps EasyOCR to extract text from image crops.

The reader is lazily initialized on first use so the server can start
fast even if the EasyOCR model weights have not been downloaded yet.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

logger = logging.getLogger("smartcart")

if TYPE_CHECKING:
    import easyocr as _easyocr_mod


class OCREngine:
    """Lazy-loaded EasyOCR reader."""

    _reader: "_easyocr_mod.Reader | None" = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _get_reader(self) -> "_easyocr_mod.Reader":
        if self._reader is None:
            try:
                import easyocr  # type: ignore
                logger.info("Loading EasyOCR English reader...")
                self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                logger.info("EasyOCR reader loaded.")
            except Exception as exc:
                logger.error("Could not load EasyOCR: %s", exc)
                raise
        return self._reader

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract_text(
        self,
        image: np.ndarray,
        min_confidence: float = 0.4,
    ) -> list[str]:
        """
        Extract visible text strings from *image* (BGR or RGB numpy array).

        Returns a list of text tokens with confidence >= min_confidence,
        sorted by descending confidence.
        """
        try:
            reader = self._get_reader()
            results = reader.readtext(image, detail=1, paragraph=False)
            # results → list of ([bbox], text, confidence)
            tokens = [
                text.strip()
                for (_bbox, text, conf) in results
                if conf >= min_confidence and text.strip()
            ]
            return tokens
        except Exception as exc:
            logger.warning("OCR extraction failed: %s", exc)
            return []


# Module-level singleton
ocr_engine = OCREngine()
