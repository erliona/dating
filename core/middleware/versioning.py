from __future__ import annotations

"""API versioning middleware."""
import logging

from aiohttp import web

logger = logging.getLogger(__name__)

DEFAULT_API_VERSION = "v1"


@web.middleware
async def versioning_middleware(request: web.Request, handler):
    """Extract and validate API version from path.

    Expects URLs like: /v1/profiles/123
    """
    path_parts = request.path.strip("/").split("/")

    # Check if first part is a version
    if path_parts and path_parts[0].startswith("v"):
        version = path_parts[0]
        # Store version in request for handlers to use
        request["api_version"] = version
    else:
        # Default version if not specified
        request["api_version"] = DEFAULT_API_VERSION
        logger.warning(
            f"No API version in path: {request.path}",
            extra={"event_type": "no_api_version", "path": request.path},
        )

    return await handler(request)
