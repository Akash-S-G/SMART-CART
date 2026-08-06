import os
import pytest
import tempfile
import shutil
from engine.context import PipelineContext
from database.db import init_db, get_db_session
from database.models import Source, Product, Image, Annotation
from plugins.annotators.annotation_node import AnnotationNode

@pytest.mark.asyncio
async def test_annotation_node():
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = {
            "pipeline": {
                "name": "test_ann_pipeline",
                "storage_dir": temp_dir,
                "nodes": []
            }
        }
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        init_db(ctx.db_path)
        
        # Create a dummy image file on disk so existence check passes
        os.makedirs(os.path.join(temp_dir, "raw"), exist_ok=True)
        img_path = os.path.join(temp_dir, "raw", "img_test.jpg")
        with open(img_path, "w") as f:
            f.write("dummy image content")

        # Set up database records
        with get_db_session(ctx.db_path) as session:
            src = Source(name="openfoodfacts", website_url="", license="")
            session.add(src)
            session.commit()
            
            prod = Product(canonical_name="Juice Bottle", source_id=src.id)
            session.add(prod)
            session.commit()
            
            # Register active image in DB
            img = Image(
                product_id=prod.id,
                source_id=src.id,
                raw_url="http://example.com/juice.jpg",
                local_path="raw/img_test.jpg",
                sha256="checksum_test_123",
                status="active"
            )
            session.add(img)
            session.commit()

        # Instantiate annotation node using mock annotator plugin
        node = AnnotationNode("annotate", {
            "annotator": "plugins.annotators.grounding_dino.GroundingDinoAnnotator",
            "prompt_template": "box containing {product_name}",
            "min_confidence": 0.6
        })
        
        # Execute node
        result_ctx = await node.execute(ctx)
        
        assert result_ctx.state["annotate_processed_count"] == 1
        assert result_ctx.state["annotate_failed_count"] == 0
        
        # Query DB to check annotation records
        with get_db_session(ctx.db_path) as session:
            annotations = session.query(Annotation).all()
            assert len(annotations) == 1
            ann = annotations[0]
            assert ann.annotator_plugin == "plugins.annotators.grounding_dino.GroundingDinoAnnotator"
            assert ann.bbox == [0.5, 0.5, 0.8, 0.8]
            assert ann.confidence == 0.85
            assert ann.status == "approved"
            
    finally:
        shutil.rmtree(temp_dir)
