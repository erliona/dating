"""Tests for profile validation functions."""

from datetime import date, timedelta

import pytest

from bot.validation import (
    ValidationError,
    calculate_age,
    validate_bio,
    validate_birth_date,
    validate_education,
    validate_gender,
    validate_goal,
    validate_height,
    validate_interests,
    validate_location,
    validate_name,
    validate_orientation,
    validate_profile_data,
)


class TestCalculateAge:
    """Tests for age calculation."""

    def test_calculate_age_exact_birthday(self):
        """Test age calculation when today is exact birthday."""
        birth_date = date.today().replace(year=date.today().year - 25)
        assert calculate_age(birth_date) == 25

    def test_calculate_age_before_birthday(self):
        """Test age calculation before birthday this year."""
        today = date.today()
        # Create a birth date that hasn't occurred yet this year
        birth_date = date(today.year - 25, today.month, today.day) + timedelta(days=1)
        if birth_date > today:
            assert calculate_age(birth_date) == 24

    def test_calculate_age_after_birthday(self):
        """Test age calculation after birthday this year."""
        today = date.today()
        # Create a birth date that has already occurred this year
        birth_date = date(today.year - 25, today.month, today.day) - timedelta(days=1)
        if birth_date <= today:
            assert calculate_age(birth_date) == 25


class TestValidateName:
    """Tests for name validation."""

    def test_valid_name(self):
        """Test valid name."""
        is_valid, error = validate_name("John Doe")
        assert is_valid is True
        assert error is None

    def test_empty_name(self):
        """Test empty name."""
        is_valid, error = validate_name("")
        assert is_valid is False
        assert "обязательно" in error.lower()

    def test_name_too_short(self):
        """Test name too short."""
        is_valid, error = validate_name("A")
        assert is_valid is False
        assert "2 символа" in error

    def test_name_too_long(self):
        """Test name too long."""
        is_valid, error = validate_name("A" * 101)
        assert is_valid is False
        assert "100 символов" in error

    def test_name_with_spaces(self):
        """Test name with leading/trailing spaces."""
        is_valid, error = validate_name("  John  ")
        assert is_valid is True


class TestValidateBirthDate:
    """Tests for birth date validation."""

    def test_valid_birth_date_18_years_old(self):
        """Test valid birth date for 18 year old."""
        birth_date = date.today().replace(year=date.today().year - 18)
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is True
        assert error is None

    def test_valid_birth_date_30_years_old(self):
        """Test valid birth date for 30 year old."""
        birth_date = date.today().replace(year=date.today().year - 30)
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is True
        assert error is None

    def test_under_18_years_old(self):
        """Test birth date for person under 18."""
        birth_date = date.today().replace(year=date.today().year - 17)
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is False
        assert "18" in error or "лет" in error

    def test_future_birth_date(self):
        """Test future birth date."""
        birth_date = date.today() + timedelta(days=1)
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is False
        assert "future" in error.lower()

    def test_invalid_age_over_120(self):
        """Test birth date resulting in age over 120."""
        birth_date = date.today().replace(year=date.today().year - 121)
        is_valid, error = validate_birth_date(birth_date)
        assert is_valid is False
        assert "Invalid" in error or "Неверная" in error


class TestValidateGender:
    """Tests for gender validation."""

    def test_valid_male(self):
        """Test valid male gender."""
        is_valid, error = validate_gender("male")
        assert is_valid is True
        assert error is None

    def test_valid_female(self):
        """Test valid female gender."""
        is_valid, error = validate_gender("female")
        assert is_valid is True
        assert error is None

    def test_valid_other(self):
        """Test valid other gender."""
        is_valid, error = validate_gender("other")
        assert is_valid is True
        assert error is None

    def test_invalid_gender(self):
        """Test invalid gender."""
        is_valid, error = validate_gender("invalid")
        assert is_valid is False
        assert "должен быть одним из" in error.lower()


class TestValidateOrientation:
    """Tests for orientation validation."""

    def test_valid_orientations(self):
        """Test all valid orientations."""
        for orientation in ["male", "female", "any"]:
            is_valid, error = validate_orientation(orientation)
            assert is_valid is True
            assert error is None

    def test_invalid_orientation(self):
        """Test invalid orientation."""
        is_valid, error = validate_orientation("invalid")
        assert is_valid is False
        assert "должна быть одной из" in error.lower()


