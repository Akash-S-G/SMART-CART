"""
Script to:
1. Ensure EVERY remaining product in the DB has a genuine uploaded Cloudinary image.
2. For the ~18 products currently using fallbacks, upload real high-res images to Cloudinary
   under smartcart/products/<sku>/ and update product_images in PostgreSQL.
"""

import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
import cloudinary
import cloudinary.uploader
import urllib.request
import uuid
from sqlalchemy import create_engine, text

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

CURATED_IMAGES = {
    'VIS-00017': 'https://images.openfoodfacts.org/images/products/890/910/602/6346/front_en.8.400.jpg', # Surf Excel
    'VIS-00001': 'https://images.openfoodfacts.org/images/products/890/172/512/3123/front_en.13.400.jpg', # Aashirvaad Atta
    'VIS-00019': 'https://m.media-amazon.com/images/I/71N1pC2rKKL._SL1500_.jpg', # Yippee Magic Masala
    'SC-TEST-COLA': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=800&q=80', # Coca Cola
    'SC-FRU-00091': 'https://images.unsplash.com/photo-1610970881699-44a5587cabec?auto=format&fit=crop&w=800&q=80', # Green Smoothie
    'SC-FRU-00129': 'https://images.unsplash.com/photo-1594911772125-07fc7a2d8d9f?auto=format&fit=crop&w=800&q=80', # Figs
    'SC-FRU-00166': 'https://images.unsplash.com/photo-1517093707446-f91cb97864f1?auto=format&fit=crop&w=800&q=80', # Granola
    'SC-FRU-00173': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80', # Plantain Chips
    'SC-FRU-00222': 'https://images.openfoodfacts.org/images/products/081/507/402/2915/front_en.212.400.jpg', # Avocado
    'SC-VEG-00067': 'https://images.unsplash.com/photo-1505253758473-96b301b5c81d?auto=format&fit=crop&w=800&q=80', # Salsa Dip
    'SC-VEG-00072': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=800&q=80', # Sun-Dried Tomatoes
    'SC-BAK-00077': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=800&q=80', # Sourdough
    'SC-BAK-00086': 'https://images.unsplash.com/photo-1586444248902-2f64eddc13df?auto=format&fit=crop&w=800&q=80', # Jason Sourdough
    'SC-BEV-00071': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80', # Hazelnut drink
    'SC-BEV-00074': 'https://images.openfoodfacts.org/images/products/611/125/242/1568/front_en.72.400.jpg', # Aquafina
    'SC-BEV-00077': 'https://images.unsplash.com/photo-1527661591475-527312dd65f5?auto=format&fit=crop&w=800&q=80', # Acyl Beverage
    'SC-FRO-00051': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=800&q=80', # Lays Chips
    'SC-FRO-00069': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80', # Ginger Shot
}

engine = create_engine('postgresql+psycopg://smartcart_user:777@localhost:5432/smartcart')

with engine.begin() as conn:
    for sku, source_url in CURATED_IMAGES.items():
        prod = conn.execute(text("SELECT id, name FROM products WHERE sku=:sku;"), {'sku': sku}).fetchone()
        if not prod:
            continue
        p_id, p_name = prod
        try:
            res = cloudinary.uploader.upload(
                source_url,
                folder=f"smartcart/products/{sku}",
                use_filename=True,
                unique_filename=False
            )
            c_url = res.get('secure_url')
            if c_url:
                # Update product_images table
                conn.execute(text("DELETE FROM product_images WHERE product_id=:pid;"), {'pid': p_id})
                conn.execute(
                    text("""
                        INSERT INTO product_images (id, product_id, image_url, is_primary, image_type)
                        VALUES (:id, :pid, :url, true, 'thumbnail');
                    """),
                    {'id': str(uuid.uuid4()), 'pid': p_id, 'url': c_url}
                )
                print(f"[OK] {sku} ({p_name}) -> {c_url}")
        except Exception as e:
            print(f"[FAIL] {sku}: {e}")

print("Upload pass complete.")
