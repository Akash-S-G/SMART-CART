"""Field normalization: names, brands, units, prices, categories and the
assembly of the products.metadata JSON payload.

The metadata JSON carries all the catalog attributes the brief asks for that are
not first-class columns (subcategory, mrp, discounts, rating, tags, gallery,
search keywords, etc.).  Every product records a `provenance` block so that
sourced vs. generated fields are distinguishable, satisfying the auditability
requirement in the brief.
"""

from __future__ import annotations

import random
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import config as cfg


def is_plausible_product_name(name: str | None) -> bool:
    """Heuristic reject of non-product junk from open datasets (place names,
    single-character, all-non-alpha, over-long descriptions, etc.)."""
    if not name:
        return False
    s = name.strip()
    if len(s) < 3 or len(s) > 60:
        return False
    # require at least some latin/digit characters (skip pure non-latin gibberish)
    ascii_alpha = sum(1 for ch in s if ch.isascii() and (ch.isalpha() or ch.isdigit()))
    if ascii_alpha < 3:
        return False
    # skip if it looks like a sentence / description rather than a product
    if s.count(" ") > 8:
        return False
    # skip names dominated by pack/code noise
    digits = sum(1 for ch in s if ch.isdigit())
    if digits > 6:
        return False
    return True


def _clean_text(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def normalize_name(raw: str | None) -> str | None:
    """Title-case without destroying brand-y capitals like 'iPhone'."""
    s = _clean_text(raw)
    if not s:
        return None
    # Keep ALL-CAPS acronyms and dot brands; otherwise title case.
    if s.isupper() and len(s) <= 6:
        return s
    return s[:255]


def normalize_brand(raw: str | None) -> str | None:
    s = _clean_text(raw)
    if not s:
        return None
    # OFF brands are comma-separated lists; take the first recognised one.
    parts = [p.strip() for p in s.split(",") if p.strip()]
    for p in parts:
        if p.lower() in cfg.KNOWN_BRANDS:
            return p
    return parts[0][:100] if parts else None


def normalize_category(name: str) -> str:
    return name.strip().title()


def parse_weight_from_text(text: str | None, name: str | None) -> tuple[float | None, str | None]:
    """Heuristic weight/unit parser from OFF quantity field or name."""
    blob = " ".join([t for t in (text, name) if t]) or ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(g|kg|ml|l|mg)\b", blob, re.IGNORECASE)
    if not m:
        return None, None
    val = float(m.group(1))
    unit = m.group(2).lower()
    return val, unit


def infer_unit_from_quantity(qty: str | None) -> str | None:
    if not qty:
        return None
    m = re.search(r"(g|kg|ml|l|mg|piece|pack|box|pcs)\b", qty, re.IGNORECASE)
    return m.group(1).lower() if m else None


def compute_pricing(base_price: float | None, *, sourced: bool) -> dict:
    """Return dict(mrp, selling_price, discount_percentage) in INR."""
    if base_price and base_price > 0:
        selling = float(base_price)
    else:
        # generated price within a believable grocery/retail band
        selling = round(random.uniform(15, 1500), 2)
    markup = random.uniform(cfg.MRP_MARKUP_MIN, cfg.MRP_MARKUP_MAX)
    mrp = float(Decimal(str(selling * markup)).quantize(Decimal("0.01"), ROUND_HALF_UP))
    # Keep MRP >= selling
    if mrp < selling:
        mrp = float(Decimal(str(selling * 1.05)).quantize(Decimal("0.01"), ROUND_HALF_UP))
    discount = round((1 - selling / mrp) * 100, 1) if mrp else 0.0
    return {
        "mrp": round(mrp, 2),
        "selling_price": round(selling, 2),
        "discount_percentage": round(discount, 1),
    }


def generate_rating_reviews(*, sourced: bool) -> tuple[float, int]:
    rating = round(random.uniform(cfg.RATING_MIN, cfg.RATING_MAX), 1)
    reviews = random.randint(cfg.REVIEW_MIN, cfg.REVIEW_MAX)
    return rating, reviews


def generate_stock() -> int:
    # Mostly in-stock, occasionally out (for realistic inventory demos)
    if random.random() < 0.05:
        return 0
    return random.randint(cfg.STOCK_MIN + 5, cfg.STOCK_MAX)


def build_keywords(name: str, brand: str | None, subcat: str | None,
                   tags: list[str]) -> list[str]:
    kws = set()
    for tok in [name, brand, subcat]:
        if tok:
            for w in re.findall(r"[A-Za-z0-9]+", tok.lower()):
                if len(w) > 1:
                    kws.add(w)
    for t in tags:
        kws.add(t.lower())
    return sorted(kws)[:25]


def build_metadata(
    *,
    sourced: bool,
    source: str,
    subcategory: str | None,
    barcode: str | None,
    mrp: float,
    selling_price: float,
    discount_percentage: float,
    rating: float,
    review_count: int,
    unit: str | None,
    weight: float | None,
    weight_unit: str | None,
    origin_country: str | None,
    tags: list[str],
    short_description: str | None,
    search_keywords: list[str],
    thumbnail: str | None,
    gallery: list[str],
    num_images: int,
    extra: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    meta = {
        "provenance": {
            "sourced": bool(sourced),
            "source": source,
            "seeded_by": cfg.SEED_SOURCE_LABEL,
            "seed_version": cfg.SEED_VERSION,
            "seeded_at": now,
        },
        "subcategory": subcategory,
        "barcode": barcode,
        "mrp": mrp,
        "selling_price": selling_price,
        "discount_percentage": discount_percentage,
        "currency": cfg.DEFAULT_CURRENCY,
        "rating": rating,
        "review_count": review_count,
        "unit": unit,
        "weight": weight,
        "weight_unit": weight_unit,
        "origin_country": origin_country,
        "tags": tags,
        "short_description": short_description,
        "search_keywords": search_keywords,
        "images": {
            "thumbnail": thumbnail,
            "gallery": gallery,
            "count": num_images,
        },
    }
    if extra:
        meta.update(extra)
    return meta


def new_sku(category_name: str, n: int) -> str:
    prefix = re.sub(r"[^A-Za-z]", "", category_name)[:3].upper() or cfg.SKU_PREFIX
    return f"{cfg.SKU_PREFIX}-{prefix}-{n:05d}"
