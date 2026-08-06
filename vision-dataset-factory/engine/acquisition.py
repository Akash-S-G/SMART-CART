import os
import csv
import yaml
import hashlib
import uuid
import requests
import imagehash
from PIL import Image
from io import BytesIO

from plugins.duckduckgo_discovery import DuckDuckGoDiscovery
from plugins.crawl4ai_plugin import Crawl4AIPlugin
from plugins.openfoodfacts_plugin import OpenFoodFactsPlugin

class AcquisitionEngine:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.target = self.config.get('target_images_per_class', 1000)
        self.families = self.config.get('families', [])
        
        self.discovery = DuckDuckGoDiscovery()
        self.crawler = Crawl4AIPlugin()
        self.off_plugin = OpenFoodFactsPlugin()
        
        self.manifest_path = "manifest.csv"
        self.base_dir = "storage"
        self.dirs = {
            "downloads": os.path.join(self.base_dir, "downloads"),
            "accepted": os.path.join(self.base_dir, "accepted"),
            "rejected": os.path.join(self.base_dir, "rejected"),
            "duplicates": os.path.join(self.base_dir, "duplicates")
        }
        
        # Load existing hashes to prevent cross-run duplication
        self.existing_sha256 = set()
        self.existing_phash = set()
        self._load_manifest()

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['sha256']: self.existing_sha256.add(row['sha256'])
                    if row['phash']: self.existing_phash.add(row['phash'])

    def append_manifest(self, record: dict):
        file_exists = os.path.exists(self.manifest_path) and os.path.getsize(self.manifest_path) > 0
        with open(self.manifest_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "image_path", "product_family", "source", "page_url", 
                "image_url", "width", "height", "sha256", "phash", "reason"
            ])
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

    def _generate_queries(self, family: str):
        variations = ["", "packet", "biscuit", "packaging", "front", "grocery", "supermarket"]
        return [f"{family} {v}".strip() for v in variations]

    def _download_and_verify(self, img_url: str, save_path: str) -> dict:
        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code != 200:
                return {"valid": False, "reason": f"HTTP {resp.status_code}"}
                
            img_bytes = resp.content
            # SHA256 check
            sha256 = hashlib.sha256(img_bytes).hexdigest()
            if sha256 in self.existing_sha256:
                return {"valid": False, "reason": "exact_duplicate_sha256", "sha256": sha256}
                
            # Image decode & Quality Check
            try:
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
                width, height = img.size
                if width < 512 or height < 512:
                    return {"valid": False, "reason": f"low_resolution_{width}x{height}", "sha256": sha256, "width": width, "height": height}
                
                # pHash check
                ph = str(imagehash.phash(img))
                if ph in self.existing_phash:
                    return {"valid": False, "reason": "near_duplicate_phash", "sha256": sha256, "phash": ph, "width": width, "height": height}
                    
                # Save to disk
                with open(save_path, 'wb') as f:
                    f.write(img_bytes)
                    
                return {"valid": True, "sha256": sha256, "phash": ph, "width": width, "height": height}
            except Exception as e:
                return {"valid": False, "reason": "corrupt_image"}
                
        except Exception as e:
            return {"valid": False, "reason": "download_failed"}

    def process_family(self, family: str):
        print(f"\n--- Processing Family: {family} ---")
        accepted_count = 0
        candidates = 0
        duplicates = 0
        rejected = 0
        
        # Ensure directories exist
        for d in self.dirs.values():
            os.makedirs(os.path.join(d, family), exist_ok=True)
            
        # 1. API Direct (OpenFoodFacts)
        print(f"[{family}] Querying OpenFoodFacts...")
        for item in self.off_plugin.discover_images(family, family):
            if accepted_count >= self.target:
                break
            candidates += 1
            result = self._process_candidate(family, item)
            if result == 'accepted': accepted_count += 1
            elif result == 'duplicate': duplicates += 1
            elif result == 'rejected': rejected += 1

        # 2. Web Crawling (DuckDuckGo -> Crawl4AI)
        if accepted_count < self.target:
            queries = self._generate_queries(family)
            for q in queries:
                if accepted_count >= self.target:
                    break
                print(f"[{family}] Researching query: '{q}'")
                
                for page_url in self.discovery.discover_pages(q, max_pages=3):
                    if accepted_count >= self.target:
                        break
                    print(f"[{family}] Crawling page: {page_url}")
                    
                    for item in self.crawler.discover_images(family, page_url):
                        if accepted_count >= self.target:
                            break
                        candidates += 1
                        result = self._process_candidate(family, item)
                        if result == 'accepted': accepted_count += 1
                        elif result == 'duplicate': duplicates += 1
                        elif result == 'rejected': rejected += 1
                        
        print(f"[{family}] Summary:")
        print(f"  Candidates found: {candidates}")
        print(f"  Rejected: {rejected}")
        print(f"  Duplicates: {duplicates}")
        print(f"  Accepted: {accepted_count}")

    def _process_candidate(self, family: str, item: dict) -> str:
        img_url = item['image_url']
        ext = img_url.split('.')[-1].split('?')[0][:4]
        if not ext.isalpha(): ext = "jpg"
        filename = f"{uuid.uuid4().hex[:8]}.{ext}"
        
        temp_path = os.path.join(self.dirs['downloads'], family, filename)
        
        res = self._download_and_verify(img_url, temp_path)
        
        record = {
            "product_family": family,
            "source": item['source'],
            "page_url": item['page_url'],
            "image_url": img_url,
            "width": res.get("width", ""),
            "height": res.get("height", ""),
            "sha256": res.get("sha256", ""),
            "phash": res.get("phash", ""),
            "reason": res.get("reason", "")
        }
        
        if res["valid"]:
            # Move to accepted
            final_path = os.path.join(self.dirs['accepted'], family, filename)
            os.rename(temp_path, final_path)
            record["image_path"] = final_path
            record["reason"] = "accepted"
            self.existing_sha256.add(res["sha256"])
            self.existing_phash.add(res["phash"])
            self.append_manifest(record)
            return 'accepted'
        else:
            # Handle rejection reason
            record["image_path"] = "" # Not accepted
            reason = res.get("reason", "unknown")
            if "duplicate" in reason:
                # Optionally save duplicates for review
                self.append_manifest(record)
                return 'duplicate'
            else:
                self.append_manifest(record)
                return 'rejected'

    def run(self):
        for family in self.families:
            self.process_family(family)

if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/acquisition.yaml"
    engine = AcquisitionEngine(config_path)
    engine.run()
