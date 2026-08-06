"""Seeder service: orchestrates download -> clean -> normalize -> image store
-> idempotent DB upsert, with progress reporting.

Design notes
------------
* Reads the project's own SQLAlchemy models so rows are 100% app-compatible.
* Sourced data comes from Open*Facts + Wikimedia (open/licensed).  Categories
  without an open product API use a clearly *generated* curated catalog; those
  rows carry provenance.sourced=False in products.metadata.
* Idempotency:
    - SKU is the dedup/upsert key.
    - On rerun we UPDATE changed metadata for existing SKUs and INSERT new ones;
      we never duplicate.  Barcode/name collisions are dropped.
* Each product row is accompanied by product_prices, product_weights, inventory
  and product_images rows (matching the normalized schema).
"""

from __future__ import annotations

import random
import re
import sys
from decimal import Decimal
from pathlib import Path

import config as cfg
from logging_utils import Progress, Stats, print_report
from http_client import HttpClient
from db import (
    ensure_tables,
    get_or_create_category,
    existing_sku_set,
    existing_barcode_set,
    get_product_by_sku,
    get_product_by_barcode,
    get_product_by_name,
    session_scope,
)
from adapters import fetch_for_plan
from image_utils import ImageStore
from normalizer import (
    normalize_name,
    normalize_brand,
    parse_weight_from_text,
    infer_unit_from_quantity,
    compute_pricing,
    generate_rating_reviews,
    generate_stock,
    build_keywords,
    build_metadata,
    new_sku,
    is_plausible_product_name,
)
from duplicate import DedupState


def _subcategory_for(plan, candidate: dict) -> str:
    subs = plan.subcategories
    if not subs:
        return None
    # try to match a subcategory from OFF tags/name, else pick a stable one
    blob = " ".join([
        " ".join(candidate.get("categories_tags", [])),
        candidate.get("name", ""),
        candidate.get("quantity", "") or "",
    ]).lower()
    for s in subs:
        if s.lower() in blob:
            return s
    # deterministic-ish: hash name to a sub to keep stable across runs
    idx = sum(ord(c) for c in candidate.get("name", "")) % len(subs)
    return subs[idx]


def _build_tags(plan, name: str, brand: str | None, subcat: str | None) -> list[str]:
    tags = set()
    words = re.findall(r"[A-Za-z]+", (name or ""))
    for w in words:
        if len(w) > 2:
            tags.add(w.lower())
    if brand:
        tags.add(brand.lower())
    if subcat:
        tags.add(subcat.lower())
    tags.add(plan.name.lower())
    return sorted(tags)[:12]


