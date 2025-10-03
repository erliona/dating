"""In-memory cache system with TTL and statistics.

Provides a simple in-memory cache for profile recommendations, matches, and settings.
For production use, replace with Redis.
"""

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Cache:
    """In-memory cache with TTL and statistics tracking."""
    
    def __init__(self):
        """Initialize cache with empty storage and stats."""
        self._storage: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._storage:
            self._misses += 1
            return None
        
        value, expiry = self._storage[key]
        
        # Check if expired
        if expiry < time.time():
            del self._storage[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        expiry = time.time() + ttl
        self._storage[key] = (value, expiry)
        logger.debug(f"Cache set: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._storage:
            del self._storage[key]
            logger.debug(f"Cache deleted: {key}")
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys starting with pattern.
        
        Args:
            pattern: Key prefix to match
            
        Returns:
            Number of keys deleted
        """
        keys_to_delete = [k for k in self._storage.keys() if k.startswith(pattern)]
        for key in keys_to_delete:
            del self._storage[key]
        
        if keys_to_delete:
            logger.debug(f"Cache pattern deleted: {pattern}, count: {len(keys_to_delete)}")
        
        return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._storage.clear()
        logger.debug("Cache cleared")
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._storage),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        now = time.time()
        expired_keys = [k for k, (_, expiry) in self._storage.items() if expiry < now]
        
        for key in expired_keys:
            del self._storage[key]
        
        if expired_keys:
            logger.debug(f"Cache cleanup: {len(expired_keys)} expired entries removed")
        
        return len(expired_keys)


# Global cache instance
_cache_instance: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance.
    
    Returns:
        Global Cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance
