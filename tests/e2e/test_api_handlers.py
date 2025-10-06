"""End-to-end tests for API handlers using API Gateway client.

These tests verify that bot API handlers correctly interact with the API Gateway client,
following the thin client architecture pattern without direct database access.
Tests cover profile, discovery, matching, and favorites operations.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
class TestThinClientProfileOperations:
    """Test profile operations through thin client architecture."""

    async def test_get_profile_through_api_gateway(self):
        """Test getting profile through API Gateway client."""
        from bot.api import create_jwt_token, get_profile_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        # Mock API Gateway client response
        mock_profile = {
            "name": "Test User",
            "age": 30,
            "birth_date": "1994-01-01",
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
            "bio": "Test bio",
            "city": "Moscow",
            "photos": [{"url": "/photos/test.jpg", "sort_order": 0}],
        }

        mock_api_client = AsyncMock()
        mock_api_client.get_profile = AsyncMock(return_value=mock_profile)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}

        response = await get_profile_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert "profile" in data
        assert data["profile"]["name"] == "Test User"
        mock_api_client.get_profile.assert_called_once_with(user_id)

    async def test_update_profile_through_api_gateway(self):
        """Test updating profile through API Gateway client."""
        from bot.api import create_jwt_token, update_profile_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        update_data = {"bio": "Updated bio", "city": "Saint Petersburg"}

        mock_api_client = AsyncMock()
        mock_api_client.update_profile = AsyncMock(return_value={"success": True})

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.json = AsyncMock(return_value=update_data)

        response = await update_profile_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        mock_api_client.update_profile.assert_called_once_with(user_id, update_data)


@pytest.mark.asyncio
class TestThinClientDiscoveryOperations:
    """Test discovery operations through thin client architecture."""

    async def test_discover_candidates_through_api_gateway(self):
        """Test discovering candidates through API Gateway client."""
        from bot.api import create_jwt_token, discover_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_candidates = {
            "profiles": [
                {
                    "id": 1,
                    "name": "Candidate 1",
                    "age": 28,
                    "gender": "female",
                    "city": "Moscow",
                    "photos": [{"url": "/photos/c1.jpg"}],
                },
                {
                    "id": 2,
                    "name": "Candidate 2",
                    "age": 32,
                    "gender": "female",
                    "city": "Moscow",
                    "photos": [{"url": "/photos/c2.jpg"}],
                },
            ],
            "next_cursor": 3,
            "count": 2,
        }

        mock_api_client = AsyncMock()
        mock_api_client.find_candidates = AsyncMock(return_value=mock_candidates)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.query = {"limit": "10", "age_min": "25", "age_max": "35"}

        response = await discover_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert "profiles" in data
        assert len(data["profiles"]) == 2
        assert data["profiles"][0]["name"] == "Candidate 1"
        # Verify filters were passed correctly
        call_args = mock_api_client.find_candidates.call_args
        assert call_args[0][0] == user_id
        filters = call_args[0][1]
        assert filters["age_min"] == 25
        assert filters["age_max"] == 35

    async def test_like_user_through_api_gateway(self):
        """Test liking a user through API Gateway client."""
        from bot.api import create_jwt_token, like_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        target_id = 67890
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_response = {"success": True, "match_id": 999}

        mock_api_client = AsyncMock()
        mock_api_client.create_interaction = AsyncMock(return_value=mock_response)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.json = AsyncMock(return_value={"target_id": target_id, "type": "like"})

        response = await like_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        assert data["match_id"] == 999
        mock_api_client.create_interaction.assert_called_once_with(
            user_id, target_id, "like"
        )

    async def test_pass_user_through_api_gateway(self):
        """Test passing on a user through API Gateway client."""
        from bot.api import create_jwt_token, pass_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        target_id = 67890
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_response = {"success": True}

        mock_api_client = AsyncMock()
        mock_api_client.create_interaction = AsyncMock(return_value=mock_response)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.json = AsyncMock(return_value={"target_id": target_id})

        response = await pass_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        mock_api_client.create_interaction.assert_called_once_with(
            user_id, target_id, "pass"
        )


@pytest.mark.asyncio
class TestThinClientMatchesOperations:
    """Test matches operations through thin client architecture."""

    async def test_get_matches_through_api_gateway(self):
        """Test getting matches through API Gateway client."""
        from bot.api import create_jwt_token, matches_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_matches = {
            "matches": [
                {
                    "match_id": 1,
                    "created_at": "2024-01-01T12:00:00",
                    "profile": {
                        "id": 100,
                        "name": "Match 1",
                        "age": 29,
                        "photos": [{"url": "/photos/m1.jpg"}],
                    },
                }
            ],
            "next_cursor": None,
            "count": 1,
        }

        mock_api_client = AsyncMock()
        mock_api_client.get_matches = AsyncMock(return_value=mock_matches)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.query = {"limit": "20"}

        response = await matches_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert "matches" in data
        assert len(data["matches"]) == 1
        assert data["matches"][0]["profile"]["name"] == "Match 1"
        mock_api_client.get_matches.assert_called_once_with(user_id, 20, None)


@pytest.mark.asyncio
class TestThinClientFavoritesOperations:
    """Test favorites operations through thin client architecture."""

    async def test_add_favorite_through_api_gateway(self):
        """Test adding to favorites through API Gateway client."""
        from bot.api import add_favorite_handler, create_jwt_token
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        target_id = 67890
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_response = {"success": True, "favorite_id": 555}

        mock_api_client = AsyncMock()
        mock_api_client.add_favorite = AsyncMock(return_value=mock_response)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.json = AsyncMock(return_value={"target_id": target_id})

        response = await add_favorite_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        assert data["favorite_id"] == 555
        mock_api_client.add_favorite.assert_called_once_with(user_id, target_id)

    async def test_remove_favorite_through_api_gateway(self):
        """Test removing from favorites through API Gateway client."""
        from bot.api import create_jwt_token, remove_favorite_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        target_id = 67890
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_response = {"success": True}

        mock_api_client = AsyncMock()
        mock_api_client.remove_favorite = AsyncMock(return_value=mock_response)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.match_info = {"target_id": str(target_id)}

        response = await remove_favorite_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert data["success"] is True
        mock_api_client.remove_favorite.assert_called_once_with(user_id, target_id)

    async def test_get_favorites_through_api_gateway(self):
        """Test getting favorites through API Gateway client."""
        from bot.api import create_jwt_token, get_favorites_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        mock_favorites = {
            "favorites": [
                {
                    "favorite_id": 10,
                    "created_at": "2024-01-01T12:00:00",
                    "profile": {
                        "id": 200,
                        "name": "Favorite User",
                        "age": 27,
                        "photos": [{"url": "/photos/fav.jpg"}],
                    },
                }
            ],
            "next_cursor": None,
            "count": 1,
        }

        mock_api_client = AsyncMock()
        mock_api_client.get_favorites = AsyncMock(return_value=mock_favorites)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}
        request.query = {"limit": "20"}

        response = await get_favorites_handler(request)

        assert response.status == 200
        data = json.loads(response.body)
        assert "favorites" in data
        assert len(data["favorites"]) == 1
        assert data["favorites"][0]["profile"]["name"] == "Favorite User"
        mock_api_client.get_favorites.assert_called_once_with(user_id, 20, None)


@pytest.mark.asyncio
class TestThinClientErrorHandling:
    """Test error handling in thin client architecture."""

    async def test_api_gateway_unavailable(self):
        """Test handling when API Gateway is unavailable."""
        from bot.api import create_jwt_token, get_profile_handler
        from bot.api_client import APIGatewayError
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        # Mock API Gateway returning error
        mock_api_client = AsyncMock()
        mock_api_client.get_profile = AsyncMock(
            side_effect=APIGatewayError("Service unavailable", status_code=503)
        )

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}

        response = await get_profile_handler(request)

        assert response.status == 503
        data = json.loads(response.body)
        assert "error" in data
        assert data["error"]["code"] == "gateway_error"

    async def test_profile_not_found(self):
        """Test handling when profile is not found."""
        from bot.api import create_jwt_token, get_profile_handler
        from bot.config import BotConfig

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
        )

        user_id = 12345
        token = create_jwt_token(user_id, config.jwt_secret)

        # Mock API Gateway returning None (profile not found)
        mock_api_client = AsyncMock()
        mock_api_client.get_profile = AsyncMock(return_value=None)

        request = MagicMock()
        request.app = {"config": config, "api_client": mock_api_client}
        request.headers = {"Authorization": f"Bearer {token}"}

        response = await get_profile_handler(request)

        assert response.status == 404
        data = json.loads(response.body)
        assert "error" in data
        assert data["error"]["code"] == "not_found"


class TestThinClientAppInitialization:
    """Test app initialization in thin client mode."""

    def test_create_app_requires_api_client(self, tmp_path):
        """Test that create_app requires api_client parameter."""
        import os
        import warnings

        from bot.api import create_app
        from bot.config import BotConfig

        storage_path = str(tmp_path / "photos")
        os.makedirs(storage_path, exist_ok=True)

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
            photo_storage_path=storage_path,
        )

        mock_api_client = MagicMock()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            app = create_app(config, mock_api_client)

        assert app is not None
        assert app["config"] == config
        assert app["api_client"] == mock_api_client

    def test_create_app_without_api_client_fails(self, tmp_path):
        """Test that create_app fails without api_client."""
        import os
        import warnings

        from bot.api import create_app
        from bot.config import BotConfig

        storage_path = str(tmp_path / "photos")
        os.makedirs(storage_path, exist_ok=True)

        config = BotConfig(
            api_gateway_url="http://localhost:8080",
            token="test:token",
            jwt_secret="test-secret",
            photo_storage_path=storage_path,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValueError, match="api_client is required"):
                create_app(config, None)
