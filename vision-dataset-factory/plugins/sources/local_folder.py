import os
import json
from typing import Dict, Any, List
from engine.context import PipelineContext
from plugins.sources.base_source import BaseSource

class LocalFolderSource(BaseSource):
    """Loads products and image paths from a local directory structure."""
    def __init__(self, name: str, config: Dict[str, Any]):
        config.setdefault("source_name", "local_folder")
        config.setdefault("license", "Proprietary/Local")
        config.setdefault("website_url", "local://filesystem")
        super().__init__(name, config)
        self.input_dir = self.config.get("input_dir", "storage/raw_local/")

    async def execute(self, context: PipelineContext) -> PipelineContext:
        resolved_input_dir = os.path.join(context.storage_dir, "..", self.input_dir) if not os.path.isabs(self.input_dir) else self.input_dir
        resolved_input_dir = os.path.abspath(resolved_input_dir)
        
        print(f"[LocalFolder] Scanning local directory: {resolved_input_dir}")
        discovered_products = []
        
        if not os.path.exists(resolved_input_dir):
            print(f"[LocalFolder] Directory does not exist: {resolved_input_dir}. Skipping.")
            context.state["discovered_products"] = []
            context.state[f"{self.name}_processed_count"] = 0
            context.state[f"{self.name}_failed_count"] = 0
            return context

        # 1. Check for manifest.json
        manifest_path = os.path.join(resolved_input_dir, "manifest.json")
        if os.path.exists(manifest_path):
            print(f"[LocalFolder] Found manifest.json. Loading metadata...")
            try:
                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                
                products_list = manifest_data.get("products", [])
                for item in products_list:
                    # Validate product fields
                    if "name" not in item:
                        continue
                    
                    # Convert local relative paths to absolute or context-relative URLs
                    image_urls = []
                    for path in item.get("images", []):
                        if not os.path.isabs(path):
                            abs_path = os.path.abspath(os.path.join(resolved_input_dir, path))
                        else:
                            abs_path = path
                        # Use file:// prefix to flag that it's local
                        image_urls.append(f"file://{abs_path}")
                        
                    prod_data = {
                        "name": item["name"],
                        "brand": item.get("brand"),
                        "variant": item.get("variant"),
                        "barcode": item.get("barcode"),
                        "category": item.get("category"),
                        "image_urls": image_urls,
                        "source": self.source_name
                    }
                    discovered_products.append(prod_data)
            except Exception as e:
                print(f"[LocalFolder] Error reading manifest.json: {e}")
        else:
            # 2. Walk directory structure: subfolder = product name
            print(f"[LocalFolder] manifest.json not found. Walking directory subfolders...")
            for entry in os.scandir(resolved_input_dir):
                if entry.is_dir():
                    product_name = entry.name
                    image_urls = []
                    
                    # Scan for images
                    for file_entry in os.scandir(entry.path):
                        if file_entry.is_file():
                            ext = os.path.splitext(file_entry.name)[1].lower()
                            if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
                                image_urls.append(f"file://{os.path.abspath(file_entry.path)}")
                                
                    if image_urls:
                        prod_data = {
                            "name": product_name,
                            "brand": None,
                            "variant": None,
                            "barcode": None,
                            "category": "local_import",
                            "image_urls": image_urls,
                            "source": self.source_name
                        }
                        discovered_products.append(prod_data)

        # Register products in the catalog
        new_registered = await self.register_products(context, discovered_products)
        
        context.state["discovered_products"] = discovered_products
        context.state[f"{self.name}_processed_count"] = len(discovered_products)
        context.state[f"{self.name}_failed_count"] = 0
        return context
