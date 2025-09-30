from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bot.db import Base  # noqa: E402


class FakeAsyncSession:
    def __init__(self, sync_session: Session):
        self._session = sync_session

    async def __aenter__(self) -> "FakeAsyncSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self._session.close()

    async def scalar(self, statement):
        return self._session.scalar(statement)

    async def scalars(self, statement):
        return self._session.scalars(statement)

    def add(self, instance) -> None:
        self._session.add(instance)

    async def commit(self) -> None:
        self._session.commit()

    async def rollback(self) -> None:
        self._session.rollback()


class FakeAsyncSessionMaker:
    def __init__(self, sync_sessionmaker: sessionmaker):
        self._sync_sessionmaker = sync_sessionmaker

    def __call__(self) -> FakeAsyncSession:
        sync_session = self._sync_sessionmaker()
        return FakeAsyncSession(sync_session)


@pytest.fixture()
def session_factory() -> Iterator[FakeAsyncSessionMaker]:
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    sync_sessionmaker = sessionmaker(engine, expire_on_commit=False)
    factory = FakeAsyncSessionMaker(sync_sessionmaker)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
