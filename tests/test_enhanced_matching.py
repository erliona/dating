"""Tests for enhanced matching functionality and new commands."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.db import ProfileRepository, MatchRepository
from bot.main import Profile


class TestMatchingAlgorithm:
    """Test smart matching algorithm with scoring."""

    @pytest.fixture
    def base_profile(self):
        """Create a base profile for testing."""
        return Profile(
            user_id=1,
            name="Test User",
            age=25,
            gender="male",
            preference="female",
            bio="Test bio",
            location="Москва",
            interests=["Программирование", "Книги", "Кино"],
            goal="serious",
        )

    @pytest.fixture
    def compatible_profile(self):
        """Create a highly compatible profile."""
        return Profile(
            user_id=2,
            name="Compatible User",
            age=24,
            gender="female",
            preference="male",
            bio="Another test bio",
            location="Москва",
            interests=["Программирование", "Кино", "Музыка"],
            goal="serious",
        )

    @pytest.fixture
    def partially_compatible_profile(self):
        """Create a partially compatible profile."""
        return Profile(
            user_id=3,
            name="Partial Match",
            age=30,
            gender="female",
            preference="male",
            bio="Different interests",
            location="Санкт-Петербург",
            interests=["Спорт", "Путешествия"],
            goal="casual",
        )

    @pytest.fixture
    def incompatible_profile(self):
        """Create an incompatible profile."""
        return Profile(
            user_id=4,
            name="Incompatible User",
            age=45,
            gender="female",
            preference="male",
            bio="Very different",
            location="Владивосток",
            interests=["Рыбалка", "Охота"],
            goal="networking",
        )

    def test_calculate_match_score_perfect_match(self, base_profile):
        """Test scoring for a perfect match."""
        # Create identical profile (except user_id)
        perfect_match = Profile(
            user_id=99,
            name="Perfect Match",
            age=base_profile.age,
            gender="female",
            preference="male",
            bio="Same bio",
            location=base_profile.location,
            interests=base_profile.interests.copy(),
            goal=base_profile.goal,
        )
        
        score = ProfileRepository._calculate_match_score(base_profile, perfect_match)
        assert score == 1.0, "Perfect match should have score of 1.0"

    def test_calculate_match_score_with_common_interests(self, base_profile, compatible_profile):
        """Test scoring with common interests."""
        score = ProfileRepository._calculate_match_score(base_profile, compatible_profile)
        # They have 2 common interests out of 4 total unique = 0.5 * 0.4 = 0.2
        # Same location = 0.3
        # Same goal = 0.2
        # Age diff 1 = 0.1
        # Total = 0.8
        assert score >= 0.75, f"Expected score >= 0.75, got {score}"

    def test_calculate_match_score_partial_match(self, base_profile, partially_compatible_profile):
        """Test scoring for partial match."""
        score = ProfileRepository._calculate_match_score(base_profile, partially_compatible_profile)
        # No common interests = 0
        # Different city but partial match = 0.0-0.15
        # Different goal = 0.0-0.1
        # Age diff 5 = 0.07
        # Should be relatively low
        assert 0.0 <= score < 0.3, f"Expected low score for partial match, got {score}"

    def test_calculate_match_score_no_common_interests(self, base_profile, incompatible_profile):
        """Test scoring with no common interests."""
        score = ProfileRepository._calculate_match_score(base_profile, incompatible_profile)
        # No common interests, different location, different goal, large age gap
        assert score < 0.2, f"Expected very low score, got {score}"

    def test_calculate_match_score_same_location_different_case(self, base_profile):
        """Test location matching is case-insensitive."""
        other = Profile(
            user_id=10,
            name="Test",
            age=25,
            gender="female",
            preference="male",
            location="москва",  # lowercase
            interests=[],
            goal=None,
        )
        score = ProfileRepository._calculate_match_score(base_profile, other)
        # Should get location points (0.3)
        assert score >= 0.3, "Location match should be case-insensitive"

    def test_calculate_match_score_partial_location_match(self, base_profile):
        """Test partial location matching."""
        other = Profile(
            user_id=11,
            name="Test",
            age=25,
            gender="female",
            preference="male",
            location="Москва, Центр",  # Contains "Москва"
            interests=[],
            goal=None,
        )
        score = ProfileRepository._calculate_match_score(base_profile, other)
        # Should get partial location points (0.15)
        assert score >= 0.15, "Partial location match should get points"

    def test_calculate_match_score_age_ranges(self, base_profile):
        """Test age compatibility scoring."""
        # Test age diff <= 3
        close_age = Profile(
            user_id=20, name="Close", age=27, gender="female",
            preference="male", interests=[], location=None, goal=None
        )
        score_close = ProfileRepository._calculate_match_score(base_profile, close_age)
        
        # Test age diff <= 5
        medium_age = Profile(
            user_id=21, name="Medium", age=30, gender="female",
            preference="male", interests=[], location=None, goal=None
        )
        score_medium = ProfileRepository._calculate_match_score(base_profile, medium_age)
        
        # Test age diff <= 10
        far_age = Profile(
            user_id=22, name="Far", age=35, gender="female",
            preference="male", interests=[], location=None, goal=None
        )
        score_far = ProfileRepository._calculate_match_score(base_profile, far_age)
        
        # Test age diff > 10
        very_far_age = Profile(
            user_id=23, name="VeryFar", age=45, gender="female",
            preference="male", interests=[], location=None, goal=None
        )
        score_very_far = ProfileRepository._calculate_match_score(base_profile, very_far_age)
        
        assert score_close > score_medium > score_far > score_very_far

    def test_calculate_match_score_related_goals(self, base_profile):
        """Test related goals get partial score."""
        # serious + casual are related
        casual_profile = Profile(
            user_id=30, name="Casual", age=25, gender="female",
            preference="male", goal="casual", interests=[], location=None
        )
        score_casual = ProfileRepository._calculate_match_score(base_profile, casual_profile)
        
        # friendship + networking are related
        base_friend = Profile(
            user_id=1, name="Base", age=25, gender="male",
            preference="female", goal="friendship", interests=[], location=None
        )
        network_profile = Profile(
            user_id=31, name="Network", age=25, gender="female",
            preference="male", goal="networking", interests=[], location=None
        )
        score_network = ProfileRepository._calculate_match_score(base_friend, network_profile)
        
        # Both should have some score from related goals
        assert score_casual > 0, "Related goals should give some score"
        assert score_network > 0, "Related goals should give some score"

    @pytest.mark.asyncio
    async def test_find_best_matches_orders_by_score(self, db_session_factory):
        """Test that find_best_matches returns profiles ordered by compatibility."""
        repo = ProfileRepository(db_session_factory)
        
        # Create base profile
        base = Profile(
            user_id=100,
            name="Base User",
            age=25,
            gender="male",
            preference="female",
            location="Москва",
            interests=["Кино", "Музыка"],
            goal="serious",
        )
        await repo.upsert(base)
        
        # Create high compatibility profile
        high = Profile(
            user_id=101,
            name="High Match",
            age=24,
            gender="female",
            preference="male",
            location="Москва",
            interests=["Кино", "Музыка", "Книги"],
            goal="serious",
        )
        await repo.upsert(high)
        
        # Create medium compatibility profile
        medium = Profile(
            user_id=102,
            name="Medium Match",
            age=30,
            gender="female",
            preference="male",
            location="Москва",
            interests=["Спорт"],
            goal="casual",
        )
        await repo.upsert(medium)
        
        # Create low compatibility profile
        low = Profile(
            user_id=103,
            name="Low Match",
            age=40,
            gender="female",
            preference="male",
            location="Владивосток",
            interests=["Охота"],
            goal="networking",
        )
        await repo.upsert(low)
        
        # Get best matches
        matches = await repo.find_best_matches(base, limit=10)
        
        # Should return all compatible profiles
        assert len(matches) == 3
        
        # First should be high compatibility
        assert matches[0].user_id == high.user_id, "Highest compatibility should be first"

    @pytest.mark.asyncio
    async def test_find_best_matches_respects_limit(self, db_session_factory):
        """Test that find_best_matches respects the limit parameter."""
        repo = ProfileRepository(db_session_factory)
        
        base = Profile(
            user_id=200,
            name="Base",
            age=25,
            gender="male",
            preference="female",
        )
        await repo.upsert(base)
        
        # Create multiple profiles
        for i in range(5):
            profile = Profile(
                user_id=201 + i,
                name=f"User {i}",
                age=25,
                gender="female",
                preference="male",
            )
            await repo.upsert(profile)
        
        # Request only 3 matches
        matches = await repo.find_best_matches(base, limit=3)
        
        assert len(matches) == 3, "Should respect limit parameter"

    @pytest.mark.asyncio
    async def test_find_best_matches_excludes_self(self, db_session_factory):
        """Test that find_best_matches excludes the user's own profile."""
        repo = ProfileRepository(db_session_factory)
        
        profile = Profile(
            user_id=300,
            name="Self",
            age=25,
            gender="female",
            preference="female",
        )
        await repo.upsert(profile)
        
        matches = await repo.find_best_matches(profile, limit=10)
        
        # Should not include self
        assert all(m.user_id != profile.user_id for m in matches)

    @pytest.mark.asyncio
    async def test_find_best_matches_respects_preferences(self, db_session_factory):
        """Test that find_best_matches respects gender preferences."""
        repo = ProfileRepository(db_session_factory)
        
        male_seeking_female = Profile(
            user_id=400,
            name="Male",
            age=25,
            gender="male",
            preference="female",
        )
        await repo.upsert(male_seeking_female)
        
        # Create incompatible profiles (wrong gender)
        male1 = Profile(user_id=401, name="M1", age=25, gender="male", preference="any")
        await repo.upsert(male1)
        
        # Create compatible profile
        female1 = Profile(user_id=402, name="F1", age=25, gender="female", preference="male")
        await repo.upsert(female1)
        
        matches = await repo.find_best_matches(male_seeking_female, limit=10)
        
        # Should only return the female profile
        assert len(matches) == 1
        assert matches[0].user_id == female1.user_id


