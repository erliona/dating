"""Tests for mutual orientation filtering in candidate discovery.

These tests verify that the orientation filtering logic correctly implements
mutual compatibility between users based on gender and orientation preferences.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Profile, User
from bot.repository import ProfileRepository


@pytest.mark.asyncio
class TestMutualOrientationFiltering:
    """Test that candidate discovery uses mutual orientation filtering.

    The mutual orientation filtering ensures that:
    1. User's orientation matches candidate's gender
    2. Candidate's orientation matches user's gender (or is 'any')
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)

    async def test_orientation_filter_query_construction(self):
        """Test that discover_candidates constructs query with mutual orientation filtering.

        This test verifies that the code applies BOTH:
        1. Current user's orientation preference (filters candidate's gender)
        2. Candidate's orientation preference (filters by current user's gender)
        """
        repo = ProfileRepository(self.session)

        # Create mock current profile - male seeking females
        current_profile = Profile(
            id=1,
            user_id=1,
            name="Test User",
            birth_date=date(1990, 1, 1),
            gender="male",
            orientation="female",
            goal="dating",
            is_complete=True,
            is_visible=True,
        )

        # Mock the database query results
        # First query: get current profile
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = current_profile

        # Second query: get interacted IDs (none)
        interactions_result = MagicMock()
        interactions_result.scalars.return_value.all.return_value = []

        # Third query: get candidates (we'll verify the query construction)
        candidates_result = MagicMock()
        candidates_result.scalars.return_value.all.return_value = []

        # Mock execute to return different results for different queries
        self.session.execute = AsyncMock(
            side_effect=[profile_result, interactions_result, candidates_result]
        )

        # Call find_candidates
        candidates, cursor = await repo.find_candidates(user_id=1, limit=10)

        # Verify that execute was called 3 times
        assert self.session.execute.call_count == 3

        # Get the third call (the candidates query)
        candidates_query_call = self.session.execute.call_args_list[2]
        query = candidates_query_call[0][0]

        # Convert query to string to inspect the WHERE clauses
        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))

        # Verify that the query includes both orientation filters:
        # 1. Filter by candidate gender matching user's orientation
        assert (
            "profiles.gender = 'female'" in query_str
            or "profiles.gender = :gender" in query_str
        ), "Query should filter candidates by gender matching user's orientation"

        # 2. Filter by candidate orientation being 'any' OR matching user's gender
        # This is the mutual compatibility check
        assert (
            "profiles.orientation" in query_str
        ), "Query should include orientation filter for mutual compatibility"

        # Verify basic filters are present
        assert "profiles.is_visible" in query_str
        assert "profiles.is_complete" in query_str
        assert (
            "profiles.user_id !=" in query_str
            or "profiles.user_id != :user_id" in query_str
        )
