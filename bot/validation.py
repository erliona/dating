"""Validation functions for profile data.

Epic B1: Profile form validation including age 18+ check.
"""

from datetime import date, datetime
from typing import Any, Optional

from .db import Education, Gender, Goal, Orientation


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()
    age = today.year - birth_date.year
    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def validate_name(name: str) -> tuple[bool, Optional[str]]:
    """Validate profile name.

    Args:
        name: User's display name

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Имя обязательно"

    if not isinstance(name, str):
        return False, "Имя должно быть строкой"

    name = name.strip()

    if len(name) < 2:
        return False, "Имя должно содержать минимум 2 символа"

    if len(name) > 100:
        return False, "Имя не может превышать 100 символов"

    return True, None


def validate_birth_date(birth_date: date) -> tuple[bool, Optional[str]]:
    """Validate birth date and check for 18+ age requirement.

    Args:
        birth_date: User's birth date

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not birth_date:
        return False, "Birth date is required"

    if not isinstance(birth_date, date):
        return False, "Invalid birth date format"

    if birth_date > date.today():
        return False, "Birth date cannot be in the future"

    age = calculate_age(birth_date)

    if age < 18:
        return False, "Вам должно быть не менее 18 лет"

    if age > 120:
        return False, "Неверная дата рождения"

    return True, None


def validate_gender(gender: str) -> tuple[bool, Optional[str]]:
    """Validate gender value.

    Args:
        gender: User's gender

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not gender:
        return False, "Пол обязателен"

    valid_genders = [g.value for g in Gender]

    if gender not in valid_genders:
        return False, f"Пол должен быть одним из: {', '.join(valid_genders)}"

    return True, None


def validate_orientation(orientation: str) -> tuple[bool, Optional[str]]:
    """Validate orientation value.

    Args:
        orientation: User's orientation preference

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not orientation:
        return False, "Ориентация обязательна"

    valid_orientations = [o.value for o in Orientation]

    if orientation not in valid_orientations:
        return (
            False,
            f"Ориентация должна быть одной из: {', '.join(valid_orientations)}",
        )

    return True, None


def validate_goal(goal: str) -> tuple[bool, Optional[str]]:
    """Validate goal value.

    Args:
        goal: User's relationship goal

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not goal:
        return False, "Цель обязательна"

    valid_goals = [g.value for g in Goal]

    if goal not in valid_goals:
        return False, f"Цель должна быть одной из: {', '.join(valid_goals)}"

    return True, None


def validate_bio(bio: Optional[str]) -> tuple[bool, Optional[str]]:
    """Validate bio text.

    Args:
        bio: User's bio/about text

    Returns:
        Tuple of (is_valid, error_message)
    """
    if bio is None:
        return True, None

    if not isinstance(bio, str):
        return False, "Bio must be a string"

    if len(bio) > 1000:
        return False, "Bio must not exceed 1000 characters"

    return True, None


def validate_interests(interests: Optional[list[str]]) -> tuple[bool, Optional[str]]:
    """Validate interests list.

    Args:
        interests: List of user's interests

    Returns:
        Tuple of (is_valid, error_message)
    """
    if interests is None:
        return True, None

    if not isinstance(interests, list):
        return False, "Interests must be a list"

    if len(interests) > 20:
        return False, "Maximum 20 interests allowed"

    for interest in interests:
        if not isinstance(interest, str):
            return False, "Each interest must be a string"

        if len(interest) > 50:
            return False, "Each interest must not exceed 50 characters"

    return True, None


def validate_height(height_cm: Optional[int]) -> tuple[bool, Optional[str]]:
    """Validate height value.

    Args:
        height_cm: Height in centimeters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if height_cm is None:
        return True, None

    if not isinstance(height_cm, int):
        return False, "Height must be an integer"

    if height_cm < 100 or height_cm > 250:
        return False, "Height must be between 100 and 250 cm"

    return True, None


def validate_education(education: Optional[str]) -> tuple[bool, Optional[str]]:
    """Validate education value.

    Args:
        education: User's education level

    Returns:
        Tuple of (is_valid, error_message)
    """
    if education is None:
        return True, None

    valid_education = [e.value for e in Education]

    if education not in valid_education:
        return False, f"Education must be one of: {', '.join(valid_education)}"

    return True, None


