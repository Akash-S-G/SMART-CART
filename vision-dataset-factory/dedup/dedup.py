import os
import asyncio
from PIL import Image as PILImage
import numpy as np
from typing import Dict, Any, List
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Image

class DeduplicationNode(PipelineNode):
    """Calculates image hashes and marks near-duplicates in the database."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.hash_size = self.config.get("hash_size", 8)
        self.hamming_threshold = self.config.get("threshold", 8) # out of 64 bits

    def compute_dhash(self, image_path: str) -> str:
        """Computes a 64-bit Difference Hash (dHash) for an image using PIL & NumPy."""
        try:
            with PILImage.open(image_path) as img:
                # Convert to grayscale and resize to (9, 8) for diff checks
                img = img.convert("L").resize((self.hash_size + 1, self.hash_size), PILImage.Resampling.LANCZOS)
                pixels = np.array(img)
                
            # Compare adjacent pixels (width-wise)
            diff = pixels[:, :-1] > pixels[:, 1:]
            
            # Pack boolean differences into a 64-bit integer
            decimal_val = 0
            for bit in diff.flatten():
                decimal_val = (decimal_val << 1) | int(bit)
                
            return f"{decimal_val:016x}"
        except Exception as e:
            print(f"[Deduplication] Error hashing image {image_path}: {e}")
            return ""

    def get_hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculates the number of differing bits between two 64-bit hex hashes."""
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        print("[Deduplication] Starting near-duplicate check stage...")
        
        # 1. Compute missing hashes for all active images
        processed_count = 0
        duplicate_count = 0
        
        with get_db_session(context.db_path) as session:
            # Query all active images
            active_images = session.query(Image).filter_by(status="active").all()
            
            for img in active_images:
                # Get absolute path
                abs_path = os.path.join(context.storage_dir, img.local_path)
                if not os.path.exists(abs_path):
                    continue
                
                # Calculate pHash (dHash) if empty
                if not img.phash:
                    # Run CPU-bound hashing in a separate thread
                    phash = await asyncio.to_thread(self.compute_dhash, abs_path)
                    if phash:
                        img.phash = phash
                        session.add(img)
                        processed_count += 1
                        
            session.commit()
            
            # Re-fetch active images now containing hashes
            active_images = session.query(Image).filter_by(status="active").all()
            
            # 2. Compare hashes to flag duplicates
            # Build list of active image records with valid hashes
            img_list = [img for img in active_images if img.phash]
            
            # Simple pairwise comparison (O(N^2) for small batches)
            # For massive production datasets, Vantage Point trees or spatial indexes would be used
            duplicates_to_flag = set()
            
            for i in range(len(img_list)):
                img1 = img_list[i]
                if img1.id in duplicates_to_flag:
                    continue
                    
                for j in range(i + 1, len(img_list)):
                    img2 = img_list[j]
                    if img2.id in duplicates_to_flag:
                        continue
                        
                    distance = self.get_hamming_distance(img1.phash, img2.phash)
                    if distance <= self.hamming_threshold:
                        # We keep img1 (older/first) and reject img2 as a duplicate
                        duplicates_to_flag.add(img2.id)
                        print(f"[Deduplication] Near-duplicate detected (dist={distance}): "
                              f"{img2.local_path} matches {img1.local_path}")
            
            # Apply duplicate flags
            for img_id in duplicates_to_flag:
                img_record = session.query(Image).filter_by(id=img_id).first()
                if img_record:
                    img_record.status = "duplicate"
                    session.add(img_record)
                    duplicate_count += 1
                    
            session.commit()
            
        print(f"[Deduplication] Deduplicated database. Hashed {processed_count} images, marked {duplicate_count} near-duplicates.")
        context.state[f"{self.name}_processed_count"] = processed_count
        context.state[f"{self.name}_failed_count"] = 0
        return context
