"""Tests for security utilities."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from bot.security import (
    RateLimiter,
    RateLimitConfig,
    sanitize_user_input,
    validate_profile_data,
    validate_webapp_data,
)


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        config = RateLimitConfig(max_requests=3, window_seconds=60)
        limiter = RateLimiter(config)
        
        user_id = 12345
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
    
    def test_blocks_requests_exceeding_limit(self):
        """Test that requests exceeding limit are blocked."""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        limiter = RateLimiter(config)
        
        user_id = 12345
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is True
        assert limiter.is_allowed(user_id) is False
        assert limiter.is_allowed(user_id) is False
    
    def test_different_users_independent_limits(self):
        """Test that different users have independent rate limits."""
        config = RateLimitConfig(max_requests=2, window_seconds=60)
        limiter = RateLimiter(config)
        
        user1 = 12345
        user2 = 67890
        
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user1) is True
        assert limiter.is_allowed(user1) is False
        
        # User 2 should still be allowed
        assert limiter.is_allowed(user2) is True
        assert limiter.is_allowed(user2) is True
        assert limiter.is_allowed(user2) is False
    
    def test_get_remaining_requests(self):
        """Test getting remaining request count."""
        config = RateLimitConfig(max_requests=5, window_seconds=60)
        limiter = RateLimiter(config)
        
        user_id = 12345
        assert limiter.get_remaining_requests(user_id) == 5
        
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 4
        
        limiter.is_allowed(user_id)
        limiter.is_allowed(user_id)
        assert limiter.get_remaining_requests(user_id) == 2


class TestValidateWebAppData:
    """Tests for WebApp data validation."""
    
    def create_valid_init_data(self, bot_token: str, user_id: int = 12345) -> str:
        """Create valid initData for testing."""
        auth_date = int(time.time())
        user_data = json.dumps({
            'id': user_id,
            'first_name': 'Test',
            'username': 'testuser',
            'language_code': 'en'
        })
        
        data = {
            'auth_date': str(auth_date),
            'user': user_data,
        }
        
        # Create data-check-string
        data_check_items = sorted(f"{k}={v}" for k, v in data.items())
        data_check_string = '\n'.join(data_check_items)
        
        # Calculate hash
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        data['hash'] = calculated_hash
        
        return urlencode(data)
    
    def test_validates_correct_data(self):
        """Test that valid data passes validation."""
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        init_data = self.create_valid_init_data(bot_token)
        
        result = validate_webapp_data(init_data, bot_token)
        assert result is not None
        assert 'user' in result
        assert result['user']['id'] == 12345
    
    def test_rejects_missing_hash(self):
        """Test that data without hash is rejected."""
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        init_data = f"auth_date={int(time.time())}&user=%7B%22id%22%3A12345%7D"
        
        result = validate_webapp_data(init_data, bot_token)
        assert result is None
    
    def test_rejects_invalid_hash(self):
        """Test that data with invalid hash is rejected."""
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        auth_date = int(time.time())
        init_data = f"auth_date={auth_date}&hash=invalid_hash&user=%7B%22id%22%3A12345%7D"
        
        result = validate_webapp_data(init_data, bot_token)
        assert result is None
    
    def test_rejects_old_data(self):
        """Test that old data is rejected."""
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        old_time = int(time.time()) - 7200  # 2 hours ago
        
        user_data = json.dumps({'id': 12345, 'first_name': 'Test'})
        data = {
            'auth_date': str(old_time),
            'user': user_data,
        }
        
        data_check_items = sorted(f"{k}={v}" for k, v in data.items())
        data_check_string = '\n'.join(data_check_items)
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        data['hash'] = calculated_hash
        init_data = urlencode(data)
        
        result = validate_webapp_data(init_data, bot_token, max_age_seconds=3600)
        assert result is None
    
    def test_rejects_missing_auth_date(self):
        """Test that data without auth_date is rejected."""
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        init_data = "hash=somehash&user=%7B%22id%22%3A12345%7D"
        
        result = validate_webapp_data(init_data, bot_token)
        assert result is None


class TestSanitizeUserInput:
    """Tests for input sanitization."""
    
    def test_sanitizes_basic_text(self):
        """Test basic text sanitization."""
        result = sanitize_user_input("  Hello World  ")
        assert result == "Hello World"
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed."""
        result = sanitize_user_input("Hello\x00World")
        assert result == "HelloWorld"
    
    def test_truncates_long_text(self):
        """Test that long text is truncated."""
        long_text = "a" * 20000
        result = sanitize_user_input(long_text, max_length=1000)
        assert len(result) == 1000
    
    def test_preserves_newlines(self):
        """Test that newlines are preserved."""
        result = sanitize_user_input("Line 1\nLine 2\nLine 3")
        assert result == "Line 1\nLine 2\nLine 3"
    
    def test_handles_non_string_input(self):
        """Test handling of non-string input."""
        result = sanitize_user_input(12345)  # type: ignore
        assert result == ""
    
    def test_removes_control_characters(self):
        """Test that control characters are removed."""
        result = sanitize_user_input("Hello\x01\x02\x03World")
        assert result == "HelloWorld"


class TestValidateProfileData:
    """Tests for profile data validation."""
    
    def test_validates_valid_profile(self):
        """Test that valid profile data passes validation."""
        data = {
            'name': 'John Doe',
            'age': 25,
            'gender': 'male',
            'preference': 'female',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is True
        assert error is None
    
    def test_validates_profile_with_optional_fields(self):
        """Test profile with optional fields."""
        data = {
            'name': 'Jane Smith',
            'age': 30,
            'gender': 'female',
            'preference': 'any',
            'bio': 'Love hiking and photography',
            'location': 'New York',
            'interests': ['hiking', 'photography', 'travel'],
            'goal': 'friendship',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is True
        assert error is None
    
    def test_rejects_missing_required_field(self):
        """Test that missing required fields are rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'male',
            # missing 'preference'
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'preference' in error
    
    def test_rejects_invalid_age(self):
        """Test that invalid age is rejected."""
        data = {
            'name': 'John',
            'age': 15,  # Too young
            'gender': 'male',
            'preference': 'female',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Age' in error
    
    def test_rejects_age_over_limit(self):
        """Test that age over limit is rejected."""
        data = {
            'name': 'John',
            'age': 150,
            'gender': 'male',
            'preference': 'female',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Age' in error
    
    def test_rejects_invalid_gender(self):
        """Test that invalid gender is rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'invalid',
            'preference': 'female',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Gender' in error
    
    def test_rejects_invalid_preference(self):
        """Test that invalid preference is rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'male',
            'preference': 'invalid',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Preference' in error
    
    def test_rejects_short_name(self):
        """Test that too short name is rejected."""
        data = {
            'name': 'J',
            'age': 25,
            'gender': 'male',
            'preference': 'female',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Name' in error
    
    def test_rejects_long_bio(self):
        """Test that too long bio is rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'male',
            'preference': 'female',
            'bio': 'a' * 1500,
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Bio' in error
    
    def test_rejects_too_many_interests(self):
        """Test that too many interests are rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'male',
            'preference': 'female',
            'interests': [f'interest{i}' for i in range(25)],
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'interests' in error
    
    def test_rejects_invalid_goal(self):
        """Test that invalid goal is rejected."""
        data = {
            'name': 'John',
            'age': 25,
            'gender': 'male',
            'preference': 'female',
            'goal': 'invalid_goal',
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert 'Goal' in error
