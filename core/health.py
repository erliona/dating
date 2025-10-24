"""
Standardized health check utilities.
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_database_connection(database_url: str) -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        engine = create_async_engine(database_url)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        await engine.dispose()
        return {"status": "connected", "error": None}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


async def check_external_service(url: str, timeout: int = 5) -> Dict[str, Any]:
    """Check external service connectivity."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                if response.status < 400:
                    return {"status": "healthy", "error": None}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_standard_health_response(
    service_name: str,
    version: str = "1.0.0",
    database_status: Optional[Dict[str, Any]] = None,
    external_services: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate standardized health check response.
    
    Args:
        service_name: Name of the service
        version: Service version
        database_status: Database connectivity status
        external_services: External services status
        
    Returns:
        Standardized health check response
    """
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": version,
        "service": service_name
    }
    
    # Add database status if provided
    if database_status:
        response["database"] = database_status["status"]
        if database_status["error"]:
            response["status"] = "unhealthy"
            response["database_error"] = database_status["error"]
    
    # Add external services status if provided
    if external_services:
        response["external_services"] = {}
        for service_name, status in external_services.items():
            response["external_services"][service_name] = status["status"]
            if status["error"]:
                response["status"] = "unhealthy"
                response["external_services"][f"{service_name}_error"] = status["error"]
    
    return response


async def comprehensive_health_check(
    service_name: str,
    version: str = "1.0.0",
    database_url: Optional[str] = None,
    external_services: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Perform comprehensive health check.
    
    Args:
        service_name: Name of the service
        version: Service version
        database_url: Database connection URL
        external_services: Dict of service_name -> url
        
    Returns:
        Comprehensive health check response
    """
    database_status = None
    external_status = None
    
    # Check database if URL provided
    if database_url:
        database_status = await check_database_connection(database_url)
    
    # Check external services if provided
    if external_services:
        external_status = {}
        for service_name, url in external_services.items():
            external_status[service_name] = await check_external_service(url)
    
    return get_standard_health_response(
        service_name=service_name,
        version=version,
        database_status=database_status,
        external_services=external_status
    )
