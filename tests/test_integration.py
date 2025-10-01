"""Integration tests for bot workflows and database interactions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.db import (
    Base,
    InteractionRepository,
    MatchRepository,
    ProfileRepository,
    UserSettingsRepository,
)
from bot.main import Profile, build_profile_from_payload, finalize_profile


@pytest.mark.asyncio
class TestProfileCreationWorkflow:
    """Integration tests for complete profile creation workflow."""

    async def test_complete_profile_creation_workflow(self, db_session_factory) -> None:
        """Test end-to-end profile creation from payload to database."""
        # Create repositories
        profile_repo = ProfileRepository(db_session_factory)
        settings_repo = UserSettingsRepository(db_session_factory)
        
        # Build profile from payload
        payload = {
            "name": "Alice",
            "age": 25,
            "gender": "female",
            "preference": "male",
            "bio": "Test bio",
            "location": "Moscow",
            "interests": ["music", "travel"],
            "goal": "serious",
            "photo_url": "https://example.com/photo.jpg"
        }
        
        user_id = 12345
        profile = build_profile_from_payload(user_id, payload)
        
        # Save profile to database
        await profile_repo.upsert(profile)
        
        # Retrieve and verify profile
        saved_profile = await profile_repo.get(user_id)
        assert saved_profile is not None
        assert saved_profile.user_id == user_id
        assert saved_profile.name == "Alice"
        assert saved_profile.age == 25
        assert saved_profile.gender == "female"
        assert saved_profile.preference == "male"
        assert saved_profile.bio == "Test bio"
        assert saved_profile.location == "Moscow"
        assert saved_profile.interests == ["music", "travel"]
        assert saved_profile.goal == "serious"
        assert saved_profile.photo_url == "https://example.com/photo.jpg"
        
        # Create default settings
        settings = await settings_repo.upsert(user_id=user_id)
        assert settings.user_id == user_id
        assert settings.lang == "ru"  # default

    async def test_profile_update_workflow(self, db_session_factory) -> None:
        """Test updating an existing profile."""
        profile_repo = ProfileRepository(db_session_factory)
        
        # Create initial profile
        initial_profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            bio="Initial bio"
        )
        await profile_repo.upsert(initial_profile)
        
        # Update profile
        updated_profile = Profile(
            user_id=12345,
            name="Alice Updated",
            age=26,
            gender="female",
            preference="any",
            bio="Updated bio",
            location="Saint Petersburg"
        )
        await profile_repo.upsert(updated_profile)
        
        # Verify update
        saved = await profile_repo.get(12345)
        assert saved is not None
        assert saved.name == "Alice Updated"
        assert saved.age == 26
        assert saved.preference == "any"
        assert saved.bio == "Updated bio"
        assert saved.location == "Saint Petersburg"


@pytest.mark.asyncio
class TestMatchingWorkflow:
    """Integration tests for user matching and interaction workflow."""

    async def test_complete_matching_workflow(self, db_session_factory) -> None:
        """Test complete workflow from like to match creation."""
        # Setup repositories
        profile_repo = ProfileRepository(db_session_factory)
        interaction_repo = InteractionRepository(db_session_factory)
        match_repo = MatchRepository(db_session_factory)
        
        # Create two profiles
        profile1 = Profile(
            user_id=111,
            name="Alice",
            age=25,
            gender="female",
            preference="male"
        )
        profile2 = Profile(
            user_id=222,
            name="Bob",
            age=28,
            gender="male",
            preference="female"
        )
        
        await profile_repo.upsert(profile1)
        await profile_repo.upsert(profile2)
        
        # Alice likes Bob
        await interaction_repo.create(111, 222, "like")
        
        # Check if mutual - should be False
        is_mutual = await interaction_repo.check_mutual_like(111, 222)
        assert is_mutual is False
        
        # Bob likes Alice back
        await interaction_repo.create(222, 111, "like")
        
        # Now check mutual - should be True
        is_mutual = await interaction_repo.check_mutual_like(111, 222)
        assert is_mutual is True
        
        # Create match
        match = await match_repo.create(111, 222)
        assert match is not None
        
        # Verify match exists
        is_matched = await match_repo.is_matched(111, 222)
        assert is_matched is True
        
        # Get matches for both users (returns list of user IDs)
        alice_matches = await match_repo.get_matches(111)
        bob_matches = await match_repo.get_matches(222)
        
        assert len(alice_matches) == 1
        assert len(bob_matches) == 1
        assert alice_matches[0] == 222
        assert bob_matches[0] == 111

    async def test_dislike_prevents_match(self, db_session_factory) -> None:
        """Test that dislike prevents match creation."""
        interaction_repo = InteractionRepository(db_session_factory)
        match_repo = MatchRepository(db_session_factory)
        
        # User 1 likes User 2
        await interaction_repo.create(111, 222, "like")
        
        # User 2 dislikes User 1
        await interaction_repo.create(222, 111, "dislike")
        
        # Check mutual like - should be False
        is_mutual = await interaction_repo.check_mutual_like(111, 222)
        assert is_mutual is False
        
        # Verify no match
        is_matched = await match_repo.is_matched(111, 222)
        assert is_matched is False

    async def test_interaction_update_workflow(self, db_session_factory) -> None:
        """Test changing interaction from like to dislike."""
        interaction_repo = InteractionRepository(db_session_factory)
        
        # Create initial like
        interaction = await interaction_repo.create(111, 222, "like")
        assert interaction.action == "like"
        
        # Change to dislike
        updated = await interaction_repo.create(111, 222, "dislike")
        assert updated.action == "dislike"
        
        # Verify the change
        retrieved = await interaction_repo.get_interaction(111, 222)
        assert retrieved is not None
        assert retrieved.action == "dislike"


@pytest.mark.asyncio
class TestUserSettingsWorkflow:
    """Integration tests for user settings management."""

    async def test_settings_creation_and_update(self, db_session_factory) -> None:
        """Test complete settings management workflow."""
        settings_repo = UserSettingsRepository(db_session_factory)
        
        # Create initial settings with defaults
        settings = await settings_repo.upsert(user_id=12345)
        assert settings.lang == "ru"
        assert settings.show_age is True
        assert settings.show_location is True
        assert settings.notify_matches is True
        
        # Update specific settings
        updated = await settings_repo.upsert(
            user_id=12345,
            lang="en",
            show_location=False,
            notify_matches=False
        )
        assert updated.lang == "en"
        assert updated.show_location is False
        assert updated.notify_matches is False
        # Verify unchanged fields remain
        assert updated.show_age is True
        
        # Retrieve and verify
        retrieved = await settings_repo.get(12345)
        assert retrieved is not None
        assert retrieved.lang == "en"
        assert retrieved.show_location is False


@pytest.mark.asyncio
class TestDatabaseConsistency:
    """Integration tests for database consistency and constraints."""

    async def test_profile_deletion_workflow(self, db_session_factory) -> None:
        """Test profile deletion and cleanup."""
        profile_repo = ProfileRepository(db_session_factory)
        
        # Create profile
        profile = Profile(
            user_id=12345,
            name="Test User",
            age=25,
            gender="male",
            preference="female"
        )
        await profile_repo.upsert(profile)
        
        # Verify exists
        assert await profile_repo.get(12345) is not None
        
        # Delete profile
        deleted = await profile_repo.delete(12345)
        assert deleted is True
        
        # Verify deleted
        assert await profile_repo.get(12345) is None
        
        # Try to delete again
        deleted_again = await profile_repo.delete(12345)
        assert deleted_again is False

    async def test_multiple_interactions_between_users(self, db_session_factory) -> None:
        """Test that interactions can be updated between the same users."""
        interaction_repo = InteractionRepository(db_session_factory)
        
        # Create like
        interaction1 = await interaction_repo.create(111, 222, "like")
        assert interaction1.action == "like"
        
        # Update to dislike
        interaction2 = await interaction_repo.create(111, 222, "dislike")
        assert interaction2.action == "dislike"
        
        # Update back to like
        interaction3 = await interaction_repo.create(111, 222, "like")
        assert interaction3.action == "like"
        
        # Verify only one interaction exists
        retrieved = await interaction_repo.get_interaction(111, 222)
        assert retrieved is not None
        assert retrieved.action == "like"

    async def test_match_idempotency(self, db_session_factory) -> None:
        """Test that creating the same match multiple times is idempotent."""
        match_repo = MatchRepository(db_session_factory)
        
        # Create match
        match1 = await match_repo.create(111, 222)
        match1_id = match1.id
        
        # Create same match again
        match2 = await match_repo.create(111, 222)
        match2_id = match2.id
        
        # Should return the same match
        assert match1_id == match2_id
        
        # Verify with reversed order
        match3 = await match_repo.create(222, 111)
        match3_id = match3.id
        
        assert match1_id == match3_id


@pytest.mark.asyncio
class TestSearchAndFiltering:
    """Integration tests for profile search and filtering."""

    async def test_find_mutual_match_with_preferences(self, db_session_factory) -> None:
        """Test finding compatible profiles based on preferences."""
        profile_repo = ProfileRepository(db_session_factory)
        
        # Create main user (male looking for female)
        main_profile = Profile(
            user_id=111,
            name="Bob",
            age=28,
            gender="male",
            preference="female"
        )
        await profile_repo.upsert(main_profile)
        
        # Create compatible profile (female looking for male)
        compatible = Profile(
            user_id=222,
            name="Alice",
            age=25,
            gender="female",
            preference="male"
        )
        await profile_repo.upsert(compatible)
        
        # Create incompatible profile (male looking for female)
        incompatible = Profile(
            user_id=333,
            name="Charlie",
            age=30,
            gender="male",
            preference="female"
        )
        await profile_repo.upsert(incompatible)
        
        # Find match for main user
        match = await profile_repo.find_mutual_match(main_profile)
        
        # Should find Alice, not Charlie
        assert match is not None
        assert match.user_id == 222
        assert match.name == "Alice"

    async def test_find_mutual_match_with_any_preference(self, db_session_factory) -> None:
        """Test matching with 'any' gender preference."""
        profile_repo = ProfileRepository(db_session_factory)
        
        # Create user with 'any' preference
        main_profile = Profile(
            user_id=111,
            name="Alex",
            age=28,
            gender="other",
            preference="any"
        )
        await profile_repo.upsert(main_profile)
        
        # Create another user looking for 'any'
        match_profile = Profile(
            user_id=222,
            name="Sam",
            age=25,
            gender="female",
            preference="any"
        )
        await profile_repo.upsert(match_profile)
        
        # Should find match
        match = await profile_repo.find_mutual_match(main_profile)
        assert match is not None
        assert match.user_id == 222

    async def test_find_mutual_match_excludes_self(self, db_session_factory) -> None:
        """Test that user is never matched with themselves."""
        profile_repo = ProfileRepository(db_session_factory)
        
        # Create single profile
        profile = Profile(
            user_id=111,
            name="Lonely User",
            age=28,
            gender="male",
            preference="male"  # Same gender as self
        )
        await profile_repo.upsert(profile)
        
        # Should not find self as match
        match = await profile_repo.find_mutual_match(profile)
        assert match is None
