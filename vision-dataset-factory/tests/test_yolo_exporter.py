import os
import pytest
import tempfile
import shutil
import yaml
from engine.context import PipelineContext
from database.db import init_db, get_db_session
from database.models import Source, Product, Image, Annotation, DatasetVersion, DatasetVersionImage
from plugins.exporters.yolo import YoloExporterNode

@pytest.mark.asyncio
async def test_yolo_exporter_node():
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = {
            "pipeline": {
                "name": "test_export_pipeline",
                "storage_dir": temp_dir,
                "nodes": []
            }
        }
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        init_db(ctx.db_path)
        
        # Create dummy image files on disk
        os.makedirs(os.path.join(temp_dir, "raw"), exist_ok=True)
        img_path1 = os.path.join(temp_dir, "raw", "img_a.jpg")
        img_path2 = os.path.join(temp_dir, "raw", "img_b.jpg")
        with open(img_path1, "w") as f:
            f.write("image A content")
        with open(img_path2, "w") as f:
            f.write("image B content")

        # Set up database records (2 products, each has 1 active image, each image has 1 approved annotation)
        with get_db_session(ctx.db_path) as session:
            src = Source(name="local", website_url="", license="")
            session.add(src)
            session.commit()
            
            prod_a = Product(canonical_name="Soda Can", source_id=src.id)
            prod_b = Product(canonical_name="Chips Bag", source_id=src.id)
            session.add(prod_a)
            session.add(prod_b)
            session.commit()
            
            img_a = Image(product_id=prod_a.id, source_id=src.id, sha256="sha_a", local_path="raw/img_a.jpg", status="active")
            img_b = Image(product_id=prod_b.id, source_id=src.id, sha256="sha_b", local_path="raw/img_b.jpg", status="active")
            session.add(img_a)
            session.add(img_b)
            session.commit()
            
            ann_a = Annotation(image_id=img_a.id, annotator_plugin="mock", bbox=[0.5, 0.4, 0.8, 0.6], confidence=0.9, status="approved")
            ann_b = Annotation(image_id=img_b.id, annotator_plugin="mock", bbox=[0.2, 0.3, 0.4, 0.5], confidence=0.8, status="approved")
            session.add(ann_a)
            session.add(ann_b)
            session.commit()

        # Instantiate exporter node (50/50 train/val split)
        node = YoloExporterNode("export", {
            "dataset_version": "v_test",
            "split_ratio": {"train": 0.5, "val": 0.5, "test": 0.0},
            "label_field": "product"
        })
        
        # Execute node
        result_ctx = await node.execute(ctx)
        
        # Verify state output counts
        assert result_ctx.state["export_processed_count"] == 2
        
        # Verify export files exist
        export_path = os.path.join(temp_dir, "exports", "v_test")
        assert os.path.exists(export_path)
        
        # Verify data.yaml contents
        yaml_path = os.path.join(export_path, "data.yaml")
        assert os.path.exists(yaml_path)
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
            
        assert data["names"] == {0: "Chips Bag", 1: "Soda Can"}
        assert data["train"] == "train/images"
        assert data["val"] == "valid/images"
        
        # Verify split distribution (with 2 items and a 50/50 split, one must be in train and one in valid)
        train_img_dir = os.path.join(export_path, "train", "images")
        val_img_dir = os.path.join(export_path, "valid", "images")
        
        train_files = os.listdir(train_img_dir)
        val_files = os.listdir(val_img_dir)
        
        assert len(train_files) == 1
        assert len(val_files) == 1
        
        # Check label files coordinates format: class_idx x_center y_center w h
        train_lbl_dir = os.path.join(export_path, "train", "labels")
        lbl_files = os.listdir(train_lbl_dir)
        assert len(lbl_files) == 1
        
        with open(os.path.join(train_lbl_dir, lbl_files[0]), "r") as f:
            content = f.read().strip()
            # Split coordinates and verify
            parts = content.split()
            assert len(parts) == 5
            # Class index should be 0 or 1
            assert parts[0] in ["0", "1"]
            
        # Verify lineage tracking records in database
        with get_db_session(ctx.db_path) as session:
            dv = session.query(DatasetVersion).filter_by(version_name="v_test").first()
            assert dv is not None
            assert dv.stats["total_images"] == 2
            
            links = session.query(DatasetVersionImage).filter_by(dataset_version_id=dv.id).all()
            assert len(links) == 2
            
    finally:
        shutil.rmtree(temp_dir)
