"""Alembic environment configuration."""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bot.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Resolve the database URL from environment variables or config."""

    return (
        os.getenv("BOT_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or "sqlite:///bot.db"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def _run_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
