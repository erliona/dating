"""Tests for security fixes related to authentication and validation."""

import hashlib
import hmac
import json
import time
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest

from bot.api import check_profile_handler, like_handler, pass_handler
from bot.config import BotConfig
from bot.db import User, Profile


def create_valid_init_data(bot_token: str, user_id: int, auth_date: int = None) -> str:
    """Helper to create valid initData with correct HMAC signature."""
    if auth_date is None:
        auth_date = int(time.time())
    
    user_data = {
        "id": user_id,
        "first_name": "Test",
        "username": "testuser"
    }
    
    data = {
        "user": json.dumps(user_data),
        "auth_date": str(auth_date),
        "hash": ""  # Will be calculated
    }
    
    # Calculate HMAC
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
    
    secret_key = hmac.new(
        key="WebAppData".encode(),
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


@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test authentication security improvements."""
    
    async def test_check_profile_requires_init_data(self):
        """Test that check_profile_handler requires init_data parameter."""
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        user_id = 12345
        
        # Mock request without init_data
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.query = {"user_id": str(user_id)}
        
        response = await check_profile_handler(request)
        
        assert response.status == 401
        data = json.loads(response.body)
        assert data["error"]["code"] == "unauthorized"
        assert "init_data parameter required" in data["error"]["message"]
    
    async def test_check_profile_rejects_invalid_init_data(self):
        """Test that check_profile_handler rejects invalid init_data."""
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        user_id = 12345
        
        # Mock request with invalid init_data
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.query = {
            "user_id": str(user_id),
            "init_data": "invalid_data"
        }
        
        response = await check_profile_handler(request)
        
        assert response.status == 401
        data = json.loads(response.body)
        assert data["error"]["code"] == "unauthorized"
        assert "invalid init_data" in data["error"]["message"]
    
    async def test_check_profile_rejects_missing_user_in_init_data(self):
        """Test that check_profile_handler rejects init_data without user parameter."""
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        user_id = 12345
        
        # Mock request with init_data missing user parameter
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.query = {
            "user_id": str(user_id),
            "init_data": "other_param=value"
        }
        
        response = await check_profile_handler(request)
        
        assert response.status == 401
        data = json.loads(response.body)
        assert data["error"]["code"] == "unauthorized"
        assert "invalid init_data" in data["error"]["message"]
    
    async def test_check_profile_rejects_init_data_without_id(self):
        """Test that check_profile_handler rejects init_data where user object lacks id."""
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        user_id = 12345
        
        # Mock request with init_data where user object lacks id
        init_data = f"user={json.dumps({'name': 'test'})}"
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.query = {
            "user_id": str(user_id),
            "init_data": init_data
        }
        
        response = await check_profile_handler(request)
        
        assert response.status == 401
        data = json.loads(response.body)
        assert data["error"]["code"] == "unauthorized"
        assert "invalid init_data" in data["error"]["message"]
    
    async def test_check_profile_rejects_mismatched_user_id(self):
        """Test that check_profile_handler rejects when authenticated user doesn't match requested user."""
        config = BotConfig(
            token="test:token",
            database_url="postgresql://test",
            jwt_secret="test-secret"
        )
        
        authenticated_user_id = 12345
        requested_user_id = 67890
        
        # Create properly signed init_data with authenticated user's ID
        init_data = create_valid_init_data(config.token, authenticated_user_id)
        
        request = MagicMock()
        request.app = {"config": config, "session_maker": MagicMock()}
        request.query = {
            "user_id": str(requested_user_id),
            "init_data": init_data
        }
        
        response = await check_profile_handler(request)
        
        assert response.status == 403
        data = json.loads(response.body)
        assert data["error"]["code"] == "unauthorized"
        assert "can only check own profile" in data["error"]["message"].lower()


@pytest.mark.asyncio
class TestTargetValidation:
    """Test target user validation in interaction endpoints."""
    
    async def test_like_handler_validates_target_exists(self):
        """Test that like_handler validates target user exists."""
        with patch('bot.api.authenticate_request', AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock()
            }
            request.json = AsyncMock(return_value={
                "target_id": 999,
                "type": "like"
            })
            
            mock_session = MagicMock()
            mock_session.commit = AsyncMock()
            mock_repository = MagicMock()
            
            user = User(id=1, tg_id=12345, username="test")
            mock_repository.get_user_by_tg_id = AsyncMock(return_value=user)
            # Target user doesn't exist
            mock_repository.get_user_by_id = AsyncMock(return_value=None)
            
            # Mock async context manager
            session_maker = MagicMock()
            session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            request.app["session_maker"] = session_maker
            
            with patch('bot.api.ProfileRepository', return_value=mock_repository):
                response = await like_handler(request)
            
            assert response.status == 404
            data = json.loads(response.body)
            assert data["error"]["code"] == "not_found"
            assert "Target user not found" in data["error"]["message"]
    
    async def test_pass_handler_validates_target_exists(self):
        """Test that pass_handler validates target user exists."""
        with patch('bot.api.authenticate_request', AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock()
            }
            request.json = AsyncMock(return_value={
                "target_id": 999
            })
            
            mock_session = MagicMock()
            mock_session.commit = AsyncMock()
            mock_repository = MagicMock()
            
            user = User(id=1, tg_id=12345, username="test")
            mock_repository.get_user_by_tg_id = AsyncMock(return_value=user)
            # Target user doesn't exist
            mock_repository.get_user_by_id = AsyncMock(return_value=None)
            
            # Mock async context manager
            session_maker = MagicMock()
            session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            request.app["session_maker"] = session_maker
            
            with patch('bot.api.ProfileRepository', return_value=mock_repository):
                response = await pass_handler(request)
            
            assert response.status == 404
            data = json.loads(response.body)
            assert data["error"]["code"] == "not_found"
            assert "Target user not found" in data["error"]["message"]
    
    async def test_like_handler_succeeds_with_valid_target(self):
        """Test that like_handler succeeds when target user exists."""
        with patch('bot.api.authenticate_request', AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock()
            }
            request.json = AsyncMock(return_value={
                "target_id": 123,
                "type": "like"
            })
            
            mock_session = MagicMock()
            mock_session.commit = AsyncMock()
            mock_repository = MagicMock()
            
            user = User(id=1, tg_id=12345, username="test")
            target_user = User(id=123, tg_id=67890, username="target")
            mock_repository.get_user_by_tg_id = AsyncMock(return_value=user)
            mock_repository.get_user_by_id = AsyncMock(return_value=target_user)
            mock_repository.create_interaction = AsyncMock()
            mock_repository.check_mutual_like = AsyncMock(return_value=False)
            
            # Mock async context manager
            session_maker = MagicMock()
            session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
            
            request.app["session_maker"] = session_maker
            
            with patch('bot.api.ProfileRepository', return_value=mock_repository):
                response = await like_handler(request)
            
            assert response.status == 200
            # Verify that create_interaction was called
            assert mock_repository.create_interaction.called
