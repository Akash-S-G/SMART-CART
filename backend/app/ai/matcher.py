"""
ProductMatcher — Hybrid YOLO class-name + OCR fuzzy text matcher.

Matching priority (highest → lowest):
  1. Exact product name lookup
  2. Case-insensitive partial name search (DB ILIKE)
  3. Fuzzy string match against every product name/brand (RapidFuzz)
  4. OCR text tokens fuzzy-matched against product names
  5. Fallback: first active product in DB
"""
from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository
from app.models.products.product import Product

logger = logging.getLogger("smartcart")

# ---------------------------------------------------------------------------
# Optional imports — degrade gracefully if not installed
# ---------------------------------------------------------------------------
try:
    from rapidfuzz import fuzz, process as rf_process  # type: ignore
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz not installed — fuzzy matching disabled.")


# Minimum similarity score (0-100) for RapidFuzz matches
_FUZZY_THRESHOLD = 65


class ProductMatcher:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _all_active_products(self) -> list[Product]:
        return (
            self.db.query(Product)
            .filter(Product.is_active == True)  # noqa: E712
            .all()
        )

    def _fuzzy_best(
        self,
        query: str,
        products: list[Product],
        threshold: int = _FUZZY_THRESHOLD,
    ) -> Product | None:
        """Return the product whose name is most similar to *query*."""
        if not _RAPIDFUZZ_AVAILABLE or not products or not query.strip():
            return None

        names = [p.name for p in products]
        result = rf_process.extractOne(
            query,
            names,
            scorer=fuzz.WRatio,
            score_cutoff=threshold,
        )
        if result is None:
            return None
        _matched_name, _score, idx = result
        logger.debug(
            "Fuzzy matched '%s' → '%s' (score=%s)", query, _matched_name, _score
        )
        return products[idx]

    # ------------------------------------------------------------------
    # Public matching API
    # ------------------------------------------------------------------

    def match(self, label: str) -> Product | None:
        """Exact product name lookup."""
        return self.products.get_by_name(label)

    def match_ignore_case(self, label: str) -> Product | None:
        """Case-insensitive partial name search (DB ILIKE)."""
        return self.products.search_name(label)

    def best_match(self, label: str) -> Product | None:
        """
        Try exact → ilike → fuzzy matching on the YOLO class label.
        """
        product = self.match(label)
        if product:
            return product

        product = self.match_ignore_case(label)
        if product:
            return product

        # Fuzzy match the YOLO class label against all product names
        all_prods = self._all_active_products()
        return self._fuzzy_best(label, all_prods)

    def ocr_match(
        self,
        ocr_tokens: list[str],
        image_crop: np.ndarray | None = None,
    ) -> Product | None:
        """
        Match OCR text tokens against product names using fuzzy scoring.

        *ocr_tokens* — list of strings extracted from the image crop by
                        EasyOCR.
        *image_crop* — the raw crop (unused in base impl, reserved for
                       embedding extensions).

        Returns the best-matching product or None.
        """
        if not ocr_tokens:
            return None

        all_prods = self._all_active_products()
        if not all_prods:
            return None

        best_product: Product | None = None
        best_score: float = 0.0

        combined_text = " ".join(ocr_tokens)

        for token in [combined_text] + ocr_tokens:
            product = self._fuzzy_best(token, all_prods, threshold=_FUZZY_THRESHOLD)
            if product is not None:
                # Score the combined text to pick the highest-scoring one
                score = fuzz.WRatio(token, product.name) if _RAPIDFUZZ_AVAILABLE else 0
                if score > best_score:
                    best_score = score
                    best_product = product

        return best_product

    def fallback_match(self) -> Product | None:
        """Return the first active product as a last resort."""
        return (
            self.db.query(Product)
            .filter(Product.is_active == True)  # noqa: E712
            .first()
        )