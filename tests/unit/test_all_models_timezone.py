"""Test timezone handling for all database models."""

from datetime import UTC, datetime

import pytest

from bot.db import Favorite, Interaction, Match, Photo, Profile, User

pytestmark = pytest.mark.unit


class TestUserModelTimezone:
    """Test User model timezone-aware datetime handling."""

    def test_user_model_accepts_timezone_aware_datetime(self):
        """Test that User model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)

        user = User(
            id=1,
            tg_id=123456789,
            username="test_user",
            first_name="Test",
            language_code="en",
            is_premium=False,
            is_banned=False,
            created_at=now_utc,
            updated_at=now_utc,
        )

        assert user.created_at == now_utc
        assert user.updated_at == now_utc
        assert user.created_at.tzinfo is not None
        assert user.updated_at.tzinfo is not None

    def test_user_model_fields_are_timezone_aware(self):
        """Test that User model has timezone-aware datetime columns."""
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")

        created_at_col = User.__table__.columns["created_at"]
        updated_at_col = User.__table__.columns["updated_at"]

        assert created_at_col.type.timezone is True
        assert updated_at_col.type.timezone is True


class TestProfileModelTimezone:
    """Test Profile model timezone-aware datetime handling."""

    def test_profile_model_accepts_timezone_aware_datetime(self):
        """Test that Profile model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)
        from datetime import date

        profile = Profile(
            id=1,
            user_id=1,
            name="Test User",
            birth_date=date(1990, 1, 1),
            gender="male",
            orientation="female",
            goal="dating",
            created_at=now_utc,
            updated_at=now_utc,
        )

        assert profile.created_at == now_utc
        assert profile.updated_at == now_utc
        assert profile.created_at.tzinfo is not None
        assert profile.updated_at.tzinfo is not None

    def test_profile_model_fields_are_timezone_aware(self):
        """Test that Profile model has timezone-aware datetime columns."""
        assert hasattr(Profile, "created_at")
        assert hasattr(Profile, "updated_at")

        created_at_col = Profile.__table__.columns["created_at"]
        updated_at_col = Profile.__table__.columns["updated_at"]

        assert created_at_col.type.timezone is True
        assert updated_at_col.type.timezone is True


class TestPhotoModelTimezone:
    """Test Photo model timezone-aware datetime handling."""

    def test_photo_model_accepts_timezone_aware_datetime(self):
        """Test that Photo model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)

        photo = Photo(
            id=1,
            user_id=1,
            url="https://example.com/photo.jpg",
            sort_order=0,
            safe_score=1.0,
            is_verified=False,
            created_at=now_utc,
        )

        assert photo.created_at == now_utc
        assert photo.created_at.tzinfo is not None

    def test_photo_model_fields_are_timezone_aware(self):
        """Test that Photo model has timezone-aware datetime columns."""
        assert hasattr(Photo, "created_at")

        created_at_col = Photo.__table__.columns["created_at"]

        assert created_at_col.type.timezone is True


class TestInteractionModelTimezone:
    """Test Interaction model timezone-aware datetime handling."""

    def test_interaction_model_accepts_timezone_aware_datetime(self):
        """Test that Interaction model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)

        interaction = Interaction(
            id=1,
            user_id=1,
            target_id=2,
            interaction_type="like",
            created_at=now_utc,
            updated_at=now_utc,
        )

        assert interaction.created_at == now_utc
        assert interaction.updated_at == now_utc
        assert interaction.created_at.tzinfo is not None
        assert interaction.updated_at.tzinfo is not None

    def test_interaction_model_fields_are_timezone_aware(self):
        """Test that Interaction model has timezone-aware datetime columns."""
        assert hasattr(Interaction, "created_at")
        assert hasattr(Interaction, "updated_at")

        created_at_col = Interaction.__table__.columns["created_at"]
        updated_at_col = Interaction.__table__.columns["updated_at"]

        assert created_at_col.type.timezone is True
        assert updated_at_col.type.timezone is True


class TestMatchModelTimezone:
    """Test Match model timezone-aware datetime handling."""

    def test_match_model_accepts_timezone_aware_datetime(self):
        """Test that Match model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)

        match = Match(
            id=1,
            user1_id=1,
            user2_id=2,
            created_at=now_utc,
        )

        assert match.created_at == now_utc
        assert match.created_at.tzinfo is not None

    def test_match_model_fields_are_timezone_aware(self):
        """Test that Match model has timezone-aware datetime columns."""
        assert hasattr(Match, "created_at")

        created_at_col = Match.__table__.columns["created_at"]

        assert created_at_col.type.timezone is True


class TestFavoriteModelTimezone:
    """Test Favorite model timezone-aware datetime handling."""

    def test_favorite_model_accepts_timezone_aware_datetime(self):
        """Test that Favorite model can be instantiated with timezone-aware datetimes."""
        now_utc = datetime.now(UTC)

        favorite = Favorite(
            id=1,
            user_id=1,
            target_id=2,
            created_at=now_utc,
        )

        assert favorite.created_at == now_utc
        assert favorite.created_at.tzinfo is not None

    def test_favorite_model_fields_are_timezone_aware(self):
        """Test that Favorite model has timezone-aware datetime columns."""
        assert hasattr(Favorite, "created_at")

        created_at_col = Favorite.__table__.columns["created_at"]

        assert created_at_col.type.timezone is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
