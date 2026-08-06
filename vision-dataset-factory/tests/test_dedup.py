import os
import pytest
import tempfile
import shutil
from PIL import Image as PILImage, ImageDraw
from engine.context import PipelineContext
from database.db import init_db, get_db_session
from database.models import Source, Product, Image
from dedup.dedup import DeduplicationNode

def create_dummy_image(path: str, color: str, draw_shape: str = None):
    """Utility to generate a test image with customizable geometry for hashing validation."""
    img = PILImage.new("RGB", (256, 256), color=color)
    draw = ImageDraw.Draw(img)
    if draw_shape == "left":
        draw.ellipse([20, 100, 80, 160], fill="white")
    elif draw_shape == "right":
        draw.ellipse([170, 100, 230, 160], fill="white")
    elif draw_shape == "noise":
        draw.ellipse([20, 100, 80, 160], fill="white")
        draw.rectangle([100, 100, 110, 110], fill="black")
    img.save(path)

@pytest.mark.asyncio
async def test_deduplication_and_hashing():
    temp_dir = tempfile.mkdtemp()
    
    # Setup context first to obtain the correct database path
    config = {
        "pipeline": {
            "name": "test_dedup",
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
        img_path1 = os.path.join(temp_dir, "raw", "img1.jpg")
        img_path2 = os.path.join(temp_dir, "raw", "img2.jpg") # Identical to img1
        img_path3 = os.path.join(temp_dir, "raw", "img3.jpg") # Slightly modified img1 (near-duplicate)
        img_path4 = os.path.join(temp_dir, "raw", "img4.jpg") # Completely different
        
        create_dummy_image(img_path1, "blue", draw_shape="left")
        create_dummy_image(img_path2, "blue", draw_shape="left")
        create_dummy_image(img_path3, "blue", draw_shape="noise")
        create_dummy_image(img_path4, "red", draw_shape="right")
        
        # Test hash computation
        node = DeduplicationNode("dedup", {"threshold": 8})
        
        hash1 = node.compute_dhash(img_path1)
        hash2 = node.compute_dhash(img_path2)
        hash3 = node.compute_dhash(img_path3)
        hash4 = node.compute_dhash(img_path4)
        
        assert len(hash1) == 16 # 64 bits = 16 hex characters
        assert hash1 == hash2 # Identical images have identical hashes
        
        # Verify distance calculations
        dist_mod = node.get_hamming_distance(hash1, hash3)
        dist_diff = node.get_hamming_distance(hash1, hash4)
        
        assert dist_mod <= 8 # Near duplicate within threshold
        assert dist_diff > 8  # Completely different image
        
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
                product_id=prod.id, source_id=src.id, sha256="sha1",
                local_path="raw/img1.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha2",
                local_path="raw/img2.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha3",
                local_path="raw/img3.jpg", status="active"
            ))
            session.add(Image(
                product_id=prod.id, source_id=src.id, sha256="sha4",
                local_path="raw/img4.jpg", status="active"
            ))
            session.commit()
            
        # Execute deduplication node
        await node.execute(ctx)
        
        # Verify results in database
        with get_db_session(ctx.db_path) as session:
            img1_rec = session.query(Image).filter_by(local_path="raw/img1.jpg").first()
            img2_rec = session.query(Image).filter_by(local_path="raw/img2.jpg").first()
            img3_rec = session.query(Image).filter_by(local_path="raw/img3.jpg").first()
            img4_rec = session.query(Image).filter_by(local_path="raw/img4.jpg").first()
            
            # img1 (the original) must stay active
            assert img1_rec.status == "active"
            
            # img2 (exact duplicate) must be flagged
            assert img2_rec.status == "duplicate"
            
            # img3 (near duplicate) must be flagged
            assert img3_rec.status == "duplicate"
            
            # img4 (different) must stay active
            assert img4_rec.status == "active"
            
    finally:
        shutil.rmtree(temp_dir)
