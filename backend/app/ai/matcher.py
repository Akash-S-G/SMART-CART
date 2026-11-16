"""
ProductMatcher — Hybrid YOLO class-name + OCR fuzzy text matcher.

Matching priority (highest → lowest):
  1. Exact product name lookup (best.pt class names are exact product names)
  2. Case-insensitive partial name search (DB ILIKE)
  3. Fuzzy string match against every product name/brand (RapidFuzz)
  4. OCR text tokens fuzzy-matched against product names
  5. Fallback: first active product in DB
"""
from __future__ import annotations

import logging
import re
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


# Minimum similarity score (0-100) for RapidFuzz matches.
_FUZZY_THRESHOLD = 75

# Generic nutrition/marketing phrases that appear on packaging but are NOT product names.
# These tokens pollute OCR matching and cause false positives.
_NOISE_WORDS = {
    "rich", "vitamin", "added", "preservatives", "natural", "fresh", "real",
    "pure", "original", "classic", "premium", "special", "daily", "every",
    "day", "new", "best", "great", "good", "value", "pack", "size",
    "ingredients", "made", "with", "just", "contains", "no", "free", "low",
    "fat", "sugar", "salt", "energy", "protein", "calcium", "iron",
    "per", "serving", "net", "weight", "grams", "litre", "liter", "ml",
    "manufactured", "marketed", "india", "product", "food", "drink",
}


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

        *ocr_tokens* — list of strings extracted from the image crop by EasyOCR.
        *image_crop* — the raw crop (unused in base impl, reserved for embedding extensions).

        Returns the best-matching product or None.
        """
        if not ocr_tokens:
            return None

        all_prods = self._all_active_products()
        if not all_prods:
            return None

        # Clean tokens: strip whitespace, drop very short, drop pure-noise generic words
        clean_tokens = [
            t.strip() for t in ocr_tokens
            if len(t.strip()) >= 3 and t.strip().lower() not in _NOISE_WORDS
        ]
        if not clean_tokens:
            return None

        combined_text = " ".join(clean_tokens).lower()

        # 1. First prioritize multi-word brand + flavor combination matching
        scored_products: list[tuple[float, Product]] = []

        for p in all_prods:
            p_name_lower = p.name.lower()
            p_brand_lower = (p.brand or "").lower()

            # Token overlap: how many words of the product name appear in OCR text
            name_words = set(p_name_lower.split())
            # Ignore common noise words when doing word overlap too
            name_words = {w for w in name_words if w not in _NOISE_WORDS}
            matched_words = sum(1 for w in name_words if w in combined_text)
            overlap_ratio = matched_words / len(name_words) if name_words else 0.0

            # RapidFuzz token_set_ratio on combined OCR text vs product name
            full_ratio = fuzz.token_set_ratio(combined_text, p_name_lower) if _RAPIDFUZZ_AVAILABLE else 0.0

            # Brand boost: if the brand word explicitly appears in OCR text, strongly prefer it
            brand_boost = 20.0 if p_brand_lower and p_brand_lower in combined_text else 0.0

            # Penalty: if product name has many words but only 1 token matched, reduce score
            coverage_penalty = -15.0 if len(name_words) >= 3 and matched_words <= 1 else 0.0

            total_score = (full_ratio * 0.55) + (overlap_ratio * 45.0) + brand_boost + coverage_penalty

            if total_score >= 65.0:
                scored_products.append((total_score, p))
                logger.debug("OCR candidate: '%s' score=%.1f (fuzzy=%.0f, overlap=%.2f, brand_boost=%.0f)",
                             p.name, total_score, full_ratio, overlap_ratio, brand_boost)

        if scored_products:
            scored_products.sort(key=lambda x: x[0], reverse=True)
            best_score, best_product = scored_products[0]
            # Only accept if top score is meaningfully better than second (or only one)
            runner_up_score = scored_products[1][0] if len(scored_products) > 1 else 0.0
            margin = best_score - runner_up_score
            if margin >= 5.0 or best_score >= 80.0:
                logger.info("OCR multi-token match selected '%s' with score %.2f (margin %.1f vs runner-up)",
                            best_product.name, best_score, margin)
                return best_product
            else:
                logger.info("OCR top candidate '%s' (%.1f) too close to '%s' (%.1f) — skipping ambiguous match.",
                            scored_products[0][1].name, best_score, scored_products[1][1].name, runner_up_score)

        # Fallback to individual token fuzzy matching
        best_product: Product | None = None
        best_score_fb: float = 0.0
        for token in clean_tokens:
            if len(token) < 4:
                continue
            product = self._fuzzy_best(token, all_prods, threshold=_FUZZY_THRESHOLD)
            if product is not None:
                score = fuzz.WRatio(token, product.name) if _RAPIDFUZZ_AVAILABLE else 0
                if score > best_score_fb:
                    best_score_fb = score
                    best_product = product

        return best_product

    def fallback_match(self) -> Product | None:
        """Return the first active product as a last resort."""
        return (
            self.db.query(Product)
            .filter(Product.is_active == True)  # noqa: E712
            .first()
        )