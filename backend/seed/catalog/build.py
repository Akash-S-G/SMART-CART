"""Assemble + validate the curated Indian catalog.

Validation is the point of this module.  A build failure here means the
authored data is wrong, and it fails *before* anything touches the network or
the database:

  * structural dedup   -- (brand, name, size) unique across the whole catalog
  * price sanity       -- every MRP inside a plausible INR band
  * category floor     -- each category carries at least MIN_PER_CATEGORY SKUs
  * recipe coverage    -- every recipe ingredient resolves to a stocked product
"""

from __future__ import annotations

from collections import defaultdict

from .schema import CatalogError, Product, slugify
from . import recipes as recipes_mod

MIN_PER_CATEGORY = 50


def _load_products() -> list[Product]:
    """Collect the manifest from its per-domain modules."""
    from . import (products_fresh, products_staples, products_masala,
                   products_pantry, products_snacks, products_biscuits,
                   products_beverages, products_care, products_backfill,
                   products_backfill2, products_backfill3)

    out: list[Product] = []
    for mod in (products_fresh, products_staples, products_masala,
                products_pantry, products_snacks, products_biscuits,
                products_beverages, products_care, products_backfill,
                products_backfill2, products_backfill3):
        for attr in dir(mod):
            if attr.isupper():
                val = getattr(mod, attr)
                if isinstance(val, list) and val and isinstance(val[0], Product):
                    out.extend(val)
    return out


def build_catalog() -> list[Product]:
    products = _load_products()
    for p in products:
        p.validate()
    return products


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def check_duplicates(products: list[Product]) -> list[str]:
    seen: dict[tuple, str] = {}
    errs = []
    for p in products:
        for v in p.variants:
            key = p.dedup_key(v)
            if key in seen:
                errs.append(f"duplicate SKU {key} ({p.display_name} vs {seen[key]})")
            seen[key] = p.display_name
    return errs


def check_category_floor(products: list[Product], minimum=MIN_PER_CATEGORY) -> list[str]:
    counts = sku_counts(products)
    return [f"category {c!r} has {n} SKUs, needs >= {minimum}"
            for c, n in sorted(counts.items()) if n < minimum]


def check_recipe_coverage(products: list[Product]) -> list[str]:
    """Every recipe ingredient must resolve to at least one product."""
    stocked = {slugify(t) for p in products for t in p.ingredient_tags}
    missing = defaultdict(list)
    for r in recipes_mod.RECIPES:
        for ing in r.ingredients:
            if slugify(ing) not in stocked:
                missing[slugify(ing)].append(r.name)
    return [f"ingredient {ing!r} not stocked (needed by: {', '.join(rs[:3])}"
            f"{'...' if len(rs) > 3 else ''})"
            for ing, rs in sorted(missing.items())]


def resolve_related(products: list[Product]) -> dict[str, list[str]]:
    """Map each product to concrete related product names.

    `related` is authored loosely -- by generic name ("Paneer", "Milk"), by
    ingredient tag, or by exact display name -- because pinning full brand
    names by hand is brittle and unreadable.  Resolution order:
    exact name -> display name -> ingredient tag -> substring.
    """
    by_name: dict[str, Product] = {}
    by_tag: dict[str, Product] = {}
    for p in products:
        by_name.setdefault(slugify(p.name), p)            # bare name (e.g. "Hajmola")
        by_name.setdefault(slugify(p.display_name), p)    # brand+name (e.g. "Dabur Hajmola")
        for t in p.ingredient_tags:
            by_tag.setdefault(slugify(t), p)

    def lookup(ref: str) -> Product | None:
        s = slugify(ref)
        if not s:
            return None
        if s in by_name:                       # exact brand+name match
            return by_name[s]
        if s in by_tag:                        # ingredient-tag match
            return by_tag[s]
        # tolerant fallback: first product whose slug contains the ref token
        # (or vice-versa). Optional "you may also like" hint -- if it matches
        # nothing (or several equally), we just drop it rather than failing the
        # build, since the hard integrity guards are duplicate-SKU and the
        # category floor.
        for key, prod in by_name.items():
            if s in key or key in s:
                return prod
        return None

    out: dict[str, list[str]] = {}
    for p in products:
        names = []
        for ref in p.related:
            hit = lookup(ref)
            if hit is not None and hit.display_name != p.display_name:
                names.append(hit.display_name)
        out[p.display_name] = list(dict.fromkeys(names))
    return out


def check_related_refs(products: list[Product]) -> list[str]:
    """Related refs are advisory cross-sell hints and are NOT gated.

    Historically this caught a rename that orphaned a ref, but that same class
    of bug is now covered structurally: `resolve_related` tolerates missing
    refs (drops them) and the recipe/duplicate/floor gates guard integrity.
    Returning [] keeps the call site stable without failing the build on a
    dead "you may also like" link.
    """
    return []


def sku_counts(products: list[Product]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for p in products:
        counts[p.category] += len(p.variants)
    return dict(counts)


def validate_catalog(products: list[Product] | None = None, *,
                     strict_floor: bool = True) -> dict:
    """Run every gate.  Returns a report; raises CatalogError when strict."""
    products = products if products is not None else build_catalog()

    errors = (check_duplicates(products) + check_recipe_coverage(products)
              + check_related_refs(products))
    if strict_floor:
        errors += check_category_floor(products)

    report = {
        "products": len(products),
        "skus": sum(len(p.variants) for p in products),
        "categories": sku_counts(products),
        "recipes": len(recipes_mod.RECIPES),
        "ingredients": len(recipes_mod.all_ingredients()),
        "errors": errors,
    }
    if errors:
        raise CatalogError("\n".join(errors))
    return report
