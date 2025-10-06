"""Tests to verify CORS configuration fix in API Gateway."""

import pytest
from aiohttp import web

pytestmark = pytest.mark.e2e

from gateway.main import create_app


class TestCORSFix:
    """Tests to verify that CORS configuration works correctly."""

    def test_create_app_with_wildcard_domain(self):
        """Test that create_app works with '*' as webapp_domain."""
        config = {
            "auth_service_url": "http://auth:8081",
            "profile_service_url": "http://profile:8082",
            "discovery_service_url": "http://discovery:8083",
            "media_service_url": "http://media:8084",
            "chat_service_url": "http://chat:8085",
            "admin_service_url": "http://admin:8086",
            "notification_service_url": "http://notification:8087",
            "webapp_domain": "*",  # This was causing ValueError before fix
        }

        # This should not raise ValueError anymore
        app = create_app(config)

        assert isinstance(app, web.Application)
        assert app["config"]["webapp_domain"] == "*"

    def test_create_app_with_specific_domain(self):
        """Test that create_app works with a specific domain."""
        config = {
            "auth_service_url": "http://auth:8081",
            "profile_service_url": "http://profile:8082",
            "discovery_service_url": "http://discovery:8083",
            "media_service_url": "http://media:8084",
            "chat_service_url": "http://chat:8085",
            "admin_service_url": "http://admin:8086",
            "notification_service_url": "http://notification:8087",
            "webapp_domain": "https://example.com",
        }

        app = create_app(config)

        assert isinstance(app, web.Application)
        assert app["config"]["webapp_domain"] == "https://example.com"

    def test_api_routes_have_cors(self):
        """Test that /api/* routes have CORS enabled (multiple methods)."""
        config = {
            "auth_service_url": "http://auth:8081",
            "profile_service_url": "http://profile:8082",
            "discovery_service_url": "http://discovery:8083",
            "media_service_url": "http://media:8084",
            "chat_service_url": "http://chat:8085",
            "admin_service_url": "http://admin:8086",
            "notification_service_url": "http://notification:8087",
            "webapp_domain": "*",
        }

        app = create_app(config)
        routes = list(app.router.routes())

        # Check that /api/auth/token has multiple methods (GET, POST, etc.)
        api_auth_routes = [r for r in routes if "/api/auth/token" in str(r.resource)]

        # Should have at least GET and POST methods
        methods = {r.method for r in api_auth_routes}
        assert (
            "GET" in methods and "POST" in methods
        ), f"Expected multiple methods for /api/auth/token, got: {methods}"

    def test_internal_routes_use_wildcard_method(self):
        """Test that internal routes (without CORS) use '*' method."""
        config = {
            "auth_service_url": "http://auth:8081",
            "profile_service_url": "http://profile:8082",
            "discovery_service_url": "http://discovery:8083",
            "media_service_url": "http://media:8084",
            "chat_service_url": "http://chat:8085",
            "admin_service_url": "http://admin:8086",
            "notification_service_url": "http://notification:8087",
            "webapp_domain": "*",
        }

        app = create_app(config)
        routes = list(app.router.routes())

        # Check that internal routes like /auth/{tail} use '*' method
        internal_routes = [
            r
            for r in routes
            if "/auth/" in str(r.resource) and "/api/auth/" not in str(r.resource)
        ]

        assert any(
            r.method == "*" for r in internal_routes
        ), "Expected internal routes to use '*' method"
