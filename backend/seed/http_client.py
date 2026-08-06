"""Resilient HTTP client with retries + polite rate limiting."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass

import config as cfg


@dataclass
class HttpResponse:
    ok: bool
    status: int
    body: bytes
    error: str | None = None


class HttpClient:
    """Thin wrapper around urllib with retries and a polite delay."""

    def __init__(
        self,
        user_agent: str = cfg.USER_AGENT,
        timeout: int = cfg.REQUEST_TIMEOUT,
        delay: float = cfg.REQUEST_DELAY,
        max_retries: int = cfg.MAX_RETRIES,
    ):
        self.ua = user_agent
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries

    def _rate_limit(self) -> None:
        if self.delay > 0:
            time.sleep(self.delay)

    def get_bytes(self, url: str, *, binary: bool = True) -> HttpResponse:
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            self._rate_limit()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.ua})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = resp.read()
                return HttpResponse(ok=True, status=resp.status, body=data)
            except urllib.error.HTTPError as e:
                # 4xx won't improve on retry
                if 400 <= e.code < 500:
                    return HttpResponse(ok=False, status=e.code, body=b"",
                                         error=f"HTTP {e.code}")
                last_err = f"HTTP {e.code}"
            except Exception as e:  # noqa: BLE001
                last_err = str(e) or type(e).__name__
            time.sleep(min(2 ** attempt, 8))
        return HttpResponse(ok=False, status=0, body=b"", error=last_err)

    def get_json(self, url: str) -> tuple[dict | None, HttpResponse]:
        resp = self.get_bytes(url)
        if not resp.ok:
            return None, resp
        try:
            import json
            return json.loads(resp.body), resp
        except Exception as e:  # noqa: BLE001
            return None, HttpResponse(ok=False, status=resp.status, body=b"",
                                       error=f"JSON parse: {e}")
