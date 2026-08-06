"""Re-source missing images for products that have 0 images.

Specifically targets the two known gaps (Surf Excel, Yippee Magic Masala) whose
vision-factory accepted images were deleted. Fetches a real, openly-licensed
front image from Open Food Facts by brand, downloads it, uploads to Cloudinary,
and attaches it to the existing product row. Idempotent: skips any product that
already has >=1 image.

Usage:
    unset PYTHONPATH
    .venv/bin/python -m seed.resync_images
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
for p in (str(HERE), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

import config as cfg  # noqa: E402
from db import session_scope  # noqa: E402
from http_client import HttpClient  # noqa: E402
from app.services.cloudinary_service import cloudinary_service  # noqa: E402
from app.models.products.product import Product  # noqa: E402
from app.models.products.product_image import ProductImage  # noqa: E402
from sqlalchemy import select, func  # noqa: E402

# Brand -> OFF brand_tags query. We pick the first hit whose name contains the
# product keyword and that has a front image.
TARGETS = {
    "Surf Excel": "surf",
    "Yippee Magic Masala": "yippee",
}


def _to_full(url: str) -> str:
    return re.sub(r"\.(\d+|[a-z]{1,3})\.jpg$", ".full.jpg", url, count=1)


def _find_image(http: HttpClient, brand_tag: str, keyword: str):
    url = (f"{cfg.OFF_BASE}/api/v2/search?brands_tags={brand_tag}"
           f"&page=1&page_size=25"
           f"&fields=code,product_name,brands,image_front_url,image_packaging_url"
           f"&json=1")
    data, _ = http.get_json(url)
    prods = (data or {}).get("products", []) or []
    for p in prods:
        nm = (p.get("product_name") or "").lower()
        br = (p.get("brands") or "").lower()
        if keyword.lower() in nm or keyword.lower() in br:
            fu = p.get("image_front_url") or p.get("image_packaging_url")
            if fu and fu.startswith("http"):
                return _to_full(fu)
    return None


def main() -> int:
    if not cloudinary_service.is_configured:
        print("[ERROR] Cloudinary not configured.")
        return 2
    http = HttpClient()
    fixed = 0
    for name, brand_tag in TARGETS.items():
        with session_scope() as db:
            prod = db.execute(
                select(Product).where(Product.name == name)
            ).scalar_one_or_none()
            if prod is None:
                print(f"[skip] product not found: {name}")
                continue
            has = db.execute(
                select(func.count(ProductImage.id))
                .where(ProductImage.product_id == prod.id)
            ).scalar_one()
            if has > 0:
                print(f"[skip] {name} already has {has} image(s)")
                continue
            img_url = _find_image(http, brand_tag, name.split()[0])
            if not img_url:
                print(f"[warn] no OFF image found for {name}")
                continue
            raw = http.get_bytes(img_url)
            if not raw or not raw.ok:
                print(f"[warn] download failed for {name}: {img_url}")
                continue
            cloud_url = cloudinary_service.upload_image(raw.body, folder="products")
            if not cloud_url:
                print(f"[warn] cloud upload failed for {name}")
                continue
            import hashlib
            db.add(ProductImage(
                product_id=prod.id,
                image_url=cloud_url,
                image_type="thumbnail",
                is_primary=True,
                content_hash=hashlib.sha256(raw.body).hexdigest(),
            ))
            db.flush()
            fixed += 1
            print(f"[ok] {name} -> {cloud_url}")
    print(f"[done] images fixed: {fixed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
