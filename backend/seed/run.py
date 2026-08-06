#!/usr/bin/env python3
"""CLI: smartcart seed_products

Usage:
  python -m seed run                 # full seed
  python -m seed run --refresh       # ignore on-disk candidate cache
  python -m seed run --category Fruits
  python -m seed run --limit 20      # cap per category (smoke test)
  python -m seed run --reset         # wipe previously-seeded rows first
  python -m seed run --quiet

The command downloads open/licensed product data + images, validates,
normalizes and inserts into PostgreSQL idempotently.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the seed package + backend are importable.
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
for p in (str(HERE), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

from seeder import seed  # noqa: E402
from db import ensure_tables, reset_seeded, session_scope  # noqa: E402
from reviews import main as reviews_main  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="seed_products",
                                     description="Seed SmartCart catalog.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run the seeding pipeline")
    run.add_argument("--refresh", action="store_true",
                     help="Ignore cached raw candidates and re-fetch from APIs")
    run.add_argument("--category", type=str, default=None,
                     help="Seed only this category (exact name)")
    run.add_argument("--limit", type=int, default=None,
                     help="Cap number of candidates per category")
    run.add_argument("--reset", action="store_true",
                     help="Delete previously-seeded rows before seeding")
    run.add_argument("--quiet", action="store_true", help="Reduce progress output")

    rev = sub.add_parser("reviews", help="Generate product reviews")
    rev.add_argument("--only-vision", action="store_true",
                     help="Only vision-dataset products")
    rev.add_argument("--force", action="store_true",
                     help="Regenerate even if reviews exist")
    rev.add_argument("--min", type=int, default=10)
    rev.add_argument("--max", type=int, default=50)
    rev.add_argument("--limit", type=int, default=None)
    rev.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "reviews":
        cli = ["--only-vision"] if args.only_vision else []
        if args.force:
            cli.append("--force")
        cli += ["--min", str(args.min), "--max", str(args.max)]
        if args.limit:
            cli += ["--limit", str(args.limit)]
        if args.quiet:
            cli.append("--quiet")
        return reviews_main(cli)
    if args.cmd == "run":
        if args.reset:
            ensure_tables()
            with session_scope() as db:
                n = reset_seeded(db)
            print(f">>> Reset: removed {n} previously-seeded product(s).")
        seed(
            refresh=args.refresh,
            only_category=args.category,
            limit_per_category=args.limit,
            quiet=args.quiet,
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
