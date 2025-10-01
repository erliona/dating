"""Security utilities for the dating bot."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl

LOGGER = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    max_requests: int = 20  # Maximum requests per window
    window_seconds: int = 60  # Time window in seconds
    
    
class RateLimiter:
    """Simple in-memory rate limiter for bot handlers."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter with configuration.
        
        Args:
            config: Rate limit configuration. If None, uses defaults.
        """
        self.config = config or RateLimitConfig()
        self._requests: Dict[int, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        
    def is_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to make a request.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        
        # Cleanup old requests periodically (every 5 minutes)
        if current_time - self._last_cleanup > 300:
            self._cleanup_old_requests(current_time)
            self._last_cleanup = current_time
        
        # Get user's request history
        user_requests = self._requests[user_id]
        
        # Remove requests outside the current window
        cutoff_time = current_time - self.config.window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        # Check if limit exceeded
        if len(user_requests) >= self.config.max_requests:
            LOGGER.warning(
                "Rate limit exceeded for user %s: %d requests in %d seconds",
                user_id, len(user_requests), self.config.window_seconds
            )
            return False
        
        # Record this request
        user_requests.append(current_time)
        return True
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Remove old request data to prevent memory buildup."""
        cutoff_time = current_time - self.config.window_seconds
        users_to_remove = []
        
        for user_id, requests in self._requests.items():
            requests[:] = [req_time for req_time in requests if req_time > cutoff_time]
            if not requests:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self._requests[user_id]
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Get number of remaining requests for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Number of requests remaining in current window
        """
        current_time = time.time()
        user_requests = self._requests.get(user_id, [])
        cutoff_time = current_time - self.config.window_seconds
        active_requests = sum(1 for req_time in user_requests if req_time > cutoff_time)
        return max(0, self.config.max_requests - active_requests)


def validate_webapp_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 3600
) -> Optional[Dict[str, Any]]:
    """Validate Telegram WebApp initData and return parsed data.
    
    Implements the validation algorithm from Telegram documentation:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Args:
        init_data: The initData string from Telegram WebApp
        bot_token: Bot token for validation
        max_age_seconds: Maximum age of data in seconds (default 1 hour)
        
    Returns:
        Parsed data dictionary if valid, None if invalid
    """
    try:
        # Parse the query string
        parsed_data = dict(parse_qsl(init_data))
        
        # Extract and remove hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            LOGGER.warning("WebApp data missing hash")
            return None
        
        # Check auth_date (data freshness)
        auth_date_str = parsed_data.get('auth_date')
        if not auth_date_str:
            LOGGER.warning("WebApp data missing auth_date")
            return None
        
        try:
            auth_date = int(auth_date_str)
            current_time = int(time.time())
            if current_time - auth_date > max_age_seconds:
                LOGGER.warning(
                    "WebApp data too old: %d seconds (max %d)",
                    current_time - auth_date, max_age_seconds
                )
                return None
        except ValueError:
            LOGGER.warning("Invalid auth_date format: %s", auth_date_str)
            return None
        
        # Create data-check-string
        data_check_items = sorted(
            f"{k}={v}" for k, v in parsed_data.items()
        )
        data_check_string = '\n'.join(data_check_items)
        
        # Calculate hash
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Compare hashes
        if not hmac.compare_digest(calculated_hash, received_hash):
            LOGGER.warning("WebApp data hash mismatch")
            return None
        
        # Parse user data if present
        if 'user' in parsed_data:
            try:
                parsed_data['user'] = json.loads(parsed_data['user'])
            except json.JSONDecodeError:
                LOGGER.warning("Failed to parse user data from WebApp")
                return None
        
        LOGGER.info("WebApp data validated successfully for user %s", 
                   parsed_data.get('user', {}).get('id', 'unknown'))
        return parsed_data
        
    except Exception as exc:
        LOGGER.exception("Error validating WebApp data: %s", exc)
        return None


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes and other control characters (except newlines, tabs)
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t\r')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_profile_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate profile data from WebApp.
    
    Args:
        data: Profile data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required fields
    required_fields = ['name', 'age', 'gender', 'preference']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate name
    name = data.get('name', '')
    if not isinstance(name, str) or not name.strip():
        return False, "Name must be a non-empty string"
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # Validate age
    age = data.get('age')
    try:
        age = int(age)
        if age < 18:
            return False, "Age must be at least 18"
        if age > 120:
            return False, "Age must be less than 120"
    except (TypeError, ValueError):
        return False, "Age must be a valid number"
    
    # Validate gender
    gender = data.get('gender', '')
    valid_genders = ['male', 'female', 'other']
    if gender not in valid_genders:
        return False, f"Gender must be one of: {', '.join(valid_genders)}"
    
    # Validate preference
    preference = data.get('preference', '')
    valid_preferences = ['male', 'female', 'any']
    if preference not in valid_preferences:
        return False, f"Preference must be one of: {', '.join(valid_preferences)}"
    
    # Optional fields validation
    if 'bio' in data:
        bio = data.get('bio', '')
        if not isinstance(bio, str):
            return False, "Bio must be a string"
        if len(bio) > 1000:
            return False, "Bio must be less than 1000 characters"
    
    if 'location' in data:
        location = data.get('location', '')
        if not isinstance(location, str):
            return False, "Location must be a string"
        if len(location) > 200:
            return False, "Location must be less than 200 characters"
    
    if 'interests' in data:
        interests = data.get('interests', [])
        if not isinstance(interests, list):
            return False, "Interests must be a list"
        if len(interests) > 20:
            return False, "Too many interests (max 20)"
        for interest in interests:
            if not isinstance(interest, str):
                return False, "Each interest must be a string"
            if len(interest) > 50:
                return False, "Each interest must be less than 50 characters"
    
    if 'goal' in data:
        goal = data.get('goal', '')
        if not isinstance(goal, str):
            return False, "Goal must be a string"
        # Accept all common goal values and aliases
        valid_goals = [
            'friendship', 'dating', 'relationship', 'networking',
            'serious', 'casual', 'friends', 'fun'
        ]
        if goal and goal not in valid_goals:
            return False, f"Goal must be one of: {', '.join(valid_goals)}"
    
    return True, None
