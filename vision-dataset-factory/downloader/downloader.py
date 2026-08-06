import os
import shutil
import urllib.request
import urllib.parse
import hashlib
import asyncio
from typing import Dict, Any, List, Tuple
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Product, Image

class DownloaderNode(PipelineNode):
    """Asynchronously downloads product images to storage/raw/."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.concurrency = self.config.get("concurrency", 5)
        self.timeout = self.config.get("timeout", 15)
        self.user_agent = self.config.get("user_agent", "VisionDatasetFactory/1.0")

    def _download_file_sync(self, url: str, dest_path: str) -> None:
        """Helper to synchronously fetch/copy a file."""
        if url.startswith("file://"):
            # Local file copy
            src_path = url.replace("file://", "")
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"Local source file not found: {src_path}")
            shutil.copy2(src_path, dest_path)
        else:
            # HTTP download
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                with open(dest_path, "wb") as f:
                    shutil.copyfileobj(response, f)

    async def download_image(self, sem: asyncio.Semaphore, url: str, storage_dir: str) -> Tuple[str, str]:
        """Downloads an image, computes its SHA256 hash, and returns (temp_filepath, sha256)."""
        async with sem:
            # Create a unique temporary filename
            temp_filename = f"temp_{hashlib.md5(url.encode()).hexdigest()}"
            temp_path = os.path.join(storage_dir, "raw", temp_filename)
            
            try:
                # Execute blocking file operations in a thread pool
                await asyncio.to_thread(self._download_file_sync, url, temp_path)
                
                # Compute SHA256 checksum
                sha256_hash = hashlib.sha256()
                with open(temp_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                sha256 = sha256_hash.hexdigest()
                
                return temp_path, sha256
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise RuntimeError(f"Failed downloading {url}: {e}")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        print("[Downloader] Starting image acquisition...")
        
        # Get products from db to map them
        with get_db_session(context.db_path) as session:
            products = session.query(Product).all()
            # Map by brand + name + source for quick lookup
            db_product_map = {
                (p.canonical_name, p.canonical_brand, p.source_id): p.id 
                for p in products
            }
            
        discovered_products = context.state.get("discovered_products", [])
        if not discovered_products:
            print("[Downloader] No discovered products found in state. Skipping.")
            context.state[f"{self.name}_processed_count"] = 0
            context.state[f"{self.name}_failed_count"] = 0
            return context

        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = []
        
        # Create tasks for all images
        for item in discovered_products:
            name = item["name"]
            brand = item.get("brand")
            source_name = item["source"]
            image_urls = item.get("image_urls", [])
            
            # Find DB IDs
            with get_db_session(context.db_path) as session:
                prod_rec = session.query(Product).filter_by(
                    canonical_name=name, canonical_brand=brand
                ).first()
                if not prod_rec:
                    continue
                product_id = prod_rec.id
                source_id = prod_rec.source_id
            
            for idx, url in enumerate(image_urls):
                tasks.append(
                    (product_id, source_id, url, idx)
                )

        print(f"[Downloader] Queued {len(tasks)} images for download.")
        
        success_count = 0
        fail_count = 0
        
        for product_id, source_id, url, idx in tasks:
            try:
                temp_path, sha256 = await self.download_image(semaphore, url, context.storage_dir)
                
                # Check if this exact raw URL is already registered for this product
                with get_db_session(context.db_path) as session:
                    already_registered = session.query(Image).filter_by(
                        product_id=product_id, raw_url=url
                    ).first()
                    
                    if already_registered:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        success_count += 1
                        continue

                # Check for SHA256 duplicate in DB to reuse storage files
                with get_db_session(context.db_path) as session:
                    existing_img = session.query(Image).filter_by(sha256=sha256).first()
                    
                    if existing_img:
                        # Duplicate image found. Register duplicate entry referencing same file
                        new_img = Image(
                            product_id=product_id,
                            source_id=source_id,
                            raw_url=url,
                            local_path=existing_img.local_path,
                            sha256=sha256,
                            status="duplicate"
                        )
                        session.add(new_img)
                        session.commit()
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        success_count += 1
                    else:
                        # New unique image file
                        ext = os.path.splitext(url.split("?")[0])[1].lower()
                        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
                            ext = ".jpg"
                        if ext == ".jpeg":
                            ext = ".jpg"
                            
                        filename = f"img_{product_id}_{idx}_{sha256[:10]}{ext}"
                        final_relative_path = os.path.join("raw", filename)
                        final_abs_path = os.path.join(context.storage_dir, final_relative_path)
                        
                        os.rename(temp_path, final_abs_path)
                        
                        new_img = Image(
                            product_id=product_id,
                            source_id=source_id,
                            raw_url=url,
                            local_path=final_relative_path,
                            sha256=sha256,
                            status="active"
                        )
                        session.add(new_img)
                        session.commit()
                        success_count += 1
                        
            except Exception as e:
                print(f"[Downloader] Download error for {url}: {e}")
                fail_count += 1
                
        context.state[f"{self.name}_processed_count"] = success_count
        context.state[f"{self.name}_failed_count"] = fail_count
        return context
