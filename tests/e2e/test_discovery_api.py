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
            "session_maker": MagicMock(),
        }
        request.headers = {}  # No Authorization header

        response = await discover_handler(request)

        assert response.status == 401

    async def test_like_handler_requires_auth(self):
        """Test that like endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "session_maker": MagicMock(),
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
                "session_maker": MagicMock(),
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
                "session_maker": MagicMock(),
            }
            request.json = AsyncMock(return_value={})

            response = await pass_handler(request)

            assert response.status == 400

    async def test_matches_handler_requires_auth(self):
        """Test that matches endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "session_maker": MagicMock(),
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
            "session_maker": MagicMock(),
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
                "session_maker": MagicMock(),
            }
            request.json = AsyncMock(return_value={})

            response = await add_favorite_handler(request)

            assert response.status == 400

    async def test_remove_favorite_requires_auth(self):
        """Test that remove favorite endpoint requires authentication."""
        request = MagicMock()
        request.app = {
            "config": MagicMock(spec=BotConfig),
            "session_maker": MagicMock(),
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
            "session_maker": MagicMock(),
        }
        request.headers = {}
        request.query = {}

        response = await get_favorites_handler(request)

        assert response.status == 401


@pytest.mark.asyncio
class TestDiscoveryFilters:
    """Test discovery filter parameters."""

    async def test_discover_with_filters(self):
        """Test discover endpoint with various filters."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock(),
            }
            request.query = {
                "limit": "20",
                "cursor": "100",
                "age_min": "25",
                "age_max": "35",
                "goal": "dating",
                "height_min": "160",
                "height_max": "180",
                "has_children": "false",
                "smoking": "false",
                "verified_only": "true",
            }

            # Mock database session and repository
            mock_session = MagicMock()
            mock_repository = MagicMock()

            user = User(id=1, tg_id=12345, username="test")
            mock_repository.get_user_by_tg_id = AsyncMock(return_value=user)
            mock_repository.find_candidates = AsyncMock(return_value=([], None))

            # Mock async context manager
            session_maker = MagicMock()
            session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            session_maker.return_value.__aexit__ = AsyncMock(return_value=None)

            request.app["session_maker"] = session_maker

            with patch("bot.api.ProfileRepository", return_value=mock_repository):
                response = await discover_handler(request)

            # Verify find_candidates was called with correct parameters
            assert mock_repository.find_candidates.called
            call_args = mock_repository.find_candidates.call_args
            assert call_args.kwargs["age_min"] == 25
            assert call_args.kwargs["age_max"] == 35
            assert call_args.kwargs["goal"] == "dating"
            assert call_args.kwargs["height_min"] == 160
            assert call_args.kwargs["height_max"] == 180
            assert call_args.kwargs["has_children"] is False
            assert call_args.kwargs["smoking"] is False
            assert call_args.kwargs["verified_only"] is True


@pytest.mark.asyncio
class TestLikeInteractionTypes:
    """Test like interaction type validation."""

    async def test_like_valid_type_like(self):
        """Test like endpoint accepts 'like' type."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock(),
            }
            request.json = AsyncMock(return_value={"target_id": 123, "type": "like"})

            # Mock database session
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

            with patch("bot.api.ProfileRepository", return_value=mock_repository):
                response = await like_handler(request)

            assert response.status == 200
            assert mock_repository.create_interaction.called

    async def test_like_valid_type_superlike(self):
        """Test like endpoint accepts 'superlike' type."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig, jwt_secret="secret"),
                "session_maker": MagicMock(),
            }
            request.json = AsyncMock(
                return_value={"target_id": 123, "type": "superlike"}
            )

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

            with patch("bot.api.ProfileRepository", return_value=mock_repository):
                response = await like_handler(request)

            assert response.status == 200

    async def test_like_invalid_type(self):
        """Test like endpoint rejects invalid type."""
        with patch("bot.api.authenticate_request", AsyncMock(return_value=12345)):
            request = MagicMock()
            request.app = {
                "config": MagicMock(spec=BotConfig),
                "session_maker": MagicMock(),
            }
            request.json = AsyncMock(return_value={"target_id": 123, "type": "invalid"})

            response = await like_handler(request)

            assert response.status == 400
