"""Curated catalog adapter.

For categories without an open structured product API (Home Cleaning, Baby Care,
Electronics, Kitchen Essentials, plus top-ups for any category), we emit clearly
*generated* products using a small vetted brand list and attach openly licensed
Wikimedia imagery.  Every generated product is tagged `sourced=False` in the
final metadata so sourced vs generated data stays distinguishable.
"""

from __future__ import annotations

import random

import config as cfg

from . import wikimedia


def fetch(plan, http) -> list[dict]:
    """Return generated candidates (sourced=False) with Wikimedia images."""
    # Build a per-subcategory image pool from the plan's wiki queries.
    pool = wikimedia.fetch_image_pool(plan, http, per_query=6)
    random.shuffle(pool)

    # Pull curated brand/variant definitions for this category's subcategories.
    items: list[tuple[str, str, str, float, str]] = []
    for sub in plan.subcategories:
        items.extend(cfg.CURATED_PRODUCTS.get(sub, []))

    out: list[dict] = []
    img_idx = 0

    def next_img() -> str | None:
        nonlocal img_idx
        if not pool:
            return None
        u = pool[img_idx % len(pool)]
        img_idx += 1
        return u

    for brand, variant, unit, price, origin in items:
        name = f"{brand} {variant}".strip()
        out.append({
            "name": name,
            "brand": brand,
            "barcode": None,
            "description": f"{brand} {variant} - {unit}. {plan.description}",
            "short_description": f"{brand} {variant} ({unit})",
            "image_urls": [next_img()] if pool else [],
            "quantity": unit,
            "country": origin,
            "categories_tags": [],
            "source": "curated-catalog",
            "sourced": False,
            # hints consumed by the seeder for pricing/weight
            "_base_price": price,
            "_unit": unit,
            "_origin": origin,
        })
    return out
