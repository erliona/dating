"""Verification endpoints for profile service."""

import logging
from aiohttp import web
from core.middleware.audit_logging import audit_log
from core.metrics.business_metrics import record_profile_updated
from core.exceptions import ValidationError, ExternalServiceError

logger = logging.getLogger(__name__)


async def request_verification(request: web.Request) -> web.Response:
    """Request profile verification.
    
    POST /profile/verification/request
    Headers: Authorization: Bearer <jwt_token>
    Body: { selfie_data }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        data = await request.json()
        
        # Validate verification data
        if not data.get('selfie_data'):
            return web.json_response({"error": "Selfie data is required"}, status=400)
        
        # Call data service
        from services.profile.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/profiles/{user_id}/verification",
            "POST",
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
            action="request_verification",
            user_id=str(user_id),
            details={"verification_requested": True},
            request=request
        )
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in request_verification: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in request_verification: {e}")
        return web.json_response({"error": "Verification request failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in request_verification: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
