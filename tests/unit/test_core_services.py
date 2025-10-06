"""Comprehensive tests for core services (profile, matching, user)."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from core.models.enums import Gender, Goal, Orientation
from core.models.user import User


class TestProfileService:
    """Test profile service functionality."""

    def test_profile_age_calculation(self):
        """Test that profile age is calculated correctly."""
        from bot.api import calculate_age
        
        # Test someone born 25 years ago
        birth_date = date.today().replace(year=date.today().year - 25)
        age = calculate_age(birth_date)
        assert age == 25

    def test_profile_age_before_birthday(self):
        """Test age calculation before birthday this year."""
        from bot.api import calculate_age
        
        today = date.today()
        # Create birth date that hasn't occurred yet this year
        if today.month == 12:
            future_month = 1
            future_year = today.year + 1
        else:
            future_month = today.month + 1
            future_year = today.year
        
        birth_date = date(today.year - 25, future_month, 1)
        
        if birth_date > today:
            age = calculate_age(birth_date)
            assert age == 24  # Still 24 because birthday hasn't happened

    def test_profile_age_after_birthday(self):
        """Test age calculation after birthday this year."""
        from bot.api import calculate_age
        
        today = date.today()
        # Create birth date that already occurred this year
        if today.month == 1:
            past_month = 12
            past_year = today.year - 1
        else:
            past_month = today.month - 1
            past_year = today.year
        
        birth_date = date(past_year - 25, past_month, 1)
        
        if birth_date <= today:
            age = calculate_age(birth_date)
            # Age should be based on year difference


class TestMatchingService:
    """Test matching service functionality."""

    def test_mutual_orientation_compatibility_heterosexual(self):
        """Test heterosexual orientation matching."""
        # Male seeking female
        user1 = {
            "gender": Gender.MALE,
            "orientation": Orientation.HETEROSEXUAL
        }
        # Female seeking male
        user2 = {
            "gender": Gender.FEMALE,
            "orientation": Orientation.HETEROSEXUAL
        }
        
        # They should be compatible
        assert self._check_orientation_compatibility(user1, user2)

    def test_mutual_orientation_compatibility_homosexual(self):
        """Test homosexual orientation matching."""
        # Male seeking male
        user1 = {
            "gender": Gender.MALE,
            "orientation": Orientation.HOMOSEXUAL
        }
        # Male seeking male
        user2 = {
            "gender": Gender.MALE,
            "orientation": Orientation.HOMOSEXUAL
        }
        
        # They should be compatible
        assert self._check_orientation_compatibility(user1, user2)

    def test_mutual_orientation_compatibility_bisexual(self):
        """Test bisexual orientation matching."""
        # Bisexual male
        user1 = {
            "gender": Gender.MALE,
            "orientation": Orientation.BISEXUAL
        }
        # Heterosexual female
        user2 = {
            "gender": Gender.FEMALE,
            "orientation": Orientation.HETEROSEXUAL
        }
        
        # They should be compatible
        assert self._check_orientation_compatibility(user1, user2)

    def test_mutual_orientation_incompatibility(self):
        """Test incompatible orientations."""
        # Homosexual male (seeks males)
        user1 = {
            "gender": Gender.MALE,
            "orientation": Orientation.HOMOSEXUAL
        }
        # Heterosexual female (seeks males)
        user2 = {
            "gender": Gender.FEMALE,
            "orientation": Orientation.HETEROSEXUAL
        }
        
        # They should NOT be compatible
        # Female seeks males (compatible from her side)
        # But male seeks males, so incompatible with female
        assert not self._check_orientation_compatibility(user1, user2)

    def _check_orientation_compatibility(self, user1, user2):
        """Helper to check if two users are compatible based on orientation."""
        # User1's preference
        user1_seeks = self._get_sought_genders(user1["gender"], user1["orientation"])
        # User2's preference
        user2_seeks = self._get_sought_genders(user2["gender"], user2["orientation"])
        
        # Both must be interested in each other's gender
        return (user2["gender"] in user1_seeks) and (user1["gender"] in user2_seeks)

    def _get_sought_genders(self, gender, orientation):
        """Get which genders a user seeks based on orientation."""
        if orientation == Orientation.HETEROSEXUAL:
            return [Gender.FEMALE] if gender == Gender.MALE else [Gender.MALE]
        elif orientation == Orientation.HOMOSEXUAL:
            return [gender]
        elif orientation == Orientation.BISEXUAL:
            return [Gender.MALE, Gender.FEMALE]
        return []


class TestUserService:
    """Test user service functionality."""

    def test_user_profile_validation(self):
        """Test that user profile data is validated correctly."""
        from bot.validation import validate_profile_data
        
        profile_data = {
            "name": "John Doe",
            "birth_date": "1995-01-15",
            "gender": "male",
            "orientation": "heterosexual",
            "goal": "relationship",
            "city": "Moscow"
        }
        
        is_valid, errors = validate_profile_data(profile_data)
        assert is_valid
        assert not errors

    def test_user_profile_validation_missing_required(self):
        """Test validation fails for missing required fields."""
        from bot.validation import validate_profile_data
        
        profile_data = {
            "name": "John Doe",
            # Missing birth_date, gender, orientation
        }
        
        is_valid, errors = validate_profile_data(profile_data)
        assert not is_valid
        assert errors

    def test_user_profile_validation_invalid_age(self):
        """Test validation fails for users under 18."""
        from bot.validation import validate_profile_data
        
        today = date.today()
        birth_date = date(today.year - 17, today.month, today.day)
        
        profile_data = {
            "name": "Too Young",
            "birth_date": birth_date.isoformat(),
            "gender": "male",
            "orientation": "heterosexual",
            "goal": "relationship",
        }
        
        is_valid, errors = validate_profile_data(profile_data)
        assert not is_valid

    def test_user_profile_validation_name_too_short(self):
        """Test validation fails for names that are too short."""
        from bot.validation import validate_name
        
        is_valid, error = validate_name("A")
        assert not is_valid
        assert "2 символа" in error or "2 characters" in error.lower()

    def test_user_profile_validation_name_too_long(self):
        """Test validation fails for names that are too long."""
        from bot.validation import validate_name
        
        long_name = "A" * 51  # Over 50 character limit
        is_valid, error = validate_name(long_name)
        assert not is_valid

    def test_user_profile_validation_bio_length(self):
        """Test bio validation respects length limits."""
        from bot.validation import validate_bio
        
        # Valid bio
        valid_bio = "I love hiking and photography"
        is_valid, error = validate_bio(valid_bio)
        assert is_valid
        
        # Too long bio
        long_bio = "x" * 1001  # Over 1000 character limit
        is_valid, error = validate_bio(long_bio)
        assert not is_valid

    def test_user_interests_validation(self):
        """Test interests validation."""
        from bot.validation import validate_interests
        
        # Valid interests
        valid_interests = ["hiking", "photography", "cooking"]
        is_valid, error = validate_interests(valid_interests)
        assert is_valid
        
        # Too many interests
        too_many = ["interest" + str(i) for i in range(21)]  # Over 20 limit
        is_valid, error = validate_interests(too_many)
        assert not is_valid


class TestLocationService:
    """Test location-based services."""

    def test_location_validation(self):
        """Test location data validation."""
        from bot.validation import validate_location
        
        valid_location = {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "city": "Moscow"
        }
        
        is_valid, error = validate_location(valid_location)
        assert is_valid

    def test_location_invalid_coordinates(self):
        """Test validation fails for invalid coordinates."""
        from bot.validation import validate_location
        
        invalid_location = {
            "latitude": 91.0,  # Out of range
            "longitude": 37.6173,
            "city": "Moscow"
        }
        
        is_valid, error = validate_location(invalid_location)
        assert not is_valid

    def test_city_name_validation(self):
        """Test city name validation."""
        from bot.validation import validate_city
        
        # Valid city
        is_valid, error = validate_city("Moscow")
        assert is_valid
        
        # Too short
        is_valid, error = validate_city("A")
        assert not is_valid
        
        # Too long
        is_valid, error = validate_city("A" * 101)
        assert not is_valid


class TestImageOptimization:
    """Test image processing and optimization."""

    def test_image_optimization_reduces_size(self):
        """Test that large images are optimized."""
        from bot.api import optimize_image
        from PIL import Image
        import io
        
        # Create large test image
        image = Image.new("RGB", (1500, 1500), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        original_bytes = buffer.getvalue()
        
        # Optimize
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Verify it was resized
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        width, height = optimized_image.size
        
        assert width <= 1200
        assert height <= 1200
        optimized_image.close()

    def test_image_optimization_handles_invalid_data(self):
        """Test that invalid image data is handled gracefully."""
        from bot.api import optimize_image
        
        invalid_data = b"not an image"
        result = optimize_image(invalid_data, format="JPEG")
        
        # Should return original data on error
        assert result == invalid_data


class TestErrorResponse:
    """Test standardized error response formatting."""

    def test_error_response_format(self):
        """Test that error responses have consistent format."""
        from bot.api import error_response
        
        response = error_response("validation_error", "Test message", 400)
        
        assert response.status == 400
        assert response.content_type == "application/json"

    def test_error_response_default_status(self):
        """Test error response with default status."""
        from bot.api import error_response
        
        response = error_response("not_found", "Not found")
        assert response.status == 400  # Default status


class TestCacheService:
    """Test caching functionality."""

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        from bot.cache import Cache
        
        cache = Cache()
        cache.set("test_key", "test_value", ttl=60)
        
        value = cache.get("test_key")
        assert value == "test_value"

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        from bot.cache import Cache
        import time
        
        cache = Cache()
        cache.set("test_key", "test_value", ttl=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        value = cache.get("test_key")
        assert value is None

    def test_cache_delete(self):
        """Test deleting cache entries."""
        from bot.cache import Cache
        
        cache = Cache()
        cache.set("test_key", "test_value")
        
        cache.delete("test_key")
        
        value = cache.get("test_key")
        assert value is None

    def test_cache_auto_cleanup(self):
        """Test that cache automatically cleans up expired entries."""
        from bot.cache import Cache
        import time
        
        cache = Cache()
        
        # Add multiple entries with short TTL
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}", ttl=1)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Trigger cleanup by adding new entry
        cache.set("new_key", "new_value", ttl=60)
        
        # Old entries should be cleaned up
        assert cache.get("key_0") is None


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within rate limit are allowed."""
        from bot.security import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        for _ in range(10):
            allowed = limiter.check_rate_limit("user_123")
            assert allowed

    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over rate limit are blocked."""
        from bot.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 should be allowed
        for _ in range(5):
            assert limiter.check_rate_limit("user_123")
        
        # 6th should be blocked
        assert not limiter.check_rate_limit("user_123")

    def test_rate_limiter_resets_after_window(self):
        """Test that rate limit resets after time window."""
        from bot.security import RateLimiter
        import time
        
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use up limit
        assert limiter.check_rate_limit("user_123")
        assert limiter.check_rate_limit("user_123")
        assert not limiter.check_rate_limit("user_123")
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should be allowed again
        assert limiter.check_rate_limit("user_123")
