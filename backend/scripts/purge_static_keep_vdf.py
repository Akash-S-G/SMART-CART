"""
SmartCart AI — Purge Static & Sync VDF Only Pipeline

1. Purges non-VDF image rows from PostgreSQL `product_images` table.
2. Deletes non-VDF image files from `backend/static/products/`.
3. Purges non-VDF assets on Cloudinary (if configured).
4. Ensures all remaining VDF dataset images are uploaded to Cloudinary and updated in DB.
5. Invokes YOLO training on the VDF dataset.
"""

from __future__ import annotations

import sys
import os
import shutil
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import app.main  # noqa - registers all models
from app.db.database import SessionLocal
from app.models.products.product_image import ProductImage
from app.services.cloudinary_service import cloudinary_service


def is_vdf_image(url_or_name: str) -> bool:
    if not url_or_name:
        return False
    lower = url_or_name.lower()
    return "vdf_" in lower or "prod_" in lower or "combined_groceries" in lower


def main():
    print(">>> SmartCart AI — Purging Static Images & Keeping VDF Dataset Only")

    db = SessionLocal()

    # 1. DB Purge of non-VDF images
    total_db = db.query(ProductImage).count()
    all_images = db.query(ProductImage).all()

    db_deleted = 0
    cloudinary_deleted = 0

    for img in all_images:
        url = img.image_url or ""
        if not is_vdf_image(url):
            # Destroy on Cloudinary if it's a Cloudinary asset
            if "cloudinary.com" in url and cloudinary_service.is_configured:
                try:
                    # Extract public_id from Cloudinary URL
                    # Example: .../products/filename.jpg -> products/filename
                    parts = url.split("/upload/")
                    if len(parts) > 1:
                        rel = parts[1].split("/", 1)[-1]
                        public_id = rel.rsplit(".", 1)[0]
                        cloudinary_service.destroy(public_id)
                        cloudinary_deleted += 1
                except Exception as e:
                    print(f"  [warn] Cloudinary destroy error: {e}")

            db.delete(img)
            db_deleted += 1

    db.commit()
    print(f"  [DB] Purged {db_deleted} non-VDF image records from PostgreSQL. Total remaining in DB: {total_db - db_deleted}")
    if cloudinary_deleted > 0:
        print(f"  [Cloudinary] Purged {cloudinary_deleted} non-VDF assets from Cloudinary.")

    # 2. Disk Purge of non-VDF files under static/products/
    static_dir = BACKEND_ROOT / "static" / "products"
    disk_deleted = 0

    if static_dir.exists():
        for file_path in list(static_dir.rglob("*")):
            if file_path.is_file():
                if not is_vdf_image(file_path.name):
                    try:
                        file_path.unlink()
                        disk_deleted += 1
                    except Exception as e:
                        print(f"  [warn] File delete failed for {file_path.name}: {e}")

        # Clean empty directories
        for dir_path in list(static_dir.rglob("*")):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                except Exception:
                    pass

    print(f"  [Disk] Purged {disk_deleted} non-VDF image files from static/products/.")

    # 3. Sync remaining VDF images to Cloudinary
    if cloudinary_service.is_configured:
        print("\n>>> Syncing VDF images to Cloudinary...")
        from seed.upload_cloudinary import main as sync_cloudinary
        sync_cloudinary()

    print("\n>>> Purge & Sync Complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
