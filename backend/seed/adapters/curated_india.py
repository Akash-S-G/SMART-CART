"""Curated Indian catalog adapter.

Bridges `seed.catalog` (the authored manifest) into the existing seeder
contract: emit candidate dicts and let seeder.py handle DB rows, ImageStore
handle downloads, and upload_cloudinary.py handle the CDN.

One candidate is emitted per *variant*, so "Amul Gold Milk" in 500 ml and 1 L
becomes two SKUs with their own MRP, weight and images.
"""

from __future__ import annotations

from ..catalog import images as catalog_images
from ..catalog.build import build_catalog, resolve_related


def _candidate(product, variant, related: list[str], img_urls: list[str],
               provenance: list[dict]) -> dict:
    return {
        "name": f"{product.display_name} {variant.size}",
        "brand": product.brand,
        "barcode": None,
        "description": product.desc,
        "short_description": f"{product.display_name} ({variant.size})",
        "image_urls": img_urls,
        "quantity": variant.size,
        "country": "India",
        "categories_tags": [],
        "source": "curated-india",
        "sourced": True,
        # hints consumed by the seeder for pricing / weight rows
        "_base_price": variant.mrp,
        "_unit": product.unit,
        "_origin": "India",
        "_weight": variant.weight,
        "_weight_unit": variant.weight_unit,
        # richer metadata the storefront and copilot can use
        "_subcategory": product.subcategory,
        "_veg": product.veg,
        "_shelf_life": product.shelf_life,
        "_search_terms": product.search,
        "_ingredient_tags": product.ingredient_tags,
        "_related": related,
        "_image_provenance": provenance,
    }


def fetch(plan, http) -> list[dict]:
    """Emit candidates for the plan's category from the curated manifest."""
    products = build_catalog()
    related_map = resolve_related(products)

    out: list[dict] = []
    for product in products:
        if plan.name and product.category != plan.name:
            continue
        cands = catalog_images.gather(product, http, want=3)
        urls = [c["url"] for c in cands]
        prov = [{"url": c["url"], "source": c["source"], "license": c["license"]}
                for c in cands]
        for variant in product.variants:
            out.append(_candidate(product, variant,
                                  related_map.get(product.display_name, []),
                                  urls, prov))
    return out
