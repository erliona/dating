"""Tests for discovery, interactions, matches, and favorites."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.e2e

from bot.db import Favorite, Interaction, Match, Profile
from bot.repository import ProfileRepository


@pytest.mark.asyncio
class TestFindCandidates:
    """Test candidate discovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)

    async def test_find_candidates_basic(self):
        """Test basic candidate finding."""
        repository = ProfileRepository(self.session)

        # Mock current user profile
        current_profile = Profile(
            id=1,
            user_id=1,
            name="User One",
            birth_date=date(1998, 1, 1),
            gender="male",
            orientation="female",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        # Mock candidate profiles
        profile2 = Profile(
            id=2,
            user_id=2,
            name="User Two",
            birth_date=date(1995, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        profile3 = Profile(
            id=3,
            user_id=3,
            name="User Three",
            birth_date=date(2001, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        # Mock database queries
        execute_calls = []

        async def mock_execute(query):
            result = MagicMock()
            execute_calls.append(query)

            # First call: get current profile
            if len(execute_calls) == 1:
                result.scalar_one_or_none.return_value = current_profile
            # Second call: get interactions
            elif len(execute_calls) == 2:
                result.scalars.return_value.all.return_value = []
            # Third call: get candidates
            else:
                result.scalars.return_value.all.return_value = [profile2, profile3]

            return result

        self.session.execute = mock_execute

        profiles, cursor = await repository.find_candidates(1, limit=10)

        assert len(profiles) == 2
        assert cursor is None

    async def test_find_candidates_with_pagination(self):
        """Test cursor-based pagination."""
        repository = ProfileRepository(self.session)

        # Mock current profile
        current_profile = Profile(
            id=1,
            user_id=1,
            name="User",
            birth_date=date(1998, 1, 1),
            gender="male",
            orientation="female",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        # Mock profiles for pagination
        profiles = [
            Profile(
                id=2,
                user_id=2,
                name="P2",
                birth_date=date(1995, 1, 1),
                gender="female",
                orientation="male",
                goal="dating",
                is_visible=True,
                is_complete=True,
            ),
            Profile(
                id=3,
                user_id=3,
                name="P3",
                birth_date=date(1996, 1, 1),
                gender="female",
                orientation="male",
                goal="dating",
                is_visible=True,
                is_complete=True,
            ),
        ]

        execute_calls = []

        async def mock_execute(query):
            result = MagicMock()
            execute_calls.append(query)

            if len(execute_calls) == 1:
                result.scalar_one_or_none.return_value = current_profile
            elif len(execute_calls) == 2:
                result.scalars.return_value.all.return_value = []
            else:
                # Return 2 profiles (limit+1 to test pagination)
                result.scalars.return_value.all.return_value = profiles

            return result

        self.session.execute = mock_execute

        found_profiles, cursor = await repository.find_candidates(1, limit=1)

        assert len(found_profiles) == 1
        assert cursor == 2  # First profile's ID


@pytest.mark.asyncio
class TestInteractions:
    """Test interaction operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)

    async def test_create_interaction(self):
        """Test creating an interaction."""
        repository = ProfileRepository(self.session)

        # Mock no existing interaction
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        self.session.flush = AsyncMock()

        await repository.create_interaction(1, 2, "like")

        # Verify interaction was added
        self.session.add.assert_called_once()
        added_interaction = self.session.add.call_args[0][0]
        assert isinstance(added_interaction, Interaction)
        assert added_interaction.user_id == 1
        assert added_interaction.target_id == 2
        assert added_interaction.interaction_type == "like"

    async def test_create_interaction_idempotent(self):
        """Test that creating same interaction is idempotent."""
        repository = ProfileRepository(self.session)

        # Mock existing interaction
        existing_interaction = Interaction(
            id=1,
            user_id=1,
            target_id=2,
            interaction_type="like",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_interaction
        self.session.execute = AsyncMock(return_value=result_mock)

        interaction = await repository.create_interaction(1, 2, "superlike")

        # Verify interaction was updated, not added
        self.session.add.assert_not_called()
        assert interaction.interaction_type == "superlike"

    async def test_check_mutual_like(self):
        """Test checking for mutual likes."""
        repository = ProfileRepository(self.session)

        # Mock mutual like found
        mutual_interaction = Interaction(
            id=2,
            user_id=2,
            target_id=1,
            interaction_type="like",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mutual_interaction
        self.session.execute = AsyncMock(return_value=result_mock)

        is_mutual = await repository.check_mutual_like(1, 2)
        assert is_mutual is True

    async def test_check_mutual_like_not_found(self):
        """Test checking for mutual likes when not found."""
        repository = ProfileRepository(self.session)

        # Mock no mutual like
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)

        is_mutual = await repository.check_mutual_like(1, 2)
        assert is_mutual is False


@pytest.mark.asyncio
class TestMatches:
    """Test match operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)

    async def test_create_match(self):
        """Test creating a match."""
        repository = ProfileRepository(self.session)

        # Mock no existing match
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        self.session.flush = AsyncMock()

        await repository.create_match(2, 1)

        # Verify match was added with normalized IDs
        self.session.add.assert_called_once()
        added_match = self.session.add.call_args[0][0]
        assert isinstance(added_match, Match)
        assert added_match.user1_id == 1  # Normalized: smaller ID first
        assert added_match.user2_id == 2

    async def test_create_match_idempotent(self):
        """Test that creating same match is idempotent."""
        repository = ProfileRepository(self.session)

        # Mock existing match
        existing_match = Match(id=1, user1_id=1, user2_id=2, created_at=datetime.now())

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_match
        self.session.execute = AsyncMock(return_value=result_mock)

        match = await repository.create_match(1, 2)

        # Verify match was not added again
        self.session.add.assert_not_called()
        assert match.id == 1

    async def test_get_matches(self):
        """Test getting user's matches."""
        repository = ProfileRepository(self.session)

        # Mock matches and profiles
        match1 = Match(id=1, user1_id=1, user2_id=2, created_at=datetime.now())
        match2 = Match(id=2, user1_id=1, user2_id=3, created_at=datetime.now())

        profile2 = Profile(
            id=2,
            user_id=2,
            name="User 2",
            birth_date=date(1995, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )
        profile3 = Profile(
            id=3,
            user_id=3,
            name="User 3",
            birth_date=date(1996, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        execute_calls = []

        async def mock_execute(query):
            result = MagicMock()
            execute_calls.append(query)

            # First call: get matches
            if len(execute_calls) == 1:
                result.scalars.return_value.all.return_value = [match1, match2]
            # Subsequent calls: get profiles
            elif len(execute_calls) == 2:
                result.scalar_one_or_none.return_value = profile2
            else:
                result.scalar_one_or_none.return_value = profile3

            return result

        self.session.execute = mock_execute

        matches, cursor = await repository.get_matches(1, limit=10)

        assert len(matches) == 2
        assert all(
            isinstance(m[0], Match) and isinstance(m[1], Profile) for m in matches
        )


@pytest.mark.asyncio
class TestFavorites:
    """Test favorite operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = MagicMock(spec=AsyncSession)

    async def test_add_favorite(self):
        """Test adding to favorites."""
        repository = ProfileRepository(self.session)

        # Mock no existing favorite
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=result_mock)
        self.session.flush = AsyncMock()

        await repository.add_favorite(1, 2)

        # Verify favorite was added
        self.session.add.assert_called_once()
        added_favorite = self.session.add.call_args[0][0]
        assert isinstance(added_favorite, Favorite)
        assert added_favorite.user_id == 1
        assert added_favorite.target_id == 2

    async def test_add_favorite_idempotent(self):
        """Test that adding same favorite is idempotent."""
        repository = ProfileRepository(self.session)

        # Mock existing favorite
        existing_favorite = Favorite(
            id=1, user_id=1, target_id=2, created_at=datetime.now()
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_favorite
        self.session.execute = AsyncMock(return_value=result_mock)

        favorite = await repository.add_favorite(1, 2)

        # Verify favorite was not added again
        self.session.add.assert_not_called()
        assert favorite.id == 1

    async def test_remove_favorite(self):
        """Test removing from favorites."""
        repository = ProfileRepository(self.session)

        # Mock successful deletion
        result_mock = MagicMock()
        result_mock.rowcount = 1
        self.session.execute = AsyncMock(return_value=result_mock)

        removed = await repository.remove_favorite(1, 2)
        assert removed is True

    async def test_remove_favorite_not_found(self):
        """Test removing non-existent favorite."""
        repository = ProfileRepository(self.session)

        # Mock no rows deleted
        result_mock = MagicMock()
        result_mock.rowcount = 0
        self.session.execute = AsyncMock(return_value=result_mock)

        removed = await repository.remove_favorite(1, 2)
        assert removed is False

    async def test_get_favorites(self):
        """Test getting user's favorites."""
        repository = ProfileRepository(self.session)

        # Mock favorites and profiles
        favorite1 = Favorite(id=1, user_id=1, target_id=2, created_at=datetime.now())
        favorite2 = Favorite(id=2, user_id=1, target_id=3, created_at=datetime.now())

        profile2 = Profile(
            id=2,
            user_id=2,
            name="User 2",
            birth_date=date(1995, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )
        profile3 = Profile(
            id=3,
            user_id=3,
            name="User 3",
            birth_date=date(1996, 1, 1),
            gender="female",
            orientation="male",
            goal="dating",
            is_visible=True,
            is_complete=True,
        )

        execute_calls = []

        async def mock_execute(query):
            result = MagicMock()
            execute_calls.append(query)

            # First call: get favorites
            if len(execute_calls) == 1:
                result.scalars.return_value.all.return_value = [favorite1, favorite2]
            # Subsequent calls: get profiles
            elif len(execute_calls) == 2:
                result.scalar_one_or_none.return_value = profile2
            else:
                result.scalar_one_or_none.return_value = profile3

            return result

        self.session.execute = mock_execute

        favorites, cursor = await repository.get_favorites(1, limit=10)

        assert len(favorites) == 2
        assert all(
            isinstance(f[0], Favorite) and isinstance(f[1], Profile) for f in favorites
        )
