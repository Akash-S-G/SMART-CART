import os
import shutil
import random
import yaml
from typing import Dict, Any, List
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Image, Annotation, DatasetVersion, DatasetVersionImage, Product

class YoloExporterNode(PipelineNode):
    """Splits active annotated images and exports them in YOLO format, saving lineage mapping."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.dataset_version = self.config.get("dataset_version", "v1.0.0")
        self.split_ratio = self.config.get("split_ratio", {"train": 0.8, "val": 0.1, "test": 0.1})
        # Determine classification mode: class per "product" or per "category"
        self.label_field = self.config.get("label_field", "product") # "product" or "category"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        print(f"[YoloExporter] Starting export for dataset version '{self.dataset_version}'...")
        
        # Prepare output directories
        export_dir = os.path.join(context.storage_dir, "exports", self.dataset_version)
        os.makedirs(export_dir, exist_ok=True)
        
        splits = ["train", "valid", "test"]
        for split in splits:
            os.makedirs(os.path.join(export_dir, split, "images"), exist_ok=True)
            os.makedirs(os.path.join(export_dir, split, "labels"), exist_ok=True)

        with get_db_session(context.db_path) as session:
            # 1. Query active images that have approved annotations
            annotated_images = session.query(Image).filter(
                Image.status == "active",
                Image.annotations.any(Annotation.status == "approved")
            ).all()

            if not annotated_images:
                print("[YoloExporter] No annotated images found to export! Skipping node.")
                context.state[f"{self.name}_processed_count"] = 0
                context.state[f"{self.name}_failed_count"] = 0
                return context

            # 2. Map classes (Product names or Categories) to indices
            # Resolve classes
            if self.label_field == "category":
                classes = sorted(list(set(img.product.category for img in annotated_images if img.product.category)))
            else: # "product"
                classes = sorted(list(set(img.product.canonical_name for img in annotated_images)))
                
            class_to_idx = {name: idx for idx, name in enumerate(classes)}
            print(f"[YoloExporter] Mapped {len(classes)} classes: {class_to_idx}")

            # 3. Group images by product to avoid data leakage during split
            product_groups: Dict[int, List[Image]] = {}
            for img in annotated_images:
                product_groups.setdefault(img.product_id, []).append(img)

            # Shuffle products deterministically for reproducible splits
            prod_ids = list(product_groups.keys())
            prod_ids.sort()
            random.seed(42)
            random.shuffle(prod_ids)

            # Distribute product groups based on ratios
            total_prods = len(prod_ids)
            train_split = int(total_prods * self.split_ratio.get("train", 0.8))
            val_split = train_split + int(total_prods * self.split_ratio.get("val", 0.1))

            train_prod_ids = set(prod_ids[:train_split])
            val_prod_ids = set(prod_ids[train_split:val_split])
            test_prod_ids = set(prod_ids[val_split:])

            # Create new dataset version record in database
            db_dataset = session.query(DatasetVersion).filter_by(version_name=self.dataset_version).first()
            if db_dataset:
                # Delete existing to prevent primary key or duplicates, or just reuse
                # We will delete link table references for this version first
                session.query(DatasetVersionImage).filter_by(dataset_version_id=db_dataset.id).delete()
            else:
                db_dataset = DatasetVersion(
                    version_name=self.dataset_version,
                    config_used={"split_ratio": self.split_ratio, "label_field": self.label_field}
                )
                session.add(db_dataset)
                session.commit()
                session.refresh(db_dataset)

            success_images = 0
            
            # 4. Copy images and write label files
            for prod_id, imgs in product_groups.items():
                if prod_id in train_prod_ids:
                    split_name = "train"
                elif prod_id in val_prod_ids:
                    split_name = "valid"
                else:
                    split_name = "test"

                for img in imgs:
                    src_abs_path = os.path.join(context.storage_dir, img.local_path)
                    if not os.path.exists(src_abs_path):
                        continue

                    # Copy image file to split images/ directory
                    ext = os.path.splitext(img.local_path)[1]
                    dest_filename = f"img_{img.id}{ext}"
                    dest_img_path = os.path.join(export_dir, split_name, "images", dest_filename)
                    
                    try:
                        shutil.copy2(src_abs_path, dest_img_path)
                        
                        # Generate labels text file
                        labels_filename = f"img_{img.id}.txt"
                        dest_label_path = os.path.join(export_dir, split_name, "labels", labels_filename)
                        
                        # Get active annotations
                        anns = [a for a in img.annotations if a.status == "approved"]
                        
                        label_lines = []
                        for ann in anns:
                            # Retrieve class index
                            class_name = img.product.category if self.label_field == "category" else img.product.canonical_name
                            class_idx = class_to_idx.get(class_name, 0)
                            
                            bbox = ann.bbox # [x_center, y_center, width, height]
                            label_lines.append(f"{class_idx} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}")

                        with open(dest_label_path, "w") as f:
                            f.write("\n".join(label_lines))

                        # Save lineage link to DB
                        for ann in anns:
                            link = DatasetVersionImage(
                                dataset_version_id=db_dataset.id,
                                image_id=img.id,
                                annotation_id=ann.id,
                                split=split_name
                            )
                            session.add(link)
                            
                        success_images += 1
                        
                    except Exception as e:
                        print(f"[YoloExporter] Error exporting image {img.id}: {e}")

            # 5. Write data.yaml YOLO config file
            data_yaml = {
                "path": os.path.abspath(export_dir),
                "train": "train/images",
                "val": "valid/images",
                "test": "test/images",
                "names": {idx: name for name, idx in class_to_idx.items()}
            }
            
            yaml_path = os.path.join(export_dir, "data.yaml")
            with open(yaml_path, "w") as f:
                yaml.dump(data_yaml, f, default_flow_style=False)

            # Update dataset version stats in database
            db_dataset.stats = {
                "total_images": success_images,
                "classes": classes,
                "class_count": len(classes)
            }
            session.add(db_dataset)
            session.commit()

        print(f"[YoloExporter] Finished exporting dataset to {export_dir}. Total images: {success_images}.")
        context.state[f"{self.name}_processed_count"] = success_images
        context.state[f"{self.name}_failed_count"] = 0
        return context