class TestMatchesCommand:
    """Test /matches command handler."""

    @pytest.mark.asyncio
    async def test_matches_handler_shows_matches(self):
        """Test that matches handler displays user's matches."""
        from bot.main import matches_handler
        from aiogram.types import Message, User
        
        # Mock message
        message = MagicMock(spec=Message)
        user = MagicMock(spec=User)
        user.id = 500
        message.from_user = user
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repositories
        mock_match_repo = AsyncMock()
        mock_match_repo.get_matches.return_value = [501, 502]
        
        mock_profile_repo = AsyncMock()
        mock_profile_repo.get.side_effect = [
            Profile(user_id=501, name="Match1", age=25, gender="female", 
                   preference="male", location="Москва", interests=["Кино"]),
            Profile(user_id=502, name="Match2", age=26, gender="female", 
                   preference="male", location="Питер", interests=["Книги"]),
        ]
        
        with patch('bot.main.get_match_repository', return_value=mock_match_repo), \
             patch('bot.main.get_repository', return_value=mock_profile_repo):
            await matches_handler(message)
        
        # Should call answer with matches
        message.answer.assert_called_once()
        args = message.answer.call_args[0]
        assert "Match1" in args[0]
        assert "Match2" in args[0]
        assert "2" in args[0]  # Count of matches

    @pytest.mark.asyncio
    async def test_matches_handler_no_matches(self):
        """Test matches handler when user has no matches."""
        from bot.main import matches_handler
        from aiogram.types import Message, User
        
        message = MagicMock(spec=Message)
        user = MagicMock(spec=User)
        user.id = 600
        message.from_user = user
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        mock_match_repo = AsyncMock()
        mock_match_repo.get_matches.return_value = []
        
        with patch('bot.main.get_match_repository', return_value=mock_match_repo), \
             patch('bot.main.get_repository', return_value=AsyncMock()):
            await matches_handler(message)
        
        message.answer.assert_called_once()
        args = message.answer.call_args[0]
        assert "нет матчей" in args[0].lower()


