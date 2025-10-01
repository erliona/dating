"""Simple in-memory cache for performance optimization."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""
    
    value: Any
    expires_at: float


class SimpleCache:
    """Simple in-memory cache with TTL support.
    
    This is a basic cache implementation for development and small-scale
    deployments. For production with multiple workers, consider using
    Redis or similar distributed cache.
    """
    
    def __init__(self, default_ttl: int = 300) -> None:
        """Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes).
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found or expired.
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        # Check if expired
        if time.time() > entry.expires_at:
            self._misses += 1
            del self._cache[key]
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (uses default if not specified).
        """
        if ttl is None:
            ttl = self._default_ttl
        
        expires_at = time.time() + ttl
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key to delete.
        """
        self._cache.pop(key, None)
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (simple prefix match).
        
        Args:
            pattern: Key prefix to match.
            
        Returns:
            Number of keys deleted.
        """
        keys_to_delete = [key for key in self._cache if key.startswith(pattern)]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats.
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }


# Global cache instance
_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Get the global cache instance.
    
    Returns:
        Global SimpleCache instance.
    """
    global _cache
    if _cache is None:
        _cache = SimpleCache()
    return _cache


def init_cache(ttl: int = 300) -> SimpleCache:
    """Initialize the global cache instance.
    
    Args:
        ttl: Default TTL in seconds.
        
    Returns:
        Initialized SimpleCache instance.
    """
    global _cache
    _cache = SimpleCache(default_ttl=ttl)
    LOGGER.info("Cache initialized with TTL=%d seconds", ttl)
    return _cache
