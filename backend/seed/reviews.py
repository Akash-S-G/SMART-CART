"""Reviews seeder: populate the `reviews` table with realistic synthetic reviews.

No open, legally-reusable review API exists for Indian supermarket products, so
per the project brief we GENERATE realistic synthetic reviews and mark every row
is_generated = TRUE. We never scrape commercial ecommerce reviews.

Behaviour:
  * Idempotent: skips products that already have >=1 review (pass --force to
    regenerate).
  * Realistic rating distribution centred on each product's stored rating.
  * 10-50 reviews per product (configurable via --min/--max).
  * Generated reviewer handles + dates spread over the past ~18 months.

Usage:
    unset PYTHONPATH
    .venv/bin/python -m seed reviews                 # all products lacking reviews
    .venv/bin/python -m seed reviews --only-vision   # only vision-dataset products
    .venv/bin/python -m seed reviews --force         # overwrite existing
    .venv/bin/python -m seed reviews --limit 5       # cap products (smoke test)
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
for p in (str(HERE), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

import config as cfg  # noqa: E402
from db import ensure_tables, session_scope  # noqa: E402
from app.models.products.review import Review  # noqa: E402
from sqlalchemy import select, func, text  # noqa: E402

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Rohan", "Kabir", "Ananya", "Diya", "Saanvi", "Aadhya", "Ishita", "Myra",
    "Kavya", "Naina", "Riya", "Aanya", "Arnav", "Dhruv", "Karthik", "Rahul",
    "Priya", "Neha", "Sneha", "Meera", "Ravi", "Suresh", "Anjali", "Deepa",
]
LAST_INITIALS = ["S", "K", "M", "R", "P", "V", "N", "B", "G", "T", "J", "C", "D"]

# Review templates keyed loosely by sentiment. {brand}/{product} substituted.
POSITIVE = [
    "Absolutely love {product} from {brand}. Quality is consistently great and "
    "it arrived well packed. Will buy again.",
    "Great product by {brand}. {product} exceeded my expectations — fresh and "
    "as described. Highly recommended.",
    "Very happy with {product}. {brand} never disappoints. Good value for money.",
    "{product} is now a regular in my cart. {brand} delivers reliable quality "
    "every time.",
    "Excellent packaging and taste. {brand}'s {product} is worth every rupee.",
    "Top notch {product}. The freshness and flavour are exactly what I expect "
    "from {brand}.",
    "Been using {brand}'s {product} for months. Consistent quality, never an "
    "off batch. Five stars.",
    "Superb {product} — the texture and taste are just right. {brand} is my "
    "go-to brand now.",
    "Pleasantly surprised by {product}. {brand} has nailed the balance of "
    "taste and price.",
    "Best {product} I have tried in this range. {brand} clearly cares about "
    "quality.",
    "Fresh, authentic and well sealed. {brand}'s {product} is a pantry staple "
    "in our home.",
    "Great shelf life and no stale smell on opening. {product} from {brand} is "
    "dependable.",
    "The {product} tastes just like the larger pack but at a better price. "
    "Happy with {brand}.",
    "Nice crisp finish and good portion size. {brand}'s {product} is a "
    "repeat purchase for me.",
    "Loved the aroma as soon as I opened it. {brand} {product} feels premium "
    "without the premium price.",
]
NEUTRAL = [
    "Decent {product} from {brand}. Does the job, nothing extraordinary but "
    "satisfactory for the price.",
    "{product} is okay. {brand} could improve the packaging a bit, but the "
    "product itself is fine.",
    "Reasonable quality. {product} met my basic expectations; might repurchase.",
    "Average experience with {brand} {product}. Works as intended, no complaints.",
    "It is an alright {product}. Tastes fine but nothing that stands out. "
    "{brand} is acceptable.",
    "Slightly pricey for what it is, but {brand}'s {product} is consistent. "
    "Will see.",
    "The {product} is fine for daily use. {brand} could be a bit more "
    "generous with quantity.",
    "Nothing wrong with {product}; just not as flavourful as I hoped. {brand} "
    "is okay.",
    "Good enough for the household. {brand}'s {product} does the basics well.",
    "Tried {product} on a friend's recommendation. Decent, though I expected "
    "a bit more from {brand}.",
    "Packaging was standard and the {product} was fresh. {brand} delivers an "
    "average-but-honest product.",
    "The {product} works for my needs. {brand} is a safe, no-surprises choice.",
]
NEGATIVE = [
    "Not very happy with {product}. {brand} usually is better — this batch "
    "seemed off. Expected more.",
    "{product} was disappointing. {brand} needs to work on consistency. "
    "Probably won't reorder.",
    "Quality of {product} has dropped. {brand} should look into this. "
    "Slightly overpriced for what it is.",
    "The {product} arrived a bit crushed and the seal looked tampered. "
    "{brand} needs better logistics.",
    "Flavour of {brand}'s {product} did not match the label. Would not buy "
    "again.",
    "Too salty / sweet for my taste. {brand}'s {product} was not enjoyable.",
    "Expiry was closer than I like on receipt. {brand} {product} felt like "
    "old stock.",
    "Overpriced for the quantity. {brand}'s {product} is not great value.",
    "Inconsistent pieces in the pack — some stale. {brand} should improve "
    "quality control.",
    "Did not like the aftertaste of {product}. {brand} is usually better.",
]

TITLES_POS = ["Excellent", "Loved it", "Great buy", "Highly recommended", "Superb quality"]
TITLES_NEU = ["Decent", "As expected", "Okay product", "Satisfactory", "Average"]
TITLES_NEG = ["Disappointed", "Not as expected", "Below par", "Won't reorder", "Poor quality"]


def _rating_buckets(center: float) -> list[tuple[float, float, list[str], list[str], float]]:
    """Return (low, high, templates, titles, weight) buckets weighted by center."""
    center = max(3.0, min(5.0, center))
    # Probability weights for pos/neu/neg based on center.
    p_pos = max(0.05, (center - 3.0) / 2.0)        # 3.0->0.05, 5.0->1.0
    p_neg = max(0.05, (3.0 - (center - 2.0)) / 2.0)  # small for high ratings
    p_neg = min(p_neg, 0.35)
    p_neu = max(0.1, 1.0 - p_pos - p_neg)
    total = p_pos + p_neu + p_neg
    p_pos, p_neu, p_neg = p_pos / total, p_neu / total, p_neg / total
    return [
        (4.0, 5.0, POSITIVE, TITLES_POS, p_pos),
        (3.0, 3.9, NEUTRAL, TITLES_NEU, p_neu),
        (1.0, 2.9, NEGATIVE, TITLES_NEG, p_neg),
    ]


def _pick_bucket(center: float) -> tuple[float, float, list[str], list[str]]:
    buckets = _rating_buckets(center)
    r = random.random()
    cum = 0.0
    for low, high, tmpl, titles, w in buckets:
        cum += w
        if r <= cum:
            return low, high, tmpl, titles
    return buckets[0][0], buckets[0][1], buckets[0][2], buckets[0][3]


def _product_rating(meta: dict | None) -> float:
    if isinstance(meta, dict):
        r = meta.get("rating")
        if isinstance(r, (int, float)):
            return float(r)
    return round(random.uniform(3.6, 4.7), 1)


def generate_reviews_for_product(name: str, brand: str | None, rating: float,
                                 n: int) -> list[dict]:
    brand = brand or "this brand"
    # Avoid awkward "X from X" when brand == product name (common for
    # single-brand product folders like "Surf Excel").
    out = []
    seen_bodies: set[str] = set()
    attempts = 0
    while len(out) < n and attempts < n * 6:
        attempts += 1
        low, high, tmpl, titles = _pick_bucket(rating)
        r = round(random.uniform(low, high), 1)
        body = random.choice(tmpl).format(product=name, brand=brand)
        # If the template embedded the brand redundantly (brand == product),
        # strip the brand mentions so we don't get "Surf Excel from Surf Excel".
        if brand == name:
            body = (body
                    .replace(f"from {brand} ", "")
                    .replace(f"from {brand}.", ".")
                    .replace(f"{brand}'s ", "")
                    .replace(f"{brand} ", "", 1))
        if body in seen_bodies:
            continue
        seen_bodies.add(body)
        title = random.choice(titles)
        user = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_INITIALS)}."
        # date within last 18 months, older reviews less helpful
        days_ago = random.randint(3, 540)
        rdate = datetime.now(timezone.utc) - timedelta(days=days_ago,
                                                        hours=random.randint(0, 23))
        helpful = max(0, int((r - 2.5) * random.randint(0, 40) + random.randint(0, 5)))
        out.append({
            "user_name": user,
            "rating": r,
            "title": title,
            "body": body,
            "is_generated": True,
            "verified_purchase": random.random() < 0.7,
            "helpful_count": helpful,
            "review_date": rdate,
        })
    return out


def _is_vision_product(meta: dict | None) -> bool:
    if isinstance(meta, dict):
        prov = meta.get("provenance") or {}
        return prov.get("source") == "vision-dataset-factory"
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="seed reviews")
    ap.add_argument("--only-vision", action="store_true",
                    help="Only generate reviews for vision-dataset products")
    ap.add_argument("--force", action="store_true",
                    help="Regenerate even if product already has reviews")
    ap.add_argument("--min", type=int, default=10)
    ap.add_argument("--max", type=int, default=50)
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap number of products (smoke test)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    ensure_tables()
    random.seed(42)  # reproducible synthetic data

    from app.models.products.product import Product

    with session_scope() as db:
        q = select(Product).where(Product.is_active == True)  # noqa: E712
        products = db.execute(q).scalars().all()
        # Snapshot the fields we need BEFORE the session closes (objects detach
        # once the session scope exits).
        product_rows = [
            (p.id, p.name, p.brand, p.metadata_ if isinstance(p.metadata_, dict) else {})
            for p in products
        ]

    if args.only_vision:
        product_rows = [r for r in product_rows if _is_vision_product(r[3])]

    total_target = 0
    inserted = 0
    skipped = 0
    products_done = 0

    for pid, name, brand, meta in product_rows:
        if args.limit and products_done >= args.limit:
            break
        with session_scope() as db:
            existing = db.execute(
                select(func.count(Review.id)).where(Review.product_id == pid)
            ).scalar_one()
            if existing > 0 and not args.force:
                skipped += 1
                products_done += 1
                continue
            if existing > 0 and args.force:
                db.execute(text("DELETE FROM reviews WHERE product_id = :pid")
                           .bindparams(pid=pid))
                db.flush()

            rating = _product_rating(meta)
            n = random.randint(args.min, args.max)
            reviews = generate_reviews_for_product(name, brand, rating, n)
            for rv in reviews:
                db.add(Review(product_id=pid, **rv))
            db.flush()
            inserted += n
            total_target += n
            products_done += 1
            if not args.quiet:
                print(f"  + {n} reviews for {name} (rating~{rating})")

    print(f"[done] products_processed={products_done} reviews_inserted={inserted} "
          f"products_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
