"""JWT authentication middleware for all microservices."""

import logging
from typing import Optional
from aiohttp import web
from core.utils.security import validate_jwt_token, ValidationError

logger = logging.getLogger(__name__)


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
        
        if not user_id:
            logger.warning("JWT token missing user_id")
            return web.json_response(
                {'error': 'Invalid token: missing user_id'}, 
                status=401
            )
        
        # Добавить user_id в контекст запроса
        request['user_id'] = user_id
        request['jwt_payload'] = payload
        
        logger.debug(f"Authenticated user {user_id} for {request.path}")
        return await handler(request)
        
    except ValidationError as e:
        logger.warning(f"JWT validation failed: {e}")
        return web.json_response(
            {'error': f'Invalid token: {e}'}, 
            status=401
        )
    except Exception as e:
        logger.error(f"JWT middleware error: {e}")
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