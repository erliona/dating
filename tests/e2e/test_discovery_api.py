"""Tests for discovery API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

pytestmark = pytest.mark.e2e

from bot.api import (
    add_favorite_handler,
    discover_handler,
    get_favorites_handler,
    like_handler,
    matches_handler,
    pass_handler,
    remove_favorite_handler,
)
from bot.config import BotConfig
from bot.db import Profile, User


@pytest.mark.asyncio
class TestDiscoveryEndpoints:
    """Test discovery API endpoints."""

    async def test_discover_handler_requires_auth(self):
        """Test that discover endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}  # No Authorization header
        request.query = {}

        response = await discover_handler(request)

        assert response.status == 401

    async def test_like_handler_requires_auth(self):
        """Test that like endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}
        request.json = AsyncMock(return_value={"target_id": 123})

        response = await like_handler(request)

        assert response.status == 401

    async def test_like_handler_requires_target_id(self):
        """Test that like endpoint requires target_id."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig),
                "api_client": AsyncMock(),
            }
            request.json = AsyncMock(return_value={})  # No target_id

            response = await like_handler(request)

            assert response.status == 400

    async def test_pass_handler_requires_target_id(self):
        """Test that pass endpoint requires target_id."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig),
                "api_client": AsyncMock(),
            }
            request.json = AsyncMock(return_value={})

            response = await pass_handler(request)

            assert response.status == 400

    async def test_matches_handler_requires_auth(self):
        """Test that matches endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}
        request.query = {}

        response = await matches_handler(request)

        assert response.status == 401

    async def test_add_favorite_requires_auth(self):
        """Test that add favorite endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}
        request.json = AsyncMock(return_value={"target_id": 123})

        response = await add_favorite_handler(request)

        assert response.status == 401

    async def test_add_favorite_requires_target_id(self):
        """Test that add favorite endpoint requires target_id."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig),
                "api_client": AsyncMock(),
            }
            request.json = AsyncMock(return_value={})

            response = await add_favorite_handler(request)

            assert response.status == 400

    async def test_remove_favorite_requires_auth(self):
        """Test that remove favorite endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}
        request.match_info = {"target_id": "123"}

        response = await remove_favorite_handler(request)

        assert response.status == 401

    async def test_get_favorites_requires_auth(self):
        """Test that get favorites endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "api_client": AsyncMock(),
        }
        request.headers = {}
        request.query = {}

        response = await get_favorites_handler(request)

        assert response.status == 401


@pytest.mark.asyncio
class TestDiscoveryFilters:
    """Test discovery filter parameters."""

    @pytest.mark.skip(
        reason="Test uses old architecture with ProfileRepository - bot now uses thin client with API Gateway"
    )
    async def test_discover_with_filters(self):
        """Test discover endpoint with various filters.
        
        DEPRECATED: This test is for old architecture where bot accessed database directly.
        Discovery now happens: Bot API Handler -> API Gateway -> Discovery Service
        Filter testing should be done in discovery service integration tests.
        """
        pass


@pytest.mark.asyncio
class TestLikeInteractionTypes:
    """Test like interaction type validation."""

    @pytest.mark.skip(
        reason="Test uses old architecture with ProfileRepository - bot now uses thin client with API Gateway"
    )
    async def test_like_valid_type_like(self):
        """Test like endpoint accepts 'like' type.
        
        DEPRECATED: Uses old architecture. Interaction type validation now happens in discovery service.
        """
        pass

    @pytest.mark.skip(
        reason="Test uses old architecture with ProfileRepository - bot now uses thin client with API Gateway"
    )
    async def test_like_valid_type_superlike(self):
        """Test like endpoint accepts 'superlike' type.
        
        DEPRECATED: Uses old architecture. Interaction type validation now happens in discovery service.
        """
        pass

    async def test_like_invalid_type(self):
        """Test like endpoint rejects invalid type."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig),
                "api_client": AsyncMock(),
            }
            request.json = AsyncMock(return_value={"target_id": 123, "type": "invalid"})

            response = await like_handler(request)

            assert response.status == 400
