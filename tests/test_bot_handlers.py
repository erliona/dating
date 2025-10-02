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


@pytest.mark.asyncio
class TestDebugHandler:
    """Test suite for the /debug command handler."""

    async def test_debug_shows_bot_status(self) -> None:
        """Test that debug command shows bot status information."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot.get_me()
        bot_info = MagicMock()
        bot_info.id = 123456789
        bot_info.username = "test_bot"
        bot_info.first_name = "Test Bot"
        message.bot.get_me = AsyncMock(return_value=bot_info)
        
        # Mock config
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        mock_config.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        mock_repo._session_factory = MagicMock()
        
        # Mock session with database counts
        mock_session = AsyncMock()
        mock_execute = AsyncMock()
        mock_scalar_result = MagicMock()
        mock_scalar_result.scalar = MagicMock(return_value=10)
        mock_execute.return_value = mock_scalar_result
        mock_session.execute = mock_execute
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_repo._session_factory.return_value = mock_session
        
        with patch("bot.main.get_config", return_value=mock_config), \
             patch("bot.main.get_repository", return_value=mock_repo), \
             patch("bot.main.get_interaction_repository", return_value=mock_repo), \
             patch("bot.main.get_match_repository", return_value=mock_repo), \
             patch("bot.main.get_settings_repository", return_value=mock_repo):
            
            await debug_handler(message)
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that response contains expected sections
        assert "Debug Information" in response
        assert "Bot Status" in response
        assert "test_bot" in response
        assert "Configuration" in response
        assert "Database Connection" in response
        assert "Connected" in response
        assert "Database Statistics" in response
        assert "Environment Variables" in response
        assert "System Information" in response

    async def test_debug_handles_bot_info_error(self) -> None:
        """Test that debug command handles bot info retrieval errors gracefully."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot.get_me() to raise error
        message.bot.get_me = AsyncMock(side_effect=Exception("Network error"))
        
        # Mock other dependencies
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        mock_config.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        
        with patch("bot.main.get_config", return_value=mock_config), \
             patch("bot.main.get_repository", return_value=mock_repo):
            
            await debug_handler(message)
        
        # Verify message was sent even with error
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that error is shown
        assert "Failed to get bot info" in response

    async def test_debug_handles_config_error(self) -> None:
        """Test that debug command handles config errors gracefully."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot info
        bot_info = MagicMock()
        bot_info.id = 123456789
        bot_info.username = "test_bot"
        bot_info.first_name = "Test Bot"
        message.bot.get_me = AsyncMock(return_value=bot_info)
        
        # Mock config to raise error
        with patch("bot.main.get_config", side_effect=RuntimeError("Config not loaded")):
            await debug_handler(message)
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that config error is shown
        assert "Config Error" in response

    async def test_debug_handles_database_error(self) -> None:
        """Test that debug command handles database connection errors gracefully."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot info
        bot_info = MagicMock()
        bot_info.id = 123456789
        bot_info.username = "test_bot"
        bot_info.first_name = "Test Bot"
        message.bot.get_me = AsyncMock(return_value=bot_info)
        
        # Mock config
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        mock_config.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Mock repository to raise error
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(side_effect=Exception("Connection refused"))
        
        with patch("bot.main.get_config", return_value=mock_config), \
             patch("bot.main.get_repository", return_value=mock_repo):
            
            await debug_handler(message)
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that connection failure is shown
        assert "Connection Failed" in response

    async def test_debug_masks_sensitive_data(self) -> None:
        """Test that debug command masks sensitive information."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot info
        bot_info = MagicMock()
        bot_info.id = 123456789
        bot_info.username = "test_bot"
        bot_info.first_name = "Test Bot"
        message.bot.get_me = AsyncMock(return_value=bot_info)
        
        # Mock config with sensitive data
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        mock_config.database_url = "postgresql+asyncpg://myuser:secretpassword@localhost:5432/testdb"
        
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        
        with patch("bot.main.get_config", return_value=mock_config), \
             patch("bot.main.get_repository", return_value=mock_repo), \
             patch.dict("os.environ", {"BOT_TOKEN": "123456:ABC-secret-token"}):
            
            await debug_handler(message)
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that password is masked
        assert "secretpassword" not in response
        assert "myuser:***@" in response
        
        # Check that token is masked
        assert "ABC-secret-token" not in response
        assert "BOT_TOKEN: ***" in response
    
    async def test_debug_works_without_database(self) -> None:
        """Test that debug command works even when database is not available."""
        from bot.main import debug_handler
        
        # Mock message and bot
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock bot info
        bot_info = MagicMock()
        bot_info.id = 123456789
        bot_info.username = "test_bot"
        bot_info.first_name = "Test Bot"
        message.bot.get_me = AsyncMock(return_value=bot_info)
        
        # Mock config
        mock_config = MagicMock()
        mock_config.webapp_url = "https://example.com/webapp"
        mock_config.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Mock repository getter to raise RuntimeError (repository not available)
        with patch("bot.main.get_config", return_value=mock_config), \
             patch("bot.main.get_repository", side_effect=RuntimeError("Profile repository is not initialized")):
            
            await debug_handler(message)
        
        # Verify message was sent
        message.answer.assert_called_once()
        response = message.answer.call_args[0][0]
        
        # Check that bot status is shown
        assert "Bot Running" in response
        assert "test_bot" in response
        
        # Check that config is shown
        assert "Config Loaded" in response
        assert "example.com" in response
        
        # Check that repository unavailability is noted
        assert "Repository Not Available" in response or "Not available" in response
        
        # Check that helpful notes are shown
        assert "Database not connected" in response

