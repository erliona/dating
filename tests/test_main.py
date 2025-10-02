"""Tests for bot/main.py - bot handlers and main entry point."""

import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiogram import Dispatcher
from aiogram.types import Message, User, WebAppData, WebAppInfo

from bot.main import (
    JsonFormatter,
    configure_logging,
    handle_create_profile,
    handle_webapp_data,
    start_handler,
)


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
            exc_info=None
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
            exc_info=exc_info
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
            exc_info=None
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
        with patch('sys.stdout'):
            configure_logging()
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0
            assert isinstance(root_logger.handlers[0].formatter, JsonFormatter)
            assert root_logger.level == logging.INFO
    
    def test_configure_logging_reduces_noise(self):
        """Test that aiogram and aiohttp loggers are set to WARNING."""
        with patch('sys.stdout'):
            configure_logging()
            
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
        
        with patch('bot.main.load_config') as mock_config:
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
        
        with patch('bot.main.load_config') as mock_config:
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
            "city": "Moscow"
        }
        message.web_app_data.data = json.dumps({
            "action": "create_profile",
            "profile": profile_data
        })
        message.answer = AsyncMock()
        message.from_user = MagicMock(
            id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=False
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
        with patch('bot.main.ProfileRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            
            # Mock user creation
            mock_user = MagicMock()
            mock_user.id = 1
            mock_repo.create_or_update_user = AsyncMock(return_value=mock_user)
            
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
                "goal": "relationship"
            }
        }
        
        repository = MagicMock()
        session = MagicMock()
        logger = logging.getLogger(__name__)
        
        await handle_create_profile(message, data, repository, session, logger)
        
        message.answer.assert_called_once()
        assert "Validation error" in message.answer.call_args[0][0]
    
    async def test_handle_create_profile_success(self):
        """Test successful profile creation."""
        message = MagicMock(spec=Message)
        message.answer = AsyncMock()
        message.from_user = MagicMock(
            id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=False
        )
        
        data = {
            "profile": {
                "name": "John Doe",
                "birth_date": "1990-01-01",
                "gender": "male",
                "orientation": "female",
                "goal": "relationship",
                "city": "Moscow"
            }
        }
        
        # Mock repository
        repository = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        repository.create_or_update_user = AsyncMock(return_value=mock_user)
        
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
