"""Tests for bot/main.py - bot handlers and main entry point."""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Message, User, WebAppData, WebAppInfo

pytestmark = pytest.mark.e2e

from bot.main import (
    send_like_notification,
    send_match_notification,
    send_message_notification,
)
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


# Bot no longer has command handlers - all interactions via WebApp


@pytest.mark.asyncio
class TestNotificationSenders:
    """Test notification sender functions."""

    async def test_send_match_notification_success(self):
        """Test sending match notification successfully."""
        # Mock bot instance
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        import bot.main

        bot.main._bot_instance = mock_bot

        match_data = {
            "id": 123,
            "name": "John Doe",
        }

        result = await send_match_notification(12345, match_data)

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]["chat_id"] == 12345
        assert "матч" in call_args[1]["text"].lower()
        assert "John Doe" in call_args[1]["text"]

        # Cleanup
        bot.main._bot_instance = None

    async def test_send_match_notification_no_bot(self):
        """Test match notification when bot is not initialized."""
        import bot.main

        bot.main._bot_instance = None

        match_data = {"id": 123, "name": "John Doe"}
        result = await send_match_notification(12345, match_data)

        assert result is False

    async def test_send_match_notification_error(self):
        """Test match notification when sending fails."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Send failed"))

        import bot.main

        bot.main._bot_instance = mock_bot

        match_data = {"id": 123, "name": "John Doe"}
        result = await send_match_notification(12345, match_data)

        assert result is False

        # Cleanup
        bot.main._bot_instance = None

    async def test_send_message_notification_success(self):
        """Test sending message notification successfully."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        import bot.main

        bot.main._bot_instance = mock_bot

        message_data = {
            "sender_name": "Jane Doe",
            "preview": "Hello there!",
        }

        result = await send_message_notification(12345, message_data)

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]["chat_id"] == 12345
        assert "Jane Doe" in call_args[1]["text"]
        assert "Hello there!" in call_args[1]["text"]

        # Cleanup
        bot.main._bot_instance = None

    async def test_send_message_notification_no_bot(self):
        """Test message notification when bot is not initialized."""
        import bot.main

        bot.main._bot_instance = None

        message_data = {"sender_name": "Jane", "preview": "Hi"}
        result = await send_message_notification(12345, message_data)

        assert result is False

    async def test_send_like_notification_success(self):
        """Test sending like notification successfully."""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        import bot.main

        bot.main._bot_instance = mock_bot

        like_data = {
            "name": "Alice",
        }

        result = await send_like_notification(12345, like_data)

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]["chat_id"] == 12345
        assert "Alice" in call_args[1]["text"]
        assert "лайкнул" in call_args[1]["text"]

        # Cleanup
        bot.main._bot_instance = None

    async def test_send_like_notification_no_bot(self):
        """Test like notification when bot is not initialized."""
        import bot.main

        bot.main._bot_instance = None

        like_data = {"name": "Alice"}
        result = await send_like_notification(12345, like_data)

        assert result is False


@pytest.mark.asyncio
class TestMainFunction:
    """Test main() bootstrap function."""

    @pytest.mark.skip(
        reason="Test hangs - main() starts long-running process. Needs refactoring to support graceful shutdown for testing."
    )
    async def test_main_config_load_error(self):
        """Test main() handles configuration load error.
        
        NOTE: This test needs to be refactored to handle graceful shutdown of main().
        """
        pass

    @pytest.mark.skip(
        reason="Test hangs - main() starts long-running process. Needs refactoring to support graceful shutdown for testing."
    )
    async def test_main_bot_creation_with_api_gateway(self):
        """Test main() creates bot with API Gateway configuration (thin client).
        
        NOTE: This test needs to be refactored to handle graceful shutdown of main().
        """
        pass

    @pytest.mark.skip(
        reason="Test hangs - main() starts long-running process. Needs refactoring to support graceful shutdown for testing."
    )
    async def test_main_without_api_gateway(self):
        """Test main() handles missing API Gateway configuration.
        
        NOTE: This test needs to be refactored to handle graceful shutdown of main().
        """
        pass

    @pytest.mark.skip(
        reason="Test hangs - main() starts long-running process. Needs refactoring to support graceful shutdown for testing."
    )
    async def test_main_bot_execution_error(self):
        """Test main() handles bot execution error.
        
        NOTE: This test needs to be refactored to handle graceful shutdown of main().
        """
        pass
