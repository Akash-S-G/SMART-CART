"""Schema + validation for the curated Indian catalog.

Design rules
------------
* A `Product` is a *product line* (Amul Gold Milk); a `Variant` is a purchasable
  pack (500 ml @ Rs 34).  Each variant becomes one SKU / DB row.
* Deduplication is **structural**, not best-effort: the key
  ``(brand, name, size)`` is asserted unique at build time, so a duplicate is a
  build failure rather than something a filter has to catch later.
* Prices are real Indian MRPs in INR and are range-checked, so a typo (Rs 3400
  for a milk packet) fails the build instead of reaching the storefront.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Sanity band for an Indian grocery MRP (rupees).  Anything outside is a typo.
MIN_PRICE_INR = 5.0
MAX_PRICE_INR = 5000.0

UNITS = {"g", "kg", "ml", "l", "piece", "pack", "dozen", "combo"}


class CatalogError(ValueError):
    """Raised when the authored catalog violates a structural invariant."""


def slugify(text: str) -> str:
    """Lowercase ASCII slug used for dedup keys and search matching."""
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@dataclass(frozen=True)
class Variant:
    """One purchasable pack of a product line."""

    size: str            # human pack size, e.g. "500 ml", "1 kg", "6 pieces"
    mrp: float           # printed MRP in INR
    weight: float | None = None      # numeric weight/volume for the cart scale
    weight_unit: str = "g"           # g | ml | piece

    def validate(self, owner: str) -> None:
        if not self.size.strip():
            raise CatalogError(f"{owner}: variant has an empty size")
        if not (MIN_PRICE_INR <= self.mrp <= MAX_PRICE_INR):
            raise CatalogError(
                f"{owner} [{self.size}]: MRP {self.mrp} outside "
                f"Rs{MIN_PRICE_INR:.0f}-{MAX_PRICE_INR:.0f}"
            )
        if self.weight is not None and self.weight <= 0:
            raise CatalogError(f"{owner} [{self.size}]: weight must be positive")


@dataclass
class Product:
    """A curated Indian product line."""

    name: str
    brand: str
    category: str
    variants: list[Variant]
    desc: str
    unit: str = "piece"
    veg: bool | None = True                     # None = not applicable
    ingredient_tags: list[str] = field(default_factory=list)   # recipe linkage
    search: list[str] = field(default_factory=list)            # hindi/regional
    related: list[str] = field(default_factory=list)
    subcategory: str | None = None
    shelf_life: str | None = None
    image_queries: list[str] = field(default_factory=list)     # web-search hints

    # ---- derived ---------------------------------------------------------- #
    @property
    def display_name(self) -> str:
        """'Amul' + 'Gold Full Cream Milk' -> 'Amul Gold Full Cream Milk'."""
        return self.name if self.name.lower().startswith(self.brand.lower()) \
            else f"{self.brand} {self.name}"

    def dedup_key(self, variant: Variant) -> tuple[str, str, str]:
        return (slugify(self.brand), slugify(self.name), slugify(variant.size))

    def query_for(self, variant: Variant) -> str:
        """Image-search query for a specific pack."""
        if self.image_queries:
            return f"{self.image_queries[0]} {variant.size}"
        return f"{self.display_name} {variant.size} India pack"

    def validate(self) -> None:
        who = self.display_name
        if not self.name.strip() or not self.brand.strip():
            raise CatalogError(f"{who}: name and brand are required")
        if not self.variants:
            raise CatalogError(f"{who}: needs at least one variant")
        if not self.desc or len(self.desc) < 20:
            raise CatalogError(f"{who}: description too short (min 20 chars)")
        if self.unit not in UNITS:
            raise CatalogError(f"{who}: unknown unit {self.unit!r}")
        seen: set[str] = set()
        for v in self.variants:
            v.validate(who)
            key = slugify(v.size)
            if key in seen:
                raise CatalogError(f"{who}: duplicate variant size {v.size!r}")
            seen.add(key)


def P(name, brand, category, variants, desc, **kw) -> Product:
    """Terse constructor so the manifest stays readable.

    Variants are given as ``(size, mrp)`` or ``(size, mrp, weight, unit)``.
    """
    vs = [v if isinstance(v, Variant) else Variant(*v) for v in variants]
    return Product(name=name, brand=brand, category=category, variants=vs,
                   desc=desc, **kw)
