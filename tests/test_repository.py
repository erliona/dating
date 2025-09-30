from __future__ import annotations

from dataclasses import replace
import asyncio

from bot.db import ProfileRepository
from bot.main import Profile
from tests.conftest import FakeAsyncSessionMaker


def test_upsert_and_get_profile(session_factory: FakeAsyncSessionMaker) -> None:
    repository = ProfileRepository(session_factory)
    profile = Profile(
        user_id=123,
        name="Alice",
        age=25,
        gender="female",
        preference="male",
        bio="Likes hiking",
        location="Berlin",
        interests=["hiking", "music"],
        goal="serious",
        photo_url="https://example.com/photo.jpg",
    )

    asyncio.run(repository.upsert(profile))
    stored = asyncio.run(repository.get(profile.user_id))

    assert stored is not None
    assert stored.user_id == profile.user_id
    assert stored.name == profile.name
    assert stored.interests == profile.interests
    assert stored.photo_url == profile.photo_url

    updated = replace(profile, bio="Updated bio", interests=["reading"], goal="casual")
    asyncio.run(repository.upsert(updated))
    stored_again = asyncio.run(repository.get(profile.user_id))

    assert stored_again is not None
    assert stored_again.bio == "Updated bio"
    assert stored_again.interests == ["reading"]
    assert stored_again.goal == "casual"


def test_find_mutual_match(session_factory: FakeAsyncSessionMaker) -> None:
    repository = ProfileRepository(session_factory)
    seeker = Profile(
        user_id=1,
        name="Alex",
        age=28,
        gender="male",
        preference="female",
        goal="serious",
    )
    candidate = Profile(
        user_id=2,
        name="Bella",
        age=26,
        gender="female",
        preference="male",
        goal="serious",
    )
    incompatible = Profile(
        user_id=3,
        name="Chris",
        age=30,
        gender="male",
        preference="male",
        goal="casual",
    )

    asyncio.run(repository.upsert(seeker))
    asyncio.run(repository.upsert(candidate))
    asyncio.run(repository.upsert(incompatible))

    match = asyncio.run(repository.find_mutual_match(seeker))
    assert match is not None
    assert match.user_id == candidate.user_id

    no_match = asyncio.run(repository.find_mutual_match(candidate))
    assert no_match is not None
    assert no_match.user_id == seeker.user_id

    mismatch = asyncio.run(repository.find_mutual_match(incompatible))
    assert mismatch is None


def test_delete_profile(session_factory: FakeAsyncSessionMaker) -> None:
    repository = ProfileRepository(session_factory)
    profile = Profile(
        user_id=456,
        name="Bob",
        age=30,
        gender="male",
        preference="female",
        bio="Test bio",
    )

    # Create profile
    asyncio.run(repository.upsert(profile))
    stored = asyncio.run(repository.get(profile.user_id))
    assert stored is not None
    assert stored.user_id == profile.user_id

    # Delete profile
    deleted = asyncio.run(repository.delete(profile.user_id))
    assert deleted is True

    # Verify profile is gone
    stored_after_delete = asyncio.run(repository.get(profile.user_id))
    assert stored_after_delete is None

    # Try to delete non-existent profile
    deleted_again = asyncio.run(repository.delete(profile.user_id))
    assert deleted_again is False
