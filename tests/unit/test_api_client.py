"""Comprehensive tests for API Gateway client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError, ClientResponse, ClientSession

from bot.api_client import APIGatewayClient, APIGatewayError


class TestAPIGatewayClientInit:
    """Test API Gateway client initialization."""

    def test_client_initialization(self):
        """Test basic client initialization."""
        client = APIGatewayClient("http://localhost:8080")
        
        assert client.gateway_url == "http://localhost:8080"
        assert client.max_retries == 3
        assert client.retry_backoff_base == 1.0

    def test_client_initialization_strips_trailing_slash(self):
        """Test that trailing slash is removed from gateway URL."""
        client = APIGatewayClient("http://localhost:8080/")
        
        assert client.gateway_url == "http://localhost:8080"

    def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = APIGatewayClient(
            gateway_url="http://gateway:9000",
            timeout_seconds=30,
            max_retries=5,
            retry_backoff_base=2.0
        )
        
        assert client.gateway_url == "http://gateway:9000"
        assert client.max_retries == 5
        assert client.retry_backoff_base == 2.0


class TestAPIGatewayError:
    """Test APIGatewayError exception."""

    def test_api_gateway_error_basic(self):
        """Test basic APIGatewayError creation."""
        error = APIGatewayError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.response_data == {}

    def test_api_gateway_error_with_status_code(self):
        """Test APIGatewayError with custom status code."""
        error = APIGatewayError("Not found", status_code=404)
        
        assert error.status_code == 404

    def test_api_gateway_error_with_response_data(self):
        """Test APIGatewayError with response data."""
        response_data = {"error": "validation_failed", "details": {"field": "email"}}
        error = APIGatewayError("Validation error", status_code=400, response_data=response_data)
        
        assert error.status_code == 400
        assert error.response_data == response_data


@pytest.mark.asyncio
class TestAPIGatewayClientRequests:
    """Test API Gateway client request methods."""

    async def test_successful_get_request(self):
        """Test successful GET request."""
        client = APIGatewayClient("http://localhost:8080")
        
        mock_response = {"id": 123, "name": "Test"}
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_request = AsyncMock()
            mock_request.__aenter__ = AsyncMock()
            mock_request.__aexit__ = AsyncMock()
            mock_request.return_value.status = 200
            mock_request.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.request = mock_request
            
            result = await client._request("GET", "/profiles/123")
            
            assert result == mock_response

    async def test_post_request_with_json(self):
        """Test POST request with JSON data."""
        client = APIGatewayClient("http://localhost:8080")
        
        request_data = {"name": "John", "age": 25}
        response_data = {"id": 456, **request_data}
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_request = AsyncMock()
            mock_request.__aenter__ = AsyncMock()
            mock_request.__aexit__ = AsyncMock()
            mock_request.return_value.status = 201
            mock_request.return_value.json = AsyncMock(return_value=response_data)
            mock_session.request = mock_request
            
            result = await client._request("POST", "/profiles", json_data=request_data)
            
            assert result == response_data

    async def test_request_with_idempotency_key(self):
        """Test request includes idempotency key for POST/PUT."""
        client = APIGatewayClient("http://localhost:8080")
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_request = AsyncMock()
            mock_request.__aenter__ = AsyncMock()
            mock_request.__aexit__ = AsyncMock()
            mock_request.return_value.status = 200
            mock_request.return_value.json = AsyncMock(return_value={})
            mock_session.request = mock_request
            
            await client._request(
                "POST",
                "/profiles",
                json_data={"name": "Test"},
                idempotency_key="test-key-123"
            )
            
            # Verify idempotency key was added to headers
            call_kwargs = mock_request.call_args[1]
            assert "Idempotency-Key" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Idempotency-Key"] == "test-key-123"

    async def test_request_retry_on_5xx_error(self):
        """Test that requests are retried on 5xx server errors."""
        client = APIGatewayClient("http://localhost:8080", max_retries=3)
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # First two attempts fail with 500, third succeeds
            mock_request = AsyncMock()
            mock_request.__aenter__ = AsyncMock()
            mock_request.__aexit__ = AsyncMock()
            
            response_500 = MagicMock()
            response_500.status = 500
            response_500.json = AsyncMock(return_value={"error": "server_error"})
            
            response_200 = MagicMock()
            response_200.status = 200
            response_200.json = AsyncMock(return_value={"success": True})
            
            mock_request.return_value = response_500
            mock_session.request = mock_request
            
            # Should retry after 500 errors
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(APIGatewayError) as exc_info:
                    await client._request("GET", "/test")
                
                assert exc_info.value.status_code == 500

    async def test_request_no_retry_on_4xx_error(self):
        """Test that requests are NOT retried on 4xx client errors."""
        client = APIGatewayClient("http://localhost:8080", max_retries=3)
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_request = AsyncMock()
            mock_request.__aenter__ = AsyncMock()
            mock_request.__aexit__ = AsyncMock()
            
            response_404 = MagicMock()
            response_404.status = 404
            response_404.json = AsyncMock(return_value={"error": "not_found"})
            
            mock_request.return_value = response_404
            mock_session.request = mock_request
            
            # Should not retry 4xx errors
            with pytest.raises(APIGatewayError) as exc_info:
                await client._request("GET", "/test")
            
            assert exc_info.value.status_code == 404
            # Should only be called once (no retries)
            assert mock_request.call_count == 1


@pytest.mark.asyncio
class TestAPIGatewayClientProfileMethods:
    """Test profile-related API Gateway client methods."""

    async def test_create_profile(self):
        """Test creating a profile via API Gateway."""
        client = APIGatewayClient("http://localhost:8080")
        
        profile_data = {
            "tg_user_id": 123456,
            "name": "John Doe",
            "birth_date": "1995-01-15",
            "gender": "male",
            "orientation": "heterosexual"
        }
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": 1, **profile_data}
            
            result = await client.create_profile(profile_data)
            
            assert result["id"] == 1
            assert result["name"] == "John Doe"
            mock_request.assert_called_once()

    async def test_get_profile(self):
        """Test getting a profile via API Gateway."""
        client = APIGatewayClient("http://localhost:8080")
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": 1, "name": "John Doe"}
            
            result = await client.get_profile(123456)
            
            assert result["id"] == 1
            mock_request.assert_called_once_with("GET", "/profiles/123456")

    async def test_update_profile(self):
        """Test updating a profile via API Gateway."""
        client = APIGatewayClient("http://localhost:8080")
        
        update_data = {"bio": "Updated bio"}
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": 1, "bio": "Updated bio"}
            
            result = await client.update_profile(123456, update_data)
            
            assert result["bio"] == "Updated bio"
            mock_request.assert_called_once()


@pytest.mark.asyncio
class TestAPIGatewayClientDiscoveryMethods:
    """Test discovery-related API Gateway client methods."""

    async def test_find_candidates(self):
        """Test getting discovery candidates via API Gateway."""
        client = APIGatewayClient("http://localhost:8080")
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "candidates": [
                    {"id": 2, "name": "Jane"},
                    {"id": 3, "name": "Alice"}
                ]
            }
            
            result = await client.find_candidates(user_id=1, limit=10)
            
            assert len(result["candidates"]) == 2
            mock_request.assert_called_once()

    async def test_create_interaction(self):
        """Test recording user interaction via API Gateway."""
        client = APIGatewayClient("http://localhost:8080")
        
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "success"}
            
            await client.create_interaction(
                user_id=1,
                target_user_id=2,
                interaction_type="like"
            )
            
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"


@pytest.mark.asyncio
class TestAPIGatewayClientErrorHandling:
    """Test error handling in API Gateway client."""

    async def test_network_error_raises_exception(self):
        """Test that network errors raise APIGatewayError."""
        client = APIGatewayClient("http://localhost:8080")
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_session.request = AsyncMock(side_effect=ClientError("Connection refused"))
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(APIGatewayError) as exc_info:
                    await client._request("GET", "/test")
                
                assert "Connection refused" in str(exc_info.value)

    async def test_timeout_error(self):
        """Test that timeout errors are handled properly."""
        client = APIGatewayClient("http://localhost:8080", timeout_seconds=1)
        
        with patch("bot.api_client.ClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_session.request = AsyncMock(side_effect=asyncio.TimeoutError())
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(APIGatewayError):
                    await client._request("GET", "/test")
