import json
import urllib.request
import urllib.parse
import asyncio
from typing import Dict, Any, List
from engine.context import PipelineContext
from plugins.sources.base_source import BaseSource

class OpenFoodFactsSource(BaseSource):
    """Discovers products via the OpenFoodFacts Search API."""
    def __init__(self, name: str, config: Dict[str, Any]):
        # Default config properties
        config.setdefault("source_name", "openfoodfacts")
        config.setdefault("license", "Open Database License (ODbL)")
        config.setdefault("website_url", "https://world.openfoodfacts.org")
        super().__init__(name, config)

        self.api_url = self.config.get("api_url", "https://world.openfoodfacts.org/cgi/search.pl")
        self.user_agent = self.config.get("user_agent", "VisionDatasetFactory/1.0")
        self.categories = self.config.get("categories", ["beverages"])
        self.limit_per_category = self.config.get("limit_per_category", 10)
        self.timeout = self.config.get("timeout", 10)

    def _fetch_category_sync(self, category: str) -> List[Dict[str, Any]]:
        """Synchronously queries the OpenFoodFacts search API for a given category."""
        params = {
            "action": "process",
            "tagtype_0": "categories",
            "tag_contains_0": "contains",
            "tag_0": category,
            "json": "true",
            "page_size": str(self.limit_per_category)
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{self.api_url}?{query_string}"
        
        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": self.user_agent}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status != 200:
                    print(f"[OpenFoodFacts] Non-200 response for category '{category}': {response.status}")
                    return []
                data = json.loads(response.read().decode("utf-8"))
                return data.get("products", [])
        except Exception as e:
            print(f"[OpenFoodFacts] HTTP request failed for category '{category}': {e}")
            return []

    async def execute(self, context: PipelineContext) -> PipelineContext:
        discovered_products = []
        
        print(f"[OpenFoodFacts] Starting product discovery for categories: {self.categories}")
        
        for category in self.categories:
            print(f"[OpenFoodFacts] Querying products for category '{category}'...")
            # Run the synchronous HTTP call in a separate thread pool to preserve async execution
            raw_products = await asyncio.to_thread(self._fetch_category_sync, category)
            
            for item in raw_products:
                # Basic product normalization
                name = item.get("product_name") or item.get("product_name_en")
                if not name:
                    continue # Skip products without a name
                
                # Gather image URLs
                image_urls = []
                # Check different front image candidates
                for key in ["image_front_url", "image_url", "image_front_small_url"]:
                    url = item.get(key)
                    if url:
                        image_urls.append(url)
                
                # Deduplicate list
                image_urls = list(dict.fromkeys(image_urls))
                
                prod_data = {
                    "name": name,
                    "brand": item.get("brands"),
                    "variant": item.get("quantity") or item.get("packaging"),
                    "barcode": item.get("code"),
                    "category": category,
                    "image_urls": image_urls,
                    "source": self.source_name
                }
                discovered_products.append(prod_data)
                
            # Yield control to allow cooperative scheduling
            await asyncio.sleep(0.5)

        # Register discovered products in the database
        new_registered = await self.register_products(context, discovered_products)
        
        # Save results in PipelineContext state so subsequent downloader node can process them
        context.state["discovered_products"] = discovered_products
        context.state[f"{self.name}_processed_count"] = len(discovered_products)
        context.state[f"{self.name}_failed_count"] = 0
        
        return context
