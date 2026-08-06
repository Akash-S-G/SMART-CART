import requests
import time
from typing import Iterator, Dict
from plugins.base_plugin import BasePlugin

class OpenFoodFactsPlugin(BasePlugin):
    @property
    def source_name(self) -> str:
        return "openfoodfacts"

    def discover_images(self, product_family: str, query: str) -> Iterator[Dict[str, str]]:
        """Queries the OFF API for the product family. Note: OFF doesn't use the 'query' variations effectively, 
        so we search by product_family to avoid redundant queries."""
        # Simple backoff logic for 503s
        base_url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 100
        }
        
        headers = {
            "User-Agent": "VisionDatasetFactory - Dataset Acquisition System"
        }

        retries = 5
        for attempt in range(retries):
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=10)
                if response.status_code == 503:
                    time.sleep(2.5 * (2 ** attempt))
                    continue
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    for prod in products:
                        barcode = str(prod.get("id", ""))
                        if not barcode: continue
                        
                        # Format barcode for URL
                        if len(barcode) >= 13:
                            bc_formatted = f"{barcode[:3]}/{barcode[3:6]}/{barcode[6:9]}/{barcode[9:]}"
                        elif len(barcode) >= 8:
                            bc_formatted = f"{barcode[:3]}/{barcode[3:6]}/{barcode[6:]}"
                        else:
                            bc_formatted = barcode
                            
                        # Extract images
                        images = prod.get("images", {})
                        for key, img_data in images.items():
                            if not isinstance(img_data, dict):
                                continue
                            if key.isdigit() or key.startswith("front") or key.startswith("packaging"):
                                # We construct the URL manually since it's not in the response
                                url = f"https://images.openfoodfacts.org/images/products/{bc_formatted}/{key}.jpg"
                                page_url = f"https://world.openfoodfacts.org/product/{barcode}"
                                yield {
                                    "image_url": url,
                                    "page_url": page_url,
                                    "source": self.source_name
                                }
                    break # Success, stop retrying
                else:
                    break # Unhandled status code
            except requests.RequestException:
                time.sleep(2.5 * (2 ** attempt))

