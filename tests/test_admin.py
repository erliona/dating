"""Tests for admin service."""

import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from services.admin.main import (
    hash_password,
    verify_password,
    create_app,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test123"
        hashed = hash_password(password)
        
        # SHA-256 produces 64 character hex string
        assert len(hashed) == 64
        assert isinstance(hashed, str)
        
        # Same password should produce same hash
        assert hash_password(password) == hashed
        
        # Different password should produce different hash
        assert hash_password("different") != hashed

    def test_verify_password(self):
        """Test password verification."""
        password = "test123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Incorrect password should not verify
        assert verify_password("wrong", hashed) is False
        assert verify_password("", hashed) is False


class TestAdminApp:
    """Test admin application creation."""

    @patch('services.admin.main.create_async_engine')
    @patch('services.admin.main.async_sessionmaker')
    def test_create_app(self, mock_session_maker, mock_engine):
        """Test app creation."""
        config = {
            "jwt_secret": "test-secret",
            "database_url": "postgresql+asyncpg://test:test@localhost:5432/test"
        }
        
        # Mock database engine and session maker
        mock_engine.return_value = MagicMock()
        mock_session_maker.return_value = MagicMock()
        
        app = create_app(config)
        
        # Check app is created
        assert isinstance(app, web.Application)
        
        # Check config is set
        assert app["config"] == config
        
        # Check routes are registered
        routes = [route.resource.canonical for route in app.router.routes()]
        
        # Should have admin routes
        assert any('/admin/login' in route for route in routes)
        assert any('/admin/stats' in route for route in routes)
        assert any('/admin/users' in route for route in routes)
        assert any('/health' in route for route in routes)


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Test admin API endpoints (integration tests would go here)."""

    async def test_health_check(self):
        """Test health check endpoint."""
        from services.admin.main import health_check
        
        request = MagicMock(spec=web.Request)
        response = await health_check(request)
        
        assert response.status == 200
        # Check with spaces since JSON formatting includes spaces
        assert b'"status": "healthy"' in response.body or b'"status":"healthy"' in response.body
        assert b'"service": "admin"' in response.body or b'"service":"admin"' in response.body


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
