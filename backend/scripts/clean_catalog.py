from __future__ import annotations

import string
import sys
from pathlib import Path

# Add backend to path
sys.path[:0] = [str(Path(__file__).resolve().parent.parent)]

import app.main
from app.db.database import SessionLocal
from app.models.products.product import Product
from app.models.products.product_image import ProductImage
from app.models.products.inventory import Inventory
from app.models.products.inventory_transaction import InventoryTransaction
from app.models.products.prodcut_detection import ProductDetection
from app.models.products.product_price import ProductPrice
from app.models.products.product_weight import ProductWeight
from app.models.cart.cart_item import CartItem
from app.models.order.order_item import OrderItem

def is_clean_english(s: str) -> bool:
    allowed = string.ascii_letters + string.digits + string.whitespace + ".,-&'()!/#%:?+*[]"
    return all(c in allowed for c in s)

def main():
    print(">>> SmartCart AI - Database Catalog Cleanup")
    db = SessionLocal()
    try:
        prods = db.query(Product).all()
        to_delete = [p for p in prods if not is_clean_english(p.name)]
        
        print(f"[info] Total products in database: {len(prods)}")
        print(f"[info] Found {len(to_delete)} products with non-English or foreign names to delete.")
        
        if not to_delete:
            print("[done] Nothing to clean!")
            return 0
            
        delete_ids = [p.id for p in to_delete]
        
        # Deleting dependent records first to satisfy foreign key constraints
        print("[info] Deleting dependent CartItem records...")
        cart_deleted = db.query(CartItem).filter(CartItem.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent ProductImage records...")
        img_deleted = db.query(ProductImage).filter(ProductImage.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent OrderItem records...")
        order_deleted = db.query(OrderItem).filter(OrderItem.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent InventoryTransaction records...")
        inv_trans_deleted = db.query(InventoryTransaction).filter(InventoryTransaction.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent Inventory records...")
        inv_deleted = db.query(Inventory).filter(Inventory.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent ProductDetection records...")
        det_deleted = db.query(ProductDetection).filter(ProductDetection.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent ProductPrice records...")
        price_deleted = db.query(ProductPrice).filter(ProductPrice.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting dependent ProductWeight records...")
        weight_deleted = db.query(ProductWeight).filter(ProductWeight.product_id.in_(delete_ids)).delete(synchronize_session=False)
        
        print("[info] Deleting Product catalog records...")
        prod_deleted = db.query(Product).filter(Product.id.in_(delete_ids)).delete(synchronize_session=False)
        
        db.commit()
        print(f"[done] Successfully completed cleanup!")
        print(f"  - Products deleted: {prod_deleted}")
        print(f"  - Images deleted: {img_deleted}")
        print(f"  - Cart items deleted: {cart_deleted}")
        print(f"  - Order items deleted: {order_deleted}")
        print(f"  - Inventory records deleted: {inv_deleted}")
        print(f"  - Inventory transactions deleted: {inv_trans_deleted}")
        print(f"  - Detection records deleted: {det_deleted}")
        print(f"  - Price records deleted: {price_deleted}")
        print(f"  - Weight records deleted: {weight_deleted}")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
