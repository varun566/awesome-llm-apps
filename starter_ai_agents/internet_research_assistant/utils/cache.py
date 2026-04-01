import threading
import time
from collections import OrderedDict
from typing import Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TTLCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _is_expired(self, entry: dict) -> bool:
        return time.time() > entry["expires_at"]

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                self.misses += 1
                logger.debug(f"Cache miss (expired): {key[:50]}")
                return None
            self._cache.move_to_end(key)
            entry["hits"] += 1
            self.hits += 1
            logger.debug(f"Cache hit: {key[:50]}")
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time(),
                "hits": 0,
            }
            while len(self._cache) > self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Cache eviction (LRU): {evicted_key[:50]}")

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def purge_expired(self) -> int:
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if self._is_expired(v)]
            for k in expired_keys:
                del self._cache[k]
            return len(expired_keys)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.hit_rate,
            }
