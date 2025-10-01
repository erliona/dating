"""Tests for the caching module."""

from __future__ import annotations

import time

import pytest

from bot.cache import SimpleCache, get_cache, init_cache


class TestSimpleCache:
    """Test suite for SimpleCache."""

    def test_cache_set_and_get(self) -> None:
        """Test basic set and get operations."""
        cache = SimpleCache(default_ttl=300)
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"

    def test_cache_get_nonexistent_key(self) -> None:
        """Test getting a non-existent key returns None."""
        cache = SimpleCache()
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_cache_expiration(self) -> None:
        """Test that cached values expire after TTL."""
        cache = SimpleCache(default_ttl=1)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        result = cache.get("key1")
        assert result is None

    def test_cache_delete(self) -> None:
        """Test deleting a key from cache."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_delete_nonexistent(self) -> None:
        """Test deleting a non-existent key doesn't raise error."""
        cache = SimpleCache()
        
        # Should not raise
        cache.delete("nonexistent")

    def test_cache_delete_pattern(self) -> None:
        """Test deleting keys by pattern."""
        cache = SimpleCache()
        
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("profile:1", "data3")
        
        deleted = cache.delete_pattern("user:")
        
        assert deleted == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("profile:1") == "data3"

    def test_cache_clear(self) -> None:
        """Test clearing all cache entries."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_cleanup_expired(self) -> None:
        """Test cleanup of expired entries."""
        cache = SimpleCache(default_ttl=1)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=10)
        
        # Wait for first key to expire
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_stats(self) -> None:
        """Test cache statistics tracking."""
        cache = SimpleCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3
        assert stats["hit_rate"] == 66.67

    def test_cache_custom_ttl(self) -> None:
        """Test setting custom TTL for specific entries."""
        cache = SimpleCache(default_ttl=10)
        
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2")  # Uses default TTL
        
        time.sleep(1.1)
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_get_cache_singleton(self) -> None:
        """Test that get_cache returns the same instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        assert cache1 is cache2

    def test_init_cache(self) -> None:
        """Test initializing cache with custom TTL."""
        cache = init_cache(ttl=600)
        
        assert cache._default_ttl == 600


class TestCacheIntegration:
    """Integration tests for cache with repositories."""

    @pytest.mark.asyncio
    async def test_profile_cache_integration(self, db_session_factory) -> None:
        """Test that ProfileRepository uses cache correctly."""
        from bot.db import ProfileModel, ProfileRepository
        from bot.main import Profile
        
        # Clear cache
        cache = get_cache()
        cache.clear()
        
        repo = ProfileRepository(db_session_factory)
        
        # Create a profile
        profile = Profile(
            user_id=12345,
            name="Test User",
            age=25,
            gender="male",
            preference="female"
        )
        
        await repo.upsert(profile)
        
        # First get should query DB
        result1 = await repo.get(12345)
        assert result1 is not None
        assert cache.get_stats()["misses"] >= 1
        
        # Second get should use cache
        stats_before = cache.get_stats()
        result2 = await repo.get(12345)
        stats_after = cache.get_stats()
        
        assert result2 is not None
        assert result2.user_id == 12345
        assert stats_after["hits"] > stats_before["hits"]

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, db_session_factory) -> None:
        """Test that cache is invalidated on profile update."""
        from bot.db import ProfileRepository
        from bot.main import Profile
        
        cache = get_cache()
        cache.clear()
        
        repo = ProfileRepository(db_session_factory)
        
        # Create and cache a profile
        profile = Profile(
            user_id=12345,
            name="Original Name",
            age=25,
            gender="male",
            preference="female"
        )
        await repo.upsert(profile)
        await repo.get(12345)  # Cache it
        
        # Update profile
        profile.name = "Updated Name"
        await repo.upsert(profile)
        
        # Cache should be invalidated
        assert cache.get("profile:12345") is None
        
        # New get should return updated data
        result = await repo.get(12345)
        assert result.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, db_session_factory) -> None:
        """Test that cache is invalidated on profile delete."""
        from bot.db import ProfileRepository
        from bot.main import Profile
        
        cache = get_cache()
        cache.clear()
        
        repo = ProfileRepository(db_session_factory)
        
        # Create and cache a profile
        profile = Profile(
            user_id=12345,
            name="Test User",
            age=25,
            gender="male",
            preference="female"
        )
        await repo.upsert(profile)
        await repo.get(12345)  # Cache it
        
        # Delete profile
        await repo.delete(12345)
        
        # Cache should be invalidated
        assert cache.get("profile:12345") is None
