"""Tests for bot handler business logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.main import handle_interaction


@pytest.mark.asyncio
class TestHandleInteraction:
    """Test suite for handle_interaction business logic."""

    async def test_handle_like_creates_interaction(self) -> None:
        """Test that like action creates an interaction."""
        # Mock message and bot
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repositories
        interaction_repo = MagicMock()
        interaction_repo.create = AsyncMock()
        interaction_repo.check_mutual_like = AsyncMock(return_value=False)
        
        match_repo = MagicMock()
        profile_repo = MagicMock()
        
        # Mock repository getters
        with patch("bot.main.get_interaction_repository", return_value=interaction_repo), \
             patch("bot.main.get_match_repository", return_value=match_repo), \
             patch("bot.main.get_repository", return_value=profile_repo):
            
            await handle_interaction(message, from_user_id=12345, to_user_id=67890, action="like")
        
        # Verify interaction was created
        interaction_repo.create.assert_called_once_with(12345, 67890, "like")
        
        # Verify mutual like was checked
        interaction_repo.check_mutual_like.assert_called_once_with(12345, 67890)
        
        # Verify response was sent
        message.answer.assert_called_once()
        assert "Симпатия отправлена" in message.answer.call_args[0][0]

    async def test_handle_dislike_creates_interaction(self) -> None:
        """Test that dislike action creates an interaction."""
        # Mock message and bot
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repositories
        interaction_repo = MagicMock()
        interaction_repo.create = AsyncMock()
        
        match_repo = MagicMock()
        profile_repo = MagicMock()
        
        # Mock repository getters
        with patch("bot.main.get_interaction_repository", return_value=interaction_repo), \
             patch("bot.main.get_match_repository", return_value=match_repo), \
             patch("bot.main.get_repository", return_value=profile_repo):
            
            await handle_interaction(message, from_user_id=12345, to_user_id=67890, action="dislike")
        
        # Verify interaction was created
        interaction_repo.create.assert_called_once_with(12345, 67890, "dislike")
        
        # Verify response was sent
        message.answer.assert_called_once()
        assert "Понятно" in message.answer.call_args[0][0]

    async def test_handle_mutual_like_creates_match(self) -> None:
        """Test that mutual like creates a match and notifies both users."""
        # Mock message and bot
        message = MagicMock()
        message.bot = MagicMock()
        message.bot.send_message = AsyncMock()
        message.answer = AsyncMock()
        
        # Mock profiles
        from bot.main import Profile
        user_profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
        )
        matched_profile = Profile(
            user_id=67890,
            name="Bob",
            age=28,
            gender="male",
            preference="female",
        )
        
        # Mock repositories
        interaction_repo = MagicMock()
        interaction_repo.create = AsyncMock()
        interaction_repo.check_mutual_like = AsyncMock(return_value=True)
        
        match_repo = MagicMock()
        match_repo.create = AsyncMock()
        
        profile_repo = MagicMock()
        profile_repo.get = AsyncMock(side_effect=lambda uid: user_profile if uid == 12345 else matched_profile)
        
        # Mock photo sending functions
        with patch("bot.main.get_interaction_repository", return_value=interaction_repo), \
             patch("bot.main.get_match_repository", return_value=match_repo), \
             patch("bot.main.get_repository", return_value=profile_repo), \
             patch("bot.main._send_photo_reply", new_callable=AsyncMock) as mock_send_photo_reply, \
             patch("bot.main._send_profile_photo", new_callable=AsyncMock) as mock_send_profile_photo:
            
            await handle_interaction(message, from_user_id=12345, to_user_id=67890, action="like")
        
        # Verify interaction was created
        interaction_repo.create.assert_called_once_with(12345, 67890, "like")
        
        # Verify mutual like was checked
        interaction_repo.check_mutual_like.assert_called_once_with(12345, 67890)
        
        # Verify match was created
        match_repo.create.assert_called_once_with(12345, 67890)
        
        # Verify both users were notified
        message.answer.assert_called_once()
        assert "взаимная симпатия" in message.answer.call_args[0][0]
        
        message.bot.send_message.assert_called_once()
        assert message.bot.send_message.call_args[1]["chat_id"] == 67890
        assert "взаимная симпатия" in message.bot.send_message.call_args[1]["text"]

    async def test_handle_interaction_with_repository_error(self) -> None:
        """Test that repository errors are handled gracefully."""
        # Mock message and bot
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repository getter to raise error
        with patch("bot.main.get_interaction_repository", side_effect=RuntimeError("Repository unavailable")):
            await handle_interaction(message, from_user_id=12345, to_user_id=67890, action="like")
        
        # Verify error message was sent
        message.answer.assert_called_once()
        assert "внутренняя ошибка" in message.answer.call_args[0][0]

    async def test_handle_interaction_with_create_error(self) -> None:
        """Test that interaction creation errors are handled gracefully."""
        # Mock message and bot
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repositories
        interaction_repo = MagicMock()
        interaction_repo.create = AsyncMock(side_effect=Exception("Database error"))
        
        match_repo = MagicMock()
        profile_repo = MagicMock()
        
        # Mock repository getters
        with patch("bot.main.get_interaction_repository", return_value=interaction_repo), \
             patch("bot.main.get_match_repository", return_value=match_repo), \
             patch("bot.main.get_repository", return_value=profile_repo):
            
            await handle_interaction(message, from_user_id=12345, to_user_id=67890, action="like")
        
        # Verify error message was sent
        message.answer.assert_called_once()
        assert "Не удалось сохранить" in message.answer.call_args[0][0]
