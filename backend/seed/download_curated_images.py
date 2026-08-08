"""One-off: download images for the curated 16-category catalog.

Mirrors ImageStore semantics (RGB, JPEG q88, longest-edge 640px, perceptual-hash
dedup) and writes to static/products/<SKU>/gallery_1.jpg + gallery_2.jpg ... so
the layout matches what the app serves. Runs independently of the DB/seeder.

Usage:
    .venv/bin/python -m seed.download_curated_images            # all
    .venv/bin/python -m seed.download_curated_images --cat "Tea & Coffee" --limit 10
"""
from __future__ import annotations

import argparse
import hashlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "seed"))

from PIL import Image  # noqa: E402

import config as cfg  # noqa: E402
from catalog import images as cimg  # noqa: E402
from catalog.build import build_catalog, slugify  # noqa: E402
from seed.http_client import HttpClient  # noqa: E402
from seed.normalizer import new_sku  # noqa: E402


def _average_hash(img: Image.Image, hash_size: int = 8) -> str:
    small = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    return "".join("1" if p > avg else "0" for p in pixels)


def _save_normalized(img: Image.Image, dest: Path) -> None:
    img = img.convert("RGB")
    w, h = img.size
    long_edge = max(w, h)
    target = cfg.TARGET_THUMB
    if long_edge > target:
        scale = target / float(long_edge)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                         Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    dest.write_bytes(buf.getvalue())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--per", type=int, default=3, help="images wanted per product")
    args = ap.parse_args()

    products = build_catalog()
    if args.cat:
        products = [p for p in products if p.category == args.cat]
    if args.limit:
        products = products[:args.limit]

    # Fail-fast: a stalled source should not block the whole run. Shorten the
    # per-request timeout so a hung fetch gives up quickly and we move on.
    cfg.REQUEST_TIMEOUT = 15
    cfg.MAX_RETRIES = 2

    http = HttpClient()
    root = cfg.IMAGES_ROOT
    root.mkdir(parents=True, exist_ok=True)

    seen_hashes: dict[str, str] = {}
    total, ok, failed, skipped = 0, 0, 0, 0

    # assign SKUs exactly like the seeder: per-category 5-digit sequence using
    # new_sku(category, n) -> "SC-<PREFIX>-<NNNNN>", so the on-disk path the
    # app serves matches the row the seeder will later create.
    seq_by_cat: dict[str, int] = {}

    for p in products:
        total += 1
        cat = p.category
        seq_by_cat[cat] = seq_by_cat.get(cat, 0) + 1
        sku = new_sku(cat, seq_by_cat[cat])
        folder = root / sku
        folder.mkdir(parents=True, exist_ok=True)

        # RESUME: if this SKU already has at least one image, skip it.
        existing = [f for f in folder.glob("gallery_*.jpg") if f.stat().st_size > 3000]
        if existing:
            ok += 1
            continue

        cands = cimg.gather(p, http, want=args.per)
        if not cands:
            skipped += 1
            print(f"  [skip] {p.display_name}: no candidate sources")
            continue

        saved = 0
        for i, c in enumerate(cands, 1):
            url = c.get("url")
            try:
                resp = http.get_bytes(url)
            except Exception as e:
                print(f"  [fail] {p.display_name}: {type(e).__name__}")
                failed += 1
                continue
            if not resp.ok:
                failed += 1
                continue
            data = resp.body
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
            except Exception:
                failed += 1
                continue
            if min(img.size) < cfg.MIN_IMAGE_DIM:
                failed += 1
                continue
            ah = _average_hash(img)
            if ah in seen_hashes:
                continue  # global near-dup
            dest = folder / f"gallery_{i}.jpg"
            _save_normalized(img, dest)
            seen_hashes[ah] = str(dest)
            saved += 1
        if saved:
            ok += 1
            print(f"  [ok]   {p.display_name}: {saved} image(s) -> {folder}")
        else:
            failed += 1
            print(f"  [fail] {p.display_name}: all candidates failed")

    print(f"\nDONE: {total} products | {ok} with images | {failed} failed | {skipped} no-source")


if __name__ == "__main__":
    main()
