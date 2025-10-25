"""Tests for chat service endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import web

from services.chat.main import (
    block_user,
    create_report,
    get_conversations,
    get_messages,
    send_message,
    update_read_state,
)


@pytest.mark.asyncio
class TestChatEndpoints:
    """Test chat service endpoints."""

    def setup_method(self):
        """Setup test instance."""
        self.app = web.Application()
        self.app["data_service_url"] = "http://data-service:8088"

    async def test_get_conversations_success(self):
        """Test successful conversations retrieval."""
        request = Mock()
        request.query = {"user_id": "123", "limit": "20"}
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "conversations": [
                    {
                        "id": 1,
                        "user_id": 123,
                        "other_user_id": 456,
                        "last_message": "Hey! How are you?",
                        "unread_count": 2,
                        "updated_at": "2024-01-24T10:30:00Z",
                    }
                ]
            }

            response = await get_conversations(request)
            assert response.status == 200

            data = await response.json()
            assert "conversations" in data
            assert len(data["conversations"]) == 1

    async def test_get_conversations_missing_user_id(self):
        """Test conversations retrieval without user_id."""
        request = Mock()
        request.query = {"limit": "20"}
        request.app = self.app

        response = await get_conversations(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_get_messages_success(self):
        """Test successful messages retrieval."""
        request = Mock()
        request.match_info = {"conversation_id": "1"}
        request.query = {"limit": "50", "offset": "0"}
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "messages": [
                    {
                        "id": 1,
                        "conversation_id": 1,
                        "sender_id": 123,
                        "content": "Hello!",
                        "content_type": "text",
                        "created_at": "2024-01-24T10:30:00Z",
                        "read_at": None,
                    }
                ]
            }

            response = await get_messages(request)
            assert response.status == 200

            data = await response.json()
            assert "messages" in data
            assert len(data["messages"]) == 1

    async def test_send_message_success(self):
        """Test successful message sending."""
        request = Mock()
        request.json = AsyncMock(
            return_value={
                "conversation_id": 1,
                "user_id": 123,
                "text": "Hello!",
                "content_type": "text",
            }
        )
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {
                "message_id": 1,
                "sent_at": "2024-01-24T10:30:00Z",
            }

            with patch("services.chat.main.event_publisher") as mock_publisher:
                mock_publisher.publish_event = AsyncMock()

                response = await send_message(request)
                assert response.status == 201

                data = await response.json()
                assert "message_id" in data
                assert "sent_at" in data

    async def test_send_message_missing_fields(self):
        """Test message sending with missing fields."""
        request = Mock()
        request.json = AsyncMock(
            return_value={
                "conversation_id": 1,
                "text": "Hello!",
                # Missing user_id
            }
        )
        request.app = self.app

        response = await send_message(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_mark_message_read_success(self):
        """Test successful message read marking."""
        request = Mock()
        request.match_info = {"message_id": "1"}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {"success": True}

            response = await update_read_state(request)
            assert response.status == 200

            data = await response.json()
            assert data["success"] is True

    async def test_mark_message_read_missing_message_id(self):
        """Test message read marking without message_id."""
        request = Mock()
        request.match_info = {}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.app = self.app

        response = await update_read_state(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_mark_message_read_missing_auth(self):
        """Test message read marking without authentication."""
        request = Mock()
        request.match_info = {"message_id": "1"}
        request.get = Mock(return_value=None)  # No user_id
        request.app = self.app

        response = await update_read_state(request)
        assert response.status == 401

        data = await response.json()
        assert "error" in data

    async def test_block_conversation_success(self):
        """Test successful conversation blocking."""
        request = Mock()
        request.match_info = {"conversation_id": "1"}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {"success": True}

            with patch("services.chat.main.event_publisher") as mock_publisher:
                mock_publisher.publish_block_event = AsyncMock()

                response = await block_user(request)
                assert response.status == 200

                data = await response.json()
                assert data["success"] is True

    async def test_block_conversation_missing_conversation_id(self):
        """Test conversation blocking without conversation_id."""
        request = Mock()
        request.match_info = {}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.app = self.app

        response = await block_user(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_report_conversation_success(self):
        """Test successful conversation reporting."""
        request = Mock()
        request.match_info = {"conversation_id": "1"}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.json = AsyncMock(
            return_value={"report_type": "spam", "reason": "Sending unwanted messages"}
        )
        request.app = self.app

        with patch("services.chat.main._call_data_service") as mock_call:
            mock_call.return_value = {"success": True}

            with patch("services.chat.main.event_publisher") as mock_publisher:
                mock_publisher.publish_report_event = AsyncMock()

                response = await create_report(request)
                assert response.status == 200

                data = await response.json()
                assert data["success"] is True

    async def test_report_conversation_missing_fields(self):
        """Test conversation reporting with missing fields."""
        request = Mock()
        request.match_info = {"conversation_id": "1"}
        request.get = Mock(return_value=123)  # user_id from JWT
        request.json = AsyncMock(
            return_value={
                "report_type": "spam"
                # Missing reason
            }
        )
        request.app = self.app

        response = await create_report(request)
        assert response.status == 400

        data = await response.json()
        assert "error" in data

    async def test_report_conversation_missing_auth(self):
        """Test conversation reporting without authentication."""
        request = Mock()
        request.match_info = {"conversation_id": "1"}
        request.get = Mock(return_value=None)  # No user_id
        request.json = AsyncMock(
            return_value={"report_type": "spam", "reason": "Sending unwanted messages"}
        )
        request.app = self.app

        response = await create_report(request)
        assert response.status == 401

        data = await response.json()
        assert "error" in data
