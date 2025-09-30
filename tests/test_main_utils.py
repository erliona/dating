from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.config import BotConfig
from bot.db import ProfileRepository
from bot.main import (
    Profile,
    attach_bot_context,
    build_profile_from_payload,
    finalize_profile,
    get_config,
    get_repository,
    normalise_choice,
    normalise_goal,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("М", "male"),
        ("female", "female"),
        ("Any", "any"),
        ("ДРУГОЙ", "other"),
    ],
)
def test_normalise_choice(value: str, expected: str) -> None:
    assert normalise_choice(value) == expected


@pytest.mark.parametrize("value", ["", "unknown"])
def test_normalise_choice_invalid(value: str) -> None:
    with pytest.raises(ValueError):
        normalise_choice(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Серьёзные отношения", "serious"),
        ("дружба", "friendship"),
        ("общение", "networking"),
        ("лёгкие встречи", "casual"),
    ],
)
def test_normalise_goal(value: str, expected: str) -> None:
    assert normalise_goal(value) == expected


@pytest.mark.parametrize("value", ["", "something else"])
def test_normalise_goal_invalid(value: str) -> None:
    with pytest.raises(ValueError):
        normalise_goal(value)


def test_build_profile_from_payload() -> None:
    payload = {
        "name": "  Alice  ",
        "age": "23",
        "gender": "Ж",
        "preference": "М",
        "bio": "  Loves traveling  ",
        "location": "  Paris  ",
        "interests": ["music", "", " art "],
        "goal": "Серьёзные отношения",
        "photo_url": "  https://example.com/photo.jpg  ",
    }

    profile = build_profile_from_payload(42, payload)

    assert profile.user_id == 42
    assert profile.name == "Alice"
    assert profile.age == 23
    assert profile.gender == "female"
    assert profile.preference == "male"
    assert profile.bio == "Loves traveling"
    assert profile.location == "Paris"
    assert profile.interests == ["music", "art"]
    assert profile.goal == "serious"
    assert profile.photo_url == "https://example.com/photo.jpg"


def test_build_profile_from_payload_validates_required_fields() -> None:
    payload = {"name": "", "age": "17", "gender": "м", "preference": "ж"}
    with pytest.raises(ValueError):
        build_profile_from_payload(1, payload)


def test_build_profile_from_payload_validates_https_url() -> None:
    payload = {
        "name": "Alice",
        "age": "25",
        "gender": "female",
        "preference": "male",
        "photo_url": "http://example.com/photo.jpg",
    }
    with pytest.raises(ValueError, match="HTTPS"):
        build_profile_from_payload(1, payload)


def test_build_profile_from_payload_accepts_https_url() -> None:
    payload = {
        "name": "Alice",
        "age": "25",
        "gender": "female",
        "preference": "male",
        "photo_url": "https://example.com/photo.jpg",
    }
    profile = build_profile_from_payload(1, payload)
    assert profile.photo_url == "https://example.com/photo.jpg"


def test_attach_bot_context(session_factory) -> None:
    repository = ProfileRepository(session_factory)
    config = BotConfig(
        token="token",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/dating",
    )
    bot = SimpleNamespace()

    attach_bot_context(bot, config, repository)

    assert get_config(bot) is config
    assert get_repository(bot) is repository

    with pytest.raises(RuntimeError):
        get_config(None)


def test_finalize_profile_saves_data(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = AsyncMock(spec=ProfileRepository)
    repository.find_mutual_match.return_value = None

    def fake_get_repository(bot: object) -> ProfileRepository:
        return repository  # type: ignore[return-value]

    monkeypatch.setattr("bot.main.get_repository", fake_get_repository)

    message = SimpleNamespace(
        bot=SimpleNamespace(send_message=AsyncMock()),
        answer=AsyncMock(),
    )

    profile = Profile(
        user_id=111,
        name="User",
        age=30,
        gender="male",
        preference="female",
    )

    asyncio.run(finalize_profile(message, profile))

    repository.upsert.assert_awaited_once_with(profile)
    repository.find_mutual_match.assert_awaited_once_with(profile)
    message.answer.assert_awaited()


def test_finalize_profile_handles_repository_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_get_repository(bot: object) -> ProfileRepository:
        raise RuntimeError("missing repository")

    monkeypatch.setattr("bot.main.get_repository", failing_get_repository)

    message = SimpleNamespace(answer=AsyncMock(), bot=SimpleNamespace())
    profile = Profile(
        user_id=222,
        name="User",
        age=21,
        gender="female",
        preference="male",
    )

    asyncio.run(finalize_profile(message, profile))

    message.answer.assert_awaited()
