"""Ingest vision-dataset-factory accepted images into the SmartCart catalog.

Reads `vision-dataset-factory/storage/accepted/<Product>/<img>` (the factory's
quality-accepted, real-brand product shots), then for each product:
  * find-or-create a backend `products` row by normalized name (MERGE — never
    creates a duplicate product; enriches an existing one if the name matches),
  * for each image: compute sha256; skip if that product already has an image
    with the same hash (persistent dedup via the `content_hash` column),
  * upload the bytes to Cloudinary and insert a `product_images` row.

Idempotent: re-running inserts 0 new rows.

Usage:
    unset PYTHONPATH
    .venv/bin/python -m seed.ingest_vision            # real run
    .venv/bin/python -m seed.ingest_vision --dry-run  # count only
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(BACKEND_ROOT), str(Path(__file__).resolve().parent)]

import config as cfg  # noqa: E402
from db import session_scope, get_product_by_name, get_or_create_category, ensure_tables  # noqa: E402
from app.services.cloudinary_service import cloudinary_service  # noqa: E402
from app.models.products.product import Product  # noqa: E402
from app.models.products.product_image import ProductImage  # noqa: E402

VDF_ROOT = BACKEND_ROOT.parent / "vision-dataset-factory"
ACCEPTED_DIR = VDF_ROOT / "storage" / "accepted"
VDF_DB = VDF_ROOT / "storage" / "vdf.db"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _product_category_lookup() -> dict[str, str]:
    """Map normalized product name -> category from the vision factory DB."""
    out: dict[str, str] = {}
    if not VDF_DB.exists():
        return out
    import sqlite3
    con = sqlite3.connect(str(VDF_DB))
    try:
        rows = con.execute(
            "select lower(canonical_name), category from products "
            "where canonical_name is not null"
        ).fetchall()
        for name, cat in rows:
            if name:
                out[name.strip()] = cat or ""
    finally:
        con.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", default=str(ACCEPTED_DIR),
                    help="override accepted images root")
    args = ap.parse_args()

    if not cloudinary_service.is_configured:
        print("[ERROR] Cloudinary not configured. Refusing to run.")
        return 2
    if not ACCEPTED_DIR.exists():
        print(f"[ERROR] accepted dir not found: {ACCEPTED_DIR}")
        return 2

    ensure_tables()
    cat_lookup = _product_category_lookup()

    folders = sorted([p for p in Path(args.source).iterdir()
                     if p.is_dir()])
    print(f"[info] {len(folders)} product folders under {ACCEPTED_DIR}")

    total_imgs = 0
    uploaded = 0
    skipped_dup = 0
    products_created = 0
    products_matched = 0

    with session_scope() as db:
        for folder in folders:
            product_name = folder.name
            norm = _norm(product_name)

            # find-or-create backend product (MERGE by name -> no duplicate)
            prod = get_product_by_name(db, product_name)
            if prod is None:
                cat_name = cat_lookup.get(norm) or "Vision Imported"
                category = get_or_create_category(db, cat_name)
                sku = f"VIS-{products_created + 1:05d}"
                prod = Product(
                    sku=sku,
                    name=product_name,
                    brand=product_name,
                    category_id=category.id,
                    is_active=True,
                    metadata_={
                        "provenance": {
                            "sourced": False,
                            "source": "vision-dataset-factory",
                            "seeded_by": cfg.SEED_SOURCE_LABEL,
                            "seed_version": cfg.SEED_VERSION,
                        },
                        "subcategory": cat_lookup.get(norm, ""),
                        "category": cat_lookup.get(norm, ""),
                    },
                )
                db.add(prod)
                db.flush()
                products_created += 1
            else:
                products_matched += 1

            # existing hashes for this product (persistent dedup)
            existing = set(
                r[0] for r in db.execute(
                    __import__("sqlalchemy").select(ProductImage.content_hash)
                    .where(ProductImage.product_id == prod.id)
                ).all()
                if r[0]
            )

            for img_path in sorted(folder.iterdir()):
                if img_path.suffix.lower() not in IMAGE_EXTS:
                    continue
                total_imgs += 1
                digest = _sha256(img_path)
                if digest in existing:
                    skipped_dup += 1
                    continue
                existing.add(digest)

                if args.dry_run:
                    skipped_dup += 1  # counted as would-skip to keep totals honest
                    continue

                cloud_url = cloudinary_service.upload_image(
                    img_path.read_bytes(), folder="products")
                if not cloud_url:
                    print(f"[warn] upload failed: {img_path}")
                    skipped_dup += 1
                    continue
                row = ProductImage(
                    product_id=prod.id,
                    image_url=cloud_url,
                    image_type="training",
                    is_primary=(not existing),
                    content_hash=digest,
                )
                db.add(row)
                uploaded += 1

        if not args.dry_run:
            db.commit()

    print(f"[done] folders={len(folders)} products_created={products_created} "
          f"products_matched={products_matched} images={total_imgs} "
          f"uploaded={uploaded} skipped_dup={skipped_dup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
