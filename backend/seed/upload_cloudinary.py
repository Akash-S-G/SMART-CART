"""Backfill: upload all local product images to Cloudinary and repoint DB rows.

The seeder already uploads *new* downloads to Cloudinary when it is configured,
but images that were seeded earlier (or already on disk) still carry local
`/static/products/...` URLs.  This script walks every product image row, uploads
the underlying file to Cloudinary, and rewrites the URL to the secure cloud URL.

Idempotent: rows whose URL already points at cloudinary.com are skipped, so the
script is safe to re-run.

Usage:
    unset PYTHONPATH
    .venv/bin/python -m seed.upload_cloudinary            # all images
    .venv/bin/python -m seed.upload_cloudimary --dry-run  # count only
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(BACKEND_ROOT), str(Path(__file__).resolve().parent)]

import config as cfg  # noqa: E402
from db import session_scope, ensure_tables  # noqa: E402
from app.services.cloudinary_service import cloudinary_service  # noqa: E402
from app.models.products.product_image import ProductImage  # noqa: E402


def _local_path_from_url(url: str) -> Path | None:
    """Map a /static/products/<sku>/<file> URL to a file under IMAGES_ROOT."""
    if "cloudinary.com" in url:
        return None
    marker = "/static/products/"
    idx = url.find(marker)
    if idx < 0:
        return None
    rel = url[idx + len(marker):]
    return cfg.IMAGES_ROOT / rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="count only, no uploads")
    args = ap.parse_args()

    if not cloudinary_service.is_configured:
        print("[ERROR] Cloudinary is NOT configured (check CLOUDINARY_* env vars). "
              "Refusing to run.")
        return 2

    ensure_tables()

    total = 0
    uploaded = 0
    skipped = 0
    failed = 0

    with session_scope() as db:
        rows = db.execute(
            __import__("sqlalchemy").select(ProductImage)
        ).scalars().all()
        total = len(rows)
        print(f"[info] {total} product image rows to process (dry_run={args.dry_run})")

        for img in rows:
            url = img.image_url or ""
            if "cloudinary.com" in url:
                skipped += 1
                continue
            local = _local_path_from_url(url)
            if local is None or not local.exists():
                # Try to resolve via the stored relative path as a fallback.
                alt = cfg.IMAGES_ROOT / Path(url.split("/static/products/", 1)[-1]) if "/static/products/" in url else None
                if alt and alt.exists():
                    local = alt
                else:
                    failed += 1
                    print(f"[warn] missing local file for {url}")
                    continue

            if args.dry_run:
                skipped += 1
                continue

            cloud_url = cloudinary_service.upload_url(str(local), folder="products")
            if not cloud_url:
                failed += 1
                print(f"[warn] upload failed for {local}")
                continue
            img.image_url = cloud_url
            # keep local file as fallback; just repoint the URL
            uploaded += 1
            if (uploaded % 25) == 0:
                print(f"[progress] uploaded {uploaded}/{total - skipped} ...")

        if not args.dry_run:
            db.commit()

    print(f"[done] total={total} uploaded={uploaded} skipped={skipped} failed={failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
