import os
import asyncio
from PIL import Image as PILImage
from typing import Dict, Any
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Image

# Gracefully import OpenCV. If not present or missing OS libraries (like libGL in headless containers),
# we fall back to Pillow-based dimension checking.
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("[QualityCheck] OpenCV not installed. Blur checks will be bypassed.")

class QualityCheckNode(PipelineNode):
    """Checks image resolution, corruption, and blurriness, updating database metadata."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.min_width = self.config.get("min_width", 224)
        self.min_height = self.config.get("min_height", 224)
        self.blur_threshold = self.config.get("blur_threshold", 100.0)

    def calculate_blur_variance(self, image_path: str) -> float:
        """Computes the Laplacian variance to measure focus/blurriness."""
        if not OPENCV_AVAILABLE:
            return 999.0 # Placeholder high-quality variance if OpenCV is unavailable
            
        try:
            image = cv2.imread(image_path)
            if image is None:
                return -1.0
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            return float(variance)
        except Exception as e:
            print(f"[QualityCheck] OpenCV error calculating blur for {image_path}: {e}")
            return -1.0

    async def execute(self, context: PipelineContext) -> PipelineContext:
        print("[QualityCheck] Starting image quality inspection...")
        
        processed_count = 0
        rejected_count = 0
        
        with get_db_session(context.db_path) as session:
            # Check all active images
            active_images = session.query(Image).filter_by(status="active").all()
            
            for img in active_images:
                abs_path = os.path.join(context.storage_dir, img.local_path)
                
                # Check 1: File existence & corruption
                if not os.path.exists(abs_path):
                    img.status = "rejected"
                    img.quality_score = 0.0
                    img.quality_metadata = {"error": "file_not_found"}
                    session.add(img)
                    rejected_count += 1
                    continue
                    
                try:
                    with PILImage.open(abs_path) as pil_img:
                        pil_img.verify()
                except Exception as e:
                    print(f"[QualityCheck] Corrupt image detected: {abs_path} - {e}")
                    img.status = "rejected"
                    img.quality_score = 0.0
                    img.quality_metadata = {"error": "corrupted", "details": str(e)}
                    session.add(img)
                    rejected_count += 1
                    continue
                
                # Re-open to get dimensions (verify() closes the file)
                try:
                    with PILImage.open(abs_path) as pil_img:
                        width, height = pil_img.size
                        img_format = pil_img.format
                except Exception:
                    img.status = "rejected"
                    img.quality_score = 0.0
                    img.quality_metadata = {"error": "read_failed"}
                    session.add(img)
                    rejected_count += 1
                    continue

                # Check 2: Resolution check
                if width < self.min_width or height < self.min_height:
                    print(f"[QualityCheck] Resolution too low ({width}x{height}): {img.local_path}")
                    img.status = "rejected"
                    img.quality_score = 0.1
                    img.quality_metadata = {
                        "width": width,
                        "height": height,
                        "format": img_format,
                        "error": "low_resolution"
                    }
                    session.add(img)
                    rejected_count += 1
                    continue

                # Check 3: Blurriness check
                # Compute in a separate thread
                blur_var = await asyncio.to_thread(self.calculate_blur_variance, abs_path)
                
                quality_metadata = {
                    "width": width,
                    "height": height,
                    "format": img_format,
                    "blur_variance": blur_var
                }
                
                # Normalization score logic
                is_blurry = blur_var < self.blur_threshold and blur_var >= 0.0
                
                if is_blurry:
                    print(f"[QualityCheck] Blurry image rejected (variance={blur_var:.2f}): {img.local_path}")
                    img.status = "rejected"
                    img.quality_score = 0.3
                    quality_metadata["error"] = "blurry"
                    img.quality_metadata = quality_metadata
                    session.add(img)
                    rejected_count += 1
                else:
                    img.status = "active"
                    # Quality score can be a normalized weight
                    img.quality_score = min(1.0, max(0.5, blur_var / 500.0))
                    img.quality_metadata = quality_metadata
                    session.add(img)
                    processed_count += 1
                    
            session.commit()
            
        print(f"[QualityCheck] Finished check. Inspected {processed_count + rejected_count} images. "
              f"Passed: {processed_count}, Rejected: {rejected_count}")
              
        context.state[f"{self.name}_processed_count"] = processed_count
        context.state[f"{self.name}_failed_count"] = rejected_count
        return context
