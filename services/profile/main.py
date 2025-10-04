"""Profile service main entry point.

This microservice handles user profile management using core services.
"""

import logging
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.services import ProfileService
from adapters.telegram.repository import TelegramProfileRepository
from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def get_profile(request: web.Request) -> web.Response:
    """Get user profile.
    
    GET /profiles/{user_id}
    """
    user_id = int(request.match_info['user_id'])
    
    profile_service: ProfileService = request.app['profile_service']
    profile = await profile_service.get_profile(user_id)
    
    if not profile:
        return web.json_response({'error': 'Profile not found'}, status=404)
    
    return web.json_response({
        'user_id': profile.user_id,
        'name': profile.name,
        'age': profile.age,
        'gender': profile.gender.value,
        'city': profile.city,
        'bio': profile.bio,
        'photos': profile.photos,
    })


async def create_profile(request: web.Request) -> web.Response:
    """Create user profile.
    
    POST /profiles
    """
    data = await request.json()
    profile_service: ProfileService = request.app['profile_service']
    
    try:
        from datetime import date
        from core.models.enums import Gender, Orientation
        
        profile = await profile_service.create_profile(
            user_id=data['user_id'],
            name=data['name'],
            birth_date=date.fromisoformat(data['birth_date']),
            gender=Gender(data['gender']),
            orientation=Orientation(data['orientation']),
            city=data['city'],
            bio=data.get('bio')
        )
        
        return web.json_response({
            'user_id': profile.user_id,
            'name': profile.name,
            'created': True
        }, status=201)
        
    except ValueError as e:
        return web.json_response({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({'status': 'healthy', 'service': 'profile'})


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app['config'] = config
    
    # Initialize database and services
    engine = create_async_engine(config['database_url'])
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create profile service with Telegram adapter
    async def get_session():
        async with async_session_maker() as session:
            return session
    
    # Store in app context (simplified - in production use dependency injection)
    app['engine'] = engine
    app['session_maker'] = async_session_maker
    
    # Add routes
    app.router.add_get('/profiles/{user_id}', get_profile)
    app.router.add_post('/profiles', create_profile)
    app.router.add_get('/health', health_check)
    
    return app


if __name__ == '__main__':
    import os
    
    # Configure structured logging
    configure_logging('profile-service', os.getenv('LOG_LEVEL', 'INFO'))
    
    config = {
        'database_url': os.getenv('DATABASE_URL', 'postgresql+asyncpg://dating:dating@localhost/dating'),
        'host': os.getenv('PROFILE_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('PROFILE_SERVICE_PORT', 8082))
    }
    
    logger.info("Starting profile-service", extra={"event_type": "service_start", "port": config['port']})
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])
