"""
DetectionService — orchestrates YOLO detection + OCR + fuzzy product matching.

Pipeline per detected bounding box
  1. YOLO gives us [class_name, confidence, bbox]
  2. Crop the bounding box region from the original image
  3. Run EasyOCR on the crop to extract text tokens
  4. Try OCR-based fuzzy match first (most accurate for labeled packaging)
  5. Fall back to YOLO class-name fuzzy match if OCR yields no result
  6. Final fallback: first active product in DB
"""
from __future__ import annotations

import logging
import time

import numpy as np
from sqlalchemy.orm import Session

from app.ai.detector import detector
from app.ai.matcher import ProductMatcher
from app.ai.ocr_engine import ocr_engine

from app.ai.schemas import (
    DetectionResult,
    DetectionResponse,
    DetectionBox,
)

from app.services.cart_service import CartService

logger = logging.getLogger("smartcart")


class DetectionService:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.matcher = ProductMatcher(db)
        self.cart = CartService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _crop(image: np.ndarray, bbox: list[float]) -> np.ndarray:
        """Crop the bounding-box region (xyxy) from *image*."""
        x1, y1, x2, y2 = (int(v) for v in bbox)
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return image  # degenerate box — return whole image
        return image[y1:y2, x1:x2]

    # ------------------------------------------------------------------
    # DETECT ONLY
    # ------------------------------------------------------------------

    def detect(
        self,
        image: np.ndarray,
    ) -> DetectionResponse:

        t0 = time.perf_counter()
        detections = detector.detect(image)
        h, w = image.shape[:2]

        results: list[DetectionResult] = []

        for idx, detection in enumerate(detections):
            x1, y1, x2, y2 = detection.bbox

            # Detect whether this box came from DINO (bounding-box-only fallback)
            is_dino_box = detection.class_name.startswith("__dino__:")
            display_label = detection.class_name[len("__dino__:"):] if is_dino_box else detection.class_name

            # ── 1. Crop bounding box ──────────────────────────────────
            crop = self._crop(image, detection.bbox)

            # ── 2. OCR on crop ────────────────────────────────────────
            ocr_tokens = ocr_engine.extract_text(crop)
            source_tag = "DINO-box" if is_dino_box else "YOLO"
            logger.info(
                "[AI-Pipeline] Crop #%d | Source: %s | Label: '%s' | Confidence: %.2f | OCR tokens: %s",
                idx, source_tag, display_label, detection.confidence, ocr_tokens,
            )

            # ── 3. OCR-based fuzzy match (highest priority always) ────
            product = None
            if ocr_tokens:
                product = self.matcher.ocr_match(ocr_tokens, crop)
                if product:
                    logger.info("[AI-Pipeline] Crop #%d matched via OCR -> Product: '%s' (SKU: %s)", idx, product.name, product.sku)

            # ── 4a. best.pt class-name direct match (YOLO-sourced boxes only) ──
            # best.pt labels ARE specific product names (e.g. "Amul Gold Full Cream Milk")
            # so attempt a direct DB lookup — no confidence gating needed.
            if product is None and not is_dino_box:
                product = self.matcher.best_match(display_label)
                if product:
                    logger.info(
                        "[AI-Pipeline] Crop #%d matched via best.pt class '%s' (conf: %.2f) -> Product: '%s'",
                        idx, display_label, detection.confidence, product.name,
                    )

            # ── 4b. DINO box: skip class-name matching (labels are generic) ────
            # For DINO-sourced boxes we rely exclusively on OCR; a generic label
            # like 'milk carton' must NOT be fuzzy-matched to a specific product.

            # ── 5. No match ───────────────────────────────────────────
            if product is None:
                logger.info(
                    "[AI-Pipeline] Crop #%d (source: %s, label: '%s', conf: %.2f) — no catalog match found.",
                    idx, source_tag, display_label, detection.confidence,
                )

            label_name = product.name if product else display_label

            bbox_box = DetectionBox(
                label=label_name,
                confidence=detection.confidence,
                x=x1,
                y=y1,
                width=x2 - x1,
                height=y2 - y1,
            )

            results.append(
                DetectionResult(
                    request_id=f"det-{idx}",
                    object_type=label_name,
                    confidence=detection.confidence,
                    bbox=bbox_box,
                    matched_product=product,
                )
            )

        inference_ms = (time.perf_counter() - t0) * 1000

        return DetectionResponse(
            detections=results,
            inference_time_ms=round(inference_ms, 2),
            image_width=w,
            image_height=h,
        )

    # ------------------------------------------------------------------
    # PROCESS REMOTE MICROSERVICE DETECTIONS
    # ------------------------------------------------------------------

    def process_remote_detections(
        self,
        remote_detections: list[dict],
        image_width: int,
        image_height: int,
        inference_time_ms: float = 0.0,
    ) -> DetectionResponse:
        results: list[DetectionResult] = []

        for idx, det in enumerate(remote_detections):
            bbox_dict = det.get("bounding_box", {})
            x = float(bbox_dict.get("x", 0))
            y = float(bbox_dict.get("y", 0))
            width = float(bbox_dict.get("width", 0))
            height = float(bbox_dict.get("height", 0))

            raw_conf = float(det.get("confidence", 0.0))
            conf = raw_conf / 100.0 if raw_conf > 1.0 else raw_conf

            ocr_text = det.get("ocr_text", "").strip()
            class_name = det.get("class_name") or det.get("object_type") or f"Item {det.get('class_id', idx)}"

            # 1. Match via OCR tokens
            product = None
            if ocr_text:
                tokens = ocr_text.split()
                product = self.matcher.ocr_match(tokens)
                if product:
                    logger.info("[AI-Remote-Pipeline] Detection #%d matched via OCR '%s' -> Product: '%s'", idx, ocr_text, product.name)

            # 2. Match via class name
            if product is None and class_name:
                product = self.matcher.best_match(class_name)
                if product:
                    logger.info("[AI-Remote-Pipeline] Detection #%d matched via Class Name '%s' -> Product: '%s'", idx, class_name, product.name)

            # 3. Fallback match
            if product is None:
                product = self.matcher.fallback_match()
                logger.info("[AI-Remote-Pipeline] Detection #%d fell back to default product -> '%s'", idx, product.name if product else "None")

            label_name = product.name if product else class_name

            bbox_box = DetectionBox(
                label=label_name,
                confidence=round(conf, 4),
                x=x,
                y=y,
                width=width,
                height=height,
            )

            results.append(
                DetectionResult(
                    request_id=f"det-{idx}",
                    object_type=label_name,
                    confidence=round(conf, 4),
                    bbox=bbox_box,
                    matched_product=product,
                )
            )

        return DetectionResponse(
            detections=results,
            inference_time_ms=round(inference_time_ms, 2),
            image_width=image_width,
            image_height=image_height,
        )

    # ------------------------------------------------------------------
    # DETECT + ADD TO CART
    # ------------------------------------------------------------------

    def detect_and_add(
        self,
        image: np.ndarray,
        user_id: str,
    ) -> DetectionResponse:

        response = self.detect(image)

        for item in response.detections:
            if item.matched_product is None:
                continue
            try:
                self.cart.add_product(
                    user_id=user_id,
                    product_id=str(item.matched_product.id),
                    quantity=1,
                )
            except Exception as exc:
                logger.warning(
                    "Could not add product %s to cart: %s",
                    item.matched_product.id, exc,
                )

        return response