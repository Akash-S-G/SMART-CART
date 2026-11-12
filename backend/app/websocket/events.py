from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.websocket.manager import ws_manager


def _money(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _status(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def emit_inventory_updated(
    *,
    product_id: str,
    sku: str | None,
    quantity: int,
    status: str,
    reorder_level: int | None,
    actor_id: str | None = None,
    transaction_type: str | None = None,
) -> None:
    data = {
        "product_id": str(product_id),
        "sku": sku,
        "quantity": quantity,
        "status": status,
        "reorder_level": reorder_level,
        "actor_id": str(actor_id) if actor_id else None,
        "transaction_type": transaction_type,
    }
    ws_manager.publish("INVENTORY_UPDATED", data, topic="inventory")
    ws_manager.publish("INVENTORY_UPDATED", data, topic="admin")


def emit_order_event(
    event_type: str,
    *,
    order_id: str,
    order_number: str | None,
    user_id: str,
    status: Any,
    total_amount: Any = None,
) -> None:
    data = {
        "order_id": str(order_id),
        "order_number": order_number,
        "user_id": str(user_id),
        "status": _status(status),
        "total_amount": _money(total_amount),
    }
    ws_manager.publish(event_type, data, topic=f"user:{user_id}")
    ws_manager.publish(event_type, data, topic="admin")


def emit_payment_verified(
    *,
    payment_id: str,
    order_id: str,
    user_id: str,
    transaction_id: str,
    amount: Any,
    status: Any,
) -> None:
    data = {
        "payment_id": str(payment_id),
        "order_id": str(order_id),
        "user_id": str(user_id),
        "transaction_id": transaction_id,
        "amount": _money(amount),
        "status": _status(status),
    }
    ws_manager.publish("PAYMENT_VERIFIED", data, topic=f"user:{user_id}")
    ws_manager.publish("PAYMENT_VERIFIED", data, topic="admin")
