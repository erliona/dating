"""Tests for core services - platform independent."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import User, UserProfile, UserSettings
from core.models.enums import Education, Gender, Goal, Orientation
from core.services import MatchingService, ProfileService, UserService


class MockUserRepository:
    """Mock implementation of IUserRepository for testing."""

    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def get_user(self, user_id: int):
        return self.users.get(user_id)

    async def create_user(self, user: User):
        user.id = self.next_id
        self.next_id += 1
        self.users[user.id] = user
        return user

    async def update_user(self, user: User):
        self.users[user.id] = user
        return user

    async def delete_user(self, user_id: int):
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False


class MockProfileRepository:
    """Mock implementation of IProfileRepository for testing."""

    def __init__(self):
        self.profiles = {}

    async def get_profile(self, user_id: int):
        return self.profiles.get(user_id)

    async def create_profile(self, profile: UserProfile):
        self.profiles[profile.user_id] = profile
        return profile

    async def update_profile(self, profile: UserProfile):
        self.profiles[profile.user_id] = profile
        return profile

    async def delete_profile(self, user_id: int):
        if user_id in self.profiles:
            del self.profiles[user_id]
            return True
        return False

    async def search_profiles(
        self, user_id: int, settings: UserSettings, limit: int = 10, offset: int = 0
    ):
        # Simple mock implementation
        return list(self.profiles.values())[:limit]


@pytest.mark.asyncio
async def test_user_service_create_user():
    """Test creating a user through UserService."""
    repo = MockUserRepository()
    service = UserService(repo)

    user = await service.create_user(
        username="testuser", first_name="Test", language_code="en"
    )

    assert user.id == 1
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.is_banned is False


@pytest.mark.asyncio
async def test_user_service_ban_user():
    """Test banning a user."""
    repo = MockUserRepository()
    service = UserService(repo)

    user = await service.create_user(username="testuser")
    assert user.is_banned is False

    await service.ban_user(user.id)

    banned_user = await service.get_user(user.id)
    assert banned_user.is_banned is True


@pytest.mark.asyncio
async def test_profile_service_create_profile():
    """Test creating a profile through ProfileService."""
    repo = MockProfileRepository()
    service = ProfileService(repo)

    profile = await service.create_profile(
        user_id=1,
        name="John Doe",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        orientation=Orientation.FEMALE,
        city="Moscow",
    )

    assert profile.user_id == 1
    assert profile.name == "John Doe"
    assert profile.gender == Gender.MALE
    assert profile.age == date.today().year - 1990


@pytest.mark.asyncio
async def test_profile_service_age_validation():
    """Test age validation in profile creation."""
    repo = MockProfileRepository()
    service = ProfileService(repo)

    # Try to create profile for user under 18
    with pytest.raises(ValueError, match="at least 18 years old"):
        await service.create_profile(
            user_id=1,
            name="Young User",
            birth_date=date.today().replace(year=date.today().year - 10),
            gender=Gender.MALE,
            orientation=Orientation.FEMALE,
            city="Moscow",
        )


@pytest.mark.asyncio
async def test_profile_service_add_photo():
    """Test adding photos to profile."""
    repo = MockProfileRepository()
    service = ProfileService(repo)

    # Create profile
    profile = await service.create_profile(
        user_id=1,
        name="John Doe",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        orientation=Orientation.FEMALE,
        city="Moscow",
    )

    # Add photo
    await service.add_photo(1, "photo1.jpg")

    profile = await service.get_profile(1)
    assert len(profile.photos) == 1
    assert "photo1.jpg" in profile.photos


@pytest.mark.asyncio
async def test_profile_service_max_photos():
    """Test maximum photo limit."""
    repo = MockProfileRepository()
    service = ProfileService(repo)

    # Create profile with 6 photos
    profile = await service.create_profile(
        user_id=1,
        name="John Doe",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        orientation=Orientation.FEMALE,
        city="Moscow",
        photos=["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg", "p5.jpg", "p6.jpg"],
    )

    # Try to add 7th photo
    with pytest.raises(ValueError, match="Maximum 6 photos"):
        await service.add_photo(1, "p7.jpg")


@pytest.mark.asyncio
async def test_matching_service_compatibility_score():
    """Test compatibility score calculation."""
    repo = MockProfileRepository()
    service = MatchingService(repo)

    profile1 = UserProfile(
        user_id=1,
        name="John",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        orientation=Orientation.FEMALE,
        city="Moscow",
        interests=["music", "sports", "travel"],
        goal=Goal.DATING,
        education=Education.BACHELOR,
        languages=["en", "ru"],
    )

    profile2 = UserProfile(
        user_id=2,
        name="Jane",
        birth_date=date(1992, 1, 1),
        gender=Gender.FEMALE,
        orientation=Orientation.MALE,
        city="Moscow",
        interests=["music", "travel", "food"],
        goal=Goal.DATING,
        education=Education.BACHELOR,
        languages=["en", "ru"],
    )

    score = service.calculate_compatibility_score(profile1, profile2)

    # Should have points for:
    # - Common interests (music, travel) = 16 points
    # - Same goal = 20 points
    # - Same education = 20 points
    # - Common languages (en, ru) = 20 points
    # Total should be 76
    assert score == 76.0


@pytest.mark.asyncio
async def test_matching_service_apply_filters():
    """Test applying user preference filters."""
    repo = MockProfileRepository()
    service = MatchingService(repo)

    settings = UserSettings(
        user_id=1, min_age=25, max_age=35, show_me=Orientation.FEMALE
    )

    profiles = [
        UserProfile(
            user_id=2,
            name="Jane",
            birth_date=date(1990, 1, 1),  # Age 34 (approx)
            gender=Gender.FEMALE,
            orientation=Orientation.MALE,
            city="Moscow",
            is_visible=True,
        ),
        UserProfile(
            user_id=3,
            name="Young",
            birth_date=date(2005, 1, 1),  # Age 19 (too young)
            gender=Gender.FEMALE,
            orientation=Orientation.MALE,
            city="Moscow",
            is_visible=True,
        ),
        UserProfile(
            user_id=4,
            name="Bob",
            birth_date=date(1990, 1, 1),  # Right age but wrong gender
            gender=Gender.MALE,
            orientation=Orientation.FEMALE,
            city="Moscow",
            is_visible=True,
        ),
    ]

    filtered = await service.apply_filters(profiles, settings)

    # Only Jane should pass all filters
    assert len(filtered) == 1
    assert filtered[0].name == "Jane"


def test_core_independence():
    """Test that core models don't depend on Telegram or any platform."""
    # This test verifies that core modules can be imported without Telegram dependencies
    from core.interfaces import IProfileRepository, IUserRepository
    from core.models import User, UserProfile, UserSettings
    from core.services import MatchingService, ProfileService, UserService

    # If we can import these without errors, core is platform-independent
    assert User is not None
    assert UserService is not None
    assert IUserRepository is not None
