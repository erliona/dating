"""Tests for webapp_handler to ensure profile creation from mini-app works."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.main import webapp_handler


@pytest.mark.asyncio
class TestWebAppHandler:
    """Test suite for webapp_handler."""

    async def test_webapp_handler_creates_profile_from_valid_data(self) -> None:
        """Test that webapp_handler correctly processes valid profile data."""
        # Mock message with web_app_data
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        # Create valid profile data
        profile_data = {
            "name": "Alice",
            "age": 25,
            "gender": "female",
            "preference": "male",
            "bio": "Test bio",
            "location": "Moscow",
            "interests": ["music", "travel"],
            "goal": "serious",
            "photo_url": "https://example.com/photo.jpg"
        }
        
        # Mock web_app_data
        web_app_data = MagicMock()
        web_app_data.data = json.dumps(profile_data)
        message.web_app_data = web_app_data
        
        # Mock finalize_profile
        with patch("bot.main.finalize_profile", new_callable=AsyncMock) as mock_finalize:
            await webapp_handler(message)
        
        # Verify finalize_profile was called with correct profile
        mock_finalize.assert_called_once()
        call_args = mock_finalize.call_args
        assert call_args[0][0] == message  # First arg is message
        profile = call_args[0][1]  # Second arg is profile
        
        assert profile.user_id == 12345
        assert profile.name == "Alice"
        assert profile.age == 25
        assert profile.gender == "female"
        assert profile.preference == "male"
        assert profile.bio == "Test bio"
        assert profile.location == "Moscow"
        assert profile.interests == ["music", "travel"]
        assert profile.goal == "serious"
        assert profile.photo_url == "https://example.com/photo.jpg"

    async def test_webapp_handler_handles_missing_web_app_data(self) -> None:
        """Test that webapp_handler handles missing web_app_data gracefully."""
        # Mock message without web_app_data
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.web_app_data = None
        
        await webapp_handler(message)
        
        # Verify error message was sent
        message.answer.assert_called_once()
        assert "Не удалось получить данные" in message.answer.call_args[0][0]

    async def test_webapp_handler_handles_delete_action(self) -> None:
        """Test that webapp_handler correctly handles delete action."""
        # Mock message with delete action
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        delete_data = {"action": "delete"}
        web_app_data = MagicMock()
        web_app_data.data = json.dumps(delete_data)
        message.web_app_data = web_app_data
        
        # Mock repository
        mock_repository = MagicMock()
        mock_repository.delete = AsyncMock(return_value=True)
        
        with patch("bot.main.get_repository", return_value=mock_repository):
            await webapp_handler(message)
        
        # Verify delete was called
        mock_repository.delete.assert_called_once_with(12345)
        
        # Verify response was sent
        message.answer.assert_called_once()
        assert "удалён" in message.answer.call_args[0][0].lower()

    async def test_webapp_handler_handles_settings_action(self) -> None:
        """Test that webapp_handler correctly handles settings update action."""
        # Mock message with settings action
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        settings_data = {
            "action": "update_settings",
            "lang": "ru",
            "show_location": True,
            "notify_matches": True
        }
        web_app_data = MagicMock()
        web_app_data.data = json.dumps(settings_data)
        message.web_app_data = web_app_data
        
        # Mock settings repository
        mock_settings_repo = MagicMock()
        mock_settings_repo.upsert = AsyncMock()
        
        with patch("bot.main.get_settings_repository", return_value=mock_settings_repo):
            await webapp_handler(message)
        
        # Verify upsert was called with correct data
        mock_settings_repo.upsert.assert_called_once()
        call_args = mock_settings_repo.upsert.call_args
        assert call_args[0][0] == 12345
        assert call_args[1]["lang"] == "ru"
        assert call_args[1]["show_location"] is True
        assert call_args[1]["notify_matches"] is True
        
        # Verify success response was sent
        message.answer.assert_called_once()
        assert "сохранены" in message.answer.call_args[0][0].lower()

    async def test_webapp_handler_handles_invalid_json(self) -> None:
        """Test that webapp_handler handles invalid JSON gracefully."""
        # Mock message with invalid JSON
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        
        web_app_data = MagicMock()
        web_app_data.data = "invalid json {{{{"
        message.web_app_data = web_app_data
        
        await webapp_handler(message)
        
        # Verify error message was sent
        message.answer.assert_called_once()
        assert "Не удалось обработать данные" in message.answer.call_args[0][0]

    async def test_webapp_handler_handles_missing_required_fields(self) -> None:
        """Test that webapp_handler handles missing required fields."""
        # Mock message with incomplete profile data
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        incomplete_data = {
            "name": "Alice"
            # Missing age, gender, preference
        }
        web_app_data = MagicMock()
        web_app_data.data = json.dumps(incomplete_data)
        message.web_app_data = web_app_data
        
        await webapp_handler(message)
        
        # Verify error message was sent about missing field or invalid data
        message.answer.assert_called_once()
        error_msg = message.answer.call_args[0][0]
        # The error message could be about validation or processing failure
        assert any(word in error_msg.lower() for word in ["данные", "некорректн", "age", "gender"])

    async def test_webapp_handler_handles_minimal_valid_profile(self) -> None:
        """Test that webapp_handler handles minimal valid profile data."""
        # Mock message with minimal profile data
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()
        message.bot = MagicMock()
        
        minimal_data = {
            "name": "Bob",
            "age": 30,
            "gender": "male",
            "preference": "female"
        }
        web_app_data = MagicMock()
        web_app_data.data = json.dumps(minimal_data)
        message.web_app_data = web_app_data
        
        # Mock finalize_profile
        with patch("bot.main.finalize_profile", new_callable=AsyncMock) as mock_finalize:
            await webapp_handler(message)
        
        # Verify finalize_profile was called
        mock_finalize.assert_called_once()
        profile = mock_finalize.call_args[0][1]
        
        assert profile.user_id == 12345
        assert profile.name == "Bob"
        assert profile.age == 30
        assert profile.gender == "male"
        assert profile.preference == "female"
        assert profile.bio is None
        assert profile.location is None
        assert profile.interests == []
        assert profile.goal is None
        assert profile.photo_url is None
