"""Image sourcing for the curated Indian catalog.

Hybrid strategy (option C), tried in order and recorded per image:

    1. openfoodfacts  -- open licence (ODbL), real Indian pack shots
    2. wikimedia      -- open licence (CC/public domain), good for fresh produce
    3. websearch      -- DuckDuckGo images; best coverage of branded packs but
                         the results are generally copyrighted, so each one is
                         stamped provenance=websearch / license=unknown

Every returned candidate carries its source and licence so the compromise is
documented per-image rather than hidden.  Nothing here writes to disk or the
database; `seed.image_utils.ImageStore` still does the downloading, validation,
perceptual-hash dedup and storage.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")

OFF_SEARCH = "https://in.openfoodfacts.org/api/v2/search"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
DDG_HTML = "https://duckduckgo.com/"
DDG_JSON = "https://duckduckgo.com/i.js"

MIN_EDGE = 400          # reject anything smaller than this on the short edge
MAX_ASPECT = 1.6        # pack shots are near-square; wider means a banner

# Hosts that serve logos, sprites or watermarked placeholders rather than packs.
_HOST_DENY = ("logo", "sprite", "placeholder", "no-image", "noimage", "avatar",
              "banner", "-ad-", "coupon", "offer", "sale", "combo", "poster")

# Generic words that carry no identifying signal when matching a filename.
_STOPWORDS = {"pack", "india", "indian", "packet", "bottle", "box", "jar",
              "pouch", "fresh", "whole", "powder", "food", "product"}

# Branded packs are effectively absent from open repositories, so for these the
# hybrid goes straight to web search rather than burning requests on Commons.
_OPEN_SOURCE_FRIENDLY = {"Fruits & Vegetables"}


class Candidate(dict):
    """An image URL plus its provenance.  A dict so it JSON-caches trivially."""

    def __init__(self, url: str, source: str, license_: str, **extra):
        super().__init__(url=url, source=source, license=license_, **extra)


def _get(http, url: str, referer: str | None = None) -> str | None:
    """Fetch text via the seeder's HttpClient, falling back to urllib."""
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    try:
        if hasattr(http, "get_text"):
            return http.get_text(url, headers=headers)
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001 - any transport failure just means no image
        return None


def _plausible(url: str, w: int = 0, h: int = 0) -> bool:
    """Cheap pre-filter; ImageStore still validates the decoded bytes."""
    if not url or not url.startswith("http"):
        return False
    low = url.lower()
    if any(bad in low for bad in _HOST_DENY):
        return False
    if w and h:
        if min(w, h) < MIN_EDGE:
            return False
        if max(w, h) / max(1, min(w, h)) > MAX_ASPECT:
            return False
    return True


# --------------------------------------------------------------------------- #
# 1. Open Food Facts (open licence)
# --------------------------------------------------------------------------- #
def from_openfoodfacts(product, http, limit: int = 2) -> list[Candidate]:
    """Match on brand + a distinctive word from the product name."""
    brand = product.brand.lower().replace(" ", "-")
    if brand in ("fresh", ""):          # loose produce has no OFF brand
        return []
    url = (f"{OFF_SEARCH}?brands_tags={urllib.parse.quote(brand)}"
           f"&page_size=40&fields=product_name,image_front_url")
    raw = _get(http, url)
    if not raw:
        return []
    try:
        products = json.loads(raw).get("products", [])
    except json.JSONDecodeError:
        return []

    words = {w for w in re.findall(r"[a-z]{4,}", product.name.lower())}
    out: list[Candidate] = []
    for p in products:
        name = (p.get("product_name") or "").lower()
        img = p.get("image_front_url") or ""
        if not _plausible(img):
            continue
        if words and not (words & set(re.findall(r"[a-z]{4,}", name))):
            continue
        out.append(Candidate(img.replace(".400.jpg", ".full.jpg"),
                             "openfoodfacts", "ODbL 1.0", matched=name))
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# 2. Wikimedia Commons (open licence)
# --------------------------------------------------------------------------- #
def from_wikimedia(product, http, limit: int = 2) -> list[Candidate]:
    """Commons full-text search over file *pages*, which happily returns book
    scans and magazine covers that merely mention the word.  So we additionally
    require the file title to contain a meaningful term from the query."""
    query = product.image_queries[0] if product.image_queries else product.name
    url = (f"{COMMONS_API}?action=query&generator=search&gsrnamespace=6"
           f"&gsrsearch={urllib.parse.quote(query)}&gsrlimit={limit * 5}"
           f"&prop=imageinfo&iiprop=url|size&iiurlwidth=1000&format=json")
    raw = _get(http, url)
    if not raw:
        return []
    try:
        pages = json.loads(raw).get("query", {}).get("pages", {})
    except json.JSONDecodeError:
        return []

    terms = {w for w in re.findall(r"[a-z]{4,}", query.lower())} - _STOPWORDS
    out: list[Candidate] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        img = info.get("thumburl") or info.get("url") or ""
        title = (page.get("title") or "").lower()
        if not _plausible(img, info.get("width", 0), info.get("height", 0)):
            continue
        if terms and not (terms & set(re.findall(r"[a-z]{4,}", title))):
            continue    # rejects 'Purgatory proved' for a butter query
        out.append(Candidate(img, "wikimedia", "CC / public domain",
                             title=page.get("title", "")))
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# 3. Web image search (best coverage, unknown licence)
# --------------------------------------------------------------------------- #
_VQD = re.compile(r'vqd=["\']?([\d-]+)["\']?')


def from_websearch(product, http, query: str | None = None,
                   limit: int = 3) -> list[Candidate]:
    q = query or (product.image_queries[0] if product.image_queries
                  else f"{product.display_name} pack india")
    html = _get(http, f"{DDG_HTML}?q={urllib.parse.quote(q)}&iax=images&ia=images")
    if not html:
        return []
    m = _VQD.search(html)
    if not m:
        return []

    time.sleep(0.6)     # be a polite client between the token and the query
    raw = _get(http,
               f"{DDG_JSON}?l=in-en&o=json&q={urllib.parse.quote(q)}"
               f"&vqd={m.group(1)}&f=,,,&p=1",
               referer=DDG_HTML)
    if not raw:
        return []
    try:
        results = json.loads(raw).get("results", [])
    except json.JSONDecodeError:
        return []

    out: list[Candidate] = []
    for r in results:
        img = r.get("image") or ""
        if not _plausible(img, r.get("width", 0), r.get("height", 0)):
            continue
        out.append(Candidate(img, "websearch", "unknown - demo use only",
                             width=r.get("width"), height=r.get("height"),
                             origin=r.get("source") or r.get("url", "")[:120]))
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# Hybrid orchestration
# --------------------------------------------------------------------------- #
def gather(product, http, want: int = 3) -> list[Candidate]:
    """Open sources first, web search to fill the gap.  Deduped by URL.

    Commons is only consulted for unbranded produce; for branded packs it has
    essentially no coverage and its full-text search returns noise.
    """
    found: list[Candidate] = []
    seen: set[str] = set()

    def add(cands):
        for c in cands:
            if c["url"] not in seen:
                seen.add(c["url"])
                found.append(c)

    add(from_openfoodfacts(product, http))
    if len(found) < want and product.category in _OPEN_SOURCE_FRIENDLY:
        add(from_wikimedia(product, http))
    if len(found) < want:
        add(from_websearch(product, http, limit=want - len(found) + 2))
    return found[:want]
