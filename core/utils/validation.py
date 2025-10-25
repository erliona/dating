from __future__ import annotations

"""Input validation utilities for security and data integrity."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_string(
    value: Any,
    field_name: str,
    max_length: int = 255,
    min_length: int = 0,
    allow_empty: bool = True,
) -> str:
    """Validate and sanitize string input.

    Args:
        value: Input value to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        min_length: Minimum allowed length
        allow_empty: Whether empty strings are allowed

    Returns:
        Sanitized string value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_empty:
            return ""
        raise ValidationError(f"{field_name} is required")

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    # Remove leading/trailing whitespace
    value = value.strip()

    if not allow_empty and not value:
        raise ValidationError(f"{field_name} cannot be empty")

    if len(value) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters")

    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")

    return value


def validate_integer(
    value: Any,
    field_name: str,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Validate integer input.

    Args:
        value: Input value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Validated integer value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} is required")

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer") from None

    if min_value is not None and int_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and int_value > max_value:
        raise ValidationError(f"{field_name} cannot exceed {max_value}")

    return int_value


def validate_float(
    value: Any,
    field_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """Validate float input.

    Args:
        value: Input value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Validated float value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} is required")

    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number") from None

    if min_value is not None and float_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")

    if max_value is not None and float_value > max_value:
        raise ValidationError(f"{field_name} cannot exceed {max_value}")

    return float_value


def validate_boolean(value: Any, field_name: str) -> bool:
    """Validate boolean input.

    Args:
        value: Input value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated boolean value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} is required")

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False

    raise ValidationError(f"{field_name} must be a boolean value")


def validate_choice(value: Any, field_name: str, choices: list[str]) -> str:
    """Validate that value is one of the allowed choices.

    Args:
        value: Input value to validate
        field_name: Name of the field for error messages
        choices: List of allowed values

    Returns:
        Validated choice value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(f"{field_name} is required")

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    if value not in choices:
        raise ValidationError(f"{field_name} must be one of: {', '.join(choices)}")

    return value


def validate_username(username: str) -> str:
    """Validate Telegram username.

    Args:
        username: Username to validate

    Returns:
        Validated username

    Raises:
        ValidationError: If validation fails
    """
    if not username:
        return ""

    # Telegram usernames: 5-32 characters, alphanumeric + underscore
    if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
        raise ValidationError(
            "Username must be 5-32 characters, alphanumeric and underscores only"
        )

    return username


def validate_telegram_id(tg_id: Any) -> int:
    """Validate Telegram user ID.

    Args:
        tg_id: Telegram ID to validate

    Returns:
        Validated Telegram ID

    Raises:
        ValidationError: If validation fails
    """
    user_id = validate_integer(tg_id, "telegram_id", min_value=1)

    # Telegram user IDs are typically 8-10 digits
    if user_id < 10000000 or user_id > 999999999999:
        raise ValidationError("Invalid Telegram user ID format")

    return user_id


def validate_age(age: Any) -> int:
    """Validate age value.

    Args:
        age: Age to validate

    Returns:
        Validated age

    Raises:
        ValidationError: If validation fails
    """
    return validate_integer(age, "age", min_value=18, max_value=100)


def validate_height(height: Any) -> int:
    """Validate height in centimeters.

    Args:
        height: Height to validate

    Returns:
        Validated height

    Raises:
        ValidationError: If validation fails
    """
    return validate_integer(height, "height", min_value=100, max_value=250)


def validate_weight(weight: Any) -> float:
    """Validate weight in kilograms.

    Args:
        weight: Weight to validate

    Returns:
        Validated weight

    Raises:
        ValidationError: If validation fails
    """
    return validate_float(weight, "weight", min_value=30.0, max_value=300.0)


def validate_location(latitude: Any, longitude: Any) -> tuple[float, float]:
    """Validate geographic coordinates.

    Args:
        latitude: Latitude to validate
        longitude: Longitude to validate

    Returns:
        Validated (latitude, longitude) tuple

    Raises:
        ValidationError: If validation fails
    """
    lat = validate_float(latitude, "latitude", min_value=-90.0, max_value=90.0)
    lon = validate_float(longitude, "longitude", min_value=-180.0, max_value=180.0)

    return lat, lon


def validate_profile_data(data: dict[str, Any]) -> dict[str, Any]:
    """Validate complete profile data.

    Args:
        data: Profile data dictionary

    Returns:
        Validated and sanitized profile data

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Profile data must be a dictionary")

    validated: dict[str, Any] = {}

    # Required fields
    validated["tg_id"] = validate_telegram_id(data.get("tg_id"))
    validated["first_name"] = validate_string(
        data.get("first_name"), "first_name", max_length=100, allow_empty=False
    )

    # Optional fields
    if "username" in data:
        validated["username"] = validate_username(data["username"])

    if "age" in data:
        validated["age"] = int(validate_age(data["age"]))

    if "gender" in data:
        validated["gender"] = validate_choice(
            data["gender"], "gender", ["male", "female", "other"]
        )

    if "orientation" in data:
        validated["orientation"] = validate_choice(
            data["orientation"],
            "orientation",
            ["straight", "gay", "lesbian", "bisexual", "pansexual", "asexual"],
        )

    if "height" in data:
        validated["height"] = int(validate_height(data["height"]))

    if "weight" in data:
        validated["weight"] = float(validate_weight(data["weight"]))

    if "bio" in data:
        validated["bio"] = validate_string(
            data["bio"], "bio", max_length=1000, allow_empty=True
        )

    if "goal" in data:
        validated["goal"] = validate_choice(
            data["goal"],
            "goal",
            ["dating", "friendship", "relationship", "marriage", "casual"],
        )

    if "has_children" in data:
        validated["has_children"] = validate_boolean(
            data["has_children"], "has_children"
        )

    if "smoking" in data:
        validated["smoking"] = validate_boolean(data["smoking"], "smoking")

    if "drinking" in data:
        validated["drinking"] = validate_boolean(data["drinking"], "drinking")

    if "education" in data:
        validated["education"] = validate_choice(
            data["education"],
            "education",
            ["high_school", "college", "university", "graduate", "other"],
        )

    if "latitude" in data and "longitude" in data:
        lat, lon = validate_location(data["latitude"], data["longitude"])
        validated["latitude"] = lat
        validated["longitude"] = lon

    # Copy other fields that don't need special validation
    for key in ["language_code", "is_premium", "is_banned"]:
        if key in data:
            validated[key] = data[key]

    return validated


def sanitize_html(text: str) -> str:
    """Basic HTML sanitization to prevent XSS.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    import html

    text = html.unescape(text)

    return text.strip()
