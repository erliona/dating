"""Tests for user interactions, matches, and settings repositories."""

from __future__ import annotations

import pytest

from bot.db import (
    Base,
    InteractionRepository,
    MatchRepository,
    ProfileModel,
    UserSettingsRepository,
)


@pytest.mark.asyncio
class TestUserSettingsRepository:
    """Test suite for UserSettingsRepository."""

    async def test_upsert_creates_new_settings(self, db_session_factory) -> None:
        """Test creating new user settings."""
        repo = UserSettingsRepository(db_session_factory)
        
        settings = await repo.upsert(
            user_id=12345,
            lang="en",
            show_location=False,
            notify_matches=True
        )
        
        assert settings.user_id == 12345
        assert settings.lang == "en"
        assert settings.show_location is False
        assert settings.notify_matches is True
        # Defaults
        assert settings.show_age is True
        assert settings.notify_messages is True

    async def test_upsert_updates_existing_settings(self, db_session_factory) -> None:
        """Test updating existing user settings."""
        repo = UserSettingsRepository(db_session_factory)
        
        # Create initial settings
        await repo.upsert(user_id=12345, lang="ru", show_location=True)
        
        # Update settings
        updated = await repo.upsert(user_id=12345, lang="en", show_age=False)
        
        assert updated.user_id == 12345
        assert updated.lang == "en"
        assert updated.show_age is False
        # Previous value should be preserved
        assert updated.show_location is True

    async def test_get_returns_settings(self, db_session_factory) -> None:
        """Test retrieving user settings."""
        repo = UserSettingsRepository(db_session_factory)
        
        # Create settings
        await repo.upsert(user_id=12345, lang="ru")
        
        # Retrieve settings
        settings = await repo.get(12345)
        
        assert settings is not None
        assert settings.user_id == 12345
        assert settings.lang == "ru"

    async def test_get_returns_none_for_nonexistent_user(self, db_session_factory) -> None:
        """Test that get returns None for non-existent user."""
        repo = UserSettingsRepository(db_session_factory)
        
        settings = await repo.get(99999)
        
        assert settings is None


