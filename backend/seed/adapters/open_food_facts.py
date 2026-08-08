"""Open Food Facts / Open Beauty Facts / Open Pet Food Facts adapter.

Fetches *real* product records (the same manufacturer packaging shots shown by
retailers) under Open*Facts' open licence, and upgrades each image URL to its
**full-resolution** variant so the catalog looks premium rather than low-res.
"""

from __future__ import annotations

import re

import config as cfg


_BASES = {
    cfg.SOURCE_OFF: cfg.OFF_BASE,
    cfg.SOURCE_OBF: cfg.OBF_BASE,
    cfg.SOURCE_OPFF: cfg.OPFF_BASE,
}

_SOURCE_NAMES = {
    cfg.SOURCE_OFF: "openfoodfacts",
    cfg.SOURCE_OBF: "openbeautyfacts",
    cfg.SOURCE_OPFF: "openpetfoodfacts",
}

_FIELDS = (
    "code,product_name,brands,categories_tags,labels_tags,"
    "image_front_url,image_ingredients_url,image_nutrition_url,"
    "image_packaging_url,quantity,countries_tags,ingredients_text,"
    "generic_name"
)

# image roles in priority order for the primary + gallery shots
_ROLE_KEYS = (
    "image_front_url",
    "image_packaging_url",
    "image_ingredients_url",
    "image_nutrition_url",
)


def _to_full(url: str) -> str:
    """Upgrade an OFF image URL to its full-resolution variant.

    OFF URLs look like:
      .../images/products/611/124/836/0130/front_fr.52.400.jpg
    The `400`/`200`/`100` token is the size; `.full.jpg` is the max-res version.
    """
    if not url or not url.startswith("http"):
        return url
    return re.sub(r"\.(\d+|[a-z]{1,3})\.jpg$", ".full.jpg", url, count=1)


def _norm_tag(tag: str) -> str:
    return tag.split(":", 1)[-1].replace("-", " ").strip()


def _is_indian(p: dict) -> bool:
    """True when the record is sold in India.

    The in.* Open*Facts hosts already scope results by country, but a handful of
    records come back with a foreign countries_tags; re-verify so the catalog
    stays an Indian grocery catalog.  Records that simply omit countries_tags
    are accepted (the country-scoped host already vouched for them).
    """
    if not cfg.INDIA_ONLY:
        return True
    tags = [str(t).strip().lower() for t in (p.get("countries_tags") or [])]
    if not tags:
        return True
    return any(t in cfg.INDIA_COUNTRY_TAGS for t in tags)


def fetch(plan, http) -> list[dict]:
    base = _BASES.get(plan.source)
    if not base or not plan.off_tag:
        return []

    tags = [plan.off_tag, *(plan.alt_off_tags or [])]

    out: list[dict] = []
    seen_codes: set[str] = set()
    page_size = 50
    max_pages = 12

    # Walk every tag in turn (previously the loop bailed out on the first tag
    # that ran dry, so alt_off_tags were mostly never used).
    for tag in tags:
        if len(out) >= cfg.API_PER_CATEGORY_CAP:
            break
        page = 1
        while len(out) < cfg.API_PER_CATEGORY_CAP and page <= max_pages:
            url = (
                f"{base}/api/v2/search"
                f"?categories_tags={tag}"
                f"&page={page}&page_size={page_size}"
                f"&fields={_FIELDS}&json=1"
            )
            data, resp = http.get_json(url)
            if data is None:
                break
            products = data.get("products") or []
            if not products:
                break
            for p in products:
                code = (p.get("code") or "").strip()
                name = (p.get("product_name") or "").strip()
                if not name:
                    continue
                if code and code in seen_codes:
                    continue
                if not _is_indian(p):
                    continue

                # Build a hi-res image set from the available role URLs.
                urls: list[str] = []
                for key in _ROLE_KEYS:
                    u = p.get(key)
                    if u and u.startswith("http"):
                        full = _to_full(u)
                        if full not in urls:
                            urls.append(full)
                if not urls:
                    continue  # no image at all -> skip (premium filter)
                seen_codes.add(code)

                countries = [str(t) for t in (p.get("countries_tags") or [])]
                lowered = {c.strip().lower() for c in countries}
                if lowered & cfg.INDIA_COUNTRY_TAGS:
                    country = "India"
                else:
                    country = _norm_tag(countries[0]) if countries else "India"
                desc = p.get("ingredients_text") or p.get("generic_name") or ""
                desc = re.sub(r"\s+", " ", desc).strip() or None
                brand = (p.get("brands") or "").strip() or None
                out.append({
                    "name": name,
                    "brand": brand,
                    "barcode": code or None,
                    "description": desc,
                    "short_description": (desc[:120] if desc else None),
                    "image_urls": urls,
                    "quantity": (p.get("quantity") or "").strip() or None,
                    "country": country,
                    "categories_tags": [str(t) for t in (p.get("categories_tags") or [])],
                    "source": _SOURCE_NAMES[plan.source],
                    "sourced": True,
                })
            page += 1

    return out
