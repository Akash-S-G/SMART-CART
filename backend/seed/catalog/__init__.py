"""Curated Indian grocery catalog.

A hand-authored, recipe-complete product manifest for the Indian market.

Unlike the Open*Facts adapters (which take whatever contributors happened to
upload), this catalog is authored product-by-product so every row is something
that genuinely sits on an Indian supermarket shelf, with a real MRP, a real
pack size and a description written for shoppers.

Modules
-------
schema    -- Product/Variant dataclasses, INR validation, structural dedup key
products  -- the manifest itself (per-category product lists)
recipes   -- Indian recipes whose ingredients MUST resolve to catalog products
build     -- assembles + validates the catalog, expands variants into SKUs
"""

from __future__ import annotations

from .schema import Product, Variant, CatalogError
from .build import build_catalog, validate_catalog

__all__ = ["Product", "Variant", "CatalogError", "build_catalog", "validate_catalog"]
