"""Geocoding integration for discovery service."""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

NOMINATIM_URL = "http://nominatim:8080"


async def reverse_geocode(lat: float, lon: float) -> dict[str, Any] | None:
    """
    Reverse geocode coordinates to get location information.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dictionary with location information or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "lat": str(lat),
                "lon": str(lon),
                "format": "json",
                "addressdetails": "1",
                "accept-language": "en",
            }

            async with session.get(f"{NOMINATIM_URL}/reverse", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "display_name": data.get("display_name", ""),
                        "city": data.get("address", {}).get("city", ""),
                        "country": data.get("address", {}).get("country", ""),
                        "country_code": data.get("address", {}).get("country_code", ""),
                        "state": data.get("address", {}).get("state", ""),
                        "postcode": data.get("address", {}).get("postcode", ""),
                    }
                else:
                    logger.warning(f"Geocoding failed: {resp.status}")
                    return None

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


async def geocode_address(address: str) -> dict[str, Any] | None:
    """
    Geocode address to get coordinates.

    Args:
        address: Address string

    Returns:
        Dictionary with coordinates or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "q": address,
                "format": "json",
                "limit": "1",
                "addressdetails": "1",
            }

            async with session.get(f"{NOMINATIM_URL}/search", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        result = data[0]
                        return {
                            "lat": float(result.get("lat", 0)),
                            "lon": float(result.get("lon", 0)),
                            "display_name": result.get("display_name", ""),
                            "city": result.get("address", {}).get("city", ""),
                            "country": result.get("address", {}).get("country", ""),
                        }
                    else:
                        logger.warning(f"No results for address: {address}")
                        return None
                else:
                    logger.warning(f"Geocoding failed: {resp.status}")
                    return None

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    import math

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Earth radius in kilometers
    r = 6371

    return c * r
