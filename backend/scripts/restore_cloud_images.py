"""
Restore Product Images:
1. Upload any un-uploaded local product images to Cloudinary (folder: smartcart/products/<SKU>).
2. Gather all genuine Cloudinary URLs for each product SKU.
3. Save the genuine Cloudinary URLs into:
   - A dedicated Postgres table/schema: `cloud.product_images` (isolated from public.product_images so local URLs are never overwritten)
   - A portable JSON mapping file: `backend/cloud_product_images.json`
"""

import os
import glob
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('backend/.env')
import cloudinary
import cloudinary.uploader
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
    
    print(f"Total products in DB: {len(products)}")

    # 1. Fetch all existing Cloudinary SKU folders
    print("Fetching Cloudinary folders under smartcart/products...")
    cloud_folders = set()
    next_cursor = None
    while True:
        if next_cursor:
            res = cloudinary.api.subfolders('smartcart/products', max_results=500, next_cursor=next_cursor)
        else:
            res = cloudinary.api.subfolders('smartcart/products', max_results=500)
        cloud_folders.update([f['name'] for f in res.get('folders', [])])
        next_cursor = res.get('next_cursor')
        if not next_cursor:
            break
    print(f"Existing SKU folders in Cloudinary: {len(cloud_folders)}")

    # 2. Check local files for any missing SKUs and upload them
    base_dir = Path("backend/static/products")
    uploaded_count = 0
    
    for p_id, sku, name in products:
        if sku not in cloud_folders:
            # find local images
            matching_files = list(base_dir.glob(f"*{sku}*.*"))
            matching_files = [f for f in matching_files if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')]
            sku_dir = base_dir / sku
            if sku_dir.is_dir():
                matching_files.extend([f for f in sku_dir.glob("*.*") if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')])
            
            if matching_files:
                # Upload the primary file
                main_file = matching_files[0]
                try:
                    res = cloudinary.uploader.upload(
                        str(main_file),
                        folder=f"smartcart/products/{sku}",
                        use_filename=True,
                        unique_filename=False
                    )
                    cloud_folders.add(sku)
                    uploaded_count += 1
                    print(f"Uploaded {sku} -> {res.get('secure_url')}")
                except Exception as e:
                    print(f"Upload failed for {sku}: {e}")

    print(f"Newly uploaded products to Cloudinary: {uploaded_count}")

    # 3. Retrieve Cloudinary URLs for all products
    print("Fetching image URLs from Cloudinary for each product...")
    product_images_cloud = []
    
    # We can batch or iterate per SKU that exists in cloud_folders
    sku_to_prod = {p[1]: p for p in products}
    
    for sku, p_info in sku_to_prod.items():
        if sku in cloud_folders:
            try:
                res = cloudinary.api.resources(
                    type="upload",
                    prefix=f"smartcart/products/{sku}",
                    max_results=10
                )
                items = res.get("resources", [])
                for idx, item in enumerate(items):
                    sec_url = item.get("secure_url")
                    if sec_url:
                        product_images_cloud.append({
                            "id": str(uuid.uuid4()),
                            "product_id": p_info[0],
                            "sku": sku,
                            "product_name": p_info[2],
                            "image_url": sec_url,
                            "is_primary": (idx == 0),
                            "image_type": "thumbnail" if idx == 0 else "gallery"
                        })
            except Exception as e:
                print(f"Error fetching resources for {sku}: {e}")

    print(f"Total cloud images gathered: {len(product_images_cloud)}")

    # 4. Save to JSON
    json_path = Path("backend/cloud_product_images.json")
    with open(json_path, "w") as f:
        json.dump(product_images_cloud, f, indent=2)
    print(f"Saved {len(product_images_cloud)} image mappings to {json_path}")

    # 5. Populate into isolated PostgreSQL table `cloud.product_images`
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS cloud;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cloud.product_images (
                id text PRIMARY KEY,
                product_id text,
                sku text,
                image_url text,
                is_primary boolean,
                image_type text
            );
        """))
        conn.execute(text("TRUNCATE TABLE cloud.product_images;"))
        
        insert_stmt = text("""
            INSERT INTO cloud.product_images (id, product_id, sku, image_url, is_primary, image_type)
            VALUES (:id, :product_id, :sku, :image_url, :is_primary, :image_type);
        """)
        
        batch = [
            {
                "id": img["id"],
                "product_id": img["product_id"],
                "sku": img["sku"],
                "image_url": img["image_url"],
                "is_primary": img["is_primary"],
                "image_type": img["image_type"]
            }
            for img in product_images_cloud
        ]
        if batch:
            conn.execute(insert_stmt, batch)
            
    print("Successfully populated `cloud.product_images` table without touching local `public.product_images`.")

if __name__ == "__main__":
    run()
