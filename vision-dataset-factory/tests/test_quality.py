import os
import pytest
import tempfile
import shutil
from PIL import Image as PILImage, ImageDraw, ImageFilter
from engine.context import PipelineContext
from database.db import init_db, get_db_session
from database.models import Source, Product, Image
from quality.quality import QualityCheckNode

def create_sharp_image(path: str, size=(300, 300)):
    """Creates a high-contrast sharp image with text and lines."""
    img = PILImage.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    # Draw sharp lines/shapes
    draw.rectangle([50, 50, 250, 250], fill="black", outline="red", width=5)
    draw.line([0, 0, size[0], size[1]], fill="blue", width=3)
    img.save(path)

def create_blurry_image(path: str, size=(300, 300)):
    """Creates a heavily blurred version of the sharp image."""
    img = PILImage.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 250, 250], fill="black", outline="red", width=5)
    draw.line([0, 0, size[0], size[1]], fill="blue", width=3)
    # Apply heavy blur filter
    blurry_img = img.filter(ImageFilter.GaussianBlur(radius=15))
    blurry_img.save(path)

@pytest.mark.asyncio
async def test_quality_checking():
    temp_dir = tempfile.mkdtemp()
    
    # Setup context first to obtain the correct database path
    config = {
        "pipeline": {
            "name": "test_quality",
            "storage_dir": temp_dir,
            "nodes": []
        }
    }
    ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
    init_db(ctx.db_path)
    
    # Create sub-folders for raw images
    os.makedirs(os.path.join(temp_dir, "raw"), exist_ok=True)
    
    try:
        # Create image file paths
        img_sharp = os.path.join(temp_dir, "raw", "sharp.jpg")
        img_blurry = os.path.join(temp_dir, "raw", "blurry.jpg")
        img_low_res = os.path.join(temp_dir, "raw", "lowres.jpg")
        img_corrupt = os.path.join(temp_dir, "raw", "corrupt.jpg")
        
        create_sharp_image(img_sharp)
        create_blurry_image(img_blurry)
        create_sharp_image(img_low_res, size=(100, 100))
        
        # Create a corrupted image file (just write text)
        with open(img_corrupt, "w") as f:
            f.write("this is not an image file")
            
        # Populate DB
        with get_db_session(ctx.db_path) as session:
            src = Source(name="local", website_url="", license="")
            session.add(src)
            session.commit()
            
            prod = Product(canonical_name="Item A", source_id=src.id)
            session.add(prod)
            session.commit()
            
            # Register the images in the DB
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha_sharp",
                local_path="raw/sharp.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha_blurry",
                local_path="raw/blurry.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha_low_res",
                local_path="raw/lowres.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha_corrupt",
                local_path="raw/corrupt.jpg", status="active"
            ))
            session.commit()
            
        # Execute quality check node
        node = QualityCheckNode("quality", {
            "min_width": 224,
            "min_height": 224,
            "blur_threshold": 100.0
        })
        await node.execute(ctx)
        
        # Verify results in database
        with get_db_session(ctx.db_path) as session:
            sharp_rec = session.query(Image).filter_by(local_path="raw/sharp.jpg").first()
            blurry_rec = session.query(Image).filter_by(local_path="raw/blurry.jpg").first()
            lowres_rec = session.query(Image).filter_by(local_path="raw/lowres.jpg").first()
            corrupt_rec = session.query(Image).filter_by(local_path="raw/corrupt.jpg").first()
            
            # sharp must stay active
            assert sharp_rec.status == "active"
            assert sharp_rec.quality_score > 0.0
            
            # low-res must be rejected
            assert lowres_rec.status == "rejected"
            assert lowres_rec.quality_metadata["error"] == "low_resolution"
            
            # corrupt must be rejected
            assert corrupt_rec.status == "rejected"
            assert corrupt_rec.quality_metadata["error"] == "corrupted"
            
            # blurry must be rejected (only if OpenCV was available, otherwise bypassed and remains active)
            from quality.quality import OPENCV_AVAILABLE
            if OPENCV_AVAILABLE:
                assert blurry_rec.status == "rejected"
                assert blurry_rec.quality_metadata["error"] == "blurry"
            else:
                assert blurry_rec.status == "active"
            
    finally:
        shutil.rmtree(temp_dir)
