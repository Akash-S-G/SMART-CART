"""
Backfill product data completeness for local psql (652 -> 1000+)
- Fixes missing description, brand, price, inventory, images
- Generates additional synthetic products to reach 1000+
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
# Import all models to register mappers (like main.py)
import app.models.products  # noqa: F401
import app.models.user  # noqa: F401
import app.models.payment  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.cart  # noqa: F401
import app.models.order  # noqa: F401
from app.models.products.product import Product
from app.models.products.product_price import ProductPrice
from app.models.products.inventory import Inventory
from app.models.products.product_image import ProductImage
from app.models.products.categories import Category
from sqlalchemy import text
import uuid
import random

# Category-aware synthetic data
CATEGORIES = {
    "Fruits": {"brand": "Fresh Farms", "img": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=500&q=80"},
    "Dairy": {"brand": "Amul", "img": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&q=80"},
    "Bakery": {"brand": "Britannia", "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&q=80"},
    "Snacks": {"brand": "Haldiram's", "img": "https://images.unsplash.com/photo-1599490659213-e2b9527bd087?w=500&q=80"},
    "Beverages": {"brand": "Coca-Cola", "img": "https://images.unsplash.com/photo-1624552184280-9e9631bbeee9?w=500&q=80"},
}

def backfill_existing(db):
    products = db.query(Product).all()
    cats = {c.id: c.name for c in db.query(Category).all()}
    # fallback cat
    fallback_cat_id = list(cats.keys())[0] if cats else None

    fixed_desc = 0
    fixed_brand = 0
    fixed_price = 0
    fixed_inv = 0
    fixed_img = 0

    for p in products:
        cat_name = cats.get(p.category_id, "Grocery")
        meta = CATEGORIES.get(cat_name, {"brand": "SmartCart Essentials", "img": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&q=80"})

        # brand
        if not p.brand:
            p.brand = meta["brand"]
            fixed_brand += 1

        # description
        if not p.description:
            p.description = f"Premium {p.name} — 100% authentic {cat_name.lower()} from {p.brand}. Freshly sourced, quality-checked, 10-min delivery. Ingredients: natural, no added preservatives. Storage: cool & dry. Weight: standard retail pack."
            fixed_desc += 1

        # price
        if not p.price:
            price = ProductPrice(id=str(uuid.uuid4()), product_id=p.id, price=round(random.uniform(29, 499), 2), discount_percentage=0)
            db.add(price)
            fixed_price += 1

        # inventory
        if not p.inventory:
            inv = Inventory(id=str(uuid.uuid4()), product_id=p.id, quantity=random.randint(20, 200), reorder_level=10, max_capacity=200)
            db.add(inv)
            fixed_inv += 1

        # images - check if has any
        if not p.images or len(p.images) == 0:
            # also check if product_images empty, create one
            img = ProductImage(id=str(uuid.uuid4()), product_id=p.id, image_url=meta["img"], is_primary=True)
            db.add(img)
            fixed_img += 1

    db.commit()
    print(f"Backfilled existing 652: desc {fixed_desc}, brand {fixed_brand}, price {fixed_price}, inv {fixed_inv}, img {fixed_img}")

def generate_new(db, target=1005):
    existing = db.query(Product).count()
    need = target - existing
    if need <= 0:
        print(f"Already {existing} >= {target}, no generation needed")
        return

    cats = db.query(Category).all()
    if not cats:
        print("No categories found, cannot generate")
        return

    # Ensure we have at least 5 categories, create missing if needed
    needed_cats = ["Vegetables", "Staples", "Personal Care", "Dairy", "Snacks"]
    for name in needed_cats:
        if not any(c.name == name for c in cats):
            c = Category(id=str(uuid.uuid4()), name=name, description=f"{name} category")
            db.add(c)
            db.commit()
            cats.append(c)

    print(f"Generating {need} new products to reach {target}...")
    for i in range(need):
        cat = random.choice(cats)
        cat_meta = CATEGORIES.get(cat.name, {"brand": "SmartCart Essentials", "img": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&q=80"})
        name = f"{cat.name} Product {existing + i + 1:04d}"
        sku = f"SC-{cat.name[:3].upper()}-{existing + i + 1:05d}"
        # Use deterministic price
        price_val = round(random.uniform(19, 599), 2)
        stock = random.randint(30, 150)
        # Create product
        p = Product(
            id=str(uuid.uuid4()),
            name=name,
            sku=sku,
            barcode=str(random.randint(8901000000000, 8901999999999)),
            description=f"Authentic {name} — {cat_meta['brand']} quality, 100% genuine, lab-tested, 10-min delivery. Perfect for daily use. Net weight: standard pack. Origin: India.",
            brand=cat_meta["brand"],
            category_id=cat.id,
            is_active=True,
        )
        db.add(p)
        db.flush()  # to get id for FK
        # price
        pp = ProductPrice(id=str(uuid.uuid4()), product_id=p.id, price=price_val, discount_percentage=random.choice([0,0,0,5,10]))
        db.add(pp)
        # inventory
        inv = Inventory(id=str(uuid.uuid4()), product_id=p.id, quantity=stock, reorder_level=10, max_capacity=200)
        db.add(inv)
        # image
        img = ProductImage(id=str(uuid.uuid4()), product_id=p.id, image_url=cat_meta["img"], is_primary=True)
        db.add(img)
        if (i+1) % 100 == 0:
            db.commit()
            print(f"  {i+1}/{need} generated")
    db.commit()
    print(f"Generation complete: {db.query(Product).count()} total")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        backfill_existing(db)
        generate_new(db, target=1005)
        # verify
        from sqlalchemy import text
        total = db.query(Product).count()
        no_desc = db.query(Product).filter((Product.description == None) | (Product.description == '')).count()
        no_brand = db.query(Product).filter((Product.brand == None) | (Product.brand == '')).count()
        # images via left join count
        no_img = db.execute(text("SELECT count(*) FROM products p LEFT JOIN product_images pi ON pi.product_id=p.id WHERE pi.product_id IS NULL")).scalar()
        print(f"FINAL: total {total}, no_desc {no_desc}, no_brand {no_brand}, no_img {no_img}")
    finally:
        db.close()
