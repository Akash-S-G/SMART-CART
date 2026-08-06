import requests
import re
import urllib.parse
import json

def test_duckduckgo(query="Parle-G"):
    print("Testing DDG...")
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = {"q": query}
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        print("DDG Status:", response.status_code)
        if response.status_code == 200:
            html = response.text
            print("DDG HTML Sample:", html[:500])
            links = re.findall(r'href="([^"]+)"', html)
            for link in links:
                if 'uddg=' in link:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                    if 'uddg' in parsed:
                        actual_url = parsed['uddg'][0]
                        print("Found URL:", actual_url)
    except Exception as e:
        print("DDG Error:", e)

def test_off(query="Parle-G"):
    print("\nTesting OFF...")
    base_url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10
    }
    headers = {
        "User-Agent": "VisionDatasetFactory - Dataset Acquisition System"
    }
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        print("OFF Status:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            print("Found OFF products:", len(products))
            for prod in products[:1]:
                print("Prod ID:", prod.get('id'))
                print("Images keys:", prod.get("images", {}).keys())
            for key, img_data in prod.get("images", {}).items():
                print(f"Key {key}: {type(img_data)}")
                if isinstance(img_data, dict):
                    print(json.dumps(img_data, indent=2)[:500])
                break
    except Exception as e:
        print("OFF Error:", e)

if __name__ == "__main__":
    test_duckduckgo()
    test_off()
