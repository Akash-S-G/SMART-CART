from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import app.models.products  # noqa: F401
import app.models.user  # noqa: F401
import app.models.payment  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.cart  # noqa: F401
import app.models.order  # noqa: F401

from app.api.products import router as product_router
from app.api.auth import router as auth_router
from app.core.exception_handler import register_exception_handlers
from app.api.carts import router as cart_router
from app.api.orders import router as order_router
from app.api.payments import router as payment_router
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware
from app.core.lifespan import lifespan
from app.api.ai import router as ai_router
from app.api.reviews import router as reviews_router

from fastapi.middleware.cors import CORSMiddleware
from app.core.security_middleware import SecurityHeadersMiddleware
from app.core.config import settings

app = FastAPI(lifespan=lifespan)

# CORS configuration
origins = settings.BACKEND_CORS_ORIGINS or [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# Serve seeded product images locally (backend/static -> /static).
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


register_exception_handlers(app)


app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


from app.api.health import router as health_router

app.include_router(health_router)
app.include_router(ai_router)
app.include_router(payment_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(reviews_router)
app.include_router(product_router)
app.include_router(auth_router)

from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.broadcast({"type": "LIVE_PING", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get('/')
def root():
    return {"message":"success"}