class TestStatsCommand:
    """Test /stats command handler."""

    @pytest.mark.asyncio
    async def test_stats_handler_shows_statistics(self):
        """Test that stats handler displays user statistics."""
        from bot.main import stats_handler
        from aiogram.types import Message, User
        
        message = MagicMock(spec=Message)
        user = MagicMock(spec=User)
        user.id = 700
        message.from_user = user
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        # Mock repositories
        mock_match_repo = AsyncMock()
        mock_match_repo.get_user_stats.return_value = {
            "matches_count": 5,
            "likes_sent": 20,
            "likes_received": 15,
            "dislikes_sent": 10,
        }
        
        mock_profile_repo = AsyncMock()
        mock_profile_repo.get.return_value = Profile(
            user_id=700, name="Test User", age=25, gender="male",
            preference="female", location="Москва", interests=["Кино", "Музыка"]
        )
        
        with patch('bot.main.get_match_repository', return_value=mock_match_repo), \
             patch('bot.main.get_repository', return_value=mock_profile_repo):
            await stats_handler(message)
        
        message.answer.assert_called_once()
        args = message.answer.call_args[0]
        assert "5" in args[0]  # matches_count
        assert "20" in args[0]  # likes_sent
        assert "15" in args[0]  # likes_received

    @pytest.mark.asyncio
    async def test_stats_handler_no_profile(self):
        """Test stats handler when user has no profile."""
        from bot.main import stats_handler
        from aiogram.types import Message, User
        
        message = MagicMock(spec=Message)
        user = MagicMock(spec=User)
        user.id = 800
        message.from_user = user
        message.bot = MagicMock()
        message.answer = AsyncMock()
        
        mock_profile_repo = AsyncMock()
        mock_profile_repo.get.return_value = None
        
        with patch('bot.main.get_match_repository', return_value=AsyncMock()), \
             patch('bot.main.get_repository', return_value=mock_profile_repo):
            await stats_handler(message)
        
        message.answer.assert_called_once()
        args = message.answer.call_args[0]
        assert "нет анкеты" in args[0].lower()