@pytest.mark.asyncio
class TestInteractionRepository:
    """Test suite for InteractionRepository."""

    async def test_create_like_interaction(self, db_session_factory) -> None:
        """Test creating a like interaction."""
        repo = InteractionRepository(db_session_factory)
        
        interaction = await repo.create(
            from_user_id=12345,
            to_user_id=67890,
            action="like"
        )
        
        assert interaction.from_user_id == 12345
        assert interaction.to_user_id == 67890
        assert interaction.action == "like"

    async def test_create_dislike_interaction(self, db_session_factory) -> None:
        """Test creating a dislike interaction."""
        repo = InteractionRepository(db_session_factory)
        
        interaction = await repo.create(
            from_user_id=12345,
            to_user_id=67890,
            action="dislike"
        )
        
        assert interaction.from_user_id == 12345
        assert interaction.to_user_id == 67890
        assert interaction.action == "dislike"

    async def test_update_existing_interaction(self, db_session_factory) -> None:
        """Test updating an existing interaction."""
        repo = InteractionRepository(db_session_factory)
        
        # Create initial interaction
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        
        # Update to dislike
        updated = await repo.create(from_user_id=12345, to_user_id=67890, action="dislike")
        
        assert updated.from_user_id == 12345
        assert updated.to_user_id == 67890
        assert updated.action == "dislike"

    async def test_get_interaction(self, db_session_factory) -> None:
        """Test retrieving an interaction."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        
        interaction = await repo.get_interaction(12345, 67890)
        
        assert interaction is not None
        assert interaction.action == "like"

    async def test_get_interaction_returns_none_for_nonexistent(self, db_session_factory) -> None:
        """Test that get_interaction returns None for non-existent interaction."""
        repo = InteractionRepository(db_session_factory)
        
        interaction = await repo.get_interaction(12345, 67890)
        
        assert interaction is None

    async def test_check_mutual_like_both_liked(self, db_session_factory) -> None:
        """Test checking mutual like when both users liked each other."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        await repo.create(from_user_id=67890, to_user_id=12345, action="like")
        
        is_mutual = await repo.check_mutual_like(12345, 67890)
        
        assert is_mutual is True

    async def test_check_mutual_like_one_sided(self, db_session_factory) -> None:
        """Test checking mutual like when only one user liked."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        
        is_mutual = await repo.check_mutual_like(12345, 67890)
        
        assert is_mutual is False

    async def test_check_mutual_like_one_disliked(self, db_session_factory) -> None:
        """Test checking mutual like when one user disliked."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        await repo.create(from_user_id=67890, to_user_id=12345, action="dislike")
        
        is_mutual = await repo.check_mutual_like(12345, 67890)
        
        assert is_mutual is False

    async def test_get_liked_users(self, db_session_factory) -> None:
        """Test getting list of liked users."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        await repo.create(from_user_id=12345, to_user_id=11111, action="like")
        await repo.create(from_user_id=12345, to_user_id=22222, action="dislike")
        
        liked = await repo.get_liked_users(12345)
        
        assert len(liked) == 2
        assert 67890 in liked
        assert 11111 in liked
        assert 22222 not in liked

    async def test_get_disliked_users(self, db_session_factory) -> None:
        """Test getting list of disliked users."""
        repo = InteractionRepository(db_session_factory)
        
        await repo.create(from_user_id=12345, to_user_id=67890, action="like")
        await repo.create(from_user_id=12345, to_user_id=11111, action="dislike")
        await repo.create(from_user_id=12345, to_user_id=22222, action="dislike")
        
        disliked = await repo.get_disliked_users(12345)
        
        assert len(disliked) == 2
        assert 11111 in disliked
        assert 22222 in disliked
        assert 67890 not in disliked


@pytest.mark.asyncio
class TestMatchRepository:
    """Test suite for MatchRepository."""

    async def test_create_match(self, db_session_factory) -> None:
        """Test creating a match between two users."""
        repo = MatchRepository(db_session_factory)
        
        match = await repo.create(user1_id=12345, user2_id=67890)
        
        assert match.user1_id == 12345
        assert match.user2_id == 67890

    async def test_create_match_normalizes_order(self, db_session_factory) -> None:
        """Test that match creation normalizes user order."""
        repo = MatchRepository(db_session_factory)
        
        # Create with user2_id < user1_id
        match = await repo.create(user1_id=67890, user2_id=12345)
        
        # Should be normalized
        assert match.user1_id == 12345
        assert match.user2_id == 67890

    async def test_create_match_idempotent(self, db_session_factory) -> None:
        """Test that creating the same match twice returns the same match."""
        repo = MatchRepository(db_session_factory)
        
        match1 = await repo.create(user1_id=12345, user2_id=67890)
        match2 = await repo.create(user1_id=12345, user2_id=67890)
        
        assert match1.id == match2.id

    async def test_get_matches(self, db_session_factory) -> None:
        """Test getting all matches for a user."""
        repo = MatchRepository(db_session_factory)
        
        await repo.create(user1_id=12345, user2_id=67890)
        await repo.create(user1_id=12345, user2_id=11111)
        await repo.create(user1_id=22222, user2_id=12345)
        
        matches = await repo.get_matches(12345)
        
        assert len(matches) == 3
        assert 67890 in matches
        assert 11111 in matches
        assert 22222 in matches

    async def test_get_matches_empty(self, db_session_factory) -> None:
        """Test getting matches for user with no matches."""
        repo = MatchRepository(db_session_factory)
        
        matches = await repo.get_matches(12345)
        
        assert matches == []

    async def test_is_matched_true(self, db_session_factory) -> None:
        """Test checking if two users are matched."""
        repo = MatchRepository(db_session_factory)
        
        await repo.create(user1_id=12345, user2_id=67890)
        
        is_matched = await repo.is_matched(12345, 67890)
        
        assert is_matched is True

    async def test_is_matched_true_reversed(self, db_session_factory) -> None:
        """Test checking match with reversed user order."""
        repo = MatchRepository(db_session_factory)
        
        await repo.create(user1_id=12345, user2_id=67890)
        
        # Check with reversed order
        is_matched = await repo.is_matched(67890, 12345)
        
        assert is_matched is True

    async def test_is_matched_false(self, db_session_factory) -> None:
        """Test checking if two users are not matched."""
        repo = MatchRepository(db_session_factory)
        
        is_matched = await repo.is_matched(12345, 67890)
        
        assert is_matched is False
