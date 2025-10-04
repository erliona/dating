"""Tests for bot/main.py - bot handlers and main entry point."""

import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Message, User, WebAppData, WebAppInfo

from bot.main import handle_create_profile, handle_webapp_data, start_handler
from core.utils.logging import JsonFormatter, configure_logging


class TestJsonFormatter:
    """Test JSON logging formatter."""

    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["function"] == "test_func"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_with_exception(self):
        """Test formatting a log record with exception."""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.module = "test"
        record.funcName = "test_func"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError: Test error" in data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting with extra custom fields."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="User action",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"
        record.user_id = 12345
        record.event_type = "user_action"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == 12345
        assert data["event_type"] == "user_action"


class TestConfigureLogging:
    """Test logging configuration."""

    def test_configure_logging_sets_json_formatter(self):
        """Test that logging is configured with JSON formatter."""
        with patch("sys.stdout"):
            configure_logging("test-service")

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0
            assert isinstance(root_logger.handlers[0].formatter, JsonFormatter)
            assert root_logger.level == logging.INFO

    def test_configure_logging_reduces_noise(self):
        """Test that aiogram and aiohttp loggers are set to WARNING."""
        with patch("sys.stdout"):
            configure_logging("test-service")

            aiogram_logger = logging.getLogger("aiogram")
            aiohttp_logger = logging.getLogger("aiohttp")

            assert aiogram_logger.level == logging.WARNING
            assert aiohttp_logger.level == logging.WARNING


@pytest.mark.asyncio
class TestStartHandler:
    """Test /start command handler."""

    async def test_start_handler_with_webapp_url(self):
        """Test /start handler when webapp URL is configured."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()

        with patch("bot.main.load_config") as mock_config:
            mock_config.return_value = MagicMock(webapp_url="https://example.com")

            await start_handler(message)

            message.answer.assert_called_once()
            call_args = message.answer.call_args
            assert "Добро пожаловать" in call_args[0][0]
            assert "reply_markup" in call_args[1]

    async def test_start_handler_without_webapp_url(self):
        """Test /start handler when webapp URL is not configured."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()

        with patch("bot.main.load_config") as mock_config:
            mock_config.return_value = MagicMock(webapp_url=None)

            await start_handler(message)

            message.answer.assert_called_once()
            call_args = message.answer.call_args
            assert "WebApp is not configured" in call_args[0][0]


