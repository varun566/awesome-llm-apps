"""
Tests for TTLCache (utils/cache.py)
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.cache import TTLCache


def test_basic_set_get():
    cache = TTLCache(max_size=10, default_ttl=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_miss_returns_none():
    cache = TTLCache()
    assert cache.get("nonexistent") is None


def test_ttl_expiry():
    cache = TTLCache(default_ttl=1)
    cache.set("key", "val", ttl=1)
    assert cache.get("key") == "val"
    time.sleep(1.1)
    assert cache.get("key") is None


def test_lru_eviction():
    cache = TTLCache(max_size=3, default_ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    # Access 'a' to make it recently used
    cache.get("a")
    # Add 'd' — 'b' should be evicted (LRU)
    cache.set("d", 4)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_hit_rate():
    cache = TTLCache()
    cache.set("k", "v")
    cache.get("k")       # hit
    cache.get("k")       # hit
    cache.get("miss")    # miss
    assert cache.hits == 2
    assert cache.misses == 1
    assert abs(cache.hit_rate - 2 / 3) < 0.01


def test_delete():
    cache = TTLCache()
    cache.set("key", "val")
    assert cache.delete("key") is True
    assert cache.get("key") is None
    assert cache.delete("key") is False


def test_clear():
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.size == 0
    assert cache.hits == 0
    assert cache.misses == 0


def test_purge_expired():
    cache = TTLCache(default_ttl=1)
    cache.set("x", "y", ttl=1)
    cache.set("z", "w", ttl=60)
    time.sleep(1.1)
    purged = cache.purge_expired()
    assert purged == 1
    assert cache.get("z") == "w"


def test_stats_structure():
    cache = TTLCache(max_size=50)
    stats = cache.stats()
    assert "size" in stats
    assert "max_size" in stats
    assert stats["max_size"] == 50


def test_overwrite_existing_key():
    cache = TTLCache()
    cache.set("key", "old")
    cache.set("key", "new")
    assert cache.get("key") == "new"


if __name__ == "__main__":
    test_basic_set_get()
    test_miss_returns_none()
    test_ttl_expiry()
    test_lru_eviction()
    test_hit_rate()
    test_delete()
    test_clear()
    test_purge_expired()
    test_stats_structure()
    test_overwrite_existing_key()
    print("All cache tests passed ✅")
