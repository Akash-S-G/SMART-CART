from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger("smartcart.ws")

PUBLIC_TOPIC = "public"
HEARTBEAT_INTERVAL = 25.0
CLIENT_TIMEOUT = 75.0
SEND_TIMEOUT = 10.0
OUTBOX_MAXSIZE = 200
SLOW_CLIENT_CLOSE_CODE = 1013


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Client:
    websocket: WebSocket
    user_id: str | None
    role: str
    topics: set[str] = field(default_factory=set)
    outbox: asyncio.Queue[dict[str, Any]] = field(
        default_factory=lambda: asyncio.Queue(maxsize=OUTBOX_MAXSIZE)
    )
    last_seen: float = field(default_factory=time.monotonic)
    expires_at: float | None = None
    sender_task: asyncio.Task[None] | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def can_access(self, topic: str) -> bool:
        if topic == PUBLIC_TOPIC:
            return True
        if topic.startswith("user:"):
            return self.user_id is not None and topic == f"user:{self.user_id}"
        if topic in {"admin", "inventory", "orders"}:
            return self.is_admin
        return False


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: dict[WebSocket, Client] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._closed = False

    @property
    def connection_count(self) -> int:
        return len(self._clients)

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._closed = False
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(), name="ws-heartbeat"
            )

    async def stop(self) -> None:
        self._closed = True
        task = self._heartbeat_task
        self._heartbeat_task = None
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        clients = list(self._clients)
        if clients:
            await asyncio.gather(
                *(self.disconnect(ws, code=1001, reason="server shutdown") for ws in clients),
                return_exceptions=True,
            )
        self._loop = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str | None = None,
        role: str = "anonymous",
        subprotocol: str | None = None,
        expires_at: float | None = None,
    ) -> Client:
        await websocket.accept(subprotocol=subprotocol)
        client = Client(
            websocket=websocket,
            user_id=user_id,
            role=role,
            expires_at=expires_at,
        )
        client.topics.add(PUBLIC_TOPIC)
        if user_id is not None:
            client.topics.add(f"user:{user_id}")
        if role == "admin":
            client.topics.add("admin")
        self._clients[websocket] = client
        client.sender_task = asyncio.create_task(
            self._sender_loop(client), name=f"ws-sender-{id(client)}"
        )
        self._enqueue(
            client,
            {
                "type": "CONNECTED",
                "data": {
                    "user_id": user_id,
                    "role": role,
                    "topics": sorted(client.topics),
                },
                "ts": _now(),
            },
        )
        logger.info(
            "ws connected user=%s role=%s connections=%d",
            user_id,
            role,
            self.connection_count,
        )
        return client

    async def disconnect(
        self,
        websocket: WebSocket,
        code: int = 1000,
        reason: str = "",
    ) -> None:
        client = self._clients.pop(websocket, None)
        if client is None:
            return
        try:
            await websocket.close(code=code, reason=reason)
        except Exception:
            pass
        task = client.sender_task
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        logger.info(
            "ws disconnected user=%s role=%s code=%s connections=%d",
            client.user_id,
            client.role,
            code,
            self.connection_count,
        )

    def touch(self, websocket: WebSocket) -> None:
        client = self._clients.get(websocket)
        if client is not None:
            client.last_seen = time.monotonic()

    def subscribe(self, websocket: WebSocket, topics: list[str]) -> tuple[list[str], list[str]]:
        client = self._clients.get(websocket)
        if client is None:
            return [], list(topics)
        accepted: list[str] = []
        denied: list[str] = []
        for topic in topics:
            if not client.can_access(topic):
                denied.append(topic)
                continue
            client.topics.add(topic)
            if topic not in accepted:
                accepted.append(topic)
        return accepted, denied

    def unsubscribe(self, websocket: WebSocket, topics: list[str]) -> list[str]:
        client = self._clients.get(websocket)
        if client is None:
            return []
        removed: list[str] = []
        for topic in topics:
            if topic == PUBLIC_TOPIC or topic.startswith("user:"):
                continue
            if topic in client.topics:
                client.topics.discard(topic)
                removed.append(topic)
        return removed

    async def broadcast(
        self,
        event_type: str,
        data: Any = None,
        topic: str = PUBLIC_TOPIC,
        exclude: set[WebSocket] | None = None,
    ) -> None:
        message = {"type": event_type, "topic": topic, "data": data, "ts": _now()}
        for client in tuple(self._clients.values()):
            if topic not in client.topics:
                continue
            if exclude is not None and client.websocket in exclude:
                continue
            self._enqueue(client, message)

    async def send(self, websocket: WebSocket, message: dict[str, Any]) -> bool:
        client = self._clients.get(websocket)
        if client is None:
            return False
        return self._enqueue(client, message)

    def publish(self, event_type: str, data: Any = None, topic: str = PUBLIC_TOPIC) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self._loop
            if loop is None or loop.is_closed():
                return
            try:
                asyncio.run_coroutine_threadsafe(
                    self.broadcast(event_type, data, topic), loop
                )
            except RuntimeError:
                logger.debug("ws publish skipped: loop unavailable")
        else:
            loop.create_task(self.broadcast(event_type, data, topic))

    def _enqueue(self, client: Client, message: dict[str, Any]) -> bool:
        task = client.sender_task
        if task is None or task.done():
            return False
        try:
            client.outbox.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning(
                "ws outbox full, dropping slow client user=%s", client.user_id
            )
            self._spawn(
                self.disconnect(
                    client.websocket,
                    code=SLOW_CLIENT_CLOSE_CODE,
                    reason="slow consumer",
                )
            )
            return False

    def _spawn(self, coro: Any) -> None:
        task = asyncio.create_task(coro)
        task.add_done_callback(self._log_task_error)

    @staticmethod
    def _log_task_error(task: asyncio.Task[Any]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.warning("ws background task failed: %s", exc)

    async def _sender_loop(self, client: Client) -> None:
        websocket = client.websocket
        try:
            while True:
                message = await client.outbox.get()
                await asyncio.wait_for(
                    websocket.send_json(message), timeout=SEND_TIMEOUT
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("ws sender stopped user=%s: %s", client.user_id, exc)
        finally:
            if self._clients.get(websocket) is client:
                self._clients.pop(websocket, None)
            client.sender_task = None
            try:
                await websocket.close(code=1011, reason="connection lost")
            except Exception:
                pass

    async def _heartbeat_loop(self) -> None:
        while not self._closed:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = time.monotonic()
            epoch = time.time()
            stale: list[WebSocket] = []
            expired: list[WebSocket] = []
            for client in tuple(self._clients.values()):
                if client.expires_at is not None and epoch >= client.expires_at:
                    expired.append(client.websocket)
                    continue
                if now - client.last_seen > CLIENT_TIMEOUT:
                    stale.append(client.websocket)
                    continue
                self._enqueue(
                    client,
                    {"type": "PING", "data": None, "ts": _now()},
                )
            if expired:
                await asyncio.gather(
                    *(
                        self.disconnect(ws, code=4401, reason="token expired")
                        for ws in expired
                    ),
                    return_exceptions=True,
                )
            if stale:
                await asyncio.gather(
                    *(
                        self.disconnect(ws, code=1001, reason="heartbeat timeout")
                        for ws in stale
                    ),
                    return_exceptions=True,
                )


ws_manager = ConnectionManager()
