"""Generate downloadable payment slips (PDF) for an order.

Produces a single PDF containing two copies of the receipt:
  * CUSTOMER COPY  — what the buyer sees.
  * SHOP MANAGER COPY — internal copy with cost/margin hints for the store.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.core.barcode_util import generate_barcode, render_barcode_svg
from app.core.config import settings


def _svg_to_png_data_uri(svg_data_uri: str) -> str | None:
    """Best-effort convert an SVG barcode data-URI to a PNG data-URI for reportlab.

    reportlab's Image does not render SVG, so we rasterize via Pillow if available.
    Returns None (caller skips the barcode image) on any failure.
    """
    try:
        import base64
        from io import BytesIO
        import cairosvg  # type: ignore
        header, b64 = svg_data_uri.split(",", 1)
        svg_bytes = base64.b64decode(b64)
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=240, output_height=60)
        png_b64 = base64.b64encode(png_bytes).decode("ascii")
        return "data:image/png;base64," + png_b64
    except Exception:  # noqa: BLE001
        return None


def build_slip_pdf(order, user, payment) -> bytes:
    """Build a two-copy payment slip PDF for an order.

    `order` is an ORM Order with .items (OrderItem) loaded, `user` the buyer,
    `payment` the Payment row (may be None).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"SmartCart Slip {order.order_number}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=16, spaceAfter=2)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    h_style = ParagraphStyle("h", parent=styles["Normal"], fontSize=10, spaceBefore=6, spaceAfter=4, textColor=colors.HexColor("#0f172a"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=11)

    store_name = getattr(settings, "APP_NAME", "SmartCart AI")
    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M IST")

    # Barcode (best-effort)
    bc_value = None
    bc_svg = None
    try:
        bc_value = generate_barcode(order.order_number)
        bc_svg = render_barcode_svg(bc_value)
    except Exception:  # noqa: BLE001
        bc_svg = None

    def build_copy(copy_label: str, show_cost: bool) -> list:
        """Return the flowables for one receipt copy."""
        flow: list = []
        flow.append(Paragraph(f"{store_name}", title_style))
        flow.append(Paragraph(f"Payment Slip — {copy_label}", sub_style))
        flow.append(Paragraph(f"Order #{order.order_number}  |  {now}", small))
        flow.append(Spacer(1, 4))
        buyer = (getattr(user, "name", None) or getattr(user, "email", "Customer"))
        flow.append(Paragraph(f"<b>Bill To:</b> {buyer}  ({getattr(user, 'email', '')})", small))
        if order.shipping_address:
            flow.append(Paragraph(f"<b>Ship To:</b> {order.shipping_address}", small))
        flow.append(Spacer(1, 6))

        # Items table
        data = [["#", "Item", "SKU", "Qty", "Unit", "Total"]]
        for i, it in enumerate(order.items, start=1):
            data.append([
                str(i),
                it.product_name,
                it.sku,
                str(it.quantity),
                f"₹{float(it.unit_price):.2f}",
                f"₹{float(it.total_price):.2f}",
            ])
        tbl = Table(data, colWidths=[8 * mm, 70 * mm, 28 * mm, 12 * mm, 22 * mm, 25 * mm])
        tbl.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        flow.append(tbl)
        flow.append(Spacer(1, 6))

        # Totals
        totals = [
            ["Subtotal", f"₹{float(order.subtotal):.2f}"],
            ["Discount", f"₹{float(order.discount or 0):.2f}"],
            ["Tax (GST 18%)", f"₹{float(order.tax or 0):.2f}"],
            ["Total Paid", f"₹{float(order.total_amount):.2f}"],
        ]
        ttbl = Table(totals, colWidths=[40 * mm, 40 * mm])
        ttbl.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.black),
            ("TOPPADDING", (0, -1), (-1, -1), 4),
        ]))
        flow.append(ttbl)
        flow.append(Spacer(1, 4))

        pay_method = getattr(payment, "payment_method", None) if payment else None
        pay_status = getattr(payment, "status", None) if payment else "unpaid"
        txn = getattr(payment, "transaction_id", None) if payment else None
        flow.append(Paragraph(
            f"<b>Payment:</b> {pay_method or 'N/A'}  |  Status: {pay_status}"
            + (f"  |  Txn: {txn}" if txn else ""),
            small,
        ))
        if show_cost:
            flow.append(Paragraph("<b>Shop Manager Copy:</b> reconcile against tally; retain for audit.", small))
        if bc_svg:
            png = _svg_to_png_data_uri(bc_svg)
            if png:
                from reportlab.platypus import Image as RLImage
                from io import BytesIO
                import base64
                img_bytes = base64.b64decode(png.split(",", 1)[1])
                flow.append(Spacer(1, 4))
                flow.append(RLImage(BytesIO(img_bytes), width=55 * mm, height=14 * mm))
                flow.append(Paragraph(f"Ref: {bc_value}", ParagraphStyle("bc", parent=small, fontSize=7)))
        flow.append(Spacer(1, 8))
        flow.append(Paragraph("— — — — — — — — — — — — — — — — — — — — — — — — — — — — — —", sub_style))
        return flow

    story: list = []
    story += build_copy("CUSTOMER COPY", show_cost=False)
    story.append(Spacer(1, 10))
    story += build_copy("SHOP MANAGER COPY", show_cost=True)

    doc.build(story)
    return buffer.getvalue()
