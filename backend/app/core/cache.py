import time
import functools
from typing import Any, Callable

class SimpleTTLCache:
    def __init__(self, default_ttl: int = 60):
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            expire_at, data = self._cache[key]
            if time.time() < expire_at:
                return data
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expire_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = (expire_at, value)

    def invalidate(self, prefix: str = "") -> None:
        if not prefix:
            self._cache.clear()
        else:
            keys_to_del = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_del:
                del self._cache[k]

cache = SimpleTTLCache(default_ttl=60)
