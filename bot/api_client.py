"""API Gateway client for bot.

This module provides a thin client interface for the bot to communicate
with microservices through the API Gateway, eliminating direct database access.
"""

import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout

logger = logging.getLogger(__name__)


class APIGatewayClient:
    """Client for communicating with API Gateway and microservices."""

    def __init__(self, gateway_url: str, timeout_seconds: int = 30):
        """Initialize API Gateway client.

        Args:
            gateway_url: Base URL of API Gateway (e.g., http://api-gateway:8080)
            timeout_seconds: Request timeout in seconds
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout_seconds, connect=10)
        logger.info(
            "API Gateway client initialized",
            extra={"event_type": "api_client_init", "gateway_url": gateway_url},
        )

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API Gateway.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /profiles/123)
            json_data: Optional JSON body
            headers: Optional headers
            params: Optional query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            Exception: If request fails
        """
        url = f"{self.gateway_url}{path}"

        try:
            async with ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    headers=headers,
                    params=params,
                ) as resp:
                    response_data = await resp.json()

                    if resp.status >= 400:
                        logger.error(
                            f"API request failed: {method} {path}",
                            extra={
                                "event_type": "api_request_failed",
                                "method": method,
                                "path": path,
                                "status": resp.status,
                                "response": response_data,
                            },
                        )
                        raise Exception(
                            f"API request failed with status {resp.status}: "
                            f"{response_data.get('error', {}).get('message', 'Unknown error')}"
                        )

                    return response_data

        except Exception as e:
            logger.error(
                f"API request error: {method} {path} - {e}",
                exc_info=True,
                extra={
                    "event_type": "api_request_error",
                    "method": method,
                    "path": path,
                },
            )
            raise

    # Profile Service endpoints
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user profile via Profile Service.

        Args:
            profile_data: Profile data dictionary

        Returns:
            Created profile data
        """
        return await self._request("POST", "/profiles/", json_data=profile_data)

    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by ID.

        Args:
            user_id: User ID

        Returns:
            Profile data or None if not found
        """
        try:
            return await self._request("GET", f"/profiles/{user_id}")
        except Exception as e:
            if "404" in str(e):
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
