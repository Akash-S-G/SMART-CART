"""Wikimedia Commons image adapter.

Used both as a fallback image source and as the primary source for categories
without an open structured product API (Home Cleaning, Baby Care, Electronics,
Kitchen Essentials).  All images are from Wikimedia Commons (CC / public domain).
"""

from __future__ import annotations

import urllib.parse

import config as cfg


def _image_urls_for_query(http, query: str, limit: int = 6) -> list[str]:
    q = urllib.parse.quote(query)
    url = (
        f"{cfg.WIKI_API}?action=query&generator=search"
        f"&gsrsearch={q}&gsrnamespace=6&gsrlimit={limit}"
        f"&prop=imageinfo&iiprop=url%7Cmime%7Csize&format=json"
    )
    data, _ = http.get_json(url)
    if not data:
        return []
    pages = (data.get("query") or {}).get("pages") or {}
    urls: list[str] = []
    for pg in pages.values():
        ii = (pg.get("imageinfo") or [{}])[0]
        mime = ii.get("mime", "")
        if mime not in ("image/jpeg", "image/png"):
            continue
        w = ii.get("width", 0)
        h = ii.get("height", 0)
        if w < cfg.MIN_IMAGE_DIM or h < cfg.MIN_IMAGE_DIM:
            continue
        u = ii.get("url")
        if u and u not in urls:
            urls.append(u)
    return urls


def fetch_image_pool(plan, http, per_query: int = 6) -> list[str]:
    """Collect a flat pool of image URLs across the plan's wiki queries."""
    pool: list[str] = []
    queries = plan.wiki_queries or [plan.name]
    for q in queries:
        urls = _image_urls_for_query(http, q, limit=per_query)
        for u in urls:
            if u not in pool:
                pool.append(u)
    return pool


def fetch_products(plan, http) -> list[dict]:
    """Build sourced-looking candidates backed by Wikimedia imagery.

    NOTE: names/brands are NOT sourced here (no open product DB); they are
    generated and tagged `sourced=False` by the seeder.  Images ARE openly
    licensed Wikimedia media.
    """
    pool = fetch_image_pool(plan, http)
    out: list[dict] = []
    for i, url in enumerate(pool):
        out.append({
            "name": f"{plan.name} item {i + 1}",
            "brand": None,
            "barcode": None,
            "description": None,
            "short_description": None,
            "image_urls": [url],
            "quantity": None,
            "country": None,
            "categories_tags": [],
            "source": "wikimedia-commons",
            "sourced": False,
        })
    return out