@pytest.mark.asyncio
class TestHandleWebappData:
    """Test WebApp data handler."""

    async def test_handle_webapp_data_no_data(self):
        """Test handler when no WebApp data is present."""
        message = MagicMock(spec=Message)
        message.web_app_data = None
        message.answer = AsyncMock()

        dispatcher = MagicMock(spec=Dispatcher)

        await handle_webapp_data(message, dispatcher)

        message.answer.assert_called_once()
        assert "No WebApp data received" in message.answer.call_args[0][0]

    async def test_handle_webapp_data_invalid_json(self):
        """Test handler with invalid JSON data."""
        message = MagicMock(spec=Message)
        message.web_app_data = MagicMock(spec=WebAppData)
        message.web_app_data.data = "invalid json"
        message.answer = AsyncMock()
        message.from_user = MagicMock(id=12345)

        dispatcher = MagicMock(spec=Dispatcher)

        await handle_webapp_data(message, dispatcher)

        message.answer.assert_called_once()
        assert "Invalid data format" in message.answer.call_args[0][0]

    async def test_handle_webapp_data_no_database(self):
        """Test handler when database is not configured."""
        message = MagicMock(spec=Message)
        message.web_app_data = MagicMock(spec=WebAppData)
        message.web_app_data.data = json.dumps({"action": "create_profile"})
        message.answer = AsyncMock()
        message.from_user = MagicMock(id=12345)

        dispatcher = MagicMock(spec=Dispatcher)
        dispatcher.workflow_data = {}

        await handle_webapp_data(message, dispatcher)

        message.answer.assert_called_once()
        assert "Database not configured" in message.answer.call_args[0][0]

    async def test_handle_webapp_data_unknown_action(self):
        """Test handler with unknown action."""
        message = MagicMock(spec=Message)
        message.web_app_data = MagicMock(spec=WebAppData)
        message.web_app_data.data = json.dumps({"action": "unknown_action"})
        message.answer = AsyncMock()
        message.from_user = MagicMock(id=12345)

        session_maker = MagicMock()
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock()
        session_maker.return_value = session_mock

        dispatcher = MagicMock(spec=Dispatcher)
        dispatcher.workflow_data = {"session_maker": session_maker}

        await handle_webapp_data(message, dispatcher)

        message.answer.assert_called_once()
        assert "Unknown action" in message.answer.call_args[0][0]

    async def test_handle_webapp_data_create_profile_success(self):
        """Test successful profile creation via WebApp data."""
        message = MagicMock(spec=Message)
        message.web_app_data = MagicMock(spec=WebAppData)
        profile_data = {
            "name": "John Doe",
            "birth_date": "1990-01-01",
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
            "city": "Moscow",
        }
        message.web_app_data.data = json.dumps(
            {"action": "create_profile", "profile": profile_data}
        )
        message.answer = AsyncMock()
        message.from_user = MagicMock(
            id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=False,
        )

        # Mock session and repository
        session_mock = MagicMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock()
        session_mock.commit = AsyncMock()

        session_maker = MagicMock()
        session_maker.return_value = session_mock

        dispatcher = MagicMock(spec=Dispatcher)
        dispatcher.workflow_data = {"session_maker": session_maker}

        # Mock repository
        with patch("bot.main.ProfileRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            # Mock user creation
            mock_user = MagicMock()
            mock_user.id = 1
            mock_repo.create_or_update_user = AsyncMock(return_value=mock_user)

            # Mock no existing profile
            mock_repo.get_profile_by_user_id = AsyncMock(return_value=None)

            # Mock profile creation
            mock_profile = MagicMock()
            mock_profile.id = 1
            mock_profile.name = "John Doe"
            mock_profile.birth_date = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
            mock_profile.gender = "male"
            mock_profile.goal = "relationship"
            mock_profile.city = "Moscow"
            mock_repo.create_profile = AsyncMock(return_value=mock_profile)

            await handle_webapp_data(message, dispatcher)

            message.answer.assert_called_once()
            assert "Профиль создан" in message.answer.call_args[0][0]


@pytest.mark.asyncio
class TestHandleCreateProfile:
    """Test profile creation handler."""

    async def test_handle_create_profile_validation_error(self):
        """Test profile creation with validation error."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        message.from_user = MagicMock(id=12345)

        data = {
            "profile": {
                "name": "",  # Invalid: empty name
                "birth_date": "1990-01-01",
                "gender": "male",
                "orientation": "female",
                "goal": "relationship",
            }
        }

        repository = MagicMock()
        session = MagicMock()
        logger = logging.getLogger(__name__)

        await handle_create_profile(message, data, repository, session, logger)

        message.answer.assert_called_once()
        assert "Validation error" in message.answer.call_args[0][0]

    async def test_handle_create_profile_duplicate(self):
        """Test profile creation when profile already exists."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        message.from_user = MagicMock(
            id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=False,
        )

        data = {
            "profile": {
                "name": "John Doe",
                "birth_date": "1990-01-01",
                "gender": "male",
                "orientation": "female",
                "goal": "relationship",
                "city": "Moscow",
            }
        }

        # Mock repository
        repository = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        repository.create_or_update_user = AsyncMock(return_value=mock_user)

        # Mock existing profile
        existing_profile = MagicMock()
        existing_profile.id = 1
        repository.get_profile_by_user_id = AsyncMock(return_value=existing_profile)

        session = MagicMock()
        logger = logging.getLogger(__name__)

        await handle_create_profile(message, data, repository, session, logger)

        # Should show error message about existing profile
        message.answer.assert_called_once()
        assert "уже есть профиль" in message.answer.call_args[0][0]
        # Should not create profile or commit
        repository.create_profile.assert_not_called()

    async def test_handle_create_profile_success(self):
        """Test successful profile creation."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        message.from_user = MagicMock(
            id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=False,
        )

        data = {
            "profile": {
                "name": "John Doe",
                "birth_date": "1990-01-01",
                "gender": "male",
                "orientation": "female",
                "goal": "relationship",
                "city": "Moscow",
            }
        }

        # Mock repository
        repository = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        repository.create_or_update_user = AsyncMock(return_value=mock_user)

        # No existing profile
        repository.get_profile_by_user_id = AsyncMock(return_value=None)

        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.name = "John Doe"
        mock_profile.birth_date = datetime.strptime("1990-01-01", "%Y-%m-%d").date()
        mock_profile.gender = "male"
        mock_profile.goal = "relationship"
        mock_profile.city = "Moscow"
        repository.create_profile = AsyncMock(return_value=mock_profile)

        session = MagicMock()
        session.commit = AsyncMock()
        logger = logging.getLogger(__name__)

        await handle_create_profile(message, data, repository, session, logger)

        message.answer.assert_called_once()
        assert "Профиль создан" in message.answer.call_args[0][0]
        session.commit.assert_called_once()


@pytest.mark.asyncio
class TestMainFunction:
    """Test main() bootstrap function."""

    async def test_main_config_load_error(self):
        """Test main() handles configuration load error."""
        with patch("bot.main.load_config") as mock_load:
            mock_load.side_effect = RuntimeError("Config error")

            with pytest.raises(RuntimeError, match="Config error"):
                from bot.main import main

                await main()

    async def test_main_bot_creation_with_database(self):
        """Test main() creates bot with database configuration."""
        with patch("bot.main.load_config") as mock_load, patch(
            "bot.main.Bot"
        ) as mock_bot, patch("bot.main.Dispatcher") as mock_dispatcher, patch(
            "bot.main.create_async_engine"
        ) as mock_engine, patch(
            "bot.main.sessionmaker"
        ) as mock_sessionmaker, patch(
            "bot.api.run_api_server"
        ) as mock_api_server:

            # Mock config with database
            mock_config = MagicMock()
            mock_config.token = "123:abc"
            mock_config.database_url = "postgresql://localhost/db"
            mock_config.webapp_url = "https://example.com"
            mock_load.return_value = mock_config

            # Mock Bot and Dispatcher
            mock_bot_instance = MagicMock()
            # Mock get_me() to return bot info
            mock_bot_info = MagicMock()
            mock_bot_info.username = "test_bot"
            mock_bot_info.id = 12345
            mock_bot_instance.get_me = AsyncMock(return_value=mock_bot_info)
            # Mock session.close() for cleanup
            mock_bot_instance.session = MagicMock()
            mock_bot_instance.session.close = AsyncMock()
            mock_bot.return_value = mock_bot_instance
            mock_dp_instance = MagicMock()
            mock_dp_instance.workflow_data = {}
            # Mock start_polling to return immediately
            mock_dp_instance.start_polling = AsyncMock(return_value=None)
            mock_dispatcher.return_value = mock_dp_instance

            # Mock database setup
            mock_engine_instance = MagicMock()
            mock_engine.return_value = mock_engine_instance
            mock_session_maker = MagicMock()
            mock_sessionmaker.return_value = mock_session_maker

            # Mock API server to be called and return awaitable
            async def noop_api_server(*args, **kwargs):
                return None

            mock_api_server.side_effect = noop_api_server

            from bot.main import main

            await main()

            # Verify bot was created
            mock_bot.assert_called_once_with(token="123:abc")

            # Verify database engine was created
            mock_engine.assert_called_once()
            assert "postgresql://localhost/db" in str(mock_engine.call_args)

            # Verify session maker was stored in dispatcher
            assert "session_maker" in mock_dp_instance.workflow_data

    async def test_main_without_database(self):
        """Test main() handles missing database configuration."""
        with patch("bot.main.load_config") as mock_load, patch(
            "bot.main.Bot"
        ) as mock_bot, patch("bot.main.Dispatcher") as mock_dispatcher:

            # Mock config without database
            mock_config = MagicMock()
            mock_config.token = "123:abc"
            mock_config.database_url = None
            mock_config.webapp_url = "https://example.com"
            mock_load.return_value = mock_config

            # Mock Bot and Dispatcher
            mock_bot_instance = MagicMock()
            # Mock get_me() to return bot info
            mock_bot_info = MagicMock()
            mock_bot_info.username = "test_bot"
            mock_bot_info.id = 12345
            mock_bot_instance.get_me = AsyncMock(return_value=mock_bot_info)
            # Mock session.close() for cleanup
            mock_bot_instance.session = MagicMock()
            mock_bot_instance.session.close = AsyncMock()
            mock_bot.return_value = mock_bot_instance
            mock_dp_instance = MagicMock()
            mock_dp_instance.workflow_data = {}
            # Mock start_polling to return immediately
            mock_dp_instance.start_polling = AsyncMock(return_value=None)
            mock_dispatcher.return_value = mock_dp_instance

            from bot.main import main

            await main()

            # Verify bot was created
            mock_bot.assert_called_once_with(token="123:abc")

            # Verify no session maker in dispatcher
            assert (
                "session_maker" not in mock_dp_instance.workflow_data
                or mock_dp_instance.workflow_data.get("session_maker") is None
            )

    async def test_main_bot_execution_error(self):
        """Test main() handles bot execution error."""
        with patch("bot.main.load_config") as mock_load, patch(
            "bot.main.Bot"
        ) as mock_bot, patch("bot.main.Dispatcher") as mock_dispatcher:

            # Mock config
            mock_config = MagicMock()
            mock_config.token = "123:abc"
            mock_config.database_url = None
            mock_load.return_value = mock_config

            # Mock Bot and Dispatcher
            mock_bot_instance = MagicMock()
            # Mock get_me() to return bot info
            mock_bot_info = MagicMock()
            mock_bot_info.username = "test_bot"
            mock_bot_info.id = 12345
            mock_bot_instance.get_me = AsyncMock(return_value=mock_bot_info)
            # Mock session.close() for cleanup
            mock_bot_instance.session = MagicMock()
            mock_bot_instance.session.close = AsyncMock()
            mock_bot.return_value = mock_bot_instance
            mock_dp_instance = MagicMock()
            mock_dp_instance.workflow_data = {}
            # Mock start_polling to raise an error
            mock_dp_instance.start_polling = AsyncMock(
                side_effect=Exception("Bot error")
            )
            mock_dispatcher.return_value = mock_dp_instance

            with pytest.raises(Exception, match="Bot error"):
                from bot.main import main

                await main()