class TestGetUserStats:
    """Test get_user_stats repository method."""

    @pytest.mark.asyncio
    async def test_get_user_stats_returns_correct_data(self, db_session_factory):
        """Test that get_user_stats returns accurate statistics."""
        from bot.db import InteractionRepository, MatchRepository
        
        match_repo = MatchRepository(db_session_factory)
        interaction_repo = InteractionRepository(db_session_factory)
        
        user_id = 900
        
        # Create some interactions
        await interaction_repo.create(user_id, 901, "like")
        await interaction_repo.create(user_id, 902, "like")
        await interaction_repo.create(user_id, 903, "dislike")
        await interaction_repo.create(904, user_id, "like")
        await interaction_repo.create(905, user_id, "like")
        
        # Create a match
        await match_repo.create(user_id, 901)
        
        # Get stats
        stats = await match_repo.get_user_stats(user_id)
        
        assert stats["matches_count"] == 1
        assert stats["likes_sent"] == 2
        assert stats["likes_received"] == 2
        assert stats["dislikes_sent"] == 1

    @pytest.mark.asyncio
    async def test_get_user_stats_empty(self, db_session_factory):
        """Test get_user_stats for user with no activity."""
        from bot.db import MatchRepository
        
        match_repo = MatchRepository(db_session_factory)
        
        stats = await match_repo.get_user_stats(999)
        
        assert stats["matches_count"] == 0
        assert stats["likes_sent"] == 0
        assert stats["likes_received"] == 0
        assert stats["dislikes_sent"] == 0
