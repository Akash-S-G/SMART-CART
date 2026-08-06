"""Progress reporting and final reporting for the seeder."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field


@dataclass
class Stats:
    started_at: float = field(default_factory=time.time)

    categories_created: int = 0
    products_processed: int = 0
    products_inserted: int = 0
    products_updated: int = 0
    products_skipped: int = 0
    duplicates_removed: int = 0

    images_downloaded: int = 0
    images_failed: int = 0
    images_deduped: int = 0
    images_validated: int = 0

    api_calls: int = 0
    api_failures: int = 0

    per_category: dict[str, int] = field(default_factory=dict)

    def elapsed(self) -> float:
        return time.time() - self.started_at

    def add_category(self, name: str, count: int) -> None:
        self.per_category[name] = count


class Progress:
    """Minimal progress printer (no external deps)."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def info(self, msg: str) -> None:
        if not self.quiet:
            print(f"[info] {msg}", flush=True)

    def step(self, msg: str) -> None:
        if not self.quiet:
            print(f"  -> {msg}", flush=True)

    def category(self, name: str, target: int) -> None:
        if not self.quiet:
            print(f"\n=== Category: {name} (target {target}) ===", flush=True)

    def product(self, idx: int, total: int, name: str) -> None:
        if not self.quiet:
            print(f"   [{idx:>4}/{total}] {name[:48]}", flush=True)

    def image(self, idx: int, total: int, ok: bool, reason: str = "") -> None:
        if not self.quiet:
            mark = "OK " if ok else "FAIL"
            tail = f" ({reason})" if reason and not ok else ""
            print(f"        img {idx:>3}/{total} {mark}{tail}", flush=True)

    def warn(self, msg: str) -> None:
        print(f"[warn] {msg}", flush=True)

    def error(self, msg: str) -> None:
        print(f"[ERROR] {msg}", file=sys.stderr, flush=True)


def print_report(stats: Stats, progress: Progress) -> None:
    """Print a detailed final summary."""
    lines = []
    lines.append("")
    lines.append("=" * 64)
    lines.append("  SmartCart AI  -  Catalog Seed Report")
    lines.append("=" * 64)
    lines.append(f"  Total execution time     : {stats.elapsed():.1f}s")
    lines.append(f"  Categories created       : {stats.categories_created}")
    lines.append(f"  Products processed       : {stats.products_processed}")
    lines.append(f"  Products inserted        : {stats.products_inserted}")
    lines.append(f"  Products updated         : {stats.products_updated}")
    lines.append(f"  Products skipped         : {stats.products_skipped}")
    lines.append(f"  Duplicates removed       : {stats.duplicates_removed}")
    lines.append(f"  Images downloaded        : {stats.images_downloaded}")
    lines.append(f"  Images validated         : {stats.images_validated}")
    lines.append(f"  Images deduped           : {stats.images_deduped}")
    lines.append(f"  Image downloads failed   : {stats.images_failed}")
    lines.append(f"  API calls                : {stats.api_calls}")
    lines.append(f"  API failures             : {stats.api_failures}")
    lines.append("-" * 64)
    lines.append("  Products per category:")
    for cat, count in stats.per_category.items():
        lines.append(f"    - {cat:<22} {count}")
    lines.append("=" * 64)
    out = "\n".join(lines)
    print(out, flush=True)
