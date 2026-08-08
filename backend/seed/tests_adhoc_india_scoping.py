
"""Ad-hoc verification of the seeder India-scoping changes.

Offline: HTTP client stubbed, no network, no DB. Each check is paired with a
pre-fix counterexample run separately via git stash to prove it discriminates.
"""
import sys
from pathlib import Path

BACKEND = Path("/home/akash/Desktop/Smart cart/backend")
sys.path[:0] = [str(BACKEND / "seed"), str(BACKEND)]

import config as cfg
from adapters import open_food_facts as off
from normalizer import is_plausible_product_name

fails = []
def check(label, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: got={got!r}")
    if not ok:
        fails.append(label)

def prod(code, name, countries, img=True):
    p = {"code": code, "product_name": name, "countries_tags": countries}
    if img:
        p["image_front_url"] = f"https://images.openfoodfacts.org/{code}/front_en.4.400.jpg"
    return p

class Http:
    """Canned pages keyed by categories_tags; records tag visit order."""
    def __init__(self, pages, deep=None):
        self.pages, self.deep, self.seen = pages, deep or set(), []
    def get_json(self, url):
        tag = url.split("categories_tags=")[1].split("&")[0]
        page = int(url.split("page=")[1].split("&")[0])
        if page == 1:
            self.seen.append(tag)
        if tag in self.deep:  # never runs dry
            return {"products": [prod(f"d{page}{i}", f"Generic {page}-{i}", ["en:india"])
                                 for i in range(50)]}, None
        return {"products": self.pages.get(tag, {}).get(page, [])}, None

class Plan:
    source, off_tag = cfg.SOURCE_OFF, "en:primary"
    alt_off_tags = ["en:alt1", "en:alt2"]

print("\n[1] fetch() walks every tag when the FIRST tag is productive")
# The real-world regression: pre-fix, a deep first tag meant alts were never
# reached -- which is why Fruits hoarded 293 rows and Dairy/Snacks stayed at 0.
cfg.API_PER_CATEGORY_CAP = 10_000
h = Http({"en:alt1": {1: [prod("a", "Staple Alt1", ["en:india"])]},
          "en:alt2": {1: [prod("b", "Staple Alt2", ["en:india"])]}},
         deep={"en:primary"})
out = off.fetch(Plan(), h)
check("all tags visited", sorted(set(h.seen)), ["en:alt1", "en:alt2", "en:primary"])
check("alt staples collected",
      sorted(c["name"] for c in out if c["name"].startswith("Staple")),
      ["Staple Alt1", "Staple Alt2"])
cfg.API_PER_CATEGORY_CAP = 260

print("\n[2] fetch() walks on past a DRY first tag")
h = Http({"en:primary": {1: []},
          "en:alt1": {1: [prod("1", "Amul Butter", ["en:india"])]},
          "en:alt2": {1: [prod("2", "Tata Salt", ["en:india"])]}})
out = off.fetch(Plan(), h)
check("tag order", h.seen, ["en:primary", "en:alt1", "en:alt2"])
check("products found", sorted(c["name"] for c in out), ["Amul Butter", "Tata Salt"])

print("\n[3] fetch() drops non-India rows, normalises origin")
h = Http({"en:primary": {1: [
              prod("10", "Haldiram Bhujia", ["en:india"]),
              prod("11", "Compote Pomme", ["en:france"]),
              prod("12", "Multi Market", ["en:france", "en:india"]),
              prod("13", "No Country", []),
              prod("14", "No Image", ["en:india"], img=False)]},
          "en:alt1": {1: []}, "en:alt2": {1: []}})
out = off.fetch(Plan(), h)
check("france-only excluded, imageless skipped",
      sorted(c["name"] for c in out),
      ["Haldiram Bhujia", "Multi Market", "No Country"])
check("origin folded to India", {c["country"] for c in out}, {"India"})

print("\n[4] _is_indian() gate")
for lbl, tags, want in [("india", ["en:india"], True), ("france", ["en:france"], False),
                        ("mixed", ["en:france", "en:india"], True),
                        ("empty/host-scoped", [], True), ("case", ["EN:India"], True)]:
    check(lbl, off._is_indian({"countries_tags": tags}), want)

print("\n[5] is_plausible_product_name() rejects barcode-as-name")
for lbl, name, want in [("bare EAN", "3948764092305", False), ("symbols", "-- 1234 --", False),
                        ("real", "Everest Chaat Masala", True), ("alnum", "3 Roses Tea", True),
                        ("empty", "", False)]:
    check(lbl, is_plausible_product_name(name), want)

print("\n[6] config integrity")
check("OFF india host", cfg.OFF_BASE, "https://in.openfoodfacts.org")
check("OBF india host", cfg.OBF_BASE, "https://in.openbeautyfacts.org")
check("OPFF india host", cfg.OPFF_BASE, "https://in.openpetfoodfacts.org")
check("world fallback kept", cfg.OFF_WORLD_BASE, "https://world.openfoodfacts.org")
check("INDIA_ONLY", cfg.INDIA_ONLY, True)
names = [p.name for p in cfg.CATEGORY_PLAN]
original = ["Fruits", "Vegetables", "Dairy", "Bakery", "Snacks", "Beverages",
            "Frozen Foods", "Instant Foods", "Breakfast", "Personal Care",
            "Home Cleaning", "Baby Care", "Pet Care", "Electronics", "Kitchen Essentials"]
check("no original category deleted", [n for n in original if n not in names], [])
check("6 new indian categories",
      sum(n in names for n in ["Atta, Rice & Dal", "Masala & Spices", "Oil & Ghee",
                               "Tea & Coffee", "Pickles & Papad",
                               "Sweeteners & Dry Fruits"]), 6)
check("names unique", len(names), len(set(names)))
check("targets positive", all(p.target > 0 for p in cfg.CATEGORY_PLAN), True)

print("\n[7] source-level guards")
check("seeder target guard",
      "if (inserted + updated) >= plan.target:" in (BACKEND/"seed"/"seeder.py").read_text(), True)
check("db pooler fix",
      '"prepare_threshold": None' in (BACKEND/"seed"/"db.py").read_text(), True)

print()
print(f"FAILED {fails}" if fails else "ALL CHECKS PASSED")
sys.exit(1 if fails else 0)
