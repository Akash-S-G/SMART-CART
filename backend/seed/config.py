"""Configuration for the SmartCart catalog seeder.

Defines:
  * The full supermarket category plan (target counts, subcategory vocab).
  * Which source adapter feeds each category.
  * Filesystem / runtime constants.
  * Data-quality thresholds.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BACKEND_ROOT = Path(__file__).resolve().parent.parent
SEED_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = BACKEND_ROOT / "static"
IMAGES_ROOT = STATIC_ROOT / "products"

# --------------------------------------------------------------------------- #
# Data sources (open / licensed)
# --------------------------------------------------------------------------- #
# NOTE: we use the *India* country subdomains (in.*) instead of world.*.
# Open*Facts serves a country-scoped view on these hosts, i.e. every product
# returned already carries countries_tags=en:india.  This is what keeps the
# catalog an *Indian* grocery catalog instead of a global (mostly French) dump.
OFF_BASE = "https://in.openfoodfacts.org"
OBF_BASE = "https://in.openbeautyfacts.org"
OPFF_BASE = "https://in.openpetfoodfacts.org"
# World-wide fallbacks, only used when the India view returns nothing at all.
OFF_WORLD_BASE = "https://world.openfoodfacts.org"
OBF_WORLD_BASE = "https://world.openbeautyfacts.org"
OPFF_WORLD_BASE = "https://world.openpetfoodfacts.org"
WIKI_API = "https://commons.wikimedia.org/w/api.php"
# User agent required by the Open*Facts robots / API etiquette.
USER_AGENT = "smartcart-ai-seeder/1.0 (educational demo; contact: dev@smartcart.example)"

# How many real products we attempt to pull per category from APIs before
# falling back to generated inventory to reach the target count.  High enough
# that after quality filtering (premium min-dim) we still hit >=50 good items.
API_PER_CATEGORY_CAP = 260

# --------------------------------------------------------------------------- #
# Indian-market scoping
# --------------------------------------------------------------------------- #
# Only keep products that are actually sold in India.  The in.* Open*Facts
# subdomains already scope by country, but a few records leak through with a
# different countries_tags, so we re-verify per candidate.
INDIA_ONLY = True
INDIA_COUNTRY_TAGS = {"en:india", "india", "en:in", "inde", "भारत"}


# Rate limiting between API/HTTP requests (seconds).
REQUEST_DELAY = 0.15
MAX_RETRIES = 4
REQUEST_TIMEOUT = 40

# --------------------------------------------------------------------------- #
# Image quality thresholds
# --------------------------------------------------------------------------- #
# Reject junk / placeholder / logo crops smaller than this.
MIN_IMAGE_DIM = 200
MIN_IMAGE_BYTES = 8_000          # reject tiny / placeholder images
# Premium floor: OFF/Wikimedia candidates whose best available image is smaller
# than this are skipped — we only keep recognisable, high-quality packaging shots.
PREMIUM_MIN_DIM = 400
TARGET_THUMB = 640               # longest edge for normalised thumbnail (premium)
DEDUP_HASH_BITS = 8              # perceptual-ish hash (average hash)

# --------------------------------------------------------------------------- #
# Idempotency / provenance
# --------------------------------------------------------------------------- #
SEED_SOURCE_LABEL = "smartcart_seeder"
SEED_VERSION = "1.0.0"


@dataclass
class CategoryPlan:
    """One supermarket category and how to populate it."""

    name: str
    target: int
    source: str                      # adapter key
    # OFF-family taxonomy tag (en:<...>) or None
    off_tag: str | None = None
    # Additional OFF tags merged into the same search (broadens results)
    alt_off_tags: list[str] = field(default_factory=list)
    # Subcategories used to build realistic metadata + search keywords
    subcategories: list[str] = field(default_factory=list)
    # Wikimedia search queries (one per subcategory slot, optional)
    wiki_queries: list[str] = field(default_factory=list)
    description: str = ""


# --------------------------------------------------------------------------- #
# The catalog plan
# --------------------------------------------------------------------------- #
CATEGORY_PLAN: list[CategoryPlan] = [
    CategoryPlan(
        name="Fruits", target=60, source="off",
        off_tag="en:fruits",
        alt_off_tags=["en:dried-fruits", "en:fruit-purees"],
        subcategories=["Fresh Fruits", "Tropical Fruits", "Berries", "Citrus"],
        description="Fresh seasonal fruits sourced from verified open food databases.",
    ),
    CategoryPlan(
        name="Vegetables", target=60, source="off",
        off_tag="en:vegetables",
        alt_off_tags=["en:legumes", "en:canned-vegetables"],
        subcategories=["Leafy Vegetables", "Root Vegetables", "Gourds", "Healthy Salads"],
        description="Fresh vegetables and greens for everyday cooking.",
    ),
    CategoryPlan(
        name="Dairy", target=55, source="off",
        off_tag="en:dairies",
        alt_off_tags=["en:milks", "en:cheeses", "en:butters", "en:yogurts", "en:paneers"],
        subcategories=["Milk", "Cheese", "Butter", "Yogurt", "Curd", "Paneer"],
        description="Milk, cheese, paneer, butter and cultured dairy products.",
    ),
    CategoryPlan(
        name="Bakery", target=50, source="off",
        off_tag="en:breads",
        alt_off_tags=["en:cakes", "en:biscuits"],
        subcategories=["Bread", "Buns", "Biscuits", "Cakes", "Rusk"],
        description="Bakery staples including bread, rusk, biscuits and cakes.",
    ),
    CategoryPlan(
        name="Snacks", target=80, source="off",
        off_tag="en:snacks",
        alt_off_tags=["en:salty-snacks", "en:crisps", "en:nuts", "en:chocolates"],
        subcategories=["Chips", "Namkeen", "Cookies", "Chocolates", "Nuts"],
        description="Packaged snacks, chips, namkeen and confectionery.",
    ),
    CategoryPlan(
        name="Beverages", target=65, source="off",
        off_tag="en:beverages",
        alt_off_tags=["en:sodas", "en:fruit-juices", "en:waters", "en:energy-drinks"],
        subcategories=["Soft Drinks", "Juices", "Tea", "Coffee", "Water", "Energy Drinks"],
        description="Drinks ranging from water and juice to tea and coffee.",
    ),
    CategoryPlan(
        name="Frozen Foods", target=50, source="off",
        off_tag="en:frozen-foods",
        alt_off_tags=["en:ice-creams"],
        subcategories=["Frozen Vegetables", "Ice Cream", "Frozen Meals", "Frozen Snacks"],
        description="Frozen vegetables, desserts and ready-to-cook meals.",
    ),
    CategoryPlan(
        name="Instant Foods", target=55, source="off",
        off_tag="en:instant-noodles",
        alt_off_tags=["en:noodles", "en:pasta"],
        subcategories=["Noodles", "Pasta", "Soups", "Ready Meals"],
        description="Instant noodles, pasta, soups and quick meals.",
    ),
    CategoryPlan(
        name="Breakfast", target=55, source="off",
        off_tag="en:breakfasts",
        alt_off_tags=["en:breakfast-cereals", "en:jams", "en:honeys"],
        subcategories=["Cereal", "Muesli", "Oats", "Spreads", "Cornflakes"],
        description="Breakfast cereals, oats, muesli and spreads.",
    ),
    # ---------------- Indian kirana / grocery staples ---------------- #
    CategoryPlan(
        name="Atta, Rice & Dal", target=60, source="off",
        off_tag="en:wheat-flours",
        alt_off_tags=["en:flours", "en:rices", "en:legumes"],
        subcategories=["Atta", "Rice", "Dal", "Besan", "Sooji", "Poha"],
        description="Wheat atta, basmati and everyday rice, dals and milling staples.",
    ),
    CategoryPlan(
        name="Masala & Spices", target=55, source="off",
        off_tag="en:spices",
        alt_off_tags=["en:salts", "en:condiments"],
        subcategories=["Whole Spices", "Ground Masala", "Blended Masala", "Salt"],
        description="Whole and ground Indian masalas, spice blends and salt.",
    ),
    CategoryPlan(
        name="Oil & Ghee", target=50, source="off",
        off_tag="en:vegetable-oils",
        alt_off_tags=["en:ghees"],
        subcategories=["Sunflower Oil", "Mustard Oil", "Groundnut Oil", "Ghee", "Refined Oil"],
        description="Cooking oils and desi ghee used in everyday Indian kitchens.",
    ),
    CategoryPlan(
        name="Tea & Coffee", target=50, source="off",
        off_tag="en:teas",
        alt_off_tags=["en:coffees"],
        subcategories=["Black Tea", "Green Tea", "Masala Chai", "Instant Coffee", "Filter Coffee"],
        description="Chai, green tea and coffee from Indian and open catalogues.",
    ),
    CategoryPlan(
        name="Pickles & Papad", target=45, source="off",
        off_tag="en:pickles",
        alt_off_tags=["en:papadums", "en:sauces"],
        subcategories=["Mango Pickle", "Mixed Pickle", "Papad", "Chutney", "Sauces"],
        description="Achaar, papad, chutneys and table sauces.",
    ),
    CategoryPlan(
        name="Sweeteners & Dry Fruits", target=50, source="off",
        off_tag="en:sugars",
        alt_off_tags=["en:sweeteners", "en:dried-fruits", "en:nuts"],
        subcategories=["Sugar", "Jaggery", "Honey", "Cashew", "Almond", "Raisins"],
        description="Sugar, jaggery, honey and dry fruits.",
    ),
    # ---------------- Non-food categories ---------------- #
    CategoryPlan(
        name="Personal Care", target=55, source="obf",
        off_tag="en:hygiene",
        alt_off_tags=["en:shampoos", "en:soaps", "en:deodorants"],
        subcategories=["Soap", "Shampoo", "Toothpaste", "Lotion", "Deodorant"],
        wiki_queries=["soap bar", "shampoo bottle", "toothpaste", "body lotion",
                      "deodorant spray", "face wash"],
        description="Personal hygiene and grooming products.",
    ),
    CategoryPlan(
        name="Home Cleaning", target=55, source="curated",
        off_tag=None,
        subcategories=["Detergent", "Dishwash", "Floor Cleaner", "Surface Cleaner", "Air Freshener"],
        wiki_queries=["laundry detergent", "dishwashing liquid", "floor cleaner bottle",
                      "surface cleaner spray", "air freshener"],
        description="Household cleaning and laundry supplies.",
    ),
    CategoryPlan(
        name="Baby Care", target=50, source="curated",
        off_tag=None,
        subcategories=["Diapers", "Baby Wipes", "Baby Food", "Baby Soap", "Baby Powder"],
        wiki_queries=["baby diapers", "baby wipes", "baby food jar", "baby soap",
                      "baby powder"],
        description="Diapering, bathing and feeding essentials for babies.",
    ),
    CategoryPlan(
        name="Pet Care", target=50, source="opff",
        off_tag="en:dog-foods",
        alt_off_tags=["en:cat-foods"],
        subcategories=["Dog Food", "Cat Food", "Pet Treats", "Pet Care"],
        wiki_queries=["dog food bag", "cat food", "pet treats"],
        description="Pet food and care products for dogs and cats.",
    ),
    CategoryPlan(
        name="Electronics", target=50, source="curated",
        off_tag=None,
        subcategories=["Chargers", "Cables", "Earphones", "Batteries", "Power Banks"],
        wiki_queries=["usb charger", "usb cable", "earphones", "aa batteries",
                      "power bank"],
        description="Small consumer electronics and accessories.",
    ),
    CategoryPlan(
        name="Kitchen Essentials", target=50, source="curated",
        off_tag=None,
        subcategories=["Cookware", "Storage", "Utensils", "Cleaning Tools"],
        wiki_queries=["cooking pot", "food storage container", "kitchen utensils",
                      "spatula"],
        description="Everyday cookware, utensils and kitchen tools.",
    ),
]

# Adapter registry keyed by CategoryPlan.source
SOURCE_OFF = "off"
SOURCE_OBF = "obf"
SOURCE_OPFF = "opff"
SOURCE_CURATED = "curated"
SOURCE_WIKIMEDIA = "wikimedia"

# Curated, clearly-generated brand catalog per subcategory.
# (brand, product_suffix) tuples used only for categories without an open API.
CURATED_BRANDS = [
    "SmartCart", "HomeEssentials", "PureLife", "FreshPick", "DailyNeeds",
    "CleanHome", "BabyBloom", "PetJoy", "TechMate", "KitchenPro",
]

CURATED_PRODUCTS: dict[str, list[tuple[str, str, str, float, str]]] = {
    # subcat -> list of (brand, variant, unit, base_price_inr, origin)
    "Detergent": [("Surf Excel", "Liquid Detergent", "1 L", 199.0, "India"),
                  ("Ariel", "Matic Top Load", "2 kg", 320.0, "India"),
                  ("Tide", "Plus Detergent", "1 kg", 180.0, "India"),
                  ("Safari", "Liquid Detergent", "500 ml", 110.0, "India")],
    "Dishwash": [("Vim", "Dishwash Gel", "750 ml", 99.0, "India"),
                 ("Maxis", "Dishwash Bar", "200 g", 30.0, "India"),
                 ("Pril", "Dishwash Liquid", "500 ml", 95.0, "India"),
                 ("Fortune", "Dishwash Gel", "400 ml", 75.0, "India")],
    "Floor Cleaner": [("Lizol", "Disinfectant", "975 ml", 185.0, "India"),
                      ("Harpic", "Floor Cleaner", "500 ml", 120.0, "India"),
                      ("Dettol", "Floor Cleaner", "950 ml", 199.0, "India")],
    "Surface Cleaner": [("Harpic", "Bathroom Cleaner", "500 ml", 130.0, "India"),
                        ("Cif", "Surface Cleaner", "500 ml", 115.0, "India"),
                        ("Colin", "Glass Cleaner", "500 ml", 105.0, "India")],
    "Air Freshener": [("Godrej", "Aer Pocket", "50 g", 75.0, "India"),
                      ("Odonil", " Bathroom Block", "40 g", 55.0, "India")],
    "Diapers": [("Pampers", "Active Baby Diapers", "M (44 ct)", 699.0, "India"),
                ("Huggies", "Wonder Pants", "L (36 ct)", 649.0, "India"),
                ("MamyPoko", "Pants", "XL (30 ct)", 499.0, "India")],
    "Baby Wipes": [("Mee Mee", "Baby Wipes", "72 pcs", 129.0, "India"),
                   ("Pampers", "Baby Wipes", "56 pcs", 119.0, "India"),
                   ("Himalaya", "Baby Wipes", "72 pcs", 135.0, "India")],
    "Baby Food": [("Nestle", "Cerelac Wheat", "300 g", 245.0, "India"),
                  ("Happa", "Organic Puree", "100 g", 150.0, "India")],
    "Baby Soap": [("Himalaya", "Baby Soap", "125 g", 60.0, "India"),
                  ("Johnson's", "Baby Soap", "100 g", 55.0, "India")],
    "Baby Powder": [("Johnson's", "Baby Powder", "200 g", 130.0, "India"),
                    ("Himalaya", "Baby Powder", "200 g", 125.0, "India")],
    "Dog Food": [("Pedigree", "Adult Dry Food", "3 kg", 599.0, "India"),
                 ("Drools", "Focus Puppy", "2 kg", 420.0, "India"),
                 ("Royal Canin", "Maxi Adult", "2 kg", 1050.0, "India")],
    "Cat Food": [("Whiskas", "Adult Dry Food", "1.2 kg", 499.0, "India"),
                 ("Me-O", "Tuna Flavour", "1 kg", 380.0, "India")],
    "Pet Treats": [("Purepet", "Dog Treat Bones", "200 g", 199.0, "India"),
                   ("Drools", "Dog Biscuits", "450 g", 220.0, "India")],
    "Pet Care": [("Himalaya", "Erina-EP Shampoo", "200 ml", 180.0, "India"),
                 ("Bath & Tonic", "Pet Conditioner", "200 ml", 199.0, "India")],
    "Chargers": [("Syska", "20W Fast Charger", "1 pc", 449.0, "India"),
                 ("Boat", "33W Charger", "1 pc", 599.0, "India"),
                 ("Ambrane", "Charger Adapter", "1 pc", 399.0, "India")],
    "Cables": [("Boat", "Type-C Cable 1m", "1 pc", 249.0, "India"),
               ("Portronics", "Lightning Cable", "1 m", 299.0, "India"),
               ("Ambrane", "Micro USB Cable", "1 m", 149.0, "India")],
    "Earphones": [("Boat", "Airdopes 131", "1 pc", 1299.0, "India"),
                  ("Realme", "Buds Wireless", "1 pc", 999.0, "India"),
                  ("Noise", "Buds Mini", "1 pc", 1199.0, "India")],
    "Batteries": [("Duracell", "AA Batteries", "4 pcs", 249.0, "India"),
                  ("Eveready", "AAA Batteries", "4 pcs", 120.0, "India"),
                  ("Energizer", "AA Batteries", "2 pcs", 199.0, "India")],
    "Power Banks": [("Mi", "10000mAh Power Bank", "1 pc", 999.0, "India"),
                    ("Syska", "20000mAh Power Bank", "1 pc", 1499.0, "India"),
                    ("Ambrane", "10000mAh Power Bank", "1 pc", 899.0, "India")],
    "Cookware": [("Prestige", "Non-stick Fry Pan", "24 cm", 599.0, "India"),
                 ("Hawkins", "Induction Base Pan", "22 cm", 699.0, "India"),
                 ("Nova", "Pressure Cooker", "3 L", 1299.0, "India")],
    "Storage": [("Tupperware", "Fridge Storage Box", "1 L", 349.0, "India"),
                ("Cello", "Airtight Container", "500 ml", 199.0, "India"),
                ("Signoraware", "Spice Jar Set", "6 pcs", 299.0, "India")],
    "Utensils": [("Pigeon", "Steel Spatula", "1 pc", 99.0, "India"),
                 ("Vinod", "Steel Ladle", "1 pc", 120.0, "India"),
                 ("Bergner", "Cooking Spoon", "1 pc", 149.0, "India")],
    "Cleaning Tools": [("Scotch-Brite", "Scrub Pad", "3 pcs", 45.0, "India"),
                       ("Gala", "Floor Wiper", "1 pc", 180.0, "India"),
                       ("Vim", "Scrubber", "1 pc", 60.0, "India")],
}

# Pricing / rating generation constants
DEFAULT_CURRENCY = "INR"
MRP_MARKUP_MIN = 1.05      # selling_price <= mrp; mrp = round(sell * markup)
MRP_MARKUP_MAX = 1.35
DISCOUNT_MIN = 0
DISCOUNT_MAX = 25
STOCK_MIN = 0
STOCK_MAX = 400
RATING_MIN = 3.2
RATING_MAX = 5.0
REVIEW_MIN = 5
REVIEW_MAX = 2400

# Brands we *recognise* from open data but still tag provenance honestly.
KNOWN_BRANDS = {
    "amul", "britannia", "haldiram", "parle", "tata", "itc", "nestle",
    "coca-cola", "pepsi", "unilever", "lays", "kurkure", "maggi", "yippee",
    "ferrero", "nutella", "kelloggs", "patanjali", "mother dairy",
    "nandini", "heritage", "pediasure", "horlicks", "cadbury",
}

# SKU prefix per category for readable identifiers
SKU_PREFIX = "SC"

# Environment overrides
ENV_DATABASE_URL = os.environ.get("DATABASE_URL")
ENV_STATIC_BASE_URL = os.environ.get("SEED_STATIC_BASE_URL",
                                       "http://localhost:8000/static/products")
