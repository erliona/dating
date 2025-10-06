"""Tests for cache system."""

import time

import pytest

pytestmark = pytest.mark.unit


from bot.cache import Cache, get_cache


class TestCache:
    """Test cache operations."""

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = Cache()

        cache.set("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = Cache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test that values expire after TTL."""
        cache = Cache()

        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_delete(self):
        """Test deleting values."""
        cache = Cache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_pattern(self):
        """Test deleting keys by pattern."""
        cache = Cache()

        cache.set("user:1:profile", "data1")
        cache.set("user:2:profile", "data2")
        cache.set("match:1", "data3")

        deleted = cache.delete_pattern("user:")
        assert deleted == 2
        assert cache.get("user:1:profile") is None
        assert cache.get("user:2:profile") is None
        assert cache.get("match:1") == "data3"

    def test_clear(self):
        """Test clearing all cache entries."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_get_stats(self):
        """Test cache statistics."""
        cache = Cache()

        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 66.67

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = Cache()

        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=60)

        time.sleep(1.1)

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_complex_values(self):
        """Test caching complex values."""
        cache = Cache()

        data = {"profiles": [{"id": 1, "name": "Test"}], "cursor": 123}

        cache.set("discovery", data)
        assert cache.get("discovery") == data


class TestGetCache:
    """Test global cache instance."""

    def test_get_cache_returns_same_instance(self):
        """Test that get_cache returns the same instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    def test_get_cache_persistent_data(self):
        """Test that data persists across get_cache calls."""
        cache1 = get_cache()
        cache1.set("test_key", "test_value")

        cache2 = get_cache()
        assert cache2.get("test_key") == "test_value"
