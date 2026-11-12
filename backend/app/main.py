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

# CORS configuration: configured origins plus local dev defaults.
origins = settings.allowed_origins()
app.add_middleware(SecurityHeadersMiddleware)

# Serve seeded product images locally (backend/static -> /static).
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


register_exception_handlers(app)


app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=60)

# CORS must be the OUTERMOST middleware. Wrapping CORSMiddleware inside
# BaseHTTPMiddleware (SecurityHeaders/Logging/RateLimit) breaks preflight
# handling and ACAO injection, so it is added last (Starlette runs the last
# added middleware first).
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api.health import router as health_router
from app.api.wishlist import router as wishlist_router
from app.api.coupons import router as coupon_router
from app.api.analytics import router as analytics_router
from app.api.addresses import router as addresses_router
from app.api.inventory import router as inventory_router
from app.websocket.router import router as websocket_router

app.include_router(health_router)
app.include_router(wishlist_router)
app.include_router(coupon_router)
app.include_router(analytics_router)
app.include_router(addresses_router)
app.include_router(inventory_router)
app.include_router(ai_router)
app.include_router(payment_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(reviews_router)
app.include_router(product_router)
app.include_router(auth_router)
app.include_router(websocket_router)

@app.get('/')
def root():
    return {"message":"success"}
