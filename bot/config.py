"""Configuration helpers for the dating bot."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import quote_plus

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(slots=True)
class BotConfig:
    """Settings required to run the bot."""

    token: str
    database_url: str
    webapp_url: str | None = None
    jwt_secret: str | None = None
    photo_storage_path: str = "/app/photos"  # Path for local photo storage
    photo_cdn_url: str | None = None  # Optional CDN URL for serving photos
    nsfw_threshold: float = 0.7  # NSFW detection threshold (0.0-1.0, higher = stricter)


def load_config() -> BotConfig:
    """Load configuration values from environment variables.

    Returns:
        BotConfig: Populated configuration instance.

    Raises:
        RuntimeError: If the bot token is missing or configuration is invalid.
    """

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required to start the bot")
    
    # Validate token format (basic check)
    token = token.strip()
    if not token:
        raise RuntimeError("BOT_TOKEN cannot be empty or whitespace")
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        "your-",
        "replace-",
        "insert-",
        "paste-",
        "add-",
        "enter-",
        "example",
        "placeholder",
        "token-here",
        "bot-token",
        "from-botfather",
    ]
    token_lower = token.lower()
    if any(pattern in token_lower for pattern in placeholder_patterns):
        raise RuntimeError(
            "BOT_TOKEN appears to be a placeholder value. "
            "Please set a real Telegram bot token from @BotFather. "
            "Valid tokens have the format: <numeric_id>:<alphanumeric_hash> "
            "(example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567)"
        )
    
    # Validate Telegram bot token format: <numeric_id>:<alphanumeric_hash>
    # Bot tokens are typically in the format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
        raise RuntimeError(
            "BOT_TOKEN has invalid format. "
            "Telegram bot tokens must match the format: <numeric_id>:<alphanumeric_hash> "
            "(example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567). "
            "Get a valid token from @BotFather on Telegram."
        )

    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url and not webapp_url.strip():
        raise RuntimeError("WEBAPP_URL cannot be empty if set; unset it or provide a valid URL")
    
    # Validate WEBAPP_URL uses HTTPS for production security
    if webapp_url:
        webapp_url = webapp_url.strip()
        # Allow localhost and 127.0.0.1 for development/testing
        is_local = any(x in webapp_url.lower() for x in ["localhost", "127.0.0.1"])
        # Check protocol case-insensitively
        webapp_url_lower = webapp_url.lower()
        if not webapp_url_lower.startswith("https://") and not is_local:
            raise RuntimeError(
                "WEBAPP_URL must use HTTPS protocol for security. "
                "Only localhost URLs are allowed to use HTTP for local development."
            )
        
        # Normalize protocol to lowercase for consistency
        # Replace the protocol part (everything before ://) with lowercase version
        if "://" in webapp_url:
            protocol, rest = webapp_url.split("://", 1)
            webapp_url = protocol.lower() + "://" + rest
    
    database_url_raw = os.getenv("BOT_DATABASE_URL") or os.getenv("DATABASE_URL")
    
    # Fallback: construct database URL from POSTGRES_* environment variables
    # This is particularly useful in Docker Compose environments where these
    # variables are already set for the database container
    if not database_url_raw:
        postgres_user = os.getenv("POSTGRES_USER")
        postgres_password = os.getenv("POSTGRES_PASSWORD")
        postgres_host = os.getenv("POSTGRES_HOST", "db")  # Default to 'db' for docker-compose
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("POSTGRES_DB")
        
        # Validate required database credentials
        missing_vars = []
        if not postgres_user:
            missing_vars.append("POSTGRES_USER")
        if not postgres_password:
            missing_vars.append("POSTGRES_PASSWORD")
        if not postgres_db:
            missing_vars.append("POSTGRES_DB")
        
        if missing_vars:
            raise RuntimeError(
                f"Missing required database environment variables: {', '.join(missing_vars)}. "
                "Either set BOT_DATABASE_URL directly, or set POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
            )
        
        # Validate credentials are not empty or whitespace-only
        if not postgres_user.strip():
            raise RuntimeError("POSTGRES_USER cannot be empty or whitespace-only")
        if not postgres_password.strip():
            raise RuntimeError("POSTGRES_PASSWORD cannot be empty or whitespace-only")
        if not postgres_db.strip():
            raise RuntimeError("POSTGRES_DB cannot be empty or whitespace-only")
        
        # Check for common placeholder patterns in password
        password_placeholders = [
            "your-",
            "replace-",
            "change-",
            "example",
            "placeholder",
            "password-here",
            "changeme",
        ]
        password_lower = postgres_password.lower()
        if any(pattern in password_lower for pattern in password_placeholders):
            raise RuntimeError(
                "POSTGRES_PASSWORD appears to be a placeholder value. "
                "Please set a real secure password."
            )
        
        # Warn about weak passwords (only in development)
        if postgres_password in ["dating", "password", "admin", "root", "postgres", "test"]:
            import logging
            logging.warning(
                "⚠️  POSTGRES_PASSWORD is set to a common/weak value. "
                "This is acceptable for local development but MUST be changed for production deployments."
            )
        
        # URL-encode the username and password to handle special characters
        encoded_user = quote_plus(postgres_user)
        encoded_password = quote_plus(postgres_password)
        database_url_raw = (
            f"postgresql+asyncpg://{encoded_user}:{encoded_password}"
            f"@{postgres_host}:{postgres_port}/{postgres_db}"
        )

    try:
        database_url = make_url(database_url_raw)
    except ArgumentError as exc:  # pragma: no cover - simple configuration guard
        raise RuntimeError(
            "BOT_DATABASE_URL must be a valid SQLAlchemy connection string. "
            "If the password contains special characters, they must be URL-encoded. "
            "Use only alphanumeric characters (A-Z, a-z, 0-9, hyphen, underscore) for database passwords "
            "to avoid URL encoding issues."
        ) from exc

    if not database_url.drivername.startswith("postgresql"):
        raise RuntimeError(
            "Only PostgreSQL databases are supported; "
            "set BOT_DATABASE_URL to a postgresql+asyncpg URL"
        )
    
    # Validate database URL has required components
    if not database_url.host:
        raise RuntimeError("BOT_DATABASE_URL must include a database host")
    
    if not database_url.database:
        raise RuntimeError("BOT_DATABASE_URL must include a database name")
    
    # JWT secret for authentication (Epic A2)
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        # For development, generate a warning
        # For production, this should be required
        import logging
        logging.warning(
            "JWT_SECRET not set. For production, set JWT_SECRET environment variable. "
            "Using temporary secret for development (not suitable for production)."
        )
        # Generate a temporary secret for development
        import secrets
        jwt_secret = secrets.token_urlsafe(32)
    
    # Photo storage configuration
    photo_storage_path = os.getenv("PHOTO_STORAGE_PATH", "/app/photos")
    photo_cdn_url = os.getenv("PHOTO_CDN_URL")  # Optional CDN URL
    
    # NSFW detection threshold (0.0-1.0, higher = stricter)
    nsfw_threshold_str = os.getenv("NSFW_THRESHOLD", "0.7")
    try:
        nsfw_threshold = float(nsfw_threshold_str)
        if not 0.0 <= nsfw_threshold <= 1.0:
            logging.warning(f"Invalid NSFW_THRESHOLD {nsfw_threshold}, using default 0.7")
            nsfw_threshold = 0.7
    except ValueError:
        logging.warning(f"Invalid NSFW_THRESHOLD format, using default 0.7")
        nsfw_threshold = 0.7

    return BotConfig(
        token=token,
        database_url=database_url.render_as_string(hide_password=False),
        webapp_url=webapp_url,
        jwt_secret=jwt_secret,
        photo_storage_path=photo_storage_path,
        photo_cdn_url=photo_cdn_url,
        nsfw_threshold=nsfw_threshold
    )
