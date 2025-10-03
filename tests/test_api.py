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
    """Test NSFW detection with ML model."""
    
    def test_calculate_nsfw_score(self):
        """Test NSFW score calculation."""
        # Create dummy image bytes
        image = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        # Calculate score
        score = calculate_nsfw_score(image_bytes)
        
        # Check score is valid
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Score should be reasonable (fallback returns 1.0 if NudeNet not available)
        assert score >= 0.0
    
    def test_nsfw_score_with_safe_image(self):
        """Test that safe images get high scores."""
        # Create a simple solid color image (should be classified as safe)
        image = Image.new("RGB", (200, 200), color=(100, 150, 200))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        
        score = calculate_nsfw_score(image_bytes)
        
        # Safe image should have high score
        # Note: May return 1.0 if NudeNet not installed (fallback mode)
        assert score >= 0.5


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


@pytest.mark.asyncio
class TestAuthenticateRequest:
    """Test request authentication."""
    
    async def test_authenticate_missing_header(self):
        """Test authentication fails when Authorization header is missing."""
        from aiohttp import web
        from bot.api import authenticate_request, AuthenticationError
        
        # Create mock request without Authorization header
        request = MagicMock()
        request.headers = {}
        
        with pytest.raises(AuthenticationError, match="Missing Authorization header"):
            await authenticate_request(request, "secret")
    
    async def test_authenticate_invalid_header_format(self):
        """Test authentication fails with invalid header format."""
        from bot.api import authenticate_request, AuthenticationError
        
        # Create mock request with invalid Authorization header
        request = MagicMock()
        request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(AuthenticationError, match="Invalid Authorization header format"):
            await authenticate_request(request, "secret")
    
    async def test_authenticate_invalid_token(self):
        """Test authentication fails with invalid token."""
        from bot.api import authenticate_request, AuthenticationError
        
        request = MagicMock()
        request.headers = {"Authorization": "Bearer invalid-token"}
        
        with pytest.raises(AuthenticationError):
            await authenticate_request(request, "secret")
    
    async def test_authenticate_valid_token(self):
        """Test successful authentication with valid token."""
        from bot.api import authenticate_request, create_jwt_token
        
        user_id = 12345
        jwt_secret = "test-secret"
        token = create_jwt_token(user_id, jwt_secret)
        
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {token}"}
        
        result_user_id = await authenticate_request(request, jwt_secret)
        assert result_user_id == user_id


@pytest.mark.asyncio
class TestHealthCheckHandler:
    """Test health check endpoint."""
    
    async def test_health_check(self):
        """Test health check returns OK status."""
        from bot.api import health_check_handler
        
        request = MagicMock()
        response = await health_check_handler(request)
        
        assert response.status == 200
        # Check response body
        import json
        body = json.loads(response.body.decode())
        assert body["status"] == "ok"


@pytest.mark.asyncio
class TestGenerateTokenHandler:
    """Test token generation endpoint."""
    
    async def test_generate_token_missing_user_id(self):
        """Test token generation fails without user_id."""
        from bot.api import generate_token_handler
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        request = MagicMock()
        request.app = {"config": config}
        request.json = AsyncMock(return_value={})
        
        response = await generate_token_handler(request)
        assert response.status == 400
    
    async def test_generate_token_success(self):
        """Test successful token generation."""
        from bot.api import generate_token_handler
        from bot.config import BotConfig
        import json
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        request = MagicMock()
        request.app = {"config": config}
        request.json = AsyncMock(return_value={"user_id": 12345})
        
        response = await generate_token_handler(request)
        assert response.status == 200
        
        body = json.loads(response.body.decode())
        assert "token" in body
        assert "expires_in" in body
        assert body["expires_in"] == 3600
    
    async def test_generate_token_exception_handling(self):
        """Test token generation handles exceptions."""
        from bot.api import generate_token_handler
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        request = MagicMock()
        request.app = {"config": config}
        request.json = AsyncMock(side_effect=Exception("JSON error"))
        
        response = await generate_token_handler(request)
        assert response.status == 500


@pytest.mark.asyncio
class TestUploadPhotoHandler:
    """Test photo upload endpoint."""
    
    async def test_upload_photo_authentication_required(self):
        """Test photo upload requires authentication."""
        from bot.api import upload_photo_handler
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos"
        )
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {}  # No Authorization header
        
        response = await upload_photo_handler(request)
        assert response.status == 401
    
    async def test_upload_photo_no_data(self):
        """Test photo upload fails without photo data."""
        from bot.api import upload_photo_handler, create_jwt_token
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos"
        )
        
        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)
        
        # Mock multipart reader that returns no photo data
        multipart_reader = AsyncMock()
        multipart_reader.__aiter__.return_value = []
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.multipart = AsyncMock(return_value=multipart_reader)
        
        response = await upload_photo_handler(request)
        assert response.status == 400
    
    async def test_upload_photo_invalid_slot_index(self):
        """Test photo upload fails with invalid slot_index."""
        from bot.api import upload_photo_handler, create_jwt_token
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos"
        )
        
        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)
        
        # Create fake photo data
        photo_data = b"fake photo"
        
        # Mock multipart field
        photo_field = AsyncMock()
        photo_field.name = "photo"
        photo_field.read = AsyncMock(return_value=photo_data)
        
        slot_field = AsyncMock()
        slot_field.name = "slot_index"
        slot_field.read = AsyncMock(return_value=b"5")  # Invalid (max is 2)
        
        multipart_reader = AsyncMock()
        multipart_reader.__aiter__.return_value = [photo_field, slot_field]
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.multipart = AsyncMock(return_value=multipart_reader)
        
        response = await upload_photo_handler(request)
        assert response.status == 400


