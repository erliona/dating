"""Tests for bot business logic and utility functions."""

from __future__ import annotations

import pytest

from bot.main import (
    Profile,
    build_profile_from_payload,
    normalise_choice,
    normalise_goal,
)


class TestNormaliseChoice:
    """Test suite for gender/preference normalization."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("М", "male"),
            ("male", "male"),
            ("m", "male"),
            ("муж", "male"),
            ("мужчина", "male"),
            ("Ж", "female"),
            ("female", "female"),
            ("f", "female"),
            ("жен", "female"),
            ("женщина", "female"),
            ("другой", "other"),
            ("o", "other"),
            ("other", "other"),
            ("инт", "other"),
            ("any", "any"),
            ("a", "any"),
            ("любой", "any"),
            ("anyone", "any"),
        ],
    )
    def test_normalise_choice_valid_values(self, value: str, expected: str) -> None:
        """Test normalization of valid gender/preference values."""
        assert normalise_choice(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            "unknown",
            "invalid",
            "123",
            "test",
        ],
    )
    def test_normalise_choice_invalid_values(self, value: str) -> None:
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError, match="Unexpected option"):
            normalise_choice(value)


class TestNormaliseGoal:
    """Test suite for goal normalization."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("serious", "serious"),
            ("relationship", "serious"),
            ("relationships", "serious"),
            ("отношения", "serious"),
            ("серьезные", "serious"),
            ("серьёзные", "serious"),
            ("серьезные отношения", "serious"),
            ("серьёзные отношения", "serious"),
            ("долгие", "serious"),
            ("долгие отношения", "serious"),
            ("семью", "serious"),
            ("брак", "serious"),
            ("long_term", "serious"),
            ("friendship", "friendship"),
            ("friends", "friendship"),
            ("дружба", "friendship"),
            ("дружбу", "friendship"),
            ("приятели", "friendship"),
            ("дружеское общение", "friendship"),
            ("найти друзей", "friendship"),
            ("networking", "networking"),
            ("общение", "networking"),
            ("компания", "networking"),
            ("общаться", "networking"),
            ("нетворкинг", "networking"),
            ("пообщаться", "networking"),
            ("casual", "casual"),
            ("fun", "casual"),
            ("легкие", "casual"),
            ("лёгкие", "casual"),
            ("легкие встречи", "casual"),
            ("лёгкие встречи", "casual"),
            ("без обязательств", "casual"),
            ("casual_dating", "casual"),
            ("флирт", "casual"),
        ],
    )
    def test_normalise_goal_valid_values(self, value: str, expected: str) -> None:
        """Test normalization of valid goal values."""
        assert normalise_goal(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            "unknown",
            "invalid",
            "test",
        ],
    )
    def test_normalise_goal_invalid_values(self, value: str) -> None:
        """Test that invalid goal values raise ValueError."""
        with pytest.raises(ValueError):
            normalise_goal(value)


class TestBuildProfileFromPayload:
    """Test suite for profile creation from webapp payload."""

    def test_build_profile_with_all_fields(self) -> None:
        """Test building a profile with all fields populated."""
        payload = {
            "name": "  Alice  ",
            "age": "25",
            "gender": "Ж",
            "preference": "М",
            "bio": "  Software engineer  ",
            "location": "  Moscow  ",
            "interests": ["music", "", " travel ", "coding"],
            "goal": "Серьёзные отношения",
            "photo_url": "  https://example.com/photo.jpg  ",
        }

        profile = build_profile_from_payload(12345, payload)

        assert profile.user_id == 12345
        assert profile.name == "Alice"
        assert profile.age == 25
        assert profile.gender == "female"
        assert profile.preference == "male"
        assert profile.bio == "Software engineer"
        assert profile.location == "Moscow"
        assert profile.interests == ["music", "travel", "coding"]
        assert profile.goal == "serious"
        assert profile.photo_url == "https://example.com/photo.jpg"

    def test_build_profile_with_minimal_fields(self) -> None:
        """Test building a profile with only required fields."""
        payload = {
            "name": "Bob",
            "age": "30",
            "gender": "male",
            "preference": "female",
        }

        profile = build_profile_from_payload(67890, payload)

        assert profile.user_id == 67890
        assert profile.name == "Bob"
        assert profile.age == 30
        assert profile.gender == "male"
        assert profile.preference == "female"
        assert profile.bio is None
        assert profile.location is None
        assert profile.interests == []
        assert profile.goal is None
        assert profile.photo_url is None

    def test_build_profile_validates_required_fields(self) -> None:
        """Test that missing required fields raise ValueError."""
        payload = {
            "name": "Alice",
            "age": "25",
            # Missing gender and preference
        }

        with pytest.raises(ValueError, match="Некорректные данные анкеты"):
            build_profile_from_payload(12345, payload)

    def test_build_profile_validates_empty_name(self) -> None:
        """Test that empty name is rejected."""
        payload = {
            "name": "   ",
            "age": "25",
            "gender": "female",
            "preference": "male",
        }

        with pytest.raises(ValueError, match="Имя не может быть пустым"):
            build_profile_from_payload(12345, payload)

    def test_build_profile_validates_minimum_age(self) -> None:
        """Test that age under 18 is rejected."""
        payload = {
            "name": "Alice",
            "age": "17",
            "gender": "female",
            "preference": "male",
        }

        with pytest.raises(ValueError, match="Возраст должен быть 18\\+"):
            build_profile_from_payload(12345, payload)

    def test_build_profile_validates_https_photo_url(self) -> None:
        """Test that non-HTTPS photo URLs are rejected."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "female",
            "preference": "male",
            "photo_url": "http://example.com/photo.jpg",
        }

        with pytest.raises(ValueError, match="HTTPS протокол"):
            build_profile_from_payload(12345, payload)

    def test_build_profile_accepts_https_photo_url(self) -> None:
        """Test that HTTPS photo URLs are accepted."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "female",
            "preference": "male",
            "photo_url": "https://example.com/photo.jpg",
        }

        profile = build_profile_from_payload(12345, payload)

        assert profile.photo_url == "https://example.com/photo.jpg"

    def test_build_profile_handles_interests_as_string(self) -> None:
        """Test that interests can be provided as comma-separated string."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "female",
            "preference": "male",
            "interests": "music, travel,  coding  , ",
        }

        profile = build_profile_from_payload(12345, payload)

        assert profile.interests == ["music", "travel", "coding"]

    def test_build_profile_handles_empty_optional_fields(self) -> None:
        """Test that empty optional fields are converted to None."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "female",
            "preference": "male",
            "bio": "",
            "location": "   ",
            "photo_url": "",
            "goal": "",
        }

        profile = build_profile_from_payload(12345, payload)

        assert profile.bio is None
        assert profile.location is None
        assert profile.photo_url is None
        assert profile.goal is None

    def test_build_profile_validates_invalid_gender(self) -> None:
        """Test that invalid gender values are rejected."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "invalid",
            "preference": "male",
        }

        with pytest.raises(ValueError, match="Некорректные данные анкеты"):
            build_profile_from_payload(12345, payload)

    def test_build_profile_validates_invalid_goal(self) -> None:
        """Test that invalid goal values are rejected."""
        payload = {
            "name": "Alice",
            "age": "25",
            "gender": "female",
            "preference": "male",
            "goal": "invalid_goal",
        }

        with pytest.raises(ValueError):
            build_profile_from_payload(12345, payload)
