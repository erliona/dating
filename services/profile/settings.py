"""Settings endpoints for profile service."""

import logging
from aiohttp import web
from core.middleware.audit_logging import audit_log
from core.metrics.business_metrics import record_profile_updated
from core.exceptions import ValidationError, ExternalServiceError

logger = logging.getLogger(__name__)


async def get_user_preferences(request: web.Request) -> web.Response:
    """Get user preferences.
    
    GET /settings/preferences
    Headers: Authorization: Bearer <jwt_token>
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        # Call data service
        from services.profile.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/settings/preferences/{user_id}",
            "GET",
            request=request
        )
        
        # Log audit
        audit_log(
            service="profile-service",
            action="get_user_preferences",
            user_id=str(user_id),
            request=request
        )
        
        return web.json_response(result)
        
    except ExternalServiceError as e:
        logger.error(f"Data service error in get_user_preferences: {e}")
        return web.json_response({"error": "Preferences not found"}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in get_user_preferences: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_user_preferences(request: web.Request) -> web.Response:
    """Update user preferences.
    
    PUT /settings/preferences
    Headers: Authorization: Bearer <jwt_token>
    Body: { preferences data }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        data = await request.json()
        
        # Validate preferences data
        required_fields = ['age_range', 'distance', 'gender_preference']
        for field in required_fields:
            if field not in data:
                return web.json_response({"error": f"Missing required field: {field}"}, status=400)
        
        # Call data service
        from services.profile.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/settings/preferences/{user_id}",
            "PUT",
            data,
            request
        )
        
        # Record metrics
        record_profile_updated(
            service="profile-service",
            result="success",
            user_id=str(user_id)
        )
        
        # Log audit
        audit_log(
            service="profile-service",
            action="update_user_preferences",
            user_id=str(user_id),
            details={"fields_updated": list(data.keys())},
            request=request
        )
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in update_user_preferences: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in update_user_preferences: {e}")
        return web.json_response({"error": "Preferences update failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in update_user_preferences: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_notification_settings(request: web.Request) -> web.Response:
    """Get notification settings.
    
    GET /settings/notifications
    Headers: Authorization: Bearer <jwt_token>
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        # Call data service
        from services.profile.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/settings/notifications/{user_id}",
            "GET",
            request=request
        )
        
        # Log audit
        audit_log(
            service="profile-service",
            action="get_notification_settings",
            user_id=str(user_id),
            request=request
        )
        
        return web.json_response(result)
        
    except ExternalServiceError as e:
        logger.error(f"Data service error in get_notification_settings: {e}")
        return web.json_response({"error": "Notification settings not found"}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in get_notification_settings: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_notification_settings(request: web.Request) -> web.Response:
    """Update notification settings.
    
    PUT /settings/notifications
    Headers: Authorization: Bearer <jwt_token>
    Body: { notification settings }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        data = await request.json()
        
        # Validate notification settings
        valid_keys = ['matches', 'messages', 'likes', 'marketing', 'push_enabled']
        for key in data.keys():
            if key not in valid_keys:
                return web.json_response({"error": f"Invalid setting: {key}"}, status=400)
        
        # Call data service
        from services.profile.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/settings/notifications/{user_id}",
            "PUT",
            data,
            request
        )
        
        # Record metrics
        record_profile_updated(
            service="profile-service",
            result="success",
            user_id=str(user_id)
        )
        
        # Log audit
        audit_log(
            service="profile-service",
            action="update_notification_settings",
            user_id=str(user_id),
            details={"fields_updated": list(data.keys())},
            request=request
        )
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in update_notification_settings: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in update_notification_settings: {e}")
        return web.json_response({"error": "Notification settings update failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in update_notification_settings: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