def seed(
    *,
    refresh: bool = False,
    only_category: str | None = None,
    quiet: bool = False,
    limit_per_category: int | None = None,
) -> Stats:
    progress = Progress(quiet=quiet)
    stats = Stats()

    ensure_tables()
    http = HttpClient()
    cache_dir = cfg.SEED_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    store = ImageStore(http, progress=progress, stats=stats)

    plans = [p for p in cfg.CATEGORY_PLAN if not only_category or p.name == only_category]

    progress.info(f"Seeding {len(plans)} categories. Static base = "
                  f"{cfg.ENV_STATIC_BASE_URL}")

    # Pre-load DB dedupe sets once.
    with session_scope() as db:
        db_skus = existing_sku_set(db)
        db_barcodes = existing_barcode_set(db)

    for plan in plans:
        progress.category(plan.name, plan.target)
        # 1) fetch raw candidates (cached on disk)
        candidates = fetch_for_plan(plan, http, cache_dir, refresh=refresh)
        if limit_per_category:
            candidates = candidates[:limit_per_category]
        stats.products_processed += len(candidates)

        # 2) category row
        with session_scope() as db:
            cat = get_or_create_category(db, plan.name, plan.description)
            cat_id = cat.id

        dedup = DedupState(db_skus=db_skus, db_barcodes=db_barcodes)
        inserted = 0
        updated = 0
        skipped = 0
        seq = 1

        for i, cand in enumerate(candidates, start=1):
            raw_name = normalize_name(cand.get("name"))
            if not raw_name or not is_plausible_product_name(raw_name):
                skipped += 1
                stats.products_skipped += 1
                continue

            # 2a) validate images up front: a product without usable imagery is
            #     skipped (brief: "Skip products whose images are unusable").
            img_urls = [u for u in (cand.get("image_urls") or []) if u]
            if not img_urls:
                skipped += 1
                stats.products_skipped += 1
                progress.product(i, len(candidates), raw_name + " [no-img]")
                continue

            # 2b) SKU (display id; kept unique via renumber. Idempotency is
            # enforced at upsert time by barcode / normalized name.)
            base_sku = new_sku(plan.name, seq)
            keep, maybe_sku = dedup.check(base_sku, cand.get("barcode"), raw_name)
            if not keep:
                stats.products_skipped += 1
                skipped += 1
                progress.product(i, len(candidates), raw_name + " [dup]")
                continue
            if maybe_sku is None:
                # renumber to a free SKU so the unique column is never violated
                while True:
                    seq += 1
                    base_sku = new_sku(plan.name, seq)
                    if base_sku not in db_skus and base_sku not in dedup.seen_skus:
                        break
            sku = base_sku
            dedup.seen_skus.add(sku)

            progress.product(i, len(candidates), raw_name)

            # 2c) download + store images
            img_res = store.store_product_images(sku, img_urls)
            if not img_res["thumbnail"]:
                # all images failed validation
                skipped += 1
                stats.products_skipped += 1
                progress.step(f"  images failed for {raw_name}")
                continue

            # 2d) normalize fields
            brand = normalize_brand(cand.get("brand"))
            subcat = _subcategory_for(plan, cand)
            sourced = bool(cand.get("sourced", False))
            qty = cand.get("quantity")
            unit = infer_unit_from_quantity(qty) or (
                cand.get("_unit") if not sourced else None)
            weight, w_unit = parse_weight_from_text(qty, raw_name)
            if weight is None and sourced is False and cand.get("_unit"):
                # derive weight from curated unit string if possible
                weight, w_unit = parse_weight_from_text(cand.get("_unit"), None)
            origin = cand.get("country") or (cand.get("_origin") if not sourced else None) or "India"
            base_price = cand.get("_base_price") if not sourced else None
            pricing = compute_pricing(base_price, sourced=sourced)
            rating, reviews = generate_rating_reviews(sourced=sourced)
            stock = generate_stock()
            tags = _build_tags(plan, raw_name, brand, subcat)
            short_desc = cand.get("short_description") or (
                raw_name[:120])
            keywords = build_keywords(raw_name, brand, subcat, tags)

            meta = build_metadata(
                sourced=sourced,
                source=cand.get("source", "unknown"),
                subcategory=subcat,
                barcode=cand.get("barcode"),
                mrp=pricing["mrp"],
                selling_price=pricing["selling_price"],
                discount_percentage=pricing["discount_percentage"],
                rating=rating,
                review_count=reviews,
                unit=unit,
                weight=weight,
                weight_unit=w_unit,
                origin_country=origin,
                tags=tags,
                short_description=short_desc,
                search_keywords=keywords,
                thumbnail=img_res["thumbnail"],
                gallery=img_res["gallery"],
                num_images=1 + len(img_res["gallery"]),
            )

            # 2e) idempotent upsert — keyed on the product's natural key
            # (barcode for sourced data, normalized name for generated), NOT
            # the SKU. This keeps reruns stable even when SKU numbering shifts.
            with session_scope() as db:
                existing = None
                if cand.get("barcode"):
                    existing = get_product_by_barcode(db, cand.get("barcode"))
                if existing is None:
                    existing = get_product_by_name(db, raw_name)

                if existing is None:
                    _insert_product(db, cat_id, sku, cand.get("barcode"),
                                     raw_name, brand, cand.get("description"),
                                     meta, pricing, weight, w_unit, unit,
                                     stock, img_res, sourced)
                    inserted += 1
                    stats.products_inserted += 1
                else:
                    # Update changed metadata; preserve provenance if it was sourced
                    existing.name = raw_name
                    existing.brand = brand
                    existing.description = cand.get("description")
                    # merge metadata, keeping provenance block
                    old_prov = {}
                    if isinstance(existing.metadata_, dict):
                        old_prov = existing.metadata_.get("provenance", {})
                    meta["provenance"] = {**meta["provenance"], **old_prov}
                    existing.metadata_ = meta
                    _upsert_children(db, existing.id, pricing, weight, w_unit,
                                     unit, stock, img_res, sourced)
                    updated += 1
                    stats.products_updated += 1

            seq += 1

        with session_scope() as db:
            pass  # category counts computed at end
        stats.add_category(plan.name, inserted + updated)
        progress.step(f"inserted={inserted} updated={updated} skipped={skipped}")

    print_report(stats, progress)
    return stats


