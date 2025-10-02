"""Tests for geolocation utilities."""

import pytest

from bot.geo import (
    encode_geohash,
    get_default_location,
    get_location_precision,
    process_location_data,
    validate_coordinates,
)


class TestEncodeGeohash:
    """Tests for geohash encoding."""
    
    def test_encode_moscow(self):
        """Test geohash encoding for Moscow."""
        # Moscow coordinates
        geohash = encode_geohash(55.7558, 37.6173, precision=5)
        assert isinstance(geohash, str)
        assert len(geohash) == 5
        # Moscow geohash should start with 'u' (rough approximation)
        assert geohash[0] in ['u', 'v']
    
    def test_encode_new_york(self):
        """Test geohash encoding for New York."""
        # New York coordinates
        geohash = encode_geohash(40.7128, -74.0060, precision=5)
        assert isinstance(geohash, str)
        assert len(geohash) == 5
    
    def test_encode_different_precisions(self):
        """Test geohash with different precision levels."""
        lat, lon = 55.7558, 37.6173
        
        geohash3 = encode_geohash(lat, lon, precision=3)
        geohash5 = encode_geohash(lat, lon, precision=5)
        geohash7 = encode_geohash(lat, lon, precision=7)
        
        assert len(geohash3) == 3
        assert len(geohash5) == 5
        assert len(geohash7) == 7
        
        # Higher precision should start with same characters
        assert geohash5.startswith(geohash3)
        assert geohash7.startswith(geohash5)
    
    def test_encode_nearby_locations(self):
        """Test that nearby locations have similar geohashes."""
        # Two nearby points in Moscow
        geohash1 = encode_geohash(55.7558, 37.6173, precision=5)
        geohash2 = encode_geohash(55.7560, 37.6175, precision=5)
        
        # Should have at least 4 common characters (very close)
        common = sum(1 for a, b in zip(geohash1, geohash2) if a == b)
        assert common >= 4


class TestGetLocationPrecision:
    """Tests for location precision helper."""
    
    def test_precision_levels(self):
        """Test precision level descriptions."""
        assert "2500km" in get_location_precision(1)
        assert "5km" in get_location_precision(5)
        assert "150m" in get_location_precision(7)
    
    def test_unknown_precision(self):
        """Test unknown precision level."""
        assert "Unknown" in get_location_precision(99)


class TestValidateCoordinates:
    """Tests for coordinate validation."""
    
    def test_valid_coordinates(self):
        """Test valid coordinates."""
        is_valid, error = validate_coordinates(55.7558, 37.6173)
        assert is_valid is True
        assert error is None
    
    def test_valid_edge_cases(self):
        """Test valid edge case coordinates."""
        # North pole
        is_valid, _ = validate_coordinates(90.0, 0.0)
        assert is_valid is True
        
        # South pole
        is_valid, _ = validate_coordinates(-90.0, 0.0)
        assert is_valid is True
        
        # Date line
        is_valid, _ = validate_coordinates(0.0, 180.0)
        assert is_valid is True
        
        is_valid, _ = validate_coordinates(0.0, -180.0)
        assert is_valid is True
    
    def test_none_coordinates(self):
        """Test None coordinates."""
        is_valid, error = validate_coordinates(None, None)
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_invalid_latitude_high(self):
        """Test latitude above maximum."""
        is_valid, error = validate_coordinates(91.0, 0.0)
        assert is_valid is False
        assert "Latitude" in error
    
    def test_invalid_latitude_low(self):
        """Test latitude below minimum."""
        is_valid, error = validate_coordinates(-91.0, 0.0)
        assert is_valid is False
        assert "Latitude" in error
    
    def test_invalid_longitude_high(self):
        """Test longitude above maximum."""
        is_valid, error = validate_coordinates(0.0, 181.0)
        assert is_valid is False
        assert "Longitude" in error
    
    def test_invalid_longitude_low(self):
        """Test longitude below minimum."""
        is_valid, error = validate_coordinates(0.0, -181.0)
        assert is_valid is False
        assert "Longitude" in error


class TestGetDefaultLocation:
    """Tests for default location lookup."""
    
    def test_default_moscow(self):
        """Test default location (Moscow)."""
        location = get_default_location()
        assert location["country"] == "Russia"
        assert location["city"] == "Moscow"
        assert location["latitude"] == 55.7558
        assert location["longitude"] == 37.6173
        assert "geohash" in location
    
    def test_known_city(self):
        """Test known city lookup."""
        location = get_default_location("Russia", "Saint Petersburg")
        assert location["country"] == "Russia"
        assert location["city"] == "Saint Petersburg"
        assert location["latitude"] == 59.9311
        assert location["longitude"] == 30.3609
    
    def test_unknown_city_fallback(self):
        """Test unknown city falls back to Moscow."""
        location = get_default_location("Unknown Country", "Unknown City")
        # Should fallback to Moscow
        assert location["latitude"] == 55.7558
        assert location["longitude"] == 37.6173


class TestProcessLocationData:
    """Tests for location data processing."""
    
    def test_process_gps_coordinates(self):
        """Test processing with GPS coordinates."""
        location = process_location_data(
            latitude=55.7558,
            longitude=37.6173,
            country="Russia",
            city="Moscow"
        )
        
        assert location["latitude"] == 55.7558
        assert location["longitude"] == 37.6173
        assert location["country"] == "Russia"
        assert location["city"] == "Moscow"
        assert "geohash" in location
        assert len(location["geohash"]) == 5
    
    def test_process_manual_location(self):
        """Test processing with manual location selection."""
        location = process_location_data(
            country="Russia",
            city="Saint Petersburg"
        )
        
        assert location["country"] == "Russia"
        assert location["city"] == "Saint Petersburg"
        assert location["latitude"] == 59.9311
        assert location["longitude"] == 30.3609
        assert "geohash" in location
    
    def test_process_no_location(self):
        """Test processing with no location data (fallback)."""
        location = process_location_data()
        
        # Should fallback to Moscow
        assert location["country"] == "Russia"
        assert location["city"] == "Moscow"
        assert location["latitude"] == 55.7558
        assert location["longitude"] == 37.6173
    
    def test_process_custom_precision(self):
        """Test processing with custom geohash precision."""
        location = process_location_data(
            latitude=55.7558,
            longitude=37.6173,
            precision=7
        )
        
        assert len(location["geohash"]) == 7
    
    def test_process_invalid_coordinates_fallback(self):
        """Test that invalid coordinates fall back to manual selection."""
        location = process_location_data(
            latitude=999.0,  # Invalid
            longitude=999.0,  # Invalid
            country="Russia",
            city="Moscow"
        )
        
        # Should fallback to manual location
        assert location["country"] == "Russia"
        assert location["city"] == "Moscow"
        assert location["latitude"] == 55.7558
        assert location["longitude"] == 37.6173
