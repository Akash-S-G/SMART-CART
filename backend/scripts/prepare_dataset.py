from __future__ import annotations

import os
import sys
import string
import requests
from pathlib import Path

# Add backend to path
sys.path[:0] = [str(Path(__file__).resolve().parent.parent)]

import app.main
from app.db.database import SessionLocal
from app.models.products.product import Product

def is_clean_english(s: str) -> bool:
    allowed = string.ascii_letters + string.digits + string.whitespace + ".,-&'()!/#%:?+*[]"
    return all(c in allowed for c in s)

def main():
    print(">>> SmartCart AI - Unified Dataset Preparation Pipeline")
    
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    root_dir = backend_dir.parent
    
    # Destination directory
    dest_dir = root_dir / "vision-dataset-factory" / "storage" / "exports" / "combined_groceries"
    train_img_dir = dest_dir / "train" / "images"
    train_lbl_dir = dest_dir / "train" / "labels"
    val_img_dir = dest_dir / "valid" / "images"
    val_lbl_dir = dest_dir / "valid" / "labels"
    
    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    print(f"[info] Export directory initialized at: {dest_dir}")
    
    db = SessionLocal()
    try:
        prods = db.query(Product).all()
        # Keep only clean english products
        active_prods = [p for p in prods if is_clean_english(p.name)]
        print(f"[info] Found {len(active_prods)} clean products in database to prepare.")
        
        # Build class index map
        class_map = {}
        for idx, p in enumerate(active_prods):
            class_map[p.id] = idx
            
        # Download images and write label files
        success_count = 0
        for idx, p in enumerate(active_prods):
            if not p.images:
                continue
                
            class_idx = class_map[p.id]
            
            # Download up to 3 images per product
            for img_idx, img_obj in enumerate(p.images[:3]):
                img_url = img_obj.image_url
                try:
                    # Determine split: 85% train, 15% validation
                    is_val = (idx % 7 == 0)
                    img_dir = val_img_dir if is_val else train_img_dir
                    lbl_dir = val_lbl_dir if is_val else train_lbl_dir
                    
                    file_name = f"prod_{p.sku}_{img_idx}.jpg"
                    img_path = img_dir / file_name
                    lbl_path = lbl_dir / f"prod_{p.sku}_{img_idx}.txt"
                    
                    # Download image
                    if not img_path.exists():
                        res = requests.get(img_url, timeout=10)
                        if res.status_code == 200:
                            with open(img_path, "wb") as f:
                                f.write(res.content)
                        else:
                            continue
                            
                    # Write YOLO label: centered bounding box covering 90% of image
                    # Format: class_index x_center y_center width height
                    with open(lbl_path, "w") as f:
                        f.write(f"{class_idx} 0.5 0.5 0.9 0.9\n")
                        
                    success_count += 1
                except Exception as e:
                    # Skip download failures gracefully
                    continue
                    
        print(f"[done] Prepared {success_count} labeled images successfully.")
        
        # Write data.yaml configuration file
        names_dict = {class_map[p.id]: p.name for p in active_prods}
        
        yaml_content = f"path: {dest_dir}\n"
        yaml_content += "train: train/images\n"
        yaml_content += "val: valid/images\n\n"
        yaml_content += "names:\n"
        for c_idx in sorted(names_dict.keys()):
            # Escape quotes in names
            clean_name = names_dict[c_idx].replace("'", "''")
            yaml_content += f"  {c_idx}: '{clean_name}'\n"
            
        with open(dest_dir / "data.yaml", "w") as f:
            f.write(yaml_content)
        print(f"[done] Created data.yaml configuration.")
        
    except Exception as e:
        print(f"[ERROR] Dataset preparation failed: {e}")
        return 1
    finally:
        db.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