def _insert_product(db, cat_id, sku, barcode, name, brand, description,
                    meta, pricing, weight, w_unit, unit, stock, img_res, sourced):
    from app.models.products.product import Product
    from app.models.products.product_price import ProductPrice
    from app.models.products.product_weight import ProductWeight
    from app.models.products.inventory import Inventory
    from app.models.products.product_image import ProductImage

    prod = Product(
        sku=sku,
        barcode=barcode,
        name=name,
        brand=brand,
        description=description,
        category_id=cat_id,
        is_active=True,
        metadata_=meta,
    )
    db.add(prod)
    db.flush()

    db.add(ProductPrice(
        product_id=prod.id,
        price=Decimal(str(pricing["selling_price"])),
        gst_percentage=Decimal("5.00"),
        discount_percentage=Decimal(str(pricing["discount_percentage"])),
    ))
    if weight is not None:
        db.add(ProductWeight(
            product_id=prod.id,
            expected_weight=Decimal(str(weight)),
            tolerance=Decimal("5"),
            unit=w_unit or "g",
        ))
    db.add(Inventory(
        product_id=prod.id,
        quantity=stock,
        reorder_level=20,
        max_capacity=500,
        location=f"A-{random.randint(1,9)}{random.randint(1,9)}",
    ))
    _add_images(db, prod.id, img_res)


def _upsert_children(db, product_id, pricing, weight, w_unit, unit, stock,
                     img_res, sourced):
    from app.models.products.product_price import ProductPrice
    from app.models.products.product_weight import ProductWeight
    from app.models.products.inventory import Inventory
    from sqlalchemy import select

    pp = db.execute(
        select(ProductPrice).where(ProductPrice.product_id == product_id)
    ).scalar_one_or_none()
    if pp is None:
        pp = ProductPrice(product_id=product_id)
        db.add(pp)
    pp.price = Decimal(str(pricing["selling_price"]))
    pp.discount_percentage = Decimal(str(pricing["discount_percentage"]))

    pw = db.execute(
        select(ProductWeight).where(ProductWeight.product_id == product_id)
    ).scalar_one_or_none()
    if weight is not None:
        if pw is None:
            pw = ProductWeight(product_id=product_id)
            db.add(pw)
        pw.expected_weight = Decimal(str(weight))
        pw.unit = w_unit or "g"

    inv = db.execute(
        select(Inventory).where(Inventory.product_id == product_id)
    ).scalar_one_or_none()
    if inv is None:
        inv = Inventory(product_id=product_id)
        db.add(inv)
    inv.quantity = stock

    # refresh images only if we received new ones this run
    if img_res["thumbnail"]:
        _add_images(db, product_id, img_res)


def _add_images(db, product_id, img_res):
    from app.models.products.product_image import ProductImage
    from sqlalchemy import select, delete

    # Replace existing seeder images to stay idempotent (keep it simple & safe)
    db.execute(
        delete(ProductImage).where(ProductImage.product_id == product_id)
    )
    imgs = []
    if img_res["thumbnail"]:
        imgs.append((img_res["thumbnail"], "thumbnail", True))
    for g in img_res["gallery"]:
        imgs.append((g, "gallery", False))
    for url, itype, is_primary in imgs:
        db.add(ProductImage(
            product_id=product_id,
            image_url=url,
            image_type=itype,
            is_primary=is_primary,
        ))