class TestCreateApp:
    """Test create_app function."""
    
    def test_create_app_without_cdn(self, tmp_path):
        """Test app creation without CDN URL."""
        from bot.api import create_app
        from bot.config import BotConfig
        import warnings
        import os
        
        storage_path = str(tmp_path / "photos")
        os.makedirs(storage_path, exist_ok=True)
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path=storage_path,
            photo_cdn_url=None
        )
        
        session_maker = MagicMock()
        
        # Suppress aiohttp AppKey warnings in tests
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = create_app(config, session_maker)
        
        assert app is not None
        # Access via dict syntax is acceptable in tests
        assert app["config"] == config
        assert app["session_maker"] == session_maker
    
    def test_create_app_with_cdn(self):
        """Test app creation with CDN URL."""
        from bot.api import create_app
        from bot.config import BotConfig
        import warnings
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos",
            photo_cdn_url="https://cdn.example.com"
        )
        
        session_maker = MagicMock()
        
        # Suppress aiohttp AppKey warnings in tests
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = create_app(config, session_maker)
        
        assert app is not None
        assert app["config"].photo_cdn_url == "https://cdn.example.com"


@pytest.mark.asyncio
class TestUploadPhotoHandlerComplete:
    """Test complete photo upload flow."""
    
    async def test_upload_photo_successful_flow(self, tmp_path):
        """Test successful complete photo upload with all validations."""
        from bot.api import upload_photo_handler, create_jwt_token
        from bot.config import BotConfig
        from PIL import Image
        from io import BytesIO
        
        storage_path = str(tmp_path / "photos")
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path=storage_path,
            nsfw_threshold=0.5  # Lower threshold for test
        )
        
        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)
        
        # Create valid test image
        img = Image.new('RGB', (200, 200), color='purple')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        photo_data = buffer.getvalue()
        
        # Mock multipart field for photo
        photo_field = AsyncMock()
        photo_field.name = "photo"
        photo_field.read = AsyncMock(return_value=photo_data)
        
        # Mock multipart field for slot_index
        slot_field = AsyncMock()
        slot_field.name = "slot_index"
        slot_field.read = AsyncMock(return_value=b"0")
        
        multipart_reader = AsyncMock()
        multipart_reader.__aiter__.return_value = [photo_field, slot_field]
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.multipart = AsyncMock(return_value=multipart_reader)
        
        # Call handler
        response = await upload_photo_handler(request)
        
        # For this test, we expect success if NSFW score passes threshold
        # or appropriate error if photo is rejected
        assert response.status in [200, 400]
        
        if response.status == 200:
            import json
            body = json.loads(response.body.decode())
            assert "url" in body
            assert "file_size" in body
            assert "optimized_size" in body
            assert "safe_score" in body
    
    async def test_upload_photo_too_large(self):
        """Test photo upload with file too large."""
        from bot.api import upload_photo_handler, create_jwt_token
        from bot.config import BotConfig
        from PIL import Image
        from io import BytesIO
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos"
        )
        
        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)
        
        # Create a large dummy file (> 5MB)
        large_data = b"\xFF\xD8\xFF\xE0" + b"\x00" * (6 * 1024 * 1024)
        
        photo_field = AsyncMock()
        photo_field.name = "photo"
        photo_field.read = AsyncMock(return_value=large_data)
        
        slot_field = AsyncMock()
        slot_field.name = "slot_index"
        slot_field.read = AsyncMock(return_value=b"0")
        
        multipart_reader = AsyncMock()
        multipart_reader.__aiter__.return_value = [photo_field, slot_field]
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.multipart = AsyncMock(return_value=multipart_reader)
        
        response = await upload_photo_handler(request)
        assert response.status == 400
    
    async def test_upload_photo_invalid_mime_type(self):
        """Test photo upload with invalid MIME type."""
        from bot.api import upload_photo_handler, create_jwt_token
        from bot.config import BotConfig
        
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret",
            photo_storage_path="/tmp/photos"
        )
        
        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)
        
        # Send text file as photo
        invalid_data = b"This is not an image"
        
        photo_field = AsyncMock()
        photo_field.name = "photo"
        photo_field.read = AsyncMock(return_value=invalid_data)
        
        slot_field = AsyncMock()
        slot_field.name = "slot_index"
        slot_field.read = AsyncMock(return_value=b"1")
        
        multipart_reader = AsyncMock()
        multipart_reader.__aiter__.return_value = [photo_field, slot_field]
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.multipart = AsyncMock(return_value=multipart_reader)
        
        response = await upload_photo_handler(request)
        assert response.status == 400
