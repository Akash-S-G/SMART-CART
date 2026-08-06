import requests
import re
import urllib.parse
from typing import Iterator, Dict
from plugins.base_plugin import BasePlugin

class Crawl4AIPlugin(BasePlugin):
    """
    Crawls a discovered webpage, extracts all <img> tags, and yields candidates.
    If 'crawl4ai' or 'bs4' is available, it uses that. Otherwise it falls back to regex 
    for robust local execution.
    """
    
    @property
    def source_name(self) -> str:
        return "crawler_engine"

    def _extract_links_and_images_regex(self, html: str, base_url: str):
        # Extract images
        img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        images = [urllib.parse.urljoin(base_url, src) for src in img_srcs if src]
        
        # Extract links for pagination/related
        a_hrefs = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html)
        links = [urllib.parse.urljoin(base_url, href) for href in a_hrefs if href]
        
        return images, links

    def discover_images(self, product_family: str, page_url: str) -> Iterator[Dict[str, str]]:
        """
        Takes a specific page_url (not a search query) and extracts image candidates.
        """
        headers = {
            "User-Agent": "VisionDatasetFactory - Dataset Acquisition System"
        }
        
        try:
            # We would use crawl4ai here. For compatibility we use requests + regex parser fallback.
            # Example crawl4ai pseudo-code:
            # from crawl4ai import WebCrawler
            # crawler = WebCrawler()
            # result = crawler.run(url=page_url)
            # return result.media.images
            
            response = requests.get(page_url, headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                images, links = self._extract_links_and_images_regex(html, page_url)
                
                for img_url in images:
                    # Basic heuristic to filter out tracking pixels or icons
                    if any(x in img_url.lower() for x in ['.svg', 'icon', 'logo', 'pixel', 'tracker']):
                        continue
                        
                    yield {
                        "image_url": img_url,
                        "page_url": page_url,
                        "source": self.source_name
                    }
        except Exception as e:
            print(f"[Crawl4AI] Error crawling {page_url}: {e}")