class TestValidateGoal:
    """Tests for goal validation."""

    def test_valid_goals(self):
        """Test all valid goals."""
        for goal in [
            "friendship",
            "dating",
            "relationship",
            "networking",
            "serious",
            "casual",
        ]:
            is_valid, error = validate_goal(goal)
            assert is_valid is True
            assert error is None

    def test_invalid_goal(self):
        """Test invalid goal."""
        is_valid, error = validate_goal("invalid")
        assert is_valid is False
        assert "должна быть одной из" in error.lower()


class TestValidateBio:
    """Tests for bio validation."""

    def test_valid_bio(self):
        """Test valid bio."""
        is_valid, error = validate_bio("This is my bio")
        assert is_valid is True
        assert error is None

    def test_none_bio(self):
        """Test None bio is allowed."""
        is_valid, error = validate_bio(None)
        assert is_valid is True
        assert error is None

    def test_bio_too_long(self):
        """Test bio exceeding max length."""
        is_valid, error = validate_bio("A" * 1001)
        assert is_valid is False
        assert "1000 characters" in error


class TestValidateInterests:
    """Tests for interests validation."""

    def test_valid_interests(self):
        """Test valid interests list."""
        is_valid, error = validate_interests(["music", "sports", "travel"])
        assert is_valid is True
        assert error is None

    def test_none_interests(self):
        """Test None interests is allowed."""
        is_valid, error = validate_interests(None)
        assert is_valid is True
        assert error is None

    def test_too_many_interests(self):
        """Test exceeding max number of interests."""
        is_valid, error = validate_interests([f"interest_{i}" for i in range(21)])
        assert is_valid is False
        assert "20 interests" in error

    def test_interest_too_long(self):
        """Test interest exceeding max length."""
        is_valid, error = validate_interests(["A" * 51])
        assert is_valid is False
        assert "50 characters" in error


class TestValidateHeight:
    """Tests for height validation."""

    def test_valid_height(self):
        """Test valid height."""
        is_valid, error = validate_height(175)
        assert is_valid is True
        assert error is None

    def test_none_height(self):
        """Test None height is allowed."""
        is_valid, error = validate_height(None)
        assert is_valid is True
        assert error is None

    def test_height_too_low(self):
        """Test height below minimum."""
        is_valid, error = validate_height(99)
        assert is_valid is False
        assert "100 and 250" in error

    def test_height_too_high(self):
        """Test height above maximum."""
        is_valid, error = validate_height(251)
        assert is_valid is False
        assert "100 and 250" in error


class TestValidateEducation:
    """Tests for education validation."""

    def test_valid_education(self):
        """Test valid education levels."""
        for education in ["high_school", "bachelor", "master", "phd", "other"]:
            is_valid, error = validate_education(education)
            assert is_valid is True
            assert error is None

    def test_none_education(self):
        """Test None education is allowed."""
        is_valid, error = validate_education(None)
        assert is_valid is True
        assert error is None

    def test_invalid_education(self):
        """Test invalid education."""
        is_valid, error = validate_education("invalid")
        assert is_valid is False
        assert "must be one of" in error.lower()


class TestValidateLocation:
    """Tests for location validation."""

    def test_valid_location(self):
        """Test valid location."""
        is_valid, error = validate_location("Russia", "Moscow")
        assert is_valid is True
        assert error is None

    def test_none_location(self):
        """Test None location is allowed."""
        is_valid, error = validate_location(None, None)
        assert is_valid is True
        assert error is None

    def test_country_too_long(self):
        """Test country name too long."""
        is_valid, error = validate_location("A" * 101, "City")
        assert is_valid is False
        assert "100 characters" in error

    def test_city_too_long(self):
        """Test city name too long."""
        is_valid, error = validate_location("Country", "A" * 101)
        assert is_valid is False
        assert "100 characters" in error


