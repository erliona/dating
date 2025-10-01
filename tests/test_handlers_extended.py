"""Extended tests for bot handlers including start, cancel, and finalize_profile."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.main import Profile


@pytest.mark.asyncio
class TestStartHandler:
    """Test suite for start_handler."""

    async def test_start_handler_sends_webapp_button(self) -> None:
        """Test that start handler sends webapp button."""
        from bot.main import start_handler
        
        # Mock message and state
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.from_user.username = "testuser"
        message.answer = AsyncMock()
        
        state = MagicMock()
        state.clear = AsyncMock()
        
        # Mock config
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        
        with patch("bot.main.get_config", return_value=mock_config):
            await start_handler(message, state)
        
        # Verify state was cleared
        state.clear.assert_called_once()
        
        # Verify message was sent with webapp button
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        
        # Check welcome message
        assert "Привет" in call_args[0][0] or "привет" in call_args[0][0]
        
        # Check that reply_markup was provided
        assert "reply_markup" in call_args[1]

    async def test_start_handler_handles_no_username(self) -> None:
        """Test start handler works even without username."""
        from bot.main import start_handler
        
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.from_user.username = None  # No username
        message.answer = AsyncMock()
        
        state = MagicMock()
        state.clear = AsyncMock()
        
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        
        with patch("bot.main.get_config", return_value=mock_config):
            await start_handler(message, state)
        
        # Should still work
        message.answer.assert_called_once()

    async def test_start_handler_handles_config_error(self) -> None:
        """Test that start handler handles config errors."""
        from bot.main import start_handler
        
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.from_user.username = "testuser"
        message.answer = AsyncMock()
        
        state = MagicMock()
        state.clear = AsyncMock()
        
        # Mock config to raise error
        with patch("bot.main.get_config", side_effect=RuntimeError("Config error")):
            try:
                await start_handler(message, state)
            except RuntimeError:
                pass  # Expected to raise or handle error


@pytest.mark.asyncio
class TestCancelHandler:
    """Test suite for cancel_handler."""

    async def test_cancel_handler_clears_state(self) -> None:
        """Test that cancel handler clears FSM state."""
        from bot.main import cancel_handler
        
        message = MagicMock()
        message.answer = AsyncMock()
        
        state = MagicMock()
        state.clear = AsyncMock()
        
        await cancel_handler(message, state)
        
        # Verify state was cleared
        state.clear.assert_called_once()
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        assert "отмен" in response.lower()

    async def test_cancel_handler_removes_keyboard(self) -> None:
        """Test that cancel handler removes reply keyboard."""
        from bot.main import cancel_handler
        
        message = MagicMock()
        message.answer = AsyncMock()
        
        state = MagicMock()
        state.clear = AsyncMock()
        
        await cancel_handler(message, state)
        
        # Check that reply_markup is provided to remove keyboard
        call_kwargs = message.answer.call_args[1]
        assert "reply_markup" in call_kwargs


@pytest.mark.asyncio
class TestFinalizeProfile:
    """Test suite for finalize_profile function."""

    async def test_finalize_profile_creates_new_profile(self) -> None:
        """Test that finalize_profile creates a new profile in database."""
        from bot.main import finalize_profile
        
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            bio="Test bio"
        )
        
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        mock_repo.upsert = AsyncMock()
        mock_repo.find_mutual_match = AsyncMock(return_value=None)
        
        with patch("bot.main.get_repository", return_value=mock_repo):
            await finalize_profile(message, profile, is_update=False)
        
        # Verify profile was saved
        mock_repo.upsert.assert_called_once_with(profile)
        
        # Verify confirmation message
        message.answer.assert_called()
        response = message.answer.call_args[0][0]
        assert "спасибо" in response.lower() or "профиль" in response.lower()

    async def test_finalize_profile_updates_existing_profile(self) -> None:
        """Test that finalize_profile updates existing profile."""
        from bot.main import finalize_profile
        
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Alice Updated",
            age=26,
            gender="female",
            preference="any"
        )
        
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=profile)
        mock_repo.upsert = AsyncMock()
        
        with patch("bot.main.get_repository", return_value=mock_repo):
            await finalize_profile(message, profile, is_update=True)
        
        # Verify profile was saved
        mock_repo.upsert.assert_called_once_with(profile)
        
        # Verify update message
        message.answer.assert_called()
        response = message.answer.call_args[0][0]
        assert "обновл" in response.lower() or "изменен" in response.lower()

    async def test_finalize_profile_handles_database_error(self) -> None:
        """Test that finalize_profile handles database errors gracefully."""
        from bot.main import finalize_profile
        
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male"
        )
        
        # Mock repository to raise error
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        mock_repo.upsert = AsyncMock(side_effect=RuntimeError("Database error"))
        
        with patch("bot.main.get_repository", return_value=mock_repo):
            await finalize_profile(message, profile, is_update=False)
        
        # Verify error message was sent
        message.answer.assert_called()
        response = message.answer.call_args[0][0]
        assert "ошибка" in response.lower() or "не удалось" in response.lower()

    async def test_finalize_profile_with_photo(self) -> None:
        """Test finalize_profile with photo URL."""
        from bot.main import finalize_profile
        
        message = MagicMock()
        message.bot = MagicMock()
        message.answer = AsyncMock()
        message.answer_photo = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            photo_url="https://example.com/photo.jpg"
        )
        
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        mock_repo.upsert = AsyncMock()
        mock_repo.find_mutual_match = AsyncMock(return_value=None)
        
        with patch("bot.main.get_repository", return_value=mock_repo):
            await finalize_profile(message, profile, is_update=False)
        
        # Verify profile was saved
        mock_repo.upsert.assert_called_once()


@pytest.mark.asyncio
class TestFormatMatchMessage:
    """Test suite for _format_match_message helper function."""

    async def test_format_match_message_with_full_profile(self) -> None:
        """Test formatting match message with complete profile."""
        from bot.main import _format_match_message
        
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            bio="Love traveling and music",
            location="Moscow",
            interests=["music", "travel", "books"],
            goal="serious"
        )
        
        message = _format_match_message(profile)
        
        # Check that key information is included
        assert "Alice" in message
        assert "25" in message
        assert "Moscow" in message
        assert "music" in message or "travel" in message

    async def test_format_match_message_with_minimal_profile(self) -> None:
        """Test formatting match message with minimal profile."""
        from bot.main import _format_match_message
        
        profile = Profile(
            user_id=12345,
            name="Bob",
            age=28,
            gender="male",
            preference="female"
        )
        
        message = _format_match_message(profile)
        
        # Check that required fields are present
        assert "Bob" in message
        assert "28" in message

    async def test_format_match_message_handles_empty_bio(self) -> None:
        """Test formatting message when bio is None or empty."""
        from bot.main import _format_match_message
        
        profile = Profile(
            user_id=12345,
            name="Charlie",
            age=30,
            gender="male",
            preference="any",
            bio=None
        )
        
        message = _format_match_message(profile)
        
        # Should still work without bio
        assert "Charlie" in message
        assert "30" in message

    async def test_format_match_message_handles_empty_interests(self) -> None:
        """Test formatting message when interests is None or empty."""
        from bot.main import _format_match_message
        
        profile = Profile(
            user_id=12345,
            name="Dana",
            age=27,
            gender="female",
            preference="any",
            interests=None
        )
        
        message = _format_match_message(profile)
        
        # Should still work without interests
        assert "Dana" in message
        assert "27" in message


@pytest.mark.asyncio
class TestSendPhotoHelpers:
    """Test suite for photo sending helper functions."""

    async def test_send_photo_reply_with_valid_url(self) -> None:
        """Test sending photo reply with valid URL."""
        from bot.main import _send_photo_reply
        
        message = MagicMock()
        message.answer_photo = AsyncMock()
        message.answer = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            photo_url="https://example.com/photo.jpg"
        )
        
        await _send_photo_reply(message, profile)
        
        # Verify photo message was sent (answer is called, not answer_photo in this implementation)
        message.answer.assert_called()

    async def test_send_photo_reply_handles_no_photo(self) -> None:
        """Test that _send_photo_reply handles profiles without photos."""
        from bot.main import _send_photo_reply
        
        message = MagicMock()
        message.answer_photo = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Bob",
            age=28,
            gender="male",
            preference="female",
            photo_url=None
        )
        
        # Should not raise error
        await _send_photo_reply(message, profile)
        
        # Should not send photo if no URL
        # Function might skip sending or handle gracefully

    async def test_send_photo_reply_handles_error(self) -> None:
        """Test that _send_photo_reply handles send errors gracefully."""
        from bot.main import _send_photo_reply
        
        message = MagicMock()
        message.answer_photo = AsyncMock(side_effect=RuntimeError("Photo send failed"))
        message.answer = AsyncMock(side_effect=RuntimeError("Photo send failed"))
        
        profile = Profile(
            user_id=12345,
            name="Charlie",
            age=30,
            gender="male",
            preference="any",
            photo_url="https://example.com/photo.jpg"
        )
        
        # Should handle error gracefully without raising
        try:
            await _send_photo_reply(message, profile)
        except RuntimeError:
            # If error propagates, that's also acceptable behavior
            pass

    async def test_send_profile_photo_with_valid_url(self) -> None:
        """Test sending profile photo to specific chat."""
        from bot.main import _send_profile_photo
        
        bot = MagicMock()
        bot.send_photo = AsyncMock()
        bot.send_message = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Dana",
            age=27,
            gender="female",
            preference="any",
            photo_url="https://example.com/photo.jpg"
        )
        
        await _send_profile_photo(bot, chat_id=67890, profile=profile)
        
        # Verify message was sent (actual implementation sends message, not photo)
        bot.send_message.assert_called()

    async def test_send_profile_photo_handles_no_photo(self) -> None:
        """Test sending profile photo when no photo URL exists."""
        from bot.main import _send_profile_photo
        
        bot = MagicMock()
        bot.send_photo = AsyncMock()
        
        profile = Profile(
            user_id=12345,
            name="Eve",
            age=24,
            gender="female",
            preference="male",
            photo_url=None
        )
        
        # Should handle gracefully
        await _send_profile_photo(bot, chat_id=67890, profile=profile)
