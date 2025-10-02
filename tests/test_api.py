"""Tests for HTTP API photo upload functionality."""

import base64
import io
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from PIL import Image

from bot.api import (
    AuthenticationError,
    calculate_nsfw_score,
    create_jwt_token,
    optimize_image,
    verify_jwt_token,
)


class TestJWTAuthentication:
    """Test JWT token creation and verification."""
    
    def test_create_jwt_token(self):
        """Test JWT token creation."""
        user_id = 12345
        jwt_secret = "test-secret-key"
        
        token = create_jwt_token(user_id, jwt_secret, expires_in=3600)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        assert payload["user_id"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_valid_token(self):
        """Test verification of valid JWT token."""
        user_id = 12345
        jwt_secret = "test-secret-key"
        
        token = create_jwt_token(user_id, jwt_secret, expires_in=3600)
        payload = verify_jwt_token(token, jwt_secret)
        
        assert payload["user_id"] == user_id
    
    def test_verify_expired_token(self):
        """Test verification of expired JWT token."""
        user_id = 12345
        jwt_secret = "test-secret-key"
        
        # Create token that expires immediately
        token = create_jwt_token(user_id, jwt_secret, expires_in=-1)
        
        with pytest.raises(AuthenticationError, match="Token has expired"):
            verify_jwt_token(token, jwt_secret)
    
    def test_verify_invalid_token(self):
        """Test verification of invalid JWT token."""
        jwt_secret = "test-secret-key"
        invalid_token = "invalid.token.here"
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            verify_jwt_token(invalid_token, jwt_secret)
    
    def test_verify_token_wrong_secret(self):
        """Test verification with wrong secret."""
        user_id = 12345
        jwt_secret = "test-secret-key"
        wrong_secret = "wrong-secret"
        
        token = create_jwt_token(user_id, jwt_secret)
        
        with pytest.raises(AuthenticationError, match="Invalid token"):
            verify_jwt_token(token, wrong_secret)


class TestImageOptimization:
    """Test image optimization functionality."""
    
    def create_test_image(self, size=(1500, 1500), format="JPEG"):
        """Create a test image."""
        image = Image.new("RGB", size, color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
    
    def test_optimize_large_image(self):
        """Test optimization of large image."""
        # Create 1500x1500 image
        original_bytes = self.create_test_image(size=(1500, 1500))
        
        # Optimize to max 1200px
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Check image was resized
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        width, height = optimized_image.size
        
        assert width <= 1200
        assert height <= 1200
        assert len(optimized_bytes) < len(original_bytes)
    
    def test_optimize_small_image(self):
        """Test optimization of already small image."""
        # Create 800x800 image (within limit)
        original_bytes = self.create_test_image(size=(800, 800))
        
        # Optimize
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Check image size unchanged
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        width, height = optimized_image.size
        
        assert width == 800
        assert height == 800
    
    def test_optimize_aspect_ratio_maintained(self):
        """Test aspect ratio is maintained during optimization."""
        # Create 2000x1000 image (2:1 ratio)
        original_bytes = self.create_test_image(size=(2000, 1000))
        
        # Optimize
        optimized_bytes = optimize_image(original_bytes, format="JPEG")
        
        # Check aspect ratio maintained
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        width, height = optimized_image.size
        
        assert width == 1200
        assert height == 600
    
    def test_optimize_png_format(self):
        """Test PNG optimization."""
        original_bytes = self.create_test_image(size=(1500, 1500), format="PNG")
        
        optimized_bytes = optimize_image(original_bytes, format="PNG")
        
        # Check it's still valid PNG
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        assert optimized_image.format == "PNG"
    
    def test_optimize_webp_format(self):
        """Test WebP optimization."""
        original_bytes = self.create_test_image(size=(1500, 1500), format="JPEG")
        
        optimized_bytes = optimize_image(original_bytes, format="WEBP")
        
        # Check it's valid WebP
        optimized_image = Image.open(io.BytesIO(optimized_bytes))
        assert optimized_image.format == "WEBP"


class TestNSFWDetection:
    """Test NSFW detection placeholder."""
    
    def test_calculate_nsfw_score(self):
        """Test NSFW score calculation."""
        # Create dummy image bytes
        image = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        # Calculate score
        score = calculate_nsfw_score(image_bytes)
        
        # Check score is valid (placeholder returns 1.0)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score == 1.0  # Placeholder always returns safe


class TestPhotoStorage:
    """Test photo storage functionality."""
    
    def test_storage_path_configuration(self):
        """Test that photo storage path can be configured."""
        from bot.config import BotConfig
        
        # Test with custom storage path
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            photo_storage_path="/custom/path",
            photo_cdn_url=None
        )
        
        assert config.photo_storage_path == "/custom/path"
        assert config.photo_cdn_url is None
    
    def test_cdn_url_configuration(self):
        """Test that CDN URL can be configured."""
        from bot.config import BotConfig
        
        # Test with CDN URL
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            photo_storage_path="/app/photos",
            photo_cdn_url="https://cdn.example.com"
        )
        
        assert config.photo_cdn_url == "https://cdn.example.com"