def validate_location(
    location_country_latitude: Optional[dict | str | float],
    city_longitude: Optional[str | float] = None,
    city: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Validate location data.

    Can be called with multiple signatures:
    1. Dict format: validate_location({"latitude": 55.7, "longitude": 37.6, "city": "Moscow"})
    2. Country/city format: validate_location("Russia", "Moscow")
    3. Coordinates format: validate_location(55.7, 37.6, "Moscow")

    Args:
        location_country_latitude: Dict with location data, country name, or latitude
        city_longitude: City name or longitude coordinate
        city: City name (only when using coordinates format)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Handle dict format (new API)
    if isinstance(location_country_latitude, dict):
        latitude = location_country_latitude.get("latitude")
        longitude = location_country_latitude.get("longitude")
        city = location_country_latitude.get("city")
        
        if latitude is not None:
            if not isinstance(latitude, (int, float)):
                return False, "Latitude must be a number"
            
            if latitude < -90 or latitude > 90:
                return False, "Latitude must be between -90 and 90"

        if longitude is not None:
            if not isinstance(longitude, (int, float)):
                return False, "Longitude must be a number"
            
            if longitude < -180 or longitude > 180:
                return False, "Longitude must be between -180 and 180"

        if city is not None:
            if not isinstance(city, str):
                return False, "City must be a string"

            if len(city) > 100:
                return False, "City name must not exceed 100 characters"
    
    # Handle coordinates format (latitude, longitude, city)
    elif isinstance(location_country_latitude, (int, float)) and isinstance(city_longitude, (int, float)):
        latitude = location_country_latitude
        longitude = city_longitude
        
        if not isinstance(latitude, (int, float)):
            return False, "Latitude must be a number"
        
        if latitude < -90 or latitude > 90:
            return False, "Latitude must be between -90 and 90"

        if not isinstance(longitude, (int, float)):
            return False, "Longitude must be a number"
        
        if longitude < -180 or longitude > 180:
            return False, "Longitude must be between -180 and 180"

        if city is not None:
            if not isinstance(city, str):
                return False, "City must be a string"

            if len(city) > 100:
                return False, "City name must not exceed 100 characters"
    
    # Handle country/city format (old API)
    else:
        country = location_country_latitude
        city = city_longitude
        
        if country is not None:
            if not isinstance(country, str):
                return False, "Country must be a string"

            if len(country) > 100:
                return False, "Country name must not exceed 100 characters"

        if city is not None:
            if not isinstance(city, str):
                return False, "City must be a string"

            if len(city) > 100:
                return False, "City name must not exceed 100 characters"

    return True, None


def validate_city(city: str) -> tuple[bool, Optional[str]]:
    """Validate city name.

    Args:
        city: City name

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not city:
        return False, "City is required"

    if not isinstance(city, str):
        return False, "City must be a string"

    if len(city) < 2:
        return False, "City name must be at least 2 characters"

    if len(city) > 100:
        return False, "City name must not exceed 100 characters"

    return True, None


def validate_profile_data(data: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate complete profile data.

    Args:
        data: Dictionary containing profile data

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_profile_data({
        ...     "name": "John Doe",
        ...     "birth_date": date(1990, 1, 1),
        ...     "gender": "male",
        ...     "orientation": "female",
        ...     "goal": "relationship"
        ... })
    """
    # Validate required fields
    required_fields = ["name", "birth_date", "gender", "orientation", "goal"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate name
    is_valid, error = validate_name(data["name"])
    if not is_valid:
        return False, error

    # Validate birth date (18+ check)
    birth_date = data["birth_date"]
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            return False, "Invalid birth date format, expected YYYY-MM-DD"

    is_valid, error = validate_birth_date(birth_date)
    if not is_valid:
        return False, error

    # Validate gender
    is_valid, error = validate_gender(data["gender"])
    if not is_valid:
        return False, error

    # Validate orientation
    is_valid, error = validate_orientation(data["orientation"])
    if not is_valid:
        return False, error

    # Validate goal
    is_valid, error = validate_goal(data["goal"])
    if not is_valid:
        return False, error

    # Validate optional fields
    if "bio" in data:
        is_valid, error = validate_bio(data["bio"])
        if not is_valid:
            return False, error

    if "interests" in data:
        is_valid, error = validate_interests(data["interests"])
        if not is_valid:
            return False, error

    if "height_cm" in data:
        is_valid, error = validate_height(data["height_cm"])
        if not is_valid:
            return False, error

    if "education" in data:
        is_valid, error = validate_education(data["education"])
        if not is_valid:
            return False, error

    # Validate location
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    city = data.get("city")
    is_valid, error = validate_location(latitude, longitude, city)
    if not is_valid:
        return False, error

    return True, None
