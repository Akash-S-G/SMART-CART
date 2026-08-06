import requests
import re
import urllib.parse
from typing import Iterator

class DuckDuckGoDiscovery:
    """
    Research module. Not an image source, but a webpage discovery tool.
    Finds URLs that might contain images.
    """
    
    def discover_pages(self, query: str, max_pages: int = 10) -> Iterator[str]:
        """
        Uses DDG HTML search to discover page URLs for a given query.
        """
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        data = {"q": query}
        
        try:
            # We use a simple regex to extract links since we might not have bs4 installed globally
            response = requests.post(url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                html = response.text
                links = re.findall(r'href="(https?://[^"]+)"', html)
                
                count = 0
                for link in links:
                    if 'duckduckgo' not in link and 'w3.org' not in link:
                        yield link
                        count += 1
                        if count >= max_pages:
                            break
        except Exception as e:
            print(f"[DuckDuckGo] Error discovering pages: {e}")

