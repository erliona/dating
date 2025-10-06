"""API Gateway client for bot.

This module provides a thin client interface for the bot to communicate
with microservices through the API Gateway, eliminating direct database access.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from aiohttp import ClientError, ClientSession, ClientTimeout

logger = logging.getLogger(__name__)


class APIGatewayError(Exception):
    """Base exception for API Gateway errors."""

    def __init__(self, message: str, status_code: int = 500, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class APIGatewayClient:
    """Client for communicating with API Gateway and microservices."""

    def __init__(
        self,
        gateway_url: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ):
        """Initialize API Gateway client.

        Args:
            gateway_url: Base URL of API Gateway (e.g., http://api-gateway:8080)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retries for 5xx errors and network failures
            retry_backoff_base: Base delay for exponential backoff (seconds)
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout_seconds, connect=10)
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        logger.info(
            "API Gateway client initialized",
            extra={
                "event_type": "api_client_init",
                "gateway_url": gateway_url,
                "timeout": timeout_seconds,
                "max_retries": max_retries,
            },
        )

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API Gateway with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /profiles/123)
            json_data: Optional JSON body
            headers: Optional headers
            params: Optional query parameters
            idempotency_key: Optional idempotency key for safe retries

        Returns:
            Response JSON as dictionary

        Raises:
            APIGatewayError: If request fails after retries
        """
        url = f"{self.gateway_url}{path}"
        request_headers = headers.copy() if headers else {}
        
        # Add idempotency key for POST/PUT operations if provided
        if idempotency_key and method in ("POST", "PUT"):
            request_headers["Idempotency-Key"] = idempotency_key

        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                async with ClientSession(timeout=self.timeout) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        json=json_data,
                        headers=request_headers,
                        params=params,
                    ) as resp:
                        try:
                            response_data = await resp.json()
                        except Exception:
                            # If response is not JSON, create error response
                            response_data = {
                                "error": {
                                    "code": "invalid_response",
                                    "message": await resp.text() or "Invalid response format"
                                }
                            }

                        # Handle 4xx errors (client errors - don't retry)
                        if 400 <= resp.status < 500:
                            error_msg = response_data.get('error', {}).get('message', 'Client error')
                            error_code = response_data.get('error', {}).get('code', 'client_error')
                            logger.warning(
                                f"API client error: {method} {path}",
                                extra={
                                    "event_type": "api_client_error",
                                    "method": method,
                                    "path": path,
                                    "status": resp.status,
                                    "error_code": error_code,
                                },
                            )
                            raise APIGatewayError(
                                error_msg,
                                status_code=resp.status,
                                response_data=response_data,
                            )

                        # Handle 5xx errors (server errors - retry with backoff)
                        if resp.status >= 500:
                            error_msg = response_data.get('error', {}).get('message', 'Server error')
                            logger.warning(
                                f"API server error (attempt {attempt + 1}/{self.max_retries}): {method} {path}",
                                extra={
                                    "event_type": "api_server_error",
                                    "method": method,
                                    "path": path,
                                    "status": resp.status,
                                    "attempt": attempt + 1,
                                },
                            )
                            if attempt < self.max_retries - 1:
                                # Exponential backoff: 1s, 2s, 4s, etc.
                                delay = self.retry_backoff_base * (2 ** attempt)
                                await asyncio.sleep(delay)
                                continue
                            else:
                                raise APIGatewayError(
                                    f"Server error after {self.max_retries} attempts: {error_msg}",
                                    status_code=resp.status,
                                    response_data=response_data,
                                )

                        # Success (2xx, 3xx)
                        return response_data

            except ClientError as e:
                # Network errors - retry with backoff
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{self.max_retries}): {method} {path} - {e}",
                    extra={
                        "event_type": "api_network_error",
                        "method": method,
                        "path": path,
                        "attempt": attempt + 1,
                    },
                )
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_backoff_base * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise APIGatewayError(
                        f"Network error after {self.max_retries} attempts: {str(e)}",
                        status_code=503,
                    ) from e
            except APIGatewayError:
                # Re-raise API errors without retry (4xx errors)
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error: {method} {path} - {e}",
                    exc_info=True,
                    extra={
                        "event_type": "api_unexpected_error",
                        "method": method,
                        "path": path,
                    },
                )
                raise APIGatewayError(
                    f"Unexpected error: {str(e)}",
                    status_code=500,
                ) from e

        # Should not reach here, but just in case
        raise APIGatewayError(
            f"Request failed after {self.max_retries} attempts",
            status_code=503,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check API Gateway health.

        Returns:
            Health check response

        Raises:
            APIGatewayError: If health check fails
        """
        return await self._request("GET", "/health")

    # Profile Service endpoints
    async def create_profile(
        self,
        profile_data: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create user profile via Profile Service with idempotency support.

        Args:
            profile_data: Profile data dictionary
            idempotency_key: Optional client-generated key for idempotent creation.
                            If not provided, one will be generated based on telegram_id.

        Returns:
            Created profile data
        """
        # Generate idempotency key from telegram_id if not provided
        if not idempotency_key and "telegram_id" in profile_data:
            idempotency_key = f"profile-create-{profile_data['telegram_id']}"
        elif not idempotency_key:
            # Fallback to UUID if no telegram_id available
            idempotency_key = f"profile-create-{uuid.uuid4()}"

        return await self._request(
            "POST",
            "/profiles/",
            json_data=profile_data,
            idempotency_key=idempotency_key,
        )

    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            Profile data or None if not found
        """
        try:
            return await self._request("GET", f"/profiles/{user_id}")
        except APIGatewayError as e:
            if e.status_code == 404:
                return None
            raise

    async def update_profile(
        self, user_id: int, profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile.

        Args:
            user_id: User ID
            profile_data: Profile data to update

        Returns:
            Updated profile data
        """
        return await self._request(
            "PUT", f"/profiles/{user_id}", json_data=profile_data
        )

    async def delete_profile(self, user_id: int) -> Dict[str, Any]:
        """Delete user profile.

        Args:
            user_id: User ID

        Returns:
            Deletion confirmation
        """
        return await self._request("DELETE", f"/profiles/{user_id}")

    # Media Service endpoints
    async def upload_photo(
        self, user_id: int, photo_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """Upload photo via Media Service.

        Args:
            user_id: User ID
            photo_data: Photo binary data
            filename: Original filename

        Returns:
            Upload result with file_id and URL
        """
        # Note: This is a simplified version. In practice, you'd use FormData
        # For now, this serves as a placeholder for the architecture
        return await self._request(
            "POST",
            "/media/upload",
            json_data={
                "user_id": user_id,
                "filename": filename,
                # Binary data would be sent via FormData in real implementation
            },
        )

    async def get_photo(self, file_id: str) -> Dict[str, Any]:
        """Get photo metadata.

        Args:
            file_id: Photo file ID

        Returns:
            Photo metadata
        """
        return await self._request("GET", f"/media/{file_id}")

    async def delete_photo(self, file_id: str) -> Dict[str, Any]:
        """Delete photo.

        Args:
            file_id: Photo file ID

        Returns:
            Deletion confirmation
        """
        return await self._request("DELETE", f"/media/{file_id}")

    # Discovery Service endpoints
    async def find_candidates(
        self, user_id: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find candidate profiles for discovery.

        Args:
            user_id: Current user ID
            filters: Optional filters (age, distance, etc.)

        Returns:
            List of candidate profiles
        """
        params = {"user_id": user_id}
        if filters:
            params.update(filters)

        result = await self._request("GET", "/discovery/candidates", params=params)
        return result.get("candidates", [])

    async def create_interaction(
        self, user_id: int, target_id: int, interaction_type: str
    ) -> Dict[str, Any]:
        """Create interaction (like, pass, superlike).

        Args:
            user_id: User performing interaction
            target_id: Target user ID
            interaction_type: Type of interaction

        Returns:
            Interaction result (with match info if applicable)
        """
        return await self._request(
            "POST",
            "/discovery/interactions",
            json_data={
                "user_id": user_id,
                "target_id": target_id,
                "type": interaction_type,
            },
        )

    async def get_matches(
        self, user_id: int, limit: int = 20, cursor: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get user's matches.

        Args:
            user_id: User ID
            limit: Maximum number of matches
            cursor: Pagination cursor

        Returns:
            Matches data with next cursor
        """
        params = {"user_id": user_id, "limit": limit}
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "/discovery/matches", params=params)

    # Auth Service endpoints
    async def authenticate(self, telegram_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate user and get JWT token.

        Args:
            telegram_id: Telegram user ID
            username: Optional username

        Returns:
            Authentication result with token
        """
        return await self._request(
            "POST",
            "/auth/telegram",
            json_data={"telegram_id": telegram_id, "username": username},
        )

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token.

        Args:
            token: JWT token

        Returns:
            Token validation result
        """
        return await self._request(
            "POST", "/auth/validate", json_data={"token": token}
        )
