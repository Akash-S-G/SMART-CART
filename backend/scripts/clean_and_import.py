"""
SmartCart — Clean non-English products & import VDF images.

Phase 1: Delete every product whose name contains non-ASCII-Basic characters.
Phase 2: For each VDF product, ensure it exists in the main DB and attach
         its images (from the vision-dataset-factory local files).
"""
from __future__ import annotations

import re
import string
import sys
import uuid
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent.parent)]

import app.main  # noqa – triggers model registration
from app.db.database import SessionLocal
from app.models.products.product import Product
from app.models.products.product_image import ProductImage
from app.models.products.inventory import Inventory
from app.models.products.inventory_transaction import InventoryTransaction
from app.models.products.prodcut_detection import ProductDetection
from app.models.products.product_price import ProductPrice
from app.models.products.product_weight import ProductWeight
from app.models.products.categories import Category
from app.models.cart.cart_item import CartItem
from app.models.order.order_item import OrderItem
from app.models.products.review import Review

import sqlite3, shutil

# ── helpers ─────────────────────────────────────────────────────────────────

ALLOWED = set(string.ascii_letters + string.digits + string.whitespace + ".,-&'()!/#%:?+*[]@")

def is_clean_english(name: str) -> bool:
    """Return True only if the name contains basic ASCII chars (English)."""
    return all(c in ALLOWED for c in name)


VDF_DB = Path("/home/akash/Desktop/Smart cart/vision-dataset-factory/storage/vdf.db")
VDF_RAW = Path("/home/akash/Desktop/Smart cart/vision-dataset-factory/storage/raw")
STATIC_DIR = Path("/home/akash/Desktop/Smart cart/backend/static/products")

# ── PHASE 1: purge non-English products ─────────────────────────────────────

def purge_non_english(db):
    prods = db.query(Product).all()
    to_delete = [p for p in prods if not is_clean_english(p.name)]

    print(f"\n{'='*60}")
    print(f"  PHASE 1 — Purge non-English products")
    print(f"{'='*60}")
    print(f"  Total products in DB:            {len(prods)}")
    print(f"  Non-English products to delete:  {len(to_delete)}")

    if not to_delete:
        print("  Nothing to clean.")
        return 0

    # Print some samples
    print("\n  Samples being removed:")
    for p in to_delete[:15]:
        print(f"    [{p.sku}] {p.name}")
    if len(to_delete) > 15:
        print(f"    ... and {len(to_delete) - 15} more")

    ids = [p.id for p in to_delete]

    # Cascade delete dependents
    tables = [
        ("CartItem",            CartItem,            CartItem.product_id),
        ("OrderItem",           OrderItem,           OrderItem.product_id),
        ("Review",              Review,              Review.product_id),
        ("InventoryTransaction", InventoryTransaction, InventoryTransaction.product_id),
        ("Inventory",           Inventory,           Inventory.product_id),
        ("ProductDetection",    ProductDetection,    ProductDetection.product_id),
        ("ProductPrice",        ProductPrice,        ProductPrice.product_id),
        ("ProductWeight",       ProductWeight,       ProductWeight.product_id),
        ("ProductImage",        ProductImage,        ProductImage.product_id),
    ]

    for label, model, col in tables:
        n = db.query(model).filter(col.in_(ids)).delete(synchronize_session=False)
        if n: print(f"    Deleted {n} {label} records")

    n = db.query(Product).filter(Product.id.in_(ids)).delete(synchronize_session=False)
    print(f"    Deleted {n} Product records")

    db.commit()
    remaining = db.query(Product).count()
    print(f"\n  Products remaining after purge: {remaining}")
    return n


# ── PHASE 2: import VDF products/images into main DB ───────────────────────

def import_vdf_products(db):
    print(f"\n{'='*60}")
    print(f"  PHASE 2 — Import VDF products & images")
    print(f"{'='*60}")

    if not VDF_DB.exists():
        print("  [SKIP] VDF database not found.")
        return

    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(VDF_DB))
    vdf_products = conn.execute(
        "SELECT id, canonical_brand, canonical_name, category FROM products"
    ).fetchall()

    products_added = 0
    images_added = 0

    # Get or create a default "Groceries" category
    cat = db.query(Category).filter(Category.name == "Groceries").first()
    if not cat:
        cat = Category(id=str(uuid.uuid4()), name="Groceries", description="General grocery items")
        db.add(cat)
        db.flush()

    for vdf_id, brand, name, category in vdf_products:
        if not is_clean_english(name):
            print(f"    [SKIP non-English VDF] {name}")
            continue

        # Check if product already exists in main DB by name (case-insensitive)
        existing = db.query(Product).filter(Product.name.ilike(name)).first()

        if not existing:
            # Create new product
            sku = f"VDF-{vdf_id:04d}"
            product_id = str(uuid.uuid4())
            new_prod = Product(
                id=product_id,
                sku=sku,
                barcode=f"VDF{vdf_id:08d}",
                name=name,
                description=f"{brand} {name}" if brand else name,
                brand=brand or "Unknown",
                category_id=cat.id,
                is_active=True,
            )
            db.add(new_prod)
            db.flush()

            # Add price
            price = ProductPrice(
                id=str(uuid.uuid4()),
                product_id=product_id,
                price=99.00,
                gst_percentage=18.0,
                discount_percentage=0.0,
            )
            db.add(price)

            # Add inventory
            inv = Inventory(
                id=str(uuid.uuid4()),
                product_id=product_id,
                quantity=50,
                reorder_level=10,
                max_capacity=200,
                location="Aisle A",
            )
            db.add(inv)

            existing = new_prod
            products_added += 1
            print(f"    [+] Product created: {name} ({sku})")
        else:
            product_id = existing.id

        # Now import VDF images for this product
        vdf_images = conn.execute(
            "SELECT id, local_path, sha256 FROM images WHERE product_id = ? AND status = 'active'",
            (vdf_id,)
        ).fetchall()

        for img_id, local_path, sha256 in vdf_images:
            # Check if image already exists
            existing_img = db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.content_hash == sha256,
            ).first()

            if existing_img:
                continue  # Already imported

            # Copy file to static dir
            src = VDF_RAW / Path(local_path).name
            if not src.exists():
                src = VDF_RAW.parent / local_path  # try relative path
            if not src.exists():
                continue

            dest_name = f"vdf_{vdf_id}_{img_id}_{src.name}"
            dest = STATIC_DIR / dest_name
            shutil.copy2(src, dest)

            img_record = ProductImage(
                id=str(uuid.uuid4()),
                product_id=product_id,
                image_url=f"/static/products/{dest_name}",
                image_type="training",
                is_primary=(img_id == vdf_images[0][0]),  # First image is primary
                content_hash=sha256,
            )
            db.add(img_record)
            images_added += 1

        db.flush()

    conn.close()
    db.commit()

    print(f"\n  Summary:")
    print(f"    New products added:  {products_added}")
    print(f"    New images imported: {images_added}")


# ── main ────────────────────────────────────────────────────────────────────

def main():
    print(">>> SmartCart AI — Catalog Cleanup & VDF Import")
    from app.db.database import engine
    from app.db.base import Base
    print("[info] Ensuring all database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        purge_non_english(db)
        import_vdf_products(db)

        final_count = db.query(Product).count()
        img_count = db.query(ProductImage).count()
        print(f"\n{'='*60}")
        print(f"  FINAL STATE")
        print(f"{'='*60}")
        print(f"  Total products:  {final_count}")
        print(f"  Total images:    {img_count}")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
