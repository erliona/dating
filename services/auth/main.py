"""Auth service main entry point.

This microservice handles authentication and JWT token management,
independent of any specific platform.
"""

import logging
from aiohttp import web

from bot.security import validate_init_data, create_jwt_token, verify_jwt_token, RateLimiter

logger = logging.getLogger(__name__)


async def validate_telegram_init_data(request: web.Request) -> web.Response:
    """Validate Telegram WebApp initData and generate JWT token.
    
    POST /auth/validate
    Body: {
        "init_data": "telegram_init_data_string",
        "bot_token": "bot_token"
    }
    """
    try:
        data = await request.json()
        init_data = data.get('init_data')
        bot_token = data.get('bot_token')
        
        if not init_data or not bot_token:
            return web.json_response(
                {'error': 'Missing init_data or bot_token'},
                status=400
            )
        
        # Validate initData
        user_data = validate_init_data(init_data, bot_token)
        if not user_data:
            return web.json_response(
                {'error': 'Invalid init_data'},
                status=401
            )
        
        # Generate JWT token
        user_id = user_data.get('id')
        jwt_secret = request.app['config'].get('jwt_secret')
        token = create_jwt_token(user_id, jwt_secret)
        
        return web.json_response({
            'token': token,
            'user_id': user_id,
            'username': user_data.get('username')
        })
        
    except Exception as e:
        logger.error(f"Error validating init_data: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


async def verify_token(request: web.Request) -> web.Response:
    """Verify JWT token.
    
    GET /auth/verify
    Header: Authorization: Bearer <token>
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Missing or invalid Authorization header'},
                status=401
            )
        
        token = auth_header.split(' ')[1]
        jwt_secret = request.app['config'].get('jwt_secret')
        
        payload = verify_jwt_token(token, jwt_secret)
        if not payload:
            return web.json_response(
                {'error': 'Invalid or expired token'},
                status=401
            )
        
        return web.json_response({
            'valid': True,
            'user_id': payload.get('user_id')
        })
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


async def refresh_token(request: web.Request) -> web.Response:
    """Refresh JWT token.
    
    POST /auth/refresh
    Header: Authorization: Bearer <old_token>
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Missing or invalid Authorization header'},
                status=401
            )
        
        old_token = auth_header.split(' ')[1]
        jwt_secret = request.app['config'].get('jwt_secret')
        
        # Verify old token
        payload = verify_jwt_token(old_token, jwt_secret)
        if not payload:
            return web.json_response(
                {'error': 'Invalid or expired token'},
                status=401
            )
        
        # Generate new token
        user_id = payload.get('user_id')
        new_token = create_jwt_token(user_id, jwt_secret)
        
        return web.json_response({
            'token': new_token,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


def create_app(config: dict) -> web.Application:
    """Create and configure the auth service application."""
    app = web.Application()
    app['config'] = config
    
    # Add routes
    app.router.add_post('/auth/validate', validate_telegram_init_data)
    app.router.add_get('/auth/verify', verify_token)
    app.router.add_post('/auth/refresh', refresh_token)
    
    return app


if __name__ == '__main__':
    import os
    
    config = {
        'jwt_secret': os.getenv('JWT_SECRET', 'your-secret-key'),
        'host': os.getenv('AUTH_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('AUTH_SERVICE_PORT', 8081))
    }
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])
