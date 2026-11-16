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

    def _get_client_ip(self, request: Request) -> str:
        # Check standard reverse proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Client IP is the first entry in the comma-separated chain
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for CORS preflight, OpenAPI docs, health checks, and static assets
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/healthz", "/readyz"] or request.url.path.startswith("/static"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
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

        current_count = len(self.requests.get(client_ip, []))
        if current_count >= self.max_requests:
            from fastapi.responses import JSONResponse
            from fastapi import status
            retry_after = int(self.window_seconds - (now - self.requests[client_ip][0])) if self.requests.get(client_ip) else self.window_seconds
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + max(1, retry_after))),
                },
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - current_count - 1))
        return response