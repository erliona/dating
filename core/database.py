"""
Database connection pool configuration.
"""

import os
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool


def create_database_engine(
    database_url: str, pool_size: int = 20, max_overflow: int = 10
) -> Any:
    """Create database engine with connection pooling.

    Args:
        database_url: Database connection URL
        pool_size: Number of connections to maintain in pool
        max_overflow: Additional connections beyond pool_size

    Returns:
        Configured async engine
    """
    return create_async_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections every hour
        echo=False,  # Set to True for SQL logging
        future=True,
    )


def create_session_factory(engine) -> sessionmaker:
    """Create session factory for database operations.

    Args:
        engine: Database engine

    Returns:
        Configured session factory
    """
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_database_config() -> dict:
    """Get database configuration from environment.

    Returns:
        Database configuration dictionary
    """
    return {
        "database_url": os.getenv("DATABASE_URL"),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
    }


# Service-specific pool configurations
SERVICE_POOL_CONFIGS = {
    "data-service": {"pool_size": 20, "max_overflow": 10},
    "auth-service": {"pool_size": 10, "max_overflow": 5},
    "profile-service": {"pool_size": 15, "max_overflow": 8},
    "discovery-service": {"pool_size": 15, "max_overflow": 8},
    "chat-service": {"pool_size": 15, "max_overflow": 8},
    "media-service": {"pool_size": 10, "max_overflow": 5},
    "notification-service": {"pool_size": 10, "max_overflow": 5},
    "admin-service": {"pool_size": 5, "max_overflow": 3},
    "telegram-bot": {"pool_size": 5, "max_overflow": 3},
}


def get_service_pool_config(service_name: str) -> dict:
    """Get pool configuration for specific service.

    Args:
        service_name: Name of the service

    Returns:
        Pool configuration for the service
    """
    return SERVICE_POOL_CONFIGS.get(service_name, {"pool_size": 10, "max_overflow": 5})
