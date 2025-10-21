"""Geolocation utilities for privacy-preserving location storage.

Epic B3: Geolocation with manual fallback and geohash storage.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def encode_geohash(latitude: float, longitude: float, precision: int = 5) -> str:
    """Encode latitude/longitude to geohash for privacy.

    This is a simple implementation. For production, consider using
    a library like python-geohash or pygeohash.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        precision: Number of characters in geohash (default 5 for ~5km precision)

    Returns:
        Geohash string
    """
    base32 = "0123456789bcdefghjkmnpqrstuvwxyz"

    lat_min, lat_max = -90.0, 90.0
    lon_min, lon_max = -180.0, 180.0

    geohash = []
    bits = 0
    bit_count = 0
    even_bit = True

    while len(geohash) < precision:
        if even_bit:
            # Longitude
            mid = (lon_min + lon_max) / 2
            if longitude > mid:
                bits |= 1 << (4 - bit_count)
                lon_min = mid
            else:
                lon_max = mid
        else:
            # Latitude
            mid = (lat_min + lat_max) / 2
            if latitude > mid:
                bits |= 1 << (4 - bit_count)
                lat_min = mid
            else:
                lat_max = mid

        even_bit = not even_bit
        bit_count += 1

        if bit_count == 5:
            geohash.append(base32[bits])
            bits = 0
            bit_count = 0

    return "".join(geohash)


def get_location_precision(precision: int) -> str:
    """Get approximate area size for geohash precision.

    Args:
        precision: Geohash precision level

    Returns:
        Human-readable area size
    """
    precision_map = {
        1: "~2500km",
        2: "~630km",
        3: "~78km",
        4: "~20km",
        5: "~5km",
        6: "~1.2km",
        7: "~150m",
        8: "~38m",
    }
    return precision_map.get(precision, "Unknown")


def validate_coordinates(
    latitude: Optional[float], longitude: Optional[float]
) -> tuple[bool, Optional[str]]:
    """Validate latitude and longitude values.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        Tuple of (is_valid, error_message)
    """
    if latitude is None or longitude is None:
        return False, "Both latitude and longitude are required"

    if not isinstance(latitude, (int, float)):
        return False, "Latitude must be a number"

    if not isinstance(longitude, (int, float)):
        return False, "Longitude must be a number"

    if latitude < -90 or latitude > 90:
        return False, "Latitude must be between -90 and 90"

    if longitude < -180 or longitude > 180:
        return False, "Longitude must be between -180 and 180"

    return True, None


def get_default_location(country: Optional[str] = None, city: Optional[str] = None) -> dict:
    """Get default location coordinates for fallback.

    Args:
        country: Country name (default: Russia)
        city: City name (default: Moscow)

    Returns:
        Dictionary with location data
    """
    # Default locations for common cities
    locations = {
        ("Russia", "Moscow"): (55.7558, 37.6173),
        ("Russia", "Saint Petersburg"): (59.9311, 30.3609),
        ("Russia", "Novosibirsk"): (55.0084, 82.9357),
        ("Russia", "Yekaterinburg"): (56.8389, 60.6057),
        ("Russia", "Kazan"): (55.7887, 49.1221),
        ("Ukraine", "Kyiv"): (50.4501, 30.5234),
        ("Belarus", "Minsk"): (53.9006, 27.5590),
        ("Kazakhstan", "Almaty"): (43.2220, 76.8512),
        ("USA", "New York"): (40.7128, -74.0060),
        ("USA", "Los Angeles"): (34.0522, -118.2437),
        ("UK", "London"): (51.5074, -0.1278),
    }

    # Default to Russia/Moscow if not specified
    if country is None:
        country = "Russia"
    if city is None:
        city = "Moscow"

    # Look up coordinates
    coords = locations.get((country, city))

    if coords is None:
        # If not found, default to Moscow
        coords = locations[("Russia", "Moscow")]
        logger.warning(
            f"Unknown location {country}/{city}, defaulting to Moscow",
            extra={"event_type": "location_fallback"},
        )

    latitude, longitude = coords
    geohash = encode_geohash(latitude, longitude, precision=5)

    return {
        "country": country,
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "geohash": geohash,
    }


def process_location_data(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    precision: int = 5,
) -> dict:
    """Process location data with fallback to manual selection.

    Args:
        latitude: GPS latitude (optional)
        longitude: GPS longitude (optional)
        country: Manual country selection (optional)
        city: Manual city selection (optional)
        precision: Geohash precision for privacy (default 5 = ~5km)

    Returns:
        Dictionary with processed location data
    """
    # If GPS coordinates provided, use them
    if latitude is not None and longitude is not None:
        is_valid, error = validate_coordinates(latitude, longitude)

        if is_valid:
            geohash = encode_geohash(latitude, longitude, precision)

            logger.info(
                "Location processed from GPS",
                extra={
                    "event_type": "location_processed",
                    "method": "gps",
                    "precision": precision,
                },
            )

            return {
                "country": country,
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "geohash": geohash,
            }
        else:
            logger.warning(
                f"Invalid GPS coordinates: {error}",
                extra={"event_type": "location_invalid"},
            )

    # Fallback to manual location selection
    location = get_default_location(country, city)

    logger.info(
        "Location processed from manual selection",
        extra={
            "event_type": "location_processed",
            "method": "manual",
            "country": location["country"],
            "city": location["city"],
        },
    )

    return location
