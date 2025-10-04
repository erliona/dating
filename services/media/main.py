"""Media service main entry point.

This microservice handles photo/video upload, validation, and optimization.
"""

import logging
import os
from pathlib import Path
from aiohttp import web

from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def upload_media(request: web.Request) -> web.Response:
    """Upload media file.
    
    POST /media/upload
    Content-Type: multipart/form-data
    """
    try:
        reader = await request.multipart()
        field = await reader.next()
        
        if not field or field.name != 'file':
            return web.json_response({'error': 'No file provided'}, status=400)
        
        # Get storage path from config
        storage_path = request.app['config'].get('storage_path', '/app/photos')
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_id = str(uuid.uuid4())
        filename = field.filename or 'upload'
        ext = Path(filename).suffix or '.jpg'
        filepath = Path(storage_path) / f"{file_id}{ext}"
        
        # Save file
        size = 0
        with open(filepath, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)
        
        return web.json_response({
            'file_id': file_id,
            'filename': filename,
            'size': size,
            'url': f'/media/{file_id}'
        }, status=201)
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def get_media(request: web.Request) -> web.Response:
    """Get media file.
    
    GET /media/{file_id}
    """
    try:
        file_id = request.match_info['file_id']
        storage_path = request.app['config'].get('storage_path', '/app/photos')
        
        # Find file with any extension
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            filepath = Path(storage_path) / f"{file_id}{ext}"
            if filepath.exists():
                return web.FileResponse(filepath)
        
        return web.json_response({'error': 'File not found'}, status=404)
        
    except Exception as e:
        logger.error(f"Error getting media: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def delete_media(request: web.Request) -> web.Response:
    """Delete media file.
    
    DELETE /media/{file_id}
    """
    try:
        file_id = request.match_info['file_id']
        storage_path = request.app['config'].get('storage_path', '/app/photos')
        
        # Find and delete file
        deleted = False
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            filepath = Path(storage_path) / f"{file_id}{ext}"
            if filepath.exists():
                filepath.unlink()
                deleted = True
                break
        
        if not deleted:
            return web.json_response({'error': 'File not found'}, status=404)
        
        return web.json_response({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting media: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({'status': 'healthy', 'service': 'media'})


def create_app(config: dict) -> web.Application:
    """Create and configure the media service application."""
    app = web.Application()
    app['config'] = config
    
    # Add routes
    app.router.add_post('/media/upload', upload_media)
    app.router.add_get('/media/{file_id}', get_media)
    app.router.add_delete('/media/{file_id}', delete_media)
    app.router.add_get('/health', health_check)
    
    return app


if __name__ == '__main__':
    # Configure structured logging
    configure_logging('media-service', os.getenv('LOG_LEVEL', 'INFO'))
    
    config = {
        'storage_path': os.getenv('PHOTO_STORAGE_PATH', '/app/photos'),
        'host': os.getenv('MEDIA_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('MEDIA_SERVICE_PORT', 8084))
    }
    
    logger.info("Starting media-service", extra={"event_type": "service_start", "port": config['port']})
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])
