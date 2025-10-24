"""Tests for Telegram security middleware."""

import pytest
from unittest.mock import Mock, patch
from aiohttp import web, ClientSession
from core.middleware.telegram_security import (
    validate_telegram_origin,
    validate_telegram_bot_secret,
    telegram_security_middleware
)


class TestTelegramOriginValidation:
    """Test Telegram origin validation."""
    
    def test_valid_origin(self):
        """Test valid Telegram origin."""
        request = Mock()
        request.headers = {
            'Origin': 'https://web.telegram.org',
            'Referer': 'https://web.telegram.org',
            'User-Agent': 'TelegramBot/1.0'
        }
        
        assert validate_telegram_origin(request) is True
    
    def test_invalid_origin(self):
        """Test invalid origin."""
        request = Mock()
        request.headers = {
            'Origin': 'https://evil.com',
            'User-Agent': 'TelegramBot/1.0'
        }
        
        assert validate_telegram_origin(request) is False
    
    def test_missing_origin(self):
        """Test missing origin header."""
        request = Mock()
        request.headers = {
            'User-Agent': 'TelegramBot/1.0'
        }
        
        assert validate_telegram_origin(request) is False
    
    def test_invalid_user_agent(self):
        """Test invalid user agent."""
        request = Mock()
        request.headers = {
            'Origin': 'https://web.telegram.org',
            'User-Agent': 'Mozilla/5.0'
        }
        
        assert validate_telegram_origin(request) is False


class TestTelegramBotSecretValidation:
    """Test Telegram bot secret validation."""
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'})
    def test_valid_secret(self):
        """Test valid bot secret."""
        request = Mock()
        request.headers = {'X-Telegram-Bot-Api-Secret-Token': 'test_secret'}
        
        assert validate_telegram_bot_secret(request) is True
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'})
    def test_invalid_secret(self):
        """Test invalid bot secret."""
        request = Mock()
        request.headers = {'X-Telegram-Bot-Api-Secret-Token': 'wrong_secret'}
        
        assert validate_telegram_bot_secret(request) is False
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'})
    def test_missing_secret(self):
        """Test missing secret header."""
        request = Mock()
        request.headers = {}
        
        assert validate_telegram_bot_secret(request) is False
    
    def test_missing_env_var(self):
        """Test missing environment variable."""
        request = Mock()
        request.headers = {'X-Telegram-Bot-Api-Secret-Token': 'test_secret'}
        
        assert validate_telegram_bot_secret(request) is False


@pytest.mark.asyncio
class TestTelegramSecurityMiddleware:
    """Test Telegram security middleware."""
    
    async def test_valid_request(self):
        """Test valid Telegram request passes middleware."""
        async def handler(request):
            return web.json_response({"status": "ok"})
        
        request = Mock()
        request.path = "/auth/validate"
        request.remote = "192.168.1.1"
        request.headers = {
            'Origin': 'https://web.telegram.org',
            'User-Agent': 'TelegramBot/1.0',
            'X-Telegram-Bot-Api-Secret-Token': 'test_secret'
        }
        
        with patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'}):
            response = await telegram_security_middleware(request, handler)
            assert response.status == 200
    
    async def test_invalid_origin(self):
        """Test invalid origin is rejected."""
        async def handler(request):
            return web.json_response({"status": "ok"})
        
        request = Mock()
        request.path = "/auth/validate"
        request.remote = "192.168.1.1"
        request.headers = {
            'Origin': 'https://evil.com',
            'User-Agent': 'TelegramBot/1.0',
            'X-Telegram-Bot-Api-Secret-Token': 'test_secret'
        }
        
        with patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'}):
            response = await telegram_security_middleware(request, handler)
            assert response.status == 403
    
    async def test_invalid_secret(self):
        """Test invalid secret is rejected."""
        async def handler(request):
            return web.json_response({"status": "ok"})
        
        request = Mock()
        request.path = "/auth/validate"
        request.remote = "192.168.1.1"
        request.headers = {
            'Origin': 'https://web.telegram.org',
            'User-Agent': 'TelegramBot/1.0',
            'X-Telegram-Bot-Api-Secret-Token': 'wrong_secret'
        }
        
        with patch.dict('os.environ', {'TELEGRAM_BOT_SECRET_TOKEN': 'test_secret'}):
            response = await telegram_security_middleware(request, handler)
            assert response.status == 403
    
    async def test_health_check_bypass(self):
        """Test health check bypasses security."""
        async def handler(request):
            return web.json_response({"status": "healthy"})
        
        request = Mock()
        request.path = "/health"
        request.remote = "192.168.1.1"
        request.headers = {}
        
        response = await telegram_security_middleware(request, handler)
        assert response.status == 200
    
    async def test_non_auth_path_bypass(self):
        """Test non-auth paths bypass security."""
        async def handler(request):
            return web.json_response({"status": "ok"})
        
        request = Mock()
        request.path = "/profiles/123"
        request.remote = "192.168.1.1"
        request.headers = {}
        
        response = await telegram_security_middleware(request, handler)
        assert response.status == 200
