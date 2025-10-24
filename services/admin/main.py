"""Admin service main entry point.

This microservice handles admin panel functionality including:
- User management
- Profile management
- Photo moderation
- System statistics
- Settings management
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiohttp
from aiohttp import web

from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import admin_jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service

logger = logging.getLogger(__name__)


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, params: dict = None):
    """Helper to call Data Service with retry logic."""
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


async def create_session_token(admin_id: int, secret: str) -> str:
    """Create a simple session token."""
    import secrets

    token = secrets.token_urlsafe(32)
    # In production, store this in Redis/database with expiry
    return token


async def verify_session_token(token: str, secret: str) -> Optional[int]:
    """Verify session token and return admin_id."""
    # In production, verify against Redis/database
    # For now, this is a placeholder
    return None


async def login_handler(request: web.Request) -> web.Response:
    """Admin login endpoint."""
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return web.json_response(
                {"error": "Username and password required"}, status=400
            )

        # For now, use a simple hardcoded admin
        # SECURITY: Use environment variables for admin credentials
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_password:
            logger.error("ADMIN_PASSWORD environment variable is required")
            return web.json_response(
                {"error": "Admin authentication not configured"}, status=500
            )
        
        if username == admin_username and password == admin_password:
            token = await create_session_token(1, request.app["config"]["jwt_secret"])
            return web.json_response(
                {
                    "token": token,
                    "admin": {
                        "id": 1,
                        "username": "admin",
                        "full_name": "Administrator",
                        "is_super_admin": True,
                    },
                }
            )
        else:
            return web.json_response({"error": "Invalid credentials"}, status=401)

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_stats_handler(request: web.Request) -> web.Response:
    """Get system statistics for dashboard."""
    try:
        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/stats",
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                return web.json_response(result, status=503)
            return web.json_response(result, status=500)
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def list_users_handler(request: web.Request) -> web.Response:
    """List users with pagination."""
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        search = request.query.get("search", "")

        data_service_url = request.app["data_service_url"]
        
        # Build query parameters
        params = {
            "page": page,
            "per_page": per_page,
        }
        if search:
            params["search"] = search
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/users",
            "GET",
            None,
            params,
            fallback=lambda *args: {"users": [], "total": 0, "page": page, "per_page": per_page}
        )
        
        if "error" in result:
            return web.json_response(result, status=500)
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_user_handler(request: web.Request) -> web.Response:
    """Get detailed user information."""
    try:
        user_id = int(request.match_info["user_id"])

        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/users/{user_id}",
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                return web.json_response(result, status=503)
            if "not found" in result.get("error", "").lower():
                return web.json_response(result, status=404)
            return web.json_response(result, status=500)
        
        return web.json_response(result)

    except ValueError:
        return web.json_response({"error": "Invalid user ID"}, status=400)
    except Exception as e:
        logger.error(f"Error getting user: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_user_handler(request: web.Request) -> web.Response:
    """Update user information."""
    try:
        user_id = int(request.match_info["user_id"])
        data = await request.json()

        data_service_url = request.app["data_service_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{data_service_url}/data/users/{user_id}", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                elif response.status == 404:
                    return web.json_response({"error": "User not found"}, status=404)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to update user"}, status=500)

    except ValueError:
        return web.json_response({"error": "Invalid user ID"}, status=400)
    except Exception as e:
        logger.error(f"Error updating user: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def list_photos_handler(request: web.Request) -> web.Response:
    """List photos for moderation."""
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        verified_only = request.query.get("verified") == "true"
        unverified_only = request.query.get("unverified") == "true"

        data_service_url = request.app["data_service_url"]
        
        # Build query parameters
        params = {
            "page": page,
            "per_page": per_page,
        }
        if verified_only:
            params["verified"] = "true"
        elif unverified_only:
            params["unverified"] = "true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/photos", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to list photos"}, status=500)

    except Exception as e:
        logger.error(f"Error listing photos: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_photo_handler(request: web.Request) -> web.Response:
    """Update photo (verify/reject)."""
    try:
        photo_id = int(request.match_info["photo_id"])
        data = await request.json()

        data_service_url = request.app["data_service_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{data_service_url}/data/photos/{photo_id}", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                elif response.status == 404:
                    return web.json_response({"error": "Photo not found"}, status=404)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to update photo"}, status=500)

    except ValueError:
        return web.json_response({"error": "Invalid photo ID"}, status=400)
    except Exception as e:
        logger.error(f"Error updating photo: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def delete_photo_handler(request: web.Request) -> web.Response:
    """Delete a photo."""
    try:
        photo_id = int(request.match_info["photo_id"])

        data_service_url = request.app["data_service_url"]
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{data_service_url}/data/photos/{photo_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                elif response.status == 404:
                    return web.json_response({"error": "Photo not found"}, status=404)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to delete photo"}, status=500)

    except ValueError:
        return web.json_response({"error": "Invalid photo ID"}, status=400)
    except Exception as e:
        logger.error(f"Error deleting photo: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "admin"})


def create_app(config: dict) -> web.Application:
    """Create and configure the admin service application."""
    app = web.Application()
    app["config"] = config
    app["data_service_url"] = config["data_service_url"]
    
    # Add standard middleware (NO JWT for public routes)
    from core.middleware.standard_stack import setup_standard_middleware_stack
    setup_standard_middleware_stack(app, "admin-service", use_auth=False, use_audit=False)
    
    # Add metrics endpoint
    add_metrics_route(app, "admin-service")

    # PUBLIC routes (NO JWT required)
    app.router.add_post("/admin/auth/login", login_handler)
    app.router.add_get("/health", health_check)
    
    # Serve admin panel static files
    app.router.add_static("/admin/", "services/admin/static/")
    
    # Redirect /admin/login to /admin/ for browser compatibility
    async def redirect_login(request):
        return web.HTTPFound('/admin/')
    app.router.add_get("/admin/login", redirect_login)
    
    # PROTECTED sub-application WITH JWT middleware
    from core.middleware.jwt_middleware import admin_jwt_middleware
    protected = web.Application(middlewares=[admin_jwt_middleware])
    protected.router.add_get("/admin/stats", get_stats_handler)
    protected.router.add_get("/admin/users", list_users_handler)
    protected.router.add_get("/admin/users/{user_id}", get_user_handler)
    protected.router.add_put("/admin/users/{user_id}", update_user_handler)
    protected.router.add_get("/admin/photos", list_photos_handler)
    protected.router.add_put("/admin/photos/{photo_id}", update_photo_handler)
    protected.router.add_delete("/admin/photos/{photo_id}", delete_photo_handler)
    
    # Mount protected app under /admin/api
    app.add_subapp("/admin/api/", protected)

    # Serve static files for admin panel
    app.router.add_static(
        "/admin-panel/",
        path=os.path.join(os.path.dirname(__file__), "static"),
        name="static",
    )

    return app


if __name__ == "__main__":
    # Configure structured logging
    configure_logging("admin-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
        "data_service_url": os.getenv("DATA_SERVICE_URL", "http://data-service:8088"),
        "host": os.getenv("ADMIN_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("ADMIN_SERVICE_PORT", 8086)),
    }

    logger.info(
        "Starting admin-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
