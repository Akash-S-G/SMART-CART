"""Source adapters.

Each adapter exposes `fetch_candidates(plan, http, cache_dir) -> list[dict]`
returning intermediate "raw candidate" dicts with a common shape:

    {
      "name": str,
      "brand": str | None,
      "barcode": str | None,
      "description": str | None,
      "short_description": str | None,
      "image_urls": list[str],
      "quantity": str | None,
      "country": str | None,
      "categories_tags": list[str],
      "source": str,          # "openfoodfacts" | "openbeautyfacts" | ...
      "sourced": True,
    }

The seeder later normalizes + enriches these into DB rows.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import config as cfg

from . import open_food_facts, wikimedia, curated


def _cache_path(cache_dir: Path, key: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.json"


def fetch_for_plan(plan, http, cache_dir: Path, refresh: bool = False) -> list[dict]:
    """Dispatch to the right adapter(s) for a category plan."""
    key = re.sub(r"[^a-z0-9]+", "_", plan.name.lower())
    cache = _cache_path(cache_dir, f"candidates_{key}")

    if not refresh and cache.exists():
        try:
            return json.loads(cache.read_text())
        except Exception:  # noqa: BLE001
            pass

    candidates: list[dict] = []
    if plan.source in (cfg.SOURCE_OFF, cfg.SOURCE_OBF, cfg.SOURCE_OPFF):
        candidates = open_food_facts.fetch(plan, http)
    elif plan.source == cfg.SOURCE_WIKIMEDIA:
        candidates = wikimedia.fetch_products(plan, http)
    elif plan.source == cfg.SOURCE_CURATED:
        candidates = curated.fetch(plan, http)

    # Persist raw candidates for fast/idempotent reruns.
    try:
        cache.write_text(json.dumps(candidates, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        pass
    return candidates
