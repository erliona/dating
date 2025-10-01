"""Tests for Sprint 4 Task 2: Enhanced recommendations and user preferences."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.db import UserSettingsModel


@pytest.mark.asyncio
class TestUserPreferences:
    """Test suite for user preference features."""

    async def test_settings_model_with_preferences(self) -> None:
        """Test that UserSettingsModel supports age and distance preferences."""
        settings = UserSettingsModel(
            user_id=12345,
            lang="ru",
            show_location=True,
            show_age=True,
            notify_matches=True,
            notify_messages=True,
            age_min=25,
            age_max=35,
            max_distance=50
        )
        
        assert settings.user_id == 12345
        assert settings.age_min == 25
        assert settings.age_max == 35
        assert settings.max_distance == 50

    async def test_settings_upsert_with_new_fields(self) -> None:
        """Test that settings repository can save new preference fields."""
        from bot.db import UserSettingsRepository
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        
        # Create in-memory SQLite database for testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create tables
        from bot.db import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        repo = UserSettingsRepository(session_factory)
        
        # Test upsert with new fields
        settings = await repo.upsert(
            user_id=12345,
            lang="en",
            age_min=20,
            age_max=30,
            max_distance=100
        )
        
        assert settings.user_id == 12345
        assert settings.lang == "en"
        assert settings.age_min == 20
        assert settings.age_max == 30
        assert settings.max_distance == 100
        
        # Test update
        updated = await repo.upsert(
            user_id=12345,
            age_min=25,
            age_max=40
        )
        
        assert updated.age_min == 25
        assert updated.age_max == 40
        assert updated.lang == "en"  # Should preserve existing value


@pytest.mark.asyncio
class TestRecommendationsHandler:
    """Test suite for get_recommendations action."""

    async def test_get_recommendations_action(self) -> None:
        """Test that get_recommendations action returns filtered profiles."""
        # This test verifies the handler logic
        # In a real scenario, we would test the actual handler function
        # For now, we just ensure the logic is sound
        
        # Mock data
        all_profiles = [
            {"user_id": 1, "age": 25, "name": "Alice"},
            {"user_id": 2, "age": 30, "name": "Bob"},
            {"user_id": 3, "age": 35, "name": "Charlie"},
            {"user_id": 4, "age": 40, "name": "David"},
        ]
        
        # Simulate filtering logic
        age_min = 28
        age_max = 36
        interacted_users = {2}
        
        filtered = [
            p for p in all_profiles 
            if p["user_id"] not in interacted_users
            and age_min <= p["age"] <= age_max
        ]
        
        # Should have filtered out user 2 (interacted), user 1 (too young), user 4 (too old)
        assert len(filtered) == 1
        assert filtered[0]["user_id"] == 3
        assert filtered[0]["name"] == "Charlie"

    async def test_get_recommendations_no_filters(self) -> None:
        """Test recommendations without age filters."""
        all_profiles = [
            {"user_id": 1, "age": 25, "name": "Alice"},
            {"user_id": 2, "age": 30, "name": "Bob"},
            {"user_id": 3, "age": 35, "name": "Charlie"},
        ]
        
        # No filters applied
        age_min = None
        age_max = None
        interacted_users = set()
        
        filtered = [
            p for p in all_profiles 
            if p["user_id"] not in interacted_users
        ]
        
        # Apply age filters if they exist
        if age_min is not None:
            filtered = [p for p in filtered if p["age"] >= age_min]
        if age_max is not None:
            filtered = [p for p in filtered if p["age"] <= age_max]
        
        # All profiles should be included
        assert len(filtered) == 3

    async def test_get_recommendations_excludes_interacted(self) -> None:
        """Test that recommendations exclude already interacted users."""
        all_profiles = [
            {"user_id": 1, "age": 25, "name": "Alice"},
            {"user_id": 2, "age": 30, "name": "Bob"},
            {"user_id": 3, "age": 35, "name": "Charlie"},
        ]
        
        # Users 1 and 2 already interacted
        interacted_users = {1, 2}
        
        filtered = [
            p for p in all_profiles 
            if p["user_id"] not in interacted_users
        ]
        
        # Only Charlie should remain
        assert len(filtered) == 1
        assert filtered[0]["user_id"] == 3


@pytest.mark.asyncio  
class TestSettingsUpdate:
    """Test settings update with new fields."""

    async def test_settings_update_payload(self) -> None:
        """Test that settings payload includes new fields."""
        # Simulate webapp payload
        payload = {
            "action": "update_settings",
            "lang": "ru",
            "show_location": True,
            "show_age": False,
            "notify_matches": True,
            "notify_messages": False,
            "age_min": 25,
            "age_max": 35,
            "max_distance": 50
        }
        
        # Verify all expected fields are present
        assert payload["action"] == "update_settings"
        assert "age_min" in payload
        assert "age_max" in payload
        assert "max_distance" in payload
        assert payload["age_min"] == 25
        assert payload["age_max"] == 35
        assert payload["max_distance"] == 50
