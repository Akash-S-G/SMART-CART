import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        request_id = str(uuid.uuid4())

        start = time.perf_counter()

        response = await call_next(request)

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "%s %s %.2f ms",
            request.method,
            request.url.path,
            elapsed,
        )

        response.headers["X-Request-ID"] = request_id

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        from collections import defaultdict
        self.requests = defaultdict(list)
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/healthz", "/readyz"] or request.url.path.startswith("/static"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Periodic cleanup every 5 minutes to remove stale IPs
        if now - self.last_cleanup > 300:
            stale_ips = [
                ip for ip, timestamps in self.requests.items()
                if not timestamps or now - timestamps[-1] > self.window_seconds
            ]
            for ip in stale_ips:
                del self.requests[ip]
            self.last_cleanup = now

        # Clean old timestamps for active IP
        timestamps = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]
        if timestamps:
            self.requests[client_ip] = timestamps
        elif client_ip in self.requests:
            del self.requests[client_ip]

        if len(self.requests.get(client_ip, [])) >= self.max_requests:
            from fastapi.responses import JSONResponse
            from fastapi import status
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)