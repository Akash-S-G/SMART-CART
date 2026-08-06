"""Duplicate detection across candidate products.

Rejects records that collide on SKU / barcode / (normalised) name either against
pre-existing DB rows or within the current seed batch.  SKU collisions are
resolved by renumbering within the batch; barcode + name collisions are dropped.
"""

from __future__ import annotations

import re

from dataclasses import dataclass, field


def norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


@dataclass
class DedupState:
    db_skus: set[str]
    db_barcodes: set[str]
    seen_skus: set[str] = field(default_factory=set)
    seen_barcodes: set[str] = field(default_factory=set)
    seen_names: set[str] = field(default_factory=set)
    removed: int = 0

    def check(self, sku: str, barcode: str | None, name: str) -> tuple[bool, str | None]:
        """Return (keep, maybe_new_sku).

        On a SKU collision we signal the caller to renumber (the SKU is only a
        display identifier; idempotency is enforced at upsert time via the
        product's natural key — barcode / normalized name).
        """
        nn = norm_name(name)
        # barcode collision -> drop (barcodes must stay unique)
        if barcode:
            if barcode in self.db_barcodes or barcode in self.seen_barcodes:
                self.removed += 1
                return False, None
        # name collision (case-insensitive) -> drop
        if nn in self.seen_names:
            self.removed += 1
            return False, None
        # sku collision -> caller renumbers to keep the SKU column unique.
        # Still record name/barcode so a later identical product in this run
        # is deduped rather than re-inserted under a renumbered SKU.
        if sku in self.db_skus or sku in self.seen_skus:
            self.seen_names.add(nn)
            if barcode:
                self.seen_barcodes.add(barcode)
            return True, None
        self.seen_skus.add(sku)
        if barcode:
            self.seen_barcodes.add(barcode)
        self.seen_names.add(nn)
        return True, sku
