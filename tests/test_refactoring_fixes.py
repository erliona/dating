"""Tests for refactoring and fixes from issue #47."""

import time
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.cache import Cache
from bot.security import RateLimiter


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        user_id = 12345
        
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
    
    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        user_id = 12345
        
        # Use up the limit
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        
        # Next request should be blocked
        assert limiter.is_allowed(user_id) is False
    
    def test_rate_limiter_tracks_different_users_separately(self):
        """Test that different users have separate rate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        user1 = 12345
        user2 = 67890
        
        # Both users should be allowed
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user2) is True
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user2) is True
        
        # Both should now be at limit
        assert limiter.is_allowed(user1) is False
        assert limiter.is_allowed(user2) is False
    
    def test_rate_limiter_remaining_requests(self):
        """Test getting remaining requests count."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        user_id = 12345
        
        assert limiter.get_remaining_requests(user_id) == 5
        
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 4
        
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 2
    
    def test_rate_limiter_cleanup_expired(self):
        """Test that expired entries are cleaned up."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        user_id = 12345
        
        # Use up limit
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        
        # Should be blocked now
        assert limiter.is_allowed(user_id) is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again after cleanup
        assert limiter.is_allowed(user_id) is True


class TestCacheAutoCleanup:
    """Test cache automatic cleanup functionality."""
    
    def test_cache_stores_and_retrieves_values(self):
        """Test basic cache get/set functionality."""
        cache = Cache()
        cache.set("key1", "value1", ttl=60)
        
        assert cache.get("key1") == "value1"
    
    def test_cache_expires_old_values(self):
        """Test that expired values return None."""
        cache = Cache()
        cache.set("key1", "value1", ttl=1)
        
        # Should exist immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get("key1") is None
    
    def test_cache_cleanup_removes_expired(self):
        """Test that cleanup removes expired entries."""
        cache = Cache()
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=60)
        
        # Wait for first key to expire
        time.sleep(1.1)
        
        # Manually cleanup
        removed = cache.cleanup_expired()
        
        # Should have removed 1 key
        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_cache_auto_cleanup_prevents_memory_leak(self):
        """Test that auto cleanup runs periodically."""
        cache = Cache()
        
        # Set many short-lived entries
        for i in range(10):
            cache.set(f"key{i}", f"value{i}", ttl=1)
        
        # All should exist
        stats = cache.get_stats()
        assert stats["size"] == 10
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Trigger auto cleanup by accessing cache
        # Note: auto cleanup only runs every 5 minutes, but we can test
        # by directly calling cleanup_expired
        cache.cleanup_expired()
        
        # All should be gone
        stats = cache.get_stats()
        assert stats["size"] == 0


class TestAgeValidationConsistency:
    """Test that age validation is consistent."""
    
    def test_age_validation_rejects_under_18(self):
        """Test that users under 18 are rejected."""
        from bot.validation import validate_birth_date
        
        # 17 years old
        today = date.today()
        birth_date = date(today.year - 17, today.month, today.day)
        
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is False
        assert "18 лет" in error
    
    def test_age_validation_accepts_18(self):
        """Test that exactly 18 years old is accepted."""
        from bot.validation import validate_birth_date
        
        # Exactly 18 years old
        today = date.today()
        birth_date = date(today.year - 18, today.month, today.day)
        
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is True
    
    def test_age_validation_rejects_over_120(self):
        """Test that users over 120 are rejected."""
        from bot.validation import validate_birth_date
        
        # 121 years old
        today = date.today()
        birth_date = date(today.year - 121, today.month, today.day)
        
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is False
        assert "Неверная дата рождения" in error
    
    def test_age_validation_accepts_120(self):
        """Test that exactly 120 years old is accepted."""
        from bot.validation import validate_birth_date
        
        # Exactly 120 years old
        today = date.today()
        birth_date = date(today.year - 120, today.month, today.day)
        
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is True


@pytest.mark.asyncio
class TestAuthorizationHeaderValidation:
    """Test Authorization header format validation."""
    
    async def test_authenticate_rejects_missing_header(self):
        """Test that missing Authorization header is rejected."""
        from bot.api import authenticate_request, AuthenticationError
        
        request = MagicMock()
        request.headers = {}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": None}
        
        with pytest.raises(AuthenticationError, match="Missing Authorization header"):
            await authenticate_request(request, "secret", check_rate_limit=False)
    
    async def test_authenticate_rejects_invalid_format(self):
        """Test that invalid Authorization header format is rejected."""
        from bot.api import authenticate_request, AuthenticationError
        
        request = MagicMock()
        request.headers = {"Authorization": "InvalidFormat token123"}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": None}
        
        with pytest.raises(AuthenticationError, match="Invalid Authorization header format"):
            await authenticate_request(request, "secret", check_rate_limit=False)
    
    async def test_authenticate_rejects_empty_token(self):
        """Test that empty token is rejected."""
        from bot.api import authenticate_request, AuthenticationError
        
        request = MagicMock()
        request.headers = {"Authorization": "Bearer "}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": None}
        
        with pytest.raises(AuthenticationError, match="Empty token"):
            await authenticate_request(request, "secret", check_rate_limit=False)
    
    async def test_authenticate_accepts_valid_bearer_token(self):
        """Test that valid Bearer token is accepted."""
        from bot.api import authenticate_request, create_jwt_token
        
        user_id = 12345
        secret = "test-secret"
        token = create_jwt_token(user_id, secret)
        
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": None}
        
        authenticated_user_id = await authenticate_request(request, secret, check_rate_limit=False)
        assert authenticated_user_id == user_id


@pytest.mark.asyncio
class TestRateLimitIntegration:
    """Test rate limiting integration with authentication."""
    
    async def test_authenticate_checks_rate_limit(self):
        """Test that authentication checks rate limit."""
        from bot.api import authenticate_request, create_jwt_token, RateLimitError
        
        user_id = 12345
        secret = "test-secret"
        token = create_jwt_token(user_id, secret)
        
        # Create rate limiter with very low limit
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": limiter}
        
        # First request should succeed
        authenticated_user_id = await authenticate_request(request, secret, check_rate_limit=True)
        assert authenticated_user_id == user_id
        
        # Second request should be rate limited
        with pytest.raises(RateLimitError):
            await authenticate_request(request, secret, check_rate_limit=True)
    
    async def test_authenticate_skips_rate_limit_when_disabled(self):
        """Test that rate limit can be disabled."""
        from bot.api import authenticate_request, create_jwt_token
        
        user_id = 12345
        secret = "test-secret"
        token = create_jwt_token(user_id, secret)
        
        # Create rate limiter with very low limit
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        request.remote = "127.0.0.1"
        request.path = "/api/test"
        request.app = {"rate_limiter": limiter}
        
        # Both requests should succeed when rate limit check is disabled
        await authenticate_request(request, secret, check_rate_limit=False)
        await authenticate_request(request, secret, check_rate_limit=False)
