"""Tests for bot/repository.py - database repository operations."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Photo, Profile, User
from bot.repository import ProfileRepository


@pytest.mark.asyncio
class TestProfileRepository:
    """Test ProfileRepository class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)
    
    async def test_create_or_update_user_new_user(self):
        """Test creating a new user."""
        repository = ProfileRepository(self.session)
        
        # Mock query result - user not found
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        self.session.flush = AsyncMock()
        
        user = await repository.create_or_update_user(
            tg_id=12345,
            username="testuser",
            first_name="Test",
            language_code="en",
            is_premium=True
        )
        
        # Verify user was added to session
        self.session.add.assert_called_once()
        self.session.flush.assert_called_once()
        
        # Verify user object
        added_user = self.session.add.call_args[0][0]
        assert isinstance(added_user, User)
        assert added_user.tg_id == 12345
        assert added_user.username == "testuser"
        assert added_user.first_name == "Test"
        assert added_user.language_code == "en"
        assert added_user.is_premium is True
    
    async def test_create_or_update_user_existing_user(self):
        """Test updating an existing user."""
        repository = ProfileRepository(self.session)
        
        # Mock existing user
        existing_user = User(
            id=1,
            tg_id=12345,
            username="oldusername",
            first_name="Old",
            language_code="ru",
            is_premium=False
        )
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_user
        self.session.execute = AsyncMock(return_value=result_mock)
        
        user = await repository.create_or_update_user(
            tg_id=12345,
            username="newusername",
            first_name="New",
            language_code="en",
            is_premium=True
        )
        
        # Verify user was updated
        assert user.username == "newusername"
        assert user.first_name == "New"
        assert user.language_code == "en"
        assert user.is_premium is True
        assert isinstance(user.updated_at, datetime)
        
        # Session.add should not be called for existing user
        self.session.add.assert_not_called()
    
    async def test_get_user_by_tg_id_found(self):
        """Test getting user by Telegram ID when found."""
        repository = ProfileRepository(self.session)
        
        mock_user = User(id=1, tg_id=12345, username="testuser")
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_user
        self.session.execute = AsyncMock(return_value=result_mock)
        
        user = await repository.get_user_by_tg_id(12345)
        
        assert user is not None
        assert user.tg_id == 12345
        assert user.username == "testuser"
    
    async def test_get_user_by_tg_id_not_found(self):
        """Test getting user by Telegram ID when not found."""
        repository = ProfileRepository(self.session)
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        
        user = await repository.get_user_by_tg_id(99999)
        
        assert user is None
    
    async def test_create_profile(self):
        """Test creating a new profile."""
        repository = ProfileRepository(self.session)
        self.session.flush = AsyncMock()
        
        profile_data = {
            "name": "John Doe",
            "birth_date": date(1990, 1, 1),
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
            "bio": "Test bio",
            "interests": ["music", "travel"],
            "height_cm": 180,
            "education": "bachelor",
            "has_children": False,
            "wants_children": True,
            "smoking": "never",
            "drinking": "socially",
            "country": "Russia",
            "city": "Moscow",
            "geohash": "ucfv0j82",
            "latitude": 55.7558,
            "longitude": 37.6173,
            "hide_distance": False,
            "hide_online": False,
            "hide_age": False,
            "allow_messages_from": "matches",
            "is_complete": True
        }
        
        profile = await repository.create_profile(1, profile_data)
        
        # Verify profile was added to session
        self.session.add.assert_called_once()
        self.session.flush.assert_called_once()
        
        # Verify profile object
        added_profile = self.session.add.call_args[0][0]
        assert isinstance(added_profile, Profile)
        assert added_profile.user_id == 1
        assert added_profile.name == "John Doe"
        assert added_profile.birth_date == date(1990, 1, 1)
        assert added_profile.gender == "male"
        assert added_profile.orientation == "female"
        assert added_profile.goal == "relationship"
        assert added_profile.bio == "Test bio"
        assert added_profile.interests == ["music", "travel"]
        assert added_profile.city == "Moscow"
    
    async def test_get_profile_by_user_id_found(self):
        """Test getting profile by user ID when found."""
        repository = ProfileRepository(self.session)
        
        mock_profile = Profile(
            id=1,
            user_id=1,
            name="John Doe",
            birth_date=date(1990, 1, 1),
            gender="male",
            orientation="female",
            goal="relationship"
        )
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_profile
        self.session.execute = AsyncMock(return_value=result_mock)
        
        profile = await repository.get_profile_by_user_id(1)
        
        assert profile is not None
        assert profile.user_id == 1
        assert profile.name == "John Doe"
    
    async def test_get_profile_by_user_id_not_found(self):
        """Test getting profile by user ID when not found."""
        repository = ProfileRepository(self.session)
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        
        profile = await repository.get_profile_by_user_id(999)
        
        assert profile is None
    
    async def test_update_profile_success(self):
        """Test updating an existing profile."""
        repository = ProfileRepository(self.session)
        
        existing_profile = Profile(
            id=1,
            user_id=1,
            name="Old Name",
            birth_date=date(1990, 1, 1),
            gender="male",
            orientation="female",
            goal="friendship",
            bio="Old bio"
        )
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_profile
        self.session.execute = AsyncMock(return_value=result_mock)
        
        update_data = {
            "name": "New Name",
            "bio": "New bio",
            "goal": "relationship"
        }
        
        profile = await repository.update_profile(1, update_data)
        
        assert profile is not None
        assert profile.name == "New Name"
        assert profile.bio == "New bio"
        assert profile.goal == "relationship"
        assert isinstance(profile.updated_at, datetime)
    
    async def test_update_profile_not_found(self):
        """Test updating a non-existent profile."""
        repository = ProfileRepository(self.session)
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        
        update_data = {"name": "New Name"}
        profile = await repository.update_profile(999, update_data)
        
        assert profile is None
    
    async def test_add_photo(self):
        """Test adding a photo to user's profile."""
        repository = ProfileRepository(self.session)
        self.session.flush = AsyncMock()
        
        photo = await repository.add_photo(
            user_id=1,
            url="https://example.com/photo.jpg",
            sort_order=0,
            safe_score=0.95,
            file_size=1024000,
            mime_type="image/jpeg",
            width=1200,
            height=1600
        )
        
        # Verify photo was added to session
        self.session.add.assert_called_once()
        self.session.flush.assert_called_once()
        
        # Verify photo object
        added_photo = self.session.add.call_args[0][0]
        assert isinstance(added_photo, Photo)
        assert added_photo.user_id == 1
        assert added_photo.url == "https://example.com/photo.jpg"
        assert added_photo.sort_order == 0
        assert added_photo.safe_score == 0.95
        assert added_photo.file_size == 1024000
        assert added_photo.mime_type == "image/jpeg"
        assert added_photo.width == 1200
        assert added_photo.height == 1600
    
    async def test_get_user_photos(self):
        """Test getting all photos for a user."""
        repository = ProfileRepository(self.session)
        
        mock_photos = [
            Photo(id=1, user_id=1, url="photo1.jpg", sort_order=0),
            Photo(id=2, user_id=1, url="photo2.jpg", sort_order=1),
            Photo(id=3, user_id=1, url="photo3.jpg", sort_order=2)
        ]
        
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = mock_photos
        result_mock.scalars.return_value = scalars_mock
        self.session.execute = AsyncMock(return_value=result_mock)
        
        photos = await repository.get_user_photos(1)
        
        assert len(photos) == 3
        assert photos[0].sort_order == 0
        assert photos[1].sort_order == 1
        assert photos[2].sort_order == 2
    
    async def test_delete_photo_success(self):
        """Test deleting a photo successfully."""
        repository = ProfileRepository(self.session)
        
        mock_photo = Photo(id=1, user_id=1, url="photo.jpg")
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_photo
        self.session.execute = AsyncMock(return_value=result_mock)
        self.session.delete = AsyncMock()
        
        result = await repository.delete_photo(photo_id=1, user_id=1)
        
        assert result is True
        self.session.delete.assert_called_once_with(mock_photo)
    
    async def test_delete_photo_not_found(self):
        """Test deleting a non-existent photo."""
        repository = ProfileRepository(self.session)
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        
        result = await repository.delete_photo(photo_id=999, user_id=1)
        
        assert result is False
        self.session.delete.assert_not_called()
    
    async def test_delete_photo_wrong_user(self):
        """Test deleting a photo with wrong user ID."""
        repository = ProfileRepository(self.session)
        
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        
        result = await repository.delete_photo(photo_id=1, user_id=999)
        
        assert result is False
