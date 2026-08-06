import os
import pytest
import tempfile
import shutil
from database.db import init_db, get_db_session
from database.models import Source, Product, Image, Annotation, DatasetVersion, DatasetVersionImage, TrainingRun, ModelVersion

def test_database_lineage_and_relations():
    # Setup temporary file for SQLite
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_vdf.db")
    
    try:
        # Initialize schema
        init_db(db_path)
        
        # Test full pipeline database insertion representing data lineage
        with get_db_session(db_path) as session:
            # 1. Create Source
            src = Source(
                name="openfoodfacts",
                website_url="https://world.openfoodfacts.org",
                license="ODbL"
            )
            session.add(src)
            session.commit()
            
            # 2. Create Product
            prod = Product(
                canonical_brand="Nestle",
                canonical_name="Maggi Noodles",
                variant="70g",
                barcode="8901058002316",
                category="Instant Foods",
                source_id=src.id,
                raw_metadata={"raw_scraped_name": "MAGGI 70 G"}
            )
            session.add(prod)
            session.commit()
            
            # 3. Create Image
            img = Image(
                product_id=prod.id,
                source_id=src.id,
                raw_url="https://world.openfoodfacts.org/images/maggi.jpg",
                local_path="raw/img_maggi_01.jpg",
                sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                phash="a1b2c3d4e5f60718",
                quality_score=0.92,
                quality_metadata={"resolution": "800x600", "blur_variance": 234.5},
                status="active"
            )
            session.add(img)
            session.commit()
            
            # 4. Create Annotation
            ann = Annotation(
                image_id=img.id,
                annotator_plugin="grounding_dino",
                model_version="gd-v1.2",
                bbox={"x_center": 0.5, "y_center": 0.5, "w": 0.8, "h": 0.6},
                confidence=0.89,
                format="yolo",
                status="approved"
            )
            session.add(ann)
            session.commit()
            
            # 5. Create Dataset Version
            dataset = DatasetVersion(
                version_name="v1.0.0",
                config_used={"split_ratio": {"train": 0.8, "val": 0.2}},
                stats={"image_count": 1, "class_breakdown": {"Instant Foods": 1}}
            )
            session.add(dataset)
            session.commit()
            
            # 6. Associate Image & Annotation to Dataset Split
            dataset_link = DatasetVersionImage(
                dataset_version_id=dataset.id,
                image_id=img.id,
                annotation_id=ann.id,
                split="train"
            )
            session.add(dataset_link)
            session.commit()
            
            # 7. Create Training Run
            run = TrainingRun(
                dataset_version_id=dataset.id,
                hyperparameters={"lr": 0.01, "epochs": 50},
                metrics={"mAP50": 0.88, "precision": 0.85, "recall": 0.81},
                logs_path="storage/logs/training/run_01"
            )
            session.add(run)
            session.commit()
            
            # 8. Create Model Registry Entry
            model = ModelVersion(
                training_run_id=run.id,
                version_name="smartcart-maggi-yolov11",
                model_path="storage/models/best.pt",
                status="production",
                deployment_ready=1
            )
            session.add(model)
            session.commit()

        # Read back and trace line-of-descent / data lineage
        with get_db_session(db_path) as session:
            # Locate the model in the registry
            model_rec = session.query(ModelVersion).filter_by(version_name="smartcart-maggi-yolov11").first()
            assert model_rec is not None
            assert model_rec.deployment_ready == 1
            
            # Trace to Training Run
            run_rec = model_rec.training_run
            assert run_rec is not None
            assert run_rec.hyperparameters["epochs"] == 50
            assert run_rec.metrics["mAP50"] == 0.88
            
            # Trace to Dataset Version
            dataset_rec = run_rec.dataset_version
            assert dataset_rec is not None
            assert dataset_rec.version_name == "v1.0.0"
            
            # Query images and labels that went into this dataset version
            links = dataset_rec.image_links
            assert len(links) == 1
            link = links[0]
            assert link.split == "train"
            
            # Trace to the Image & Product Details
            img_rec = link.image
            assert img_rec.sha256.startswith("e3b0c442")
            assert img_rec.quality_score == 0.92
            
            prod_rec = img_rec.product
            assert prod_rec.canonical_brand == "Nestle"
            assert prod_rec.barcode == "8901058002316"
            
            # Trace to the Scraper / Source details
            src_rec = prod_rec.source
            assert src_rec.name == "openfoodfacts"
            
            # Trace the Annotation used in the training split
            ann_rec = link.annotation
            assert ann_rec.annotator_plugin == "grounding_dino"
            assert ann_rec.bbox["x_center"] == 0.5
            
    finally:
        shutil.rmtree(temp_dir)