class TestValidateProfileData:
    """Tests for complete profile validation."""

    def test_valid_profile_minimal(self):
        """Test valid profile with minimal required fields."""
        data = {
            "name": "John Doe",
            "birth_date": date.today().replace(year=date.today().year - 25),
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is True
        assert error is None

    def test_valid_profile_complete(self):
        """Test valid profile with all fields."""
        data = {
            "name": "John Doe",
            "birth_date": date.today().replace(year=date.today().year - 25),
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
            "bio": "Hello, I'm John",
            "interests": ["music", "sports"],
            "height_cm": 180,
            "education": "bachelor",
            "country": "Russia",
            "city": "Moscow",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is True
        assert error is None

    def test_missing_required_field(self):
        """Test profile missing required field."""
        data = {
            "name": "John Doe",
            "birth_date": date.today().replace(year=date.today().year - 25),
            "gender": "male",
            # Missing orientation and goal
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert "Missing required field" in error

    def test_invalid_name_in_profile(self):
        """Test profile with invalid name."""
        data = {
            "name": "A",  # Too short
            "birth_date": date.today().replace(year=date.today().year - 25),
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert "2 символа" in error

    def test_under_age_in_profile(self):
        """Test profile with under 18 age."""
        data = {
            "name": "John Doe",
            "birth_date": date.today().replace(year=date.today().year - 17),
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert "18" in error or "лет" in error

    def test_birth_date_string_format(self):
        """Test profile with birth date as string."""
        data = {
            "name": "John Doe",
            "birth_date": "1990-01-01",
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is True
        assert error is None

    def test_invalid_birth_date_string(self):
        """Test profile with invalid birth date string."""
        data = {
            "name": "John Doe",
            "birth_date": "invalid-date",
            "gender": "male",
            "orientation": "female",
            "goal": "relationship",
        }
        is_valid, error = validate_profile_data(data)
        assert is_valid is False
        assert "Invalid birth date format" in error


class TestValidateNameEdgeCases:
    """Additional edge case tests for name validation."""

    def test_name_non_string_type(self):
        """Test name validation with non-string type."""
        is_valid, error = validate_name(123)
        assert is_valid is False
        assert "должно быть строкой" in error.lower()

    def test_name_none(self):
        """Test name validation with None."""
        is_valid, error = validate_name(None)
        assert is_valid is False
        assert "обязательно" in error.lower()


class TestValidateBirthDateEdgeCases:
    """Additional edge case tests for birth date validation."""

    def test_birth_date_none(self):
        """Test birth date validation with None."""
        is_valid, error = validate_birth_date(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_birth_date_invalid_type(self):
        """Test birth date validation with invalid type."""
        is_valid, error = validate_birth_date("2000-01-01")
        assert is_valid is False
        assert "invalid" in error.lower()


class TestValidateGenderEdgeCases:
    """Additional edge case tests for gender validation."""

    def test_gender_none(self):
        """Test gender validation with None."""
        is_valid, error = validate_gender(None)
        assert is_valid is False
        assert "обязателен" in error.lower()


class TestValidateOrientationEdgeCases:
    """Additional edge case tests for orientation validation."""

    def test_orientation_none(self):
        """Test orientation validation with None."""
        is_valid, error = validate_orientation(None)
        assert is_valid is False
        assert "обязательна" in error.lower()


class TestValidateGoalEdgeCases:
    """Additional edge case tests for goal validation."""

    def test_goal_none(self):
        """Test goal validation with None."""
        is_valid, error = validate_goal(None)
        assert is_valid is False
        assert "обязательна" in error.lower()


class TestValidateBioEdgeCases:
    """Additional edge case tests for bio validation."""

    def test_bio_non_string_type(self):
        """Test bio validation with non-string type."""
        is_valid, error = validate_bio(123)
        assert is_valid is False
        assert "must be a string" in error.lower()


class TestValidateInterestsEdgeCases:
    """Additional edge case tests for interests validation."""

    def test_interests_non_list_type(self):
        """Test interests validation with non-list type."""
        is_valid, error = validate_interests("not a list")
        assert is_valid is False
        assert "must be a list" in error.lower()

    def test_interests_non_string_items(self):
        """Test interests validation with non-string items."""
        is_valid, error = validate_interests([123, 456])
        assert is_valid is False
        assert "must be a string" in error.lower()
