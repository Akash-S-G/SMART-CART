"""
Script to:
1. Identify and delete ALL Pet Care products (by category 'Pet Care' or SKU 'SC-PET%').
2. Identify and delete all products that contain numbers in their name
   (e.g., 'Product 0653', 'Baby Care Product 0666', weights/specs like 'Whiskas And 400g', etc.).
3. Clean all associated records across child tables (product_images, product_prices, inventory, etc.).
4. Delete corresponding local image files under backend/static/products/.
5. Update backend/scripts/catalog_names.txt.
"""

import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine, text

def run():
    engine = create_engine('postgresql+psycopg://smartcart_user:777@localhost:5432/smartcart')
    
    with engine.connect() as conn:
        # Find products to delete:
        # Condition 1: Pet care products (sku starts with SC-PET or category is Pet Care)
        # Condition 2: Products whose name contains digits [0-9]
        query = text("""
            SELECT p.id, p.sku, p.name, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.sku LIKE 'SC-PET%'
               OR c.name ILIKE '%pet%'
               OR p.name ~ '[0-9]';
        """)
        to_delete = conn.execute(query).fetchall()

    print(f"Total products identified for removal: {len(to_delete)}")
    
    if not to_delete:
        print("No matching products found.")
        return

    del_ids = [r[0] for r in to_delete]
    del_skus = [r[1] for r in to_delete]

    print("Sample products being removed:")
    for r in to_delete[:15]:
        print(f"  [{r[3]}] {r[1]} --> {r[2]}")

    # Clean local image files for deleted SKUs
    static_products_dir = Path("backend/static/products")
    deleted_files_count = 0
    deleted_dirs_count = 0

    for sku in del_skus:
        # 1. Matching individual files (e.g., prod_SC-PET-00004_0.jpg)
        for f in static_products_dir.glob(f"*{sku}*.*"):
            if f.is_file():
                try:
                    f.unlink()
                    deleted_files_count += 1
                except Exception as e:
                    pass
        # 2. Matching SKU directories (e.g., backend/static/products/SC-PET-00004/)
        sku_dir = static_products_dir / sku
        if sku_dir.is_dir():
            try:
                shutil.rmtree(sku_dir)
                deleted_dirs_count += 1
            except Exception as e:
                pass

    print(f"Deleted {deleted_files_count} local image files and {deleted_dirs_count} SKU directories.")

    with engine.begin() as conn:
        # Cascade delete across all child tables
        child_tables = [
            'product_images',
            'product_prices',
            'inventory',
            'product_weights',
            'product_detection',
            'cart_items',
            'order_items',
            'reviews',
            'wishlists',
            'inventory_transactions'
        ]
        
        for table in child_tables:
            conn.execute(
                text(f"DELETE FROM {table} WHERE product_id = ANY(:ids);"),
                {'ids': del_ids}
            )
            print(f"Cleaned references from {table}")

        # Clean from backup and cloud tables if present
        conn.execute(
            text("DELETE FROM cloud.product_images WHERE product_id = ANY(:ids);"),
            {'ids': del_ids}
        )
        conn.execute(
            text("DELETE FROM public.product_images_backup WHERE product_id = ANY(:ids);"),
            {'ids': del_ids}
        )

        # Delete from products
        res = conn.execute(
            text("DELETE FROM products WHERE id = ANY(:ids);"),
            {'ids': del_ids}
        )
        print(f"Successfully deleted {res.rowcount} products from database.")

        # If Pet Care category is empty, we can clean up category or keep it
        pet_cat_count = conn.execute(text("SELECT count(*) FROM products p JOIN categories c ON p.category_id=c.id WHERE c.name ILIKE '%pet%';")).scalar()
        if pet_cat_count == 0:
            conn.execute(text("DELETE FROM categories WHERE name ILIKE '%pet%';"))
            print("Removed empty 'Pet Care' category.")

    # Re-fetch remaining products and update catalog_names.txt
    with engine.connect() as conn:
        remaining = conn.execute(text("SELECT sku, name FROM products ORDER BY sku;")).fetchall()

    with open('backend/scripts/catalog_names.txt', 'w') as f:
        for sku, name in remaining:
            f.write(f"{sku}\t{name}\n")

    print(f"Updated backend/scripts/catalog_names.txt: {len(remaining)} clean products remaining.")

if __name__ == "__main__":
    run()
