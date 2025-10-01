"""Tests for analytics module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.analytics import (
    AnalyticsCollector,
    AnalyticsMetrics,
    MetricsCounter,
    get_metrics_counter,
    track_command,
    track_interaction,
    track_profile_action,
)
from bot.db import MatchModel, ProfileModel, UserInteractionModel


@pytest.fixture
def metrics_counter():
    """Create a fresh metrics counter for each test."""
    counter = MetricsCounter()
    return counter


class TestMetricsCounter:
    """Tests for MetricsCounter class."""
    
    def test_increment_single_metric(self, metrics_counter):
        """Test incrementing a single metric."""
        metrics_counter.increment("test_metric")
        metrics = metrics_counter.get_metrics()
        
        assert metrics["counters"]["test_metric"] == 1
    
    def test_increment_multiple_times(self, metrics_counter):
        """Test incrementing a metric multiple times."""
        metrics_counter.increment("test_metric")
        metrics_counter.increment("test_metric")
        metrics_counter.increment("test_metric")
        
        metrics = metrics_counter.get_metrics()
        assert metrics["counters"]["test_metric"] == 3
    
    def test_increment_with_value(self, metrics_counter):
        """Test incrementing with custom value."""
        metrics_counter.increment("test_metric", 5)
        metrics = metrics_counter.get_metrics()
        
        assert metrics["counters"]["test_metric"] == 5
    
    def test_multiple_metrics(self, metrics_counter):
        """Test tracking multiple different metrics."""
        metrics_counter.increment("metric_a")
        metrics_counter.increment("metric_b", 2)
        metrics_counter.increment("metric_c", 3)
        
        metrics = metrics_counter.get_metrics()
        assert metrics["counters"]["metric_a"] == 1
        assert metrics["counters"]["metric_b"] == 2
        assert metrics["counters"]["metric_c"] == 3
    
    def test_get_metrics_includes_uptime(self, metrics_counter):
        """Test that get_metrics includes uptime information."""
        metrics = metrics_counter.get_metrics()
        
        assert "uptime_seconds" in metrics
        assert "start_time" in metrics
        assert metrics["uptime_seconds"] >= 0
    
    def test_reset_clears_counters(self, metrics_counter):
        """Test that reset clears all counters."""
        metrics_counter.increment("test_metric", 5)
        metrics_counter.reset()
        
        metrics = metrics_counter.get_metrics()
        assert metrics["counters"] == {}


class TestTrackingFunctions:
    """Tests for tracking helper functions."""
    
    def test_track_command(self):
        """Test track_command function."""
        counter = get_metrics_counter()
        counter.reset()
        
        track_command("start")
        track_command("help")
        track_command("start")
        
        metrics = counter.get_metrics()
        assert metrics["counters"]["command_start"] == 2
        assert metrics["counters"]["command_help"] == 1
        assert metrics["counters"]["commands_total"] == 3
    
    def test_track_interaction(self):
        """Test track_interaction function."""
        counter = get_metrics_counter()
        counter.reset()
        
        track_interaction("like")
        track_interaction("dislike")
        track_interaction("like")
        
        metrics = counter.get_metrics()
        assert metrics["counters"]["interaction_like"] == 2
        assert metrics["counters"]["interaction_dislike"] == 1
        assert metrics["counters"]["interactions_total"] == 3
    
    def test_track_profile_action(self):
        """Test track_profile_action function."""
        counter = get_metrics_counter()
        counter.reset()
        
        track_profile_action("create")
        track_profile_action("update")
        track_profile_action("create")
        
        metrics = counter.get_metrics()
        assert metrics["counters"]["profile_create"] == 2
        assert metrics["counters"]["profile_update"] == 1
        assert metrics["counters"]["profiles_total"] == 3


@pytest.mark.asyncio
class TestAnalyticsCollector:
    """Tests for AnalyticsCollector class."""
    
    async def test_get_total_users(self, db_session_factory: async_sessionmaker):
        """Test getting total user count."""
        # Create test profiles
        async with db_session_factory() as session:
            profile1 = ProfileModel(
                user_id=1, name="User1", age=25, gender="male", preference="female"
            )
            profile2 = ProfileModel(
                user_id=2, name="User2", age=26, gender="female", preference="male"
            )
            session.add_all([profile1, profile2])
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.total_users == 2
    
    async def test_get_average_age(self, db_session_factory: async_sessionmaker):
        """Test calculating average age."""
        async with db_session_factory() as session:
            profile1 = ProfileModel(
                user_id=1, name="User1", age=20, gender="male", preference="female"
            )
            profile2 = ProfileModel(
                user_id=2, name="User2", age=30, gender="female", preference="male"
            )
            session.add_all([profile1, profile2])
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.avg_age == 25.0
    
    async def test_get_gender_distribution(self, db_session_factory: async_sessionmaker):
        """Test gender distribution calculation."""
        async with db_session_factory() as session:
            profiles = [
                ProfileModel(
                    user_id=i,
                    name=f"User{i}",
                    age=25,
                    gender="male" if i % 2 == 0 else "female",
                    preference="any",
                )
                for i in range(1, 6)  # 3 female, 2 male
            ]
            session.add_all(profiles)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.gender_distribution["male"] == 2
        assert metrics.gender_distribution["female"] == 3
    
    async def test_get_total_matches(self, db_session_factory: async_sessionmaker):
        """Test getting total match count."""
        async with db_session_factory() as session:
            match1 = MatchModel(user1_id=1, user2_id=2)
            match2 = MatchModel(user1_id=3, user2_id=4)
            session.add_all([match1, match2])
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.total_matches == 2
    
    async def test_get_interaction_counts(self, db_session_factory: async_sessionmaker):
        """Test getting interaction counts."""
        async with db_session_factory() as session:
            interactions = [
                UserInteractionModel(from_user_id=1, to_user_id=2, action="like"),
                UserInteractionModel(from_user_id=1, to_user_id=3, action="like"),
                UserInteractionModel(from_user_id=2, to_user_id=3, action="dislike"),
            ]
            session.add_all(interactions)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.total_interactions == 3
        assert metrics.likes_sent == 2
        assert metrics.dislikes_sent == 1
    
    async def test_match_rate_calculation(self, db_session_factory: async_sessionmaker):
        """Test match rate calculation."""
        async with db_session_factory() as session:
            # Create 10 likes and 2 matches
            interactions = [
                UserInteractionModel(from_user_id=1, to_user_id=i, action="like")
                for i in range(2, 12)
            ]
            matches = [
                MatchModel(user1_id=1, user2_id=2),
                MatchModel(user1_id=1, user2_id=3),
            ]
            session.add_all(interactions + matches)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        # 2 matches out of 10 likes = 20%
        assert metrics.match_rate == 20.0
    
    async def test_engagement_rate(self, db_session_factory: async_sessionmaker):
        """Test engagement rate calculation."""
        async with db_session_factory() as session:
            # Create 5 profiles
            profiles = [
                ProfileModel(
                    user_id=i, name=f"User{i}", age=25, gender="any", preference="any"
                )
                for i in range(1, 6)
            ]
            # Only 2 users have made interactions
            interactions = [
                UserInteractionModel(from_user_id=1, to_user_id=2, action="like"),
                UserInteractionModel(from_user_id=2, to_user_id=3, action="like"),
            ]
            session.add_all(profiles + interactions)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        # 2 active users out of 5 = 40%
        assert metrics.engagement_rate == 40.0
    
    async def test_location_distribution(self, db_session_factory: async_sessionmaker):
        """Test location distribution calculation."""
        async with db_session_factory() as session:
            profiles = [
                ProfileModel(
                    user_id=1,
                    name="User1",
                    age=25,
                    gender="any",
                    preference="any",
                    location="Moscow",
                ),
                ProfileModel(
                    user_id=2,
                    name="User2",
                    age=25,
                    gender="any",
                    preference="any",
                    location="Moscow",
                ),
                ProfileModel(
                    user_id=3,
                    name="User3",
                    age=25,
                    gender="any",
                    preference="any",
                    location="Saint Petersburg",
                ),
            ]
            session.add_all(profiles)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.location_distribution["Moscow"] == 2
        assert metrics.location_distribution["Saint Petersburg"] == 1
    
    async def test_goal_distribution(self, db_session_factory: async_sessionmaker):
        """Test goal distribution calculation."""
        async with db_session_factory() as session:
            profiles = [
                ProfileModel(
                    user_id=1,
                    name="User1",
                    age=25,
                    gender="any",
                    preference="any",
                    goal="serious",
                ),
                ProfileModel(
                    user_id=2,
                    name="User2",
                    age=25,
                    gender="any",
                    preference="any",
                    goal="casual",
                ),
                ProfileModel(
                    user_id=3,
                    name="User3",
                    age=25,
                    gender="any",
                    preference="any",
                    goal="serious",
                ),
            ]
            session.add_all(profiles)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.goal_distribution["serious"] == 2
        assert metrics.goal_distribution["casual"] == 1
    
    async def test_get_user_analytics(self, db_session_factory: async_sessionmaker):
        """Test getting analytics for a specific user."""
        async with db_session_factory() as session:
            # Create profiles
            profile1 = ProfileModel(
                user_id=1,
                name="User1",
                age=25,
                gender="male",
                preference="female",
                location="Moscow",
                interests=["music", "sport"],
            )
            profile2 = ProfileModel(
                user_id=2, name="User2", age=26, gender="female", preference="male"
            )
            
            # Create interactions
            interactions = [
                UserInteractionModel(from_user_id=1, to_user_id=2, action="like"),
                UserInteractionModel(from_user_id=2, to_user_id=1, action="like"),
                UserInteractionModel(from_user_id=3, to_user_id=1, action="like"),
            ]
            
            # Create match
            match = MatchModel(user1_id=1, user2_id=2)
            
            session.add_all([profile1, profile2] + interactions + [match])
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        analytics = await collector.get_user_analytics(1)
        
        assert analytics["user_id"] == 1
        assert analytics["profile"]["name"] == "User1"
        assert analytics["profile"]["age"] == 25
        assert analytics["profile"]["interests_count"] == 2
        assert analytics["interactions"]["likes_sent"] == 1
        assert analytics["interactions"]["likes_received"] == 2
        assert analytics["interactions"]["matches"] == 1
        assert analytics["interactions"]["match_rate"] == 100.0
    
    async def test_get_user_analytics_nonexistent_user(
        self, db_session_factory: async_sessionmaker
    ):
        """Test getting analytics for non-existent user."""
        collector = AnalyticsCollector(db_session_factory)
        analytics = await collector.get_user_analytics(999)
        
        assert analytics == {}
    
    async def test_get_matching_quality_metrics(
        self, db_session_factory: async_sessionmaker
    ):
        """Test matching quality metrics."""
        async with db_session_factory() as session:
            # 5 likes, 2 matches = 40% mutual like rate
            interactions = [
                UserInteractionModel(from_user_id=1, to_user_id=i, action="like")
                for i in range(2, 7)
            ]
            matches = [
                MatchModel(user1_id=1, user2_id=2),
                MatchModel(user1_id=1, user2_id=3),
            ]
            session.add_all(interactions + matches)
            await session.commit()
        
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_matching_quality_metrics()
        
        assert metrics["total_likes"] == 5
        assert metrics["total_matches"] == 2
        assert metrics["mutual_like_rate"] == 40.0
    
    async def test_empty_database(self, db_session_factory: async_sessionmaker):
        """Test analytics with empty database."""
        collector = AnalyticsCollector(db_session_factory)
        metrics = await collector.get_overall_metrics()
        
        assert metrics.total_users == 0
        assert metrics.avg_age == 0.0
        assert metrics.total_matches == 0
        assert metrics.total_interactions == 0
        assert metrics.match_rate == 0.0
        assert metrics.engagement_rate == 0.0


class TestAnalyticsMetrics:
    """Tests for AnalyticsMetrics dataclass."""
    
    def test_default_values(self):
        """Test default values of AnalyticsMetrics."""
        metrics = AnalyticsMetrics()
        
        assert metrics.total_users == 0
        assert metrics.active_users_24h == 0
        assert metrics.active_users_7d == 0
        assert metrics.total_matches == 0
        assert metrics.total_interactions == 0
        assert metrics.likes_sent == 0
        assert metrics.dislikes_sent == 0
        assert metrics.match_rate == 0.0
        assert metrics.avg_age == 0.0
        assert metrics.gender_distribution == {}
        assert metrics.popular_interests == []
        assert metrics.location_distribution == {}
        assert metrics.goal_distribution == {}
        assert metrics.engagement_rate == 0.0
    
    def test_custom_values(self):
        """Test creating AnalyticsMetrics with custom values."""
        metrics = AnalyticsMetrics(
            total_users=100,
            total_matches=25,
            match_rate=25.0,
            gender_distribution={"male": 60, "female": 40},
        )
        
        assert metrics.total_users == 100
        assert metrics.total_matches == 25
        assert metrics.match_rate == 25.0
        assert metrics.gender_distribution == {"male": 60, "female": 40}
