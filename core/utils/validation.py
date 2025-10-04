"""Core validation utilities - platform independent."""

import re
from datetime import date


def validate_age(birth_date: date, min_age: int = 18, max_age: int = 100) -> bool:
    """Validate if age is within acceptable range.

    Args:
        birth_date: User's birth date
        min_age: Minimum acceptable age (default 18)
        max_age: Maximum acceptable age (default 100)

    Returns:
        True if age is valid

    Raises:
        ValueError: If age is outside acceptable range
    """
    today = date.today()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )

    if age < min_age:
        raise ValueError(f"User must be at least {min_age} years old")
    if age > max_age:
        raise ValueError(f"Invalid birth date (age {age} is too high)")

    return True


def validate_name(name: str, min_length: int = 2, max_length: int = 100) -> bool:
    """Validate user name.

    Args:
        name: User's name
        min_length: Minimum name length (default 2)
        max_length: Maximum name length (default 100)

    Returns:
        True if name is valid

    Raises:
        ValueError: If name is invalid
    """
    name = name.strip()

    if not name:
        raise ValueError("Name cannot be empty")

    if len(name) < min_length:
        raise ValueError(f"Name must be at least {min_length} characters")

    if len(name) > max_length:
        raise ValueError(f"Name must not exceed {max_length} characters")

    return True


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid

    Raises:
        ValueError: If email is invalid
    """
    if not email:
        raise ValueError("Email cannot be empty")

    # Simple email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValueError("Invalid email format")

    return True
