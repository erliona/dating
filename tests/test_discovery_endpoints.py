"""Tests for discovery service endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import web

from services.discovery.main import get_candidates, get_likes, get_matches, swipe_user


@pytest.mark.asyncio
class TestDiscoveryEndpoints:
    """Test discovery service endpoints."""

    def setup_method(self):
        """Setup test instance."""
        self.app = web.Application()
        self.app["data_service_url"] = "http://data-service:8088"

    async def test_get_candidates_success(self):
        """Test successful candidate retrieval."""
        request = Mock()
        request.query = {"user_id": "123", "limit": "10"}
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "candidates": [
                    {"id": 1, "name": "Alice", "age": 25},
                    {"id": 2, "name": "Bob", "age": 30},
                ],
                "cursor": "next_page_token",
            }

            response = await get_candidates(request)
            assert response.status == 200

            data = await response.json()
            assert "candidates" in data
            assert len(data["candidates"]) == 2

    async def test_get_candidates_missing_user_id(self):
        """Test candidate retrieval without user_id."""
        request = Mock()
        request.query = {"limit": "10"}
        request.app = self.app

        response = await get_candidates(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_swipe_user_like(self):
        """Test swipe like action."""
        request = Mock()
        request.json = AsyncMock(
            return_value={"user_id": 123, "target_user_id": 456, "action": "like"}
        )
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {"is_match": True, "match_id": "match_123"}

            with patch("services.discovery.main.event_publisher") as mock_publisher:
                mock_publisher.publish_match_event = AsyncMock()

                response = await swipe_user(request)
                assert response.status == 200

                data = await response.json()
                assert data["is_match"] is True

    async def test_swipe_user_pass(self):
        """Test swipe pass action."""
        request = Mock()
        request.json = AsyncMock(
            return_value={"user_id": 123, "target_user_id": 456, "action": "pass"}
        )
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {"is_match": False}

            response = await swipe_user(request)
            assert response.status == 200

            data = await response.json()
            assert data["is_match"] is False

    async def test_swipe_user_invalid_action(self):
        """Test swipe with invalid action."""
        request = Mock()
        request.json = AsyncMock(return_value={"user_id": 123, "action": "invalid"})
        request.app = self.app

        response = await swipe_user(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_get_likes_success(self):
        """Test successful likes retrieval."""
        request = Mock()
        request.query = {"user_id": "123", "limit": "20"}
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "likes": [
                    {"id": 1, "name": "Alice", "age": 25},
                    {"id": 2, "name": "Bob", "age": 30},
                ]
            }

            response = await get_likes(request)
            assert response.status == 200

            data = await response.json()
            assert "likes" in data
            assert len(data["likes"]) == 2

    async def test_get_likes_missing_user_id(self):
        """Test likes retrieval without user_id."""
        request = Mock()
        request.query = {"limit": "20"}
        request.app = self.app

        response = await get_likes(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_get_matches_success(self):
        """Test successful matches retrieval."""
        request = Mock()
        request.query = {"user_id": "123", "limit": "20"}
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "matches": [
                    {"id": 1, "name": "Alice", "age": 25},
                    {"id": 2, "name": "Bob", "age": 30},
                ]
            }

            response = await get_matches(request)
            assert response.status == 200

            data = await response.json()
            assert "matches" in data
            assert len(data["matches"]) == 2

    async def test_get_candidates_with_geocoding(self):
        """Test candidate retrieval with geocoding."""
        request = Mock()
        request.query = {"user_id": "123", "lat": "40.7128", "lon": "-74.0060"}
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {"candidates": [{"id": 1, "name": "Alice"}]}

            with patch("services.discovery.geocoding.reverse_geocode") as mock_geocode:
                mock_geocode.return_value = {
                    "city": "New York",
                    "country": "United States",
                }

                response = await get_candidates(request)
                assert response.status == 200

                # Verify geocoding was called
                mock_geocode.assert_called_once_with(40.7128, -74.0060)

    async def test_get_candidates_with_filters(self):
        """Test candidate retrieval with filters."""
        request = Mock()
        request.query = {
            "user_id": "123",
            "age_min": "25",
            "age_max": "35",
            "max_distance_km": "50",
            "verified_only": "true",
        }
        request.app = self.app

        with patch("services.discovery.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "candidates": [{"id": 1, "name": "Alice", "age": 30}]
            }

            response = await get_candidates(request)
            assert response.status == 200

            # Verify filters were passed to data service
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert "age_min" in call_args[1]["params"]
            assert "age_max" in call_args[1]["params"]
            assert "max_distance_km" in call_args[1]["params"]
            assert "verified_only" in call_args[1]["params"]
