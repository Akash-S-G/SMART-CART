"""Barcode generation helpers.

Generates retail-style barcodes (EAN-13 when possible, otherwise Code128) and
returns an SVG data-URI so the frontend can preview/print without extra deps.
"""
from __future__ import annotations

import io
import random
from datetime import datetime, timezone

from barcode import EAN13, Code128
from barcode.writer import SVGWriter


def _ean13_check_digit(base12: str) -> str:
    """Compute the EAN-13 check digit for a 12-digit base."""
    total = 0
    for i, ch in enumerate(base12):
        total += int(ch) * (1 if i % 2 == 0 else 3)
    return str((10 - (total % 10)) % 10)


def generate_barcode(existing: str | None = None) -> str:
    """Return a valid barcode string (EAN-13 preferred).

    If an existing EAN-13/12-digit value is supplied and valid, it is reused.
    Otherwise a fresh India-retail-style EAN-13 is minted.
    """
    if existing:
        digits = "".join(ch for ch in existing if ch.isdigit())
        if len(digits) == 13 and digits.isdigit():
            base = digits[:12]
            if _ean13_check_digit(base) == digits[12]:
                return digits
        if len(digits) == 12 and digits.isdigit():
            return digits + _ean13_check_digit(digits)

    # Mint a new EAN-13: 890 = India GS1 prefix, then random + check digit.
    base = "890" + "".join(random.choice("0123456789") for _ in range(9))
    return base + _ean13_check_digit(base)


def render_barcode_svg(barcode_value: str) -> str:
    """Render a barcode to an SVG data-URI."""
    digits = "".join(ch for ch in barcode_value if ch.isdigit())
    writer = SVGWriter()
    if len(digits) == 12:
        digits = digits + _ean13_check_digit(digits)
    if len(digits) == 13:
        rv = EAN13(digits, writer=writer)
    else:
        rv = Code128(barcode_value, writer=writer)
    buffer = io.BytesIO()
    rv.write(buffer)
    svg = buffer.getvalue().decode("utf-8")
    encoded = svg.encode("utf-8")
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(encoded).decode("ascii")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
