"""
Fast batch fetch of Cloudinary images for all products:
Fetches 500 images at a time from smartcart/products prefix instead of 1 request per SKU.
Stores in:
- Postgres schema table: `cloud.product_images`
- JSON file: `backend/cloud_product_images.json`
Local `public.product_images` is NEVER modified.
"""

import os
import re
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('backend/.env')
import cloudinary
import cloudinary.api
from sqlalchemy import create_engine, text

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def run():
    engine = create_engine('postgresql+psycopg://smartcart_user:777@localhost:5432/smartcart')
    
    with engine.connect() as conn:
        products = conn.execute(text("SELECT id, sku, name FROM products;")).fetchall()
    
    sku_to_prod = {p[1]: (p[0], p[2]) for p in products}
    print(f"Loaded {len(products)} products from DB.")

    # Fetch all resources under smartcart/products in pages of 500
    print("Fetching Cloudinary resources in batches of 500...")
    all_resources = []
    next_cursor = None
    page = 1
    while True:
        if next_cursor:
            res = cloudinary.api.resources(
                type="upload",
                prefix="smartcart/products",
                max_results=500,
                next_cursor=next_cursor
            )
        else:
            res = cloudinary.api.resources(
                type="upload",
                prefix="smartcart/products",
                max_results=500
            )
        items = res.get("resources", [])
        all_resources.extend(items)
        print(f"Page {page}: fetched {len(items)} items (total: {len(all_resources)})")
        page += 1
        next_cursor = res.get("next_cursor")
        if not next_cursor:
            break

    print(f"Total Cloudinary resources retrieved: {len(all_resources)}")

    # Map resources to SKUs
    # Public ID pattern: smartcart/products/<SKU>/<filename> OR smartcart/products/<id>
    sku_images = {}
    pattern = re.compile(r"smartcart/products/([^/]+)/")

    for r in all_resources:
        pub_id = r.get("public_id", "")
        sec_url = r.get("secure_url", "")
        m = pattern.search(pub_id)
        if m:
            sku = m.group(1)
            sku_images.setdefault(sku, []).append(sec_url)

    print(f"Matched images for {len(sku_images)} distinct SKUs.")

    records = []
    matched_db_products = 0

    for sku, (p_id, p_name) in sku_to_prod.items():
        urls = sku_images.get(sku, [])
        if urls:
            matched_db_products += 1
            for idx, u in enumerate(urls):
                records.append({
                    "id": str(uuid.uuid4()),
                    "product_id": p_id,
                    "sku": sku,
                    "product_name": p_name,
                    "image_url": u,
                    "is_primary": (idx == 0),
                    "image_type": "thumbnail" if idx == 0 else "gallery"
                })

    print(f"DB products mapped with authentic Cloudinary images: {matched_db_products} / {len(products)}")
    print(f"Total cloud image records generated: {len(records)}")

    # 1. Save JSON
    json_path = Path("backend/cloud_product_images.json")
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved JSON mapping to {json_path}")

    # 2. Save to separate database schema: cloud.product_images
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS cloud;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cloud.product_images (
                id text PRIMARY KEY,
                product_id text,
                sku text,
                product_name text,
                image_url text,
                is_primary boolean,
                image_type text
            );
        """))
        conn.execute(text("TRUNCATE TABLE cloud.product_images;"))
        if records:
            conn.execute(
                text("""
                    INSERT INTO cloud.product_images (id, product_id, sku, product_name, image_url, is_primary, image_type)
                    VALUES (:id, :product_id, :sku, :product_name, :image_url, :is_primary, :image_type);
                """),
                records
            )

    print("Finished! Local `public.product_images` was left untouched.")

if __name__ == "__main__":
    run()
