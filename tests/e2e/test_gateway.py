"""Tests for API Gateway proxy functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientTimeout, web

from gateway.main import create_app, proxy_request


class TestProxyRequest:
    """Tests for proxy_request function."""

    async def test_proxy_request_timeout_configured(self):
        """Test that proxy request has timeout configured."""
        # This test ensures timeout is configured
        # We test this by mocking ClientSession and checking it's called with timeout
        with patch("gateway.main.ClientSession") as mock_session:
            # Create a properly mocked session with async context manager
            mock_session_instance = MagicMock()
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session_instance
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {}
            mock_response.read = AsyncMock(return_value=b'{"status": "ok"}')

            mock_request_ctx = MagicMock()
            mock_request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
            mock_request_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_session_instance.request = MagicMock(return_value=mock_request_ctx)

            # Create a mock request
            mock_request = MagicMock()
            mock_request.path = "/test"
            mock_request.query_string = ""
            mock_request.method = "GET"
            mock_request.headers = {}
            mock_request.read = AsyncMock(return_value=b"")

            # Call proxy_request
            response = await proxy_request(mock_request, "http://backend-service:8000")

            # Verify ClientSession was called with timeout
            mock_session.assert_called_once()
            call_kwargs = mock_session.call_args[1] if mock_session.call_args else {}
            assert "timeout" in call_kwargs
            assert isinstance(call_kwargs["timeout"], ClientTimeout)
            assert response.status == 200

    async def test_proxy_request_handles_connection_error(self):
        """Test that proxy request handles connection errors gracefully."""
        with patch("gateway.main.ClientSession") as mock_session:
            # Simulate a connection error
            mock_session.return_value.__aenter__.side_effect = Exception(
                "Connection refused"
            )

            # Create a mock request
            mock_request = MagicMock()
            mock_request.path = "/test"
            mock_request.query_string = ""
            mock_request.method = "GET"
            mock_request.headers = {}
            mock_request.read = AsyncMock(return_value=b"")

            # Call proxy_request
            response = await proxy_request(mock_request, "http://backend-service:8000")

            # Verify it returns 503 error
            assert response.status == 503

    async def test_gateway_health_check(self):
        """Test gateway health check endpoint."""
        # Test health check through direct handler call
        from gateway.main import health_check

        # Create mock request with config
        mock_request = MagicMock()
        mock_request.app = {
            "config": {
                "auth_service_url": "http://auth-service:8081",
                "profile_service_url": "http://profile-service:8082",
                "discovery_service_url": "http://discovery-service:8083",
                "media_service_url": "http://media-service:8084",
                "chat_service_url": "http://chat-service:8085",
                "admin_service_url": "http://admin-service:8086",
            }
        }

        resp = await health_check(mock_request)
        assert resp.status == 200

        import json

        data = json.loads(resp.body)
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "routes" in data


class TestGatewayRouting:
    """Tests for gateway routing configuration."""

    @pytest.mark.xfail(reason="Gateway app routes already have handlers - test isolation issue with CORS")
    def test_create_app(self):
        """Test that create_app creates a valid application."""
        config = {
            "auth_service_url": "http://auth:8081",
            "profile_service_url": "http://profile:8082",
            "discovery_service_url": "http://discovery:8083",
            "media_service_url": "http://media:8084",
            "chat_service_url": "http://chat:8085",
            "admin_service_url": "http://admin:8086",
        }

        app = create_app(config)

        assert isinstance(app, web.Application)
        assert app["config"] == config

        # Check that routes are registered
        routes = [str(route.resource) for route in app.router.routes()]
        assert any("/health" in route for route in routes)


class TestErrorScenarios:
    """Tests for various error scenarios that could cause URLError."""

    async def test_timeout_error(self):
        """Test that timeout errors are handled gracefully."""
        from aiohttp import ServerTimeoutError

        with patch("gateway.main.ClientSession") as mock_session:
            # Simulate a timeout error
            mock_session.return_value.__aenter__.side_effect = ServerTimeoutError(
                "Timeout"
            )

            mock_request = MagicMock()
            mock_request.path = "/test"
            mock_request.query_string = ""
            mock_request.method = "GET"
            mock_request.headers = {}
            mock_request.read = AsyncMock(return_value=b"")

            response = await proxy_request(mock_request, "http://backend:8000")

            assert response.status == 503

    async def test_connection_refused_error(self):
        """Test that connection refused errors are handled gracefully."""
        with patch("gateway.main.ClientSession") as mock_session:
            # Simulate a connection refused error
            mock_session.return_value.__aenter__.side_effect = ConnectionRefusedError(
                "Connection refused"
            )

            mock_request = MagicMock()
            mock_request.path = "/test"
            mock_request.query_string = ""
            mock_request.method = "GET"
            mock_request.headers = {}
            mock_request.read = AsyncMock(return_value=b"")

            response = await proxy_request(mock_request, "http://backend:8000")

            assert response.status == 503
