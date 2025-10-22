"""Enhanced health check utilities with dependency validation."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple

import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker with dependency validation."""
    
    def __init__(self, service_name: str, dependencies: Optional[Dict[str, str]] = None):
        """
        Initialize health checker.
        
        Args:
            service_name: Name of the service
            dependencies: Dict of dependency name -> URL
        """
        self.service_name = service_name
        self.dependencies = dependencies or {}
    
    async def check_dependency(self, name: str, url: str) -> Tuple[bool, str]:
        """
        Check if a dependency is healthy.
        
        Args:
            name: Dependency name
            url: Dependency URL
            
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "healthy":
                            return True, f"{name} is healthy"
                        else:
                            return False, f"{name} returned unhealthy status"
                    else:
                        return False, f"{name} returned status {response.status}"
        except asyncio.TimeoutError:
            return False, f"{name} timeout after 5s"
        except Exception as e:
            return False, f"{name} error: {e}"
    
    async def check_all_dependencies(self) -> Dict[str, Dict[str, str]]:
        """
        Check all dependencies.
        
        Returns:
            Dict of dependency results
        """
        results = {}
        
        for name, url in self.dependencies.items():
            is_healthy, message = await self.check_dependency(name, url)
            results[name] = {
                "healthy": is_healthy,
                "message": message,
                "url": url
            }
        
        return results
    
    async def get_health_status(self) -> Dict:
        """
        Get comprehensive health status.
        
        Returns:
            Health status dict
        """
        # Check dependencies
        dependency_results = await self.check_all_dependencies()
        
        # Determine overall health
        all_healthy = all(result["healthy"] for result in dependency_results.values())
        
        status = {
            "status": "healthy" if all_healthy else "unhealthy",
            "service": self.service_name,
            "dependencies": dependency_results,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Log health check
        logger.info(
            f"Health check completed for {self.service_name}",
            extra={
                "event_type": "health_check",
                "service": self.service_name,
                "overall_healthy": all_healthy,
                "dependencies_checked": len(dependency_results),
                "unhealthy_dependencies": [
                    name for name, result in dependency_results.items() 
                    if not result["healthy"]
                ]
            }
        )
        
        return status


def create_health_checker(service_name: str, dependencies: Optional[Dict[str, str]] = None) -> HealthChecker:
    """Create a health checker instance."""
    return HealthChecker(service_name, dependencies)


async def simple_health_check(request: web.Request) -> web.Response:
    """Simple health check that only checks if service is running."""
    return web.json_response({
        "status": "healthy",
        "service": request.app.get("service_name", "unknown")
    })


async def enhanced_health_check(request: web.Request) -> web.Response:
    """Enhanced health check with dependency validation."""
    health_checker = request.app.get("health_checker")
    
    if not health_checker:
        # Fallback to simple health check
        return await simple_health_check(request)
    
    status = await health_checker.get_health_status()
    
    # Return appropriate HTTP status
    http_status = 200 if status["status"] == "healthy" else 503
    
    return web.json_response(status, status=http_status)
