# SmartCart AI — Product Catalog Seeder

A reusable, idempotent pipeline that populates the `smartcart` PostgreSQL
database with a realistic, production-quality supermarket catalog.

## Data sources (all open / licensed)

| Source | Used for | License / terms |
| ------ | -------- | --------------- |
| Open Food Facts (`world.openfoodfacts.org`) | Fruits, Vegetables, Dairy, Bakery, Snacks, Beverages, Frozen, Instant Foods, Breakfast | Open DB License (ODbL) — permitted |
| Open Beauty Facts (`world.openbeautyfacts.org`) | Personal Care | ODbL — permitted |
| Open Pet Food Facts (`world.openpetfoodfacts.org`) | Pet Care | ODbL — permitted |
| Wikimedia Commons (`commons.wikimedia.org`) | General product imagery | CC / public domain |
| Curated brand catalog (local) | Home Cleaning, Baby Care, Electronics, Kitchen Essentials | Clearly tagged `sourced=False` |

**No data is scraped from Amazon / Flipkart / Walmart or any ToS-prohibited site.**

## Provenance / auditability

Every product row stores a `provenance` block inside the `products.metadata`
JSON column:

```json
{
  "provenance": {
    "sourced": true,            // false for generated curated rows
    "source": "openfoodfacts",
    "seeded_by": "smartcart_seeder",
    "seed_version": "1.0.0",
    "seeded_at": "2026-08-05T..."
  }
}
```

Sourced vs. generated fields are therefore distinguishable on every row.

## What gets written

* `categories` — the 15 supermarket categories.
* `products` — SKU, barcode, name, brand, description, `metadata` (subcategory,
  MRP, selling price, discount, rating, review count, unit, weight, country,
  tags, search keywords, gallery image URLs).
* `product_prices` — selling price + GST + discount %.
* `product_weights` — expected weight + tolerance (smart-cart scale check).
* `inventory` — stock quantity, reorder level, location.
* `product_images` — thumbnail + gallery, stored locally under
  `backend/static/products/<sku>/...` and served at `/static/products/...`.

## Usage

```bash
# from backend/
./seed_products.sh                 # full seed (uses .venv)
# or directly:
python -m seed run

# options
python -m seed run --reset         # wipe previously-seeded rows, then seed
python -m seed run --refresh       # ignore cached raw candidates, re-fetch APIs
python -m seed run --category Fruits
python -m seed run --limit 20      # cap candidates per category (smoke test)
python -m seed run --quiet
```

`seed_products.sh` at the repo root delegates to `backend/seed`.

## Idempotency

* SKU is the upsert key. Re-running **updates** changed metadata and **preserves**
  existing rows — never duplicates.
* `--reset` removes only rows this tool created (matched by `provenance.seeded_by`)
  and sweeps orphaned child rows.
* Barcode / name collisions are dropped at validation time.

## Layout

```
backend/seed/
  config.py          # category plan, source map, thresholds
  http_client.py     # retrying, rate-limited HTTP
  db.py              # engine, category upsert, reset
  adapters/          # openfoodfacts, wikimedia, curated
  image_utils.py     # download, validate, normalize, perceptual dedup
  normalizer.py      # name/brand/unit/price + metadata assembly
  duplicate.py       # sku/barcode/name dedup
  seeder.py          # orchestrator
  logging_utils.py   # progress + final report
  run.py             # CLI entrypoint
  cache/             # on-disk raw-candidate cache (speeds reruns)
  ../static/products # downloaded, normalized images
```
