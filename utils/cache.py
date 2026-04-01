"""
Caching system for Internet Research Assistant
"""
import asyncio
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import sqlite3
from config.settings import settings
from utils.logger import logger

class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        pass

class MemoryCache(CacheBackend):
    """In-memory cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires_at'] is None or datetime.utcnow() < entry['expires_at']:
                entry['hit_count'] += 1
                self.hits += 1
                logger.debug(f"Cache hit for key: {key}")
                return entry['value']
            else:
                del self.cache[key]
                logger.debug(f"Cache entry expired for key: {key}")
        
        self.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if len(self.cache) >= self.max_size:
            # Simple eviction: remove oldest entry
            oldest_key = min(self.cache.keys(), 
                            key=lambda k: self.cache[k]['created_at'])
            del self.cache[oldest_key]
            logger.debug(f"Evicted cache entry: {oldest_key}")
        
        self.cache[key] = {
            'value': value,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
            'hit_count': 0
        }
        logger.debug(f"Cache set for key: {key} with TTL: {ttl}")
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        self.cache.clear()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': len(self.cache),
            'max_size': self.max_size
        }

class SQLiteCache(CacheBackend):
    """SQLite-based persistent cache"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._init_db()
        self.hits = 0
        self.misses = 0
    
    def _init_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    async def get(self, key: str) -> Optional[Any]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT value, expires_at FROM cache 
            WHERE key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
        ''', (key,))
        
        result = c.fetchone()
        
        if result:
            c.execute('UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?', (key,))
            conn.commit()
            self.hits += 1
            conn.close()
            return json.loads(result[0])
        
        self.misses += 1
        conn.close()
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        expires_at = None
        if ttl:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        
        c.execute('''
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, ?)
        ''', (key, json.dumps(value), expires_at))
        
        conn.commit()
        conn.close()
        return True
    
    async def delete(self, key: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM cache WHERE key = ?', (key,))
        conn.commit()
        conn.close()
        return True
    
    async def clear(self) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM cache')
        conn.commit()
        conn.close()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM cache')
        size = c.fetchone()[0]
        conn.close()
        
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'size': size
        }

def get_cache() -> CacheBackend:
    """Factory function to get appropriate cache backend""" 
    if settings.CACHE_TYPE == "memory":
        return MemoryCache(max_size=settings.CACHE_MAX_SIZE)
    elif settings.CACHE_TYPE == "sqlite":
        return SQLiteCache()
    else:
        logger.warning("Unsupported cache type, using memory cache")
        return MemoryCache(max_size=settings.CACHE_MAX_SIZE)
