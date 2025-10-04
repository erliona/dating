"""Discovery service main entry point.

This microservice handles matching algorithm and candidate discovery.
"""

import logging
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.services import MatchingService
from adapters.telegram.repository import TelegramProfileRepository
from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def get_candidates(request: web.Request) -> web.Response:
    """Get candidate profiles for matching.
    
    GET /discovery/candidates
    Query params: user_id, limit
    """
    try:
        user_id = int(request.query.get('user_id', 0))
        limit = int(request.query.get('limit', 10))
        
        if not user_id:
            return web.json_response({'error': 'user_id is required'}, status=400)
        
        # TODO: Implement candidate discovery using MatchingService
        # For now, return empty list
        return web.json_response({
            'candidates': [],
            'count': 0
        })
        
    except ValueError as e:
        return web.json_response({'error': 'Invalid parameters'}, status=400)
    except Exception as e:
        logger.error(f"Error getting candidates: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def like_profile(request: web.Request) -> web.Response:
    """Like a profile.
    
    POST /discovery/like
    Body: {"user_id": int, "target_id": int}
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        target_id = data.get('target_id')
        
        if not user_id or not target_id:
            return web.json_response(
                {'error': 'user_id and target_id are required'},
                status=400
            )
        
        # TODO: Implement like logic
        return web.json_response({
            'success': True,
            'matched': False
        })
        
    except Exception as e:
        logger.error(f"Error liking profile: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def get_matches(request: web.Request) -> web.Response:
    """Get user matches.
    
    GET /discovery/matches
    Query params: user_id
    """
    try:
        user_id = int(request.query.get('user_id', 0))
        
        if not user_id:
            return web.json_response({'error': 'user_id is required'}, status=400)
        
        # TODO: Implement matches retrieval
        return web.json_response({
            'matches': [],
            'count': 0
        })
        
    except Exception as e:
        logger.error(f"Error getting matches: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({'status': 'healthy', 'service': 'discovery'})


def create_app(config: dict) -> web.Application:
    """Create and configure the discovery service application."""
    app = web.Application()
    app['config'] = config
    
    # Initialize database connection
    engine = create_async_engine(config['database_url'])
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    app['engine'] = engine
    app['session_maker'] = async_session_maker
    
    # Add routes
    app.router.add_get('/discovery/candidates', get_candidates)
    app.router.add_post('/discovery/like', like_profile)
    app.router.add_get('/discovery/matches', get_matches)
    app.router.add_get('/health', health_check)
    
    return app


if __name__ == '__main__':
    import os
    
    # Configure structured logging
    configure_logging('discovery-service', os.getenv('LOG_LEVEL', 'INFO'))
    
    config = {
        'database_url': os.getenv('DATABASE_URL', 'postgresql+asyncpg://dating:dating@localhost/dating'),
        'host': os.getenv('DISCOVERY_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('DISCOVERY_SERVICE_PORT', 8083))
    }
    
    logger.info("Starting discovery-service", extra={"event_type": "service_start", "port": config['port']})
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])
