from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any

from anyio import to_thread
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.jwt import jwt_manager
from app.core.config import settings
from app.db.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.websocket.manager import ws_manager

logger = logging.getLogger("smartcart.ws")

router = APIRouter(tags=["Realtime"])

MAX_MESSAGE_BYTES = 8192
MAX_TOPICS_PER_MESSAGE = 32
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 10.0

IDENTITY_CACHE_TTL = 60.0
_identity_cache: dict[str, tuple[float, tuple[str, str] | None]] = {}
_BEARER_PROTOCOL_PREFIX = "bearer."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error(message: str) -> dict[str, Any]:
    return {"type": "ERROR", "data": {"message": message}, "ts": _now()}


def _topics(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("topics")
    if not isinstance(raw, list):
        return []
    topics: list[str] = []
    for item in raw[:MAX_TOPICS_PER_MESSAGE]:
        if isinstance(item, str) and item and len(item) <= 64 and item not in topics:
            topics.append(item)
    return topics


def _extract_bearer_subprotocol(websocket: WebSocket) -> tuple[str | None, str | None]:
    header = websocket.headers.get("sec-websocket-protocol", "")
    for protocol in header.split(","):
        candidate = protocol.strip()
        if candidate.startswith(_BEARER_PROTOCOL_PREFIX):
            token = candidate[len(_BEARER_PROTOCOL_PREFIX):].strip()
            if token:
                return candidate, token
    return None, None


def _load_identity(user_id: str) -> tuple[str, str] | None:
    db = SessionLocal()
    try:
        user = UserRepository(db).get_active_user(user_id)
        if user is None:
            return None
        return str(user.id), user.role
    finally:
        db.close()


async def _resolve_identity(token: str) -> tuple[str, str, float | None] | None:
    try:
        payload = jwt_manager.verify_token(token)
    except Exception:
        return None
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        return None
    exp = payload.get("exp")
    expires_at = float(exp) if isinstance(exp, (int, float)) else None

    now = asyncio.get_running_loop().time()
    cached = _identity_cache.get(user_id)
    if cached is not None and now - cached[0] < IDENTITY_CACHE_TTL:
        identity = cached[1]
    else:
        try:
            identity = await to_thread.run_sync(_load_identity, user_id)
        except Exception as exc:
            logger.warning("ws identity lookup failed: %s", exc)
            return None
        _identity_cache[user_id] = (now, identity)

    if identity is None:
        return None
    return identity[0], identity[1], expires_at


async def _handle_message(websocket: WebSocket, raw: str) -> None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        await ws_manager.send(websocket, _error("invalid json payload"))
        return
    if not isinstance(payload, dict):
        await ws_manager.send(websocket, _error("payload must be an object"))
        return

    kind = payload.get("type")
    if kind == "ping":
        await ws_manager.send(websocket, {"type": "PONG", "data": None, "ts": _now()})
        return
    if kind == "pong":
        return
    if kind == "subscribe":
        accepted, denied = ws_manager.subscribe(websocket, _topics(payload))
        await ws_manager.send(
            websocket,
            {
                "type": "SUBSCRIBED",
                "data": {"topics": accepted, "denied": denied},
                "ts": _now(),
            },
        )
        return
    if kind == "unsubscribe":
        removed = ws_manager.unsubscribe(websocket, _topics(payload))
        await ws_manager.send(
            websocket,
            {
                "type": "UNSUBSCRIBED",
                "data": {"topics": removed},
                "ts": _now(),
            },
        )
        return
    await ws_manager.send(websocket, _error(f"unsupported message type: {kind!r}"))


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_origins():
        await websocket.accept()
        await websocket.close(code=4403, reason="origin not allowed")
        return

    subprotocol, header_token = _extract_bearer_subprotocol(websocket)
    token = token or header_token

    if token:
        identity = await _resolve_identity(token)
        if identity is None:
            await websocket.accept()
            await websocket.close(code=4401, reason="invalid or expired token")
            return
        user_id, role, expires_at = identity
    else:
        user_id, role, expires_at = None, "anonymous", None

    await ws_manager.connect(
        websocket,
        user_id=user_id,
        role=role,
        subprotocol=subprotocol,
        expires_at=expires_at,
    )
    window: deque[float] = deque()
    loop = asyncio.get_running_loop()
    try:
        while True:
            raw = await websocket.receive_text()
            ws_manager.touch(websocket)

            now = loop.time()
            while window and now - window[0] > RATE_LIMIT_WINDOW:
                window.popleft()
            if len(window) >= RATE_LIMIT_MAX:
                await ws_manager.disconnect(
                    websocket, code=1008, reason="rate limit exceeded"
                )
                break
            window.append(now)

            if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
                await ws_manager.send(websocket, _error("message too large"))
                continue

            await _handle_message(websocket, raw)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("ws receive loop stopped: %s", exc)
    finally:
        await ws_manager.disconnect(websocket)
