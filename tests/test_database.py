"""Tests for database models and repository."""

from __future__ import annotations

import pytest

from bot.db import ProfileModel, ProfileRepository
from bot.main import Profile


class TestProfileModel:
    """Test suite for ProfileModel ORM class."""

    def test_profile_model_creation(self) -> None:
        """Test creating a ProfileModel instance."""
        model = ProfileModel(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            bio="Test bio",
            location="Test City",
            interests=["music", "travel"],
            goal="serious",
            photo_url="https://example.com/photo.jpg",
        )

        assert model.user_id == 12345
        assert model.name == "Alice"
        assert model.age == 25
        assert model.gender == "female"
        assert model.preference == "male"
        assert model.bio == "Test bio"
        assert model.location == "Test City"
        assert model.interests == ["music", "travel"]
        assert model.goal == "serious"
        assert model.photo_url == "https://example.com/photo.jpg"

    def test_profile_model_to_profile(self) -> None:
        """Test converting ProfileModel to Profile dataclass."""
        model = ProfileModel(
            user_id=12345,
            name="Bob",
            age=30,
            gender="male",
            preference="female",
            interests=["sports", "gaming"],
        )

        profile = model.to_profile()

        assert isinstance(profile, Profile)
        assert profile.user_id == 12345
        assert profile.name == "Bob"
        assert profile.age == 30
        assert profile.gender == "male"
        assert profile.preference == "female"
        assert profile.interests == ["sports", "gaming"]

    def test_profile_model_from_profile(self) -> None:
        """Test creating ProfileModel from Profile dataclass."""
        profile = Profile(
            user_id=67890,
            name="Charlie",
            age=28,
            gender="male",
            preference="any",
            bio="Software developer",
            location="Moscow",
            interests=["coding", "reading"],
            goal="friendship",
            photo_url="https://example.com/charlie.jpg",
        )

        model = ProfileModel.from_profile(profile)

        assert model.user_id == 67890
        assert model.name == "Charlie"
        assert model.age == 28
        assert model.gender == "male"
        assert model.preference == "any"
        assert model.bio == "Software developer"
        assert model.location == "Moscow"
        assert model.interests == ["coding", "reading"]
        assert model.goal == "friendship"
        assert model.photo_url == "https://example.com/charlie.jpg"

    def test_profile_model_update_from_profile(self) -> None:
        """Test updating ProfileModel from Profile dataclass."""
        model = ProfileModel(
            user_id=11111,
            name="Old Name",
            age=20,
            gender="female",
            preference="male",
        )

        profile = Profile(
            user_id=11111,
            name="New Name",
            age=21,
            gender="female",
            preference="any",
            bio="Updated bio",
            interests=["art"],
        )

        model.update_from_profile(profile)

        assert model.name == "New Name"
        assert model.age == 21
        assert model.preference == "any"
        assert model.bio == "Updated bio"
        assert model.interests == ["art"]


class TestProfileRepository:
    """Test suite for ProfileRepository."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_profile(self, profile_repository: ProfileRepository) -> None:
        """Test that upsert creates a new profile when it doesn't exist."""
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
            bio="Test bio",
            interests=["music"],
        )

        await profile_repository.upsert(profile)

        retrieved = await profile_repository.get(12345)
        assert retrieved is not None
        assert retrieved.user_id == 12345
        assert retrieved.name == "Alice"
        assert retrieved.age == 25

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_profile(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that upsert updates an existing profile."""
        # Create initial profile
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
        )
        await profile_repository.upsert(profile)

        # Update the profile
        updated_profile = Profile(
            user_id=12345,
            name="Alice Updated",
            age=26,
            gender="female",
            preference="any",
            bio="New bio",
        )
        await profile_repository.upsert(updated_profile)

        retrieved = await profile_repository.get(12345)
        assert retrieved is not None
        assert retrieved.name == "Alice Updated"
        assert retrieved.age == 26
        assert retrieved.preference == "any"
        assert retrieved.bio == "New bio"

    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent_profile(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that get returns None when profile doesn't exist."""
        result = await profile_repository.get(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_profile(self, profile_repository: ProfileRepository) -> None:
        """Test that delete removes a profile."""
        profile = Profile(
            user_id=12345,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
        )
        await profile_repository.upsert(profile)

        deleted = await profile_repository.delete(12345)
        assert deleted is True

        retrieved = await profile_repository.get(12345)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_nonexistent_profile(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that delete returns False when profile doesn't exist."""
        deleted = await profile_repository.delete(99999)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_find_mutual_match_finds_compatible_profile(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that find_mutual_match finds compatible profiles."""
        # Create profile looking for male
        profile1 = Profile(
            user_id=1,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
        )
        await profile_repository.upsert(profile1)

        # Create matching profile looking for female
        profile2 = Profile(
            user_id=2,
            name="Bob",
            age=28,
            gender="male",
            preference="female",
        )

        match = await profile_repository.find_mutual_match(profile2)

        assert match is not None
        assert match.user_id == 1
        assert match.name == "Alice"

    @pytest.mark.asyncio
    async def test_find_mutual_match_excludes_self(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that find_mutual_match doesn't match a profile with itself."""
        profile = Profile(
            user_id=1,
            name="Alice",
            age=25,
            gender="female",
            preference="female",
        )
        await profile_repository.upsert(profile)

        match = await profile_repository.find_mutual_match(profile)

        assert match is None

    @pytest.mark.asyncio
    async def test_find_mutual_match_respects_gender_preferences(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that find_mutual_match respects gender preferences."""
        # Create female looking for male
        profile1 = Profile(
            user_id=1,
            name="Alice",
            age=25,
            gender="female",
            preference="male",
        )
        await profile_repository.upsert(profile1)

        # Try to match with female looking for female (should not match)
        profile2 = Profile(
            user_id=2,
            name="Eve",
            age=27,
            gender="female",
            preference="female",
        )

        match = await profile_repository.find_mutual_match(profile2)

        assert match is None

    @pytest.mark.asyncio
    async def test_find_mutual_match_with_any_preference(
        self, profile_repository: ProfileRepository
    ) -> None:
        """Test that 'any' preference matches with anyone interested."""
        # Create profile with 'any' preference
        profile1 = Profile(
            user_id=1,
            name="Alice",
            age=25,
            gender="female",
            preference="any",
        )
        await profile_repository.upsert(profile1)

        # Profile looking for female or any
        profile2 = Profile(
            user_id=2,
            name="Bob",
            age=28,
            gender="male",
            preference="any",
        )

        match = await profile_repository.find_mutual_match(profile2)

        assert match is not None
        assert match.user_id == 1
