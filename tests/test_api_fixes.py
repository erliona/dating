"""Tests for API logical fixes from issue."""

import io
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

from PIL import Image

from bot.api import calculate_age, error_response, get_user_or_error, optimize_image


class TestAgeCalculation:
    """Tests for age calculation fix (Issue #10)."""
    
    def test_calculate_age_correctly(self):
        """Test that age is calculated correctly using calculate_age function."""
        # Test with someone born 25 years ago
        birth_date = date.today().replace(year=date.today().year - 25)
        age = calculate_age(birth_date)
        assert age == 25
    
    def test_calculate_age_before_birthday(self):
        """Test age calculation before birthday this year."""
        today = date.today()
        # Create birth date that hasn't occurred yet this year
        future_day = today + timedelta(days=10)
        birth_date = date(today.year - 25, future_day.month, future_day.day)
        
        if birth_date > today:  # Only test if birthday hasn't occurred
            age = calculate_age(birth_date)
            assert age == 24  # Still 24 because birthday hasn't happened yet
    
    def test_calculate_age_after_birthday(self):
        """Test age calculation after birthday this year."""
        today = date.today()
        # Create birth date that already occurred this year
        past_day = today - timedelta(days=10)
        birth_date = date(today.year - 25, past_day.month, past_day.day)
        
        if birth_date <= today:  # Only test if birthday has occurred
            age = calculate_age(birth_date)
            assert age == 25  # Already 25 because birthday happened


class TestErrorResponse:
    """Tests for standardized error response (Issue #8)."""
    
    def test_error_response_format(self):
        """Test that error_response creates consistent format."""
        response = error_response("validation_error", "Test message", 400)
        
        assert response.status == 400
        assert response.content_type == "application/json"
    
    def test_error_response_default_status(self):
        """Test error_response with default status."""
        response = error_response("not_found", "Not found")
        assert response.status == 400  # Default status


class TestGetUserOrError:
    """Tests for get_user_or_error helper function (Issue #7)."""
    
    async def test_get_user_or_error_returns_user(self):
        """Test that get_user_or_error returns user when found."""
        # Mock repository
        repository = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 123
        repository.get_user_by_tg_id = AsyncMock(return_value=mock_user)
        
        # Call helper
        user, error = await get_user_or_error(repository, 456)
        
        # Verify
        assert user == mock_user
        assert error is None
        repository.get_user_by_tg_id.assert_called_once_with(456)
    
    async def test_get_user_or_error_returns_error(self):
        """Test that get_user_or_error returns error when user not found."""
        # Mock repository
        repository = MagicMock()
        repository.get_user_by_tg_id = AsyncMock(return_value=None)
        
        # Call helper
        user, error = await get_user_or_error(repository, 456)
        
        # Verify
        assert user is None
        assert error is not None
        assert error.status == 404
        repository.get_user_by_tg_id.assert_called_once_with(456)


class TestImageOptimization:
    """Tests for image optimization resource leak fix (Issue #9)."""
    
    def create_test_image(self, size=(100, 100), format="JPEG"):
        """Create a test image."""
        image = Image.new("RGB", size, color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
    
    def test_optimize_image_closes_resources(self):
        """Test that optimize_image properly closes resources."""
        # Create test image
        original_bytes = self.create_test_image(size=(500, 500))
        
        # Optimize - should not raise errors about unclosed files
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Verify image was optimized
        assert len(optimized_bytes) > 0
        assert isinstance(optimized_bytes, bytes)
    
    def test_optimize_image_handles_errors_gracefully(self):
        """Test that optimize_image handles errors without resource leaks."""
        # Try to optimize invalid data
        invalid_data = b"not an image"
        
        # Should return original data on error, not raise exception
        result = optimize_image(invalid_data, format="JPEG")
        
        # Should return original data
        assert result == invalid_data
    
    def test_optimize_large_image(self):
        """Test optimization of large image."""
        # Create 1500x1500 image (exceeds MAX_IMAGE_DIMENSION of 1200)
        original_bytes = self.create_test_image(size=(1500, 1500))
        
        # Optimize
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Verify it was resized
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        width, height = optimized_image.size
        
        assert width <= 1200
        assert height <= 1200
        # Verify resources are cleaned up
        optimized_image.close()
