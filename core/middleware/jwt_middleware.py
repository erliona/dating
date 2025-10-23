"""JWT authentication middleware for all microservices."""

import logging
from typing import Optional
from aiohttp import web
from core.utils.security import validate_jwt_token, ValidationError
from core.middleware.security_metrics import record_jwt_validation, record_auth_failure
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# JWT validation metrics
JWT_TOKENS_EXPIRED = Counter(
    'jwt_tokens_expired_total',
    'Total expired JWT tokens',
    ['service']
)

JWT_VALIDATION_FAILED = Counter(
    'jwt_validation_failed_total',
    'Failed JWT validations',
    ['service', 'reason']
)


@web.middleware
async def jwt_middleware(request: web.Request, handler) -> web.Response:
    """
    JWT authentication middleware.
    
    Validates JWT tokens for all protected endpoints.
    Adds user_id to request context for authenticated requests.
    """
    
    # Пропустить health checks, metrics и sync-metrics
    if request.path.startswith('/health') or request.path.startswith('/metrics') or request.path.startswith('/sync-metrics'):
        return await handler(request)
    
    # Пропустить auth endpoints (кроме verify)
    if request.path.startswith('/auth/') and not request.path.startswith('/auth/verify'):
        return await handler(request)
    
    # Пропустить admin login
    if request.path == '/admin/login':
        return await handler(request)
    
    # Проверить JWT токен
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning(f"Missing Authorization header for {request.path}")
        record_auth_failure(
            service=request.app.get('service_name', 'unknown'),
            reason='missing_auth_header',
            user_id='unknown',
            path=request.path
        )
        return web.json_response(
            {'error': 'Missing or invalid Authorization header'}, 
            status=401
        )
    
    token = auth_header.split(' ')[1]
    jwt_secret = request.app.get('config', {}).get('jwt_secret')
    
    if not jwt_secret:
        logger.error("JWT secret not configured")
        return web.json_response(
            {'error': 'Server configuration error'}, 
            status=500
        )
    
    try:
        payload = validate_jwt_token(token, jwt_secret)
        user_id = payload.get('user_id')
        token_type = payload.get('token_type', 'access')
        
        if not user_id:
            logger.warning("JWT token missing user_id")
            record_jwt_validation(
                service=request.app.get('service_name', 'unknown'),
                result='failure',
                token_type=token_type,
                reason='missing_user_id',
                user_id='unknown'
            )
            return web.json_response(
                {'error': 'Invalid token: missing user_id'}, 
                status=401
            )
        
        # Добавить user_id в контекст запроса
        request['user_id'] = user_id
        request['jwt_payload'] = payload
        
        # Record successful validation
        record_jwt_validation(
            service=request.app.get('service_name', 'unknown'),
            result='success',
            token_type=token_type,
            user_id=str(user_id)
        )
        
        logger.debug(f"Authenticated user {user_id} for {request.path}")
        return await handler(request)
        
    except ValidationError as e:
        logger.warning(f"JWT validation failed: {e}")
        
        # Record JWT validation failure
        JWT_VALIDATION_FAILED.labels(
            service=request.app.get('service_name', 'unknown'),
            reason=str(e.code) if hasattr(e, 'code') else 'validation_error'
        ).inc()
        
        # Check if it's an expired token
        if 'expired' in str(e).lower():
            JWT_TOKENS_EXPIRED.labels(
                service=request.app.get('service_name', 'unknown')
            ).inc()
        
        record_jwt_validation(
            service=request.app.get('service_name', 'unknown'),
            result='failure',
            token_type='unknown',
            reason=str(e),
            user_id='unknown'
        )
        return web.json_response(
            {'error': f'Invalid token: {e}'}, 
            status=401
        )
    except Exception as e:
        logger.error(f"JWT middleware error: {e}")
        record_jwt_validation(
            service=request.app.get('service_name', 'unknown'),
            result='error',
            token_type='unknown',
            reason='middleware_error',
            user_id='unknown'
        )
        return web.json_response(
            {'error': 'Authentication error'}, 
            status=500
        )


@web.middleware
async def admin_jwt_middleware(request: web.Request, handler) -> web.Response:
    """
    Admin JWT authentication middleware.
    
    Validates admin JWT tokens for admin endpoints.
    """
    
    # Пропустить health checks, metrics и login
    if request.path.startswith('/health') or request.path.startswith('/metrics') or request.path == '/admin/login':
        return await handler(request)
    
    # Проверить admin JWT токен
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning(f"Missing Authorization header for admin endpoint {request.path}")
        return web.json_response(
            {'error': 'Missing or invalid Authorization header'}, 
            status=401
        )
    
    token = auth_header.split(' ')[1]
    jwt_secret = request.app.get('config', {}).get('jwt_secret')
    
    if not jwt_secret:
        logger.error("JWT secret not configured for admin service")
        return web.json_response(
            {'error': 'Server configuration error'}, 
            status=500
        )
    
    try:
        payload = validate_jwt_token(token, jwt_secret)
        admin_id = payload.get('admin_id')
        
        if not admin_id:
            logger.warning("Admin JWT token missing admin_id")
            return web.json_response(
                {'error': 'Invalid admin token: missing admin_id'}, 
                status=401
            )
        
        # Добавить admin_id в контекст запроса
        request['admin_id'] = admin_id
        request['jwt_payload'] = payload
        
        logger.debug(f"Authenticated admin {admin_id} for {request.path}")
        return await handler(request)
        
    except ValidationError as e:
        logger.warning(f"Admin JWT validation failed: {e}")
        return web.json_response(
            {'error': f'Invalid admin token: {e}'}, 
            status=401
        )
    except Exception as e:
        logger.error(f"Admin JWT middleware error: {e}")
        return web.json_response(
            {'error': 'Admin authentication error'}, 
            status=500
        )