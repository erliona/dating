"""Shared pytest fixtures for the dating bot tests."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.cache import get_cache
from bot.db import Base, ProfileRepository


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear all environment variables that might affect configuration."""
    for key in (
        "BOT_TOKEN",
        "BOT_DATABASE_URL",
        "DATABASE_URL",
        "WEBAPP_URL",
        "DEBUG",
        "RUN_DB_MIGRATIONS",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
async def db_engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session_factory(db_engine):
    """Create a session factory for testing."""
    # Clear cache before each test to avoid interference
    cache = get_cache()
    cache.clear()
    
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(db_session_factory):
    """Provide a database session for tests."""
    async with db_session_factory() as session:
        yield session


@pytest.fixture
def profile_repository(db_session_factory):
    """Create a ProfileRepository instance for testing."""
    return ProfileRepository(db_session_factory)
