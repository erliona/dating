"""Analytics and metrics collection for the dating bot."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import and_, case, cast, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.types import Float

from .db import (
    MatchModel,
    ProfileModel,
    UserInteractionModel,
    UserSettingsModel,
)

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.ext.asyncio import AsyncSession


LOGGER = logging.getLogger(__name__)


@dataclass
class AnalyticsMetrics:
    """Container for analytics metrics."""
    
    total_users: int = 0
    active_users_24h: int = 0
    active_users_7d: int = 0
    total_matches: int = 0
    total_interactions: int = 0
    likes_sent: int = 0
    dislikes_sent: int = 0
    match_rate: float = 0.0
    avg_age: float = 0.0
    gender_distribution: dict[str, int] = field(default_factory=dict)
    popular_interests: list[tuple[str, int]] = field(default_factory=list)
    location_distribution: dict[str, int] = field(default_factory=dict)
    goal_distribution: dict[str, int] = field(default_factory=dict)
    daily_registrations: list[dict[str, Any]] = field(default_factory=list)
    daily_matches: list[dict[str, Any]] = field(default_factory=list)
    engagement_rate: float = 0.0


class AnalyticsCollector:
    """Collects and aggregates analytics data from the database."""
    
    def __init__(self, session_factory: async_sessionmaker) -> None:
        """Initialize the analytics collector.
        
        Args:
            session_factory: SQLAlchemy async session factory.
        """
        self._session_factory = session_factory
        
    async def get_overall_metrics(self) -> AnalyticsMetrics:
        """Get overall system metrics.
        
        Returns:
            AnalyticsMetrics object with all collected metrics.
        """
        async with self._session_factory() as session:
            metrics = AnalyticsMetrics()
            
            # Basic user metrics
            metrics.total_users = await self._get_total_users(session)
            metrics.avg_age = await self._get_average_age(session)
            
            # Interaction metrics
            metrics.total_matches = await self._get_total_matches(session)
            metrics.total_interactions = await self._get_total_interactions(session)
            metrics.likes_sent = await self._get_likes_count(session)
            metrics.dislikes_sent = await self._get_dislikes_count(session)
            
            # Calculate match rate
            if metrics.likes_sent > 0:
                metrics.match_rate = (metrics.total_matches / metrics.likes_sent) * 100
            
            # Engagement rate (users who have interacted vs total users)
            active_users = await self._get_active_users_count(session)
            if metrics.total_users > 0:
                metrics.engagement_rate = (active_users / metrics.total_users) * 100
            
            # Distribution metrics
            metrics.gender_distribution = await self._get_gender_distribution(session)
            metrics.popular_interests = await self._get_popular_interests(session)
            metrics.location_distribution = await self._get_location_distribution(session)
            metrics.goal_distribution = await self._get_goal_distribution(session)
            
            return metrics
    
    async def get_time_series_metrics(self, days: int = 30) -> dict[str, Any]:
        """Get time series metrics for the specified period.
        
        Args:
            days: Number of days to look back.
            
        Returns:
            Dictionary with time series data.
        """
        async with self._session_factory() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Daily registrations would require a created_at field
            # For now, return basic structure
            return {
                "period_days": days,
                "total_matches_in_period": await self._get_matches_in_period(
                    session, cutoff_date
                ),
                "total_interactions_in_period": await self._get_interactions_in_period(
                    session, cutoff_date
                ),
            }
    
    async def get_user_analytics(self, user_id: int) -> dict[str, Any]:
        """Get analytics for a specific user.
        
        Args:
            user_id: User ID to get analytics for.
            
        Returns:
            Dictionary with user-specific analytics.
        """
        async with self._session_factory() as session:
            profile = await session.scalar(
                select(ProfileModel).where(ProfileModel.user_id == user_id)
            )
            
            if not profile:
                return {}
            
            # Get user interactions
            likes_sent = await session.scalar(
                select(func.count())
                .select_from(UserInteractionModel)
                .where(
                    and_(
                        UserInteractionModel.from_user_id == user_id,
                        UserInteractionModel.action == "like",
                    )
                )
            ) or 0
            
            likes_received = await session.scalar(
                select(func.count())
                .select_from(UserInteractionModel)
                .where(
                    and_(
                        UserInteractionModel.to_user_id == user_id,
                        UserInteractionModel.action == "like",
                    )
                )
            ) or 0
            
            matches_count = await session.scalar(
                select(func.count())
                .select_from(MatchModel)
                .where(
                    (MatchModel.user1_id == user_id) | (MatchModel.user2_id == user_id)
                )
            ) or 0
            
            # Calculate match success rate
            match_rate = (matches_count / likes_sent * 100) if likes_sent > 0 else 0.0
            
            # Calculate popularity score (likes received vs average)
            avg_likes = await self._get_average_likes_received(session)
            popularity_score = (
                (likes_received / avg_likes * 100) if avg_likes > 0 else 0.0
            )
            
            return {
                "user_id": user_id,
                "profile": {
                    "name": profile.name,
                    "age": profile.age,
                    "gender": profile.gender,
                    "location": profile.location,
                    "interests_count": len(profile.interests or []),
                },
                "interactions": {
                    "likes_sent": likes_sent,
                    "likes_received": likes_received,
                    "matches": matches_count,
                    "match_rate": round(match_rate, 2),
                },
                "popularity_score": round(popularity_score, 2),
            }
    
    async def get_matching_quality_metrics(self) -> dict[str, Any]:
        """Get metrics about matching algorithm quality.
        
        Returns:
            Dictionary with matching quality metrics.
        """
        async with self._session_factory() as session:
            # Get mutual like rate (both users liked each other)
            total_likes = await self._get_likes_count(session)
            total_matches = await self._get_total_matches(session)
            
            mutual_like_rate = (
                (total_matches / total_likes * 100) if total_likes > 0 else 0.0
            )
            
            # Get average response rate (likes back)
            # This would require tracking who saw whose profile
            # For now, use matches as proxy
            
            return {
                "total_likes": total_likes,
                "total_matches": total_matches,
                "mutual_like_rate": round(mutual_like_rate, 2),
                "recommendation_quality": "N/A",  # Would need tracking data
            }
    
    # Helper methods for specific queries
    
    async def _get_total_users(self, session: AsyncSession) -> int:
        """Get total number of users."""
        result = await session.scalar(select(func.count()).select_from(ProfileModel))
        return result or 0
    
    async def _get_average_age(self, session: AsyncSession) -> float:
        """Get average user age."""
        result = await session.scalar(
            select(func.avg(ProfileModel.age)).select_from(ProfileModel)
        )
        return round(float(result), 1) if result else 0.0
    
    async def _get_total_matches(self, session: AsyncSession) -> int:
        """Get total number of matches."""
        result = await session.scalar(select(func.count()).select_from(MatchModel))
        return result or 0
    
    async def _get_total_interactions(self, session: AsyncSession) -> int:
        """Get total number of interactions."""
        result = await session.scalar(
            select(func.count()).select_from(UserInteractionModel)
        )
        return result or 0
    
    async def _get_likes_count(self, session: AsyncSession) -> int:
        """Get total number of likes."""
        result = await session.scalar(
            select(func.count())
            .select_from(UserInteractionModel)
            .where(UserInteractionModel.action == "like")
        )
        return result or 0
    
    async def _get_dislikes_count(self, session: AsyncSession) -> int:
        """Get total number of dislikes."""
        result = await session.scalar(
            select(func.count())
            .select_from(UserInteractionModel)
            .where(UserInteractionModel.action == "dislike")
        )
        return result or 0
    
    async def _get_active_users_count(self, session: AsyncSession) -> int:
        """Get count of users who have made at least one interaction."""
        result = await session.scalar(
            select(func.count(func.distinct(UserInteractionModel.from_user_id)))
            .select_from(UserInteractionModel)
        )
        return result or 0
    
    async def _get_gender_distribution(self, session: AsyncSession) -> dict[str, int]:
        """Get distribution of users by gender."""
        result = await session.execute(
            select(ProfileModel.gender, func.count())
            .select_from(ProfileModel)
            .group_by(ProfileModel.gender)
        )
        return {row[0]: row[1] for row in result.fetchall()}
    
    async def _get_popular_interests(
        self, session: AsyncSession, limit: int = 10
    ) -> list[tuple[str, int]]:
        """Get most popular interests.
        
        Args:
            session: Database session.
            limit: Maximum number of interests to return.
            
        Returns:
            List of (interest, count) tuples.
        """
        # This is a simplified version - would need unnest for proper counting
        # For now, return empty list as proper implementation requires JSONB operations
        return []
    
    async def _get_location_distribution(
        self, session: AsyncSession, limit: int = 10
    ) -> dict[str, int]:
        """Get distribution of users by location."""
        result = await session.execute(
            select(ProfileModel.location, func.count())
            .select_from(ProfileModel)
            .where(ProfileModel.location.isnot(None))
            .group_by(ProfileModel.location)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return {row[0]: row[1] for row in result.fetchall()}
    
    async def _get_goal_distribution(self, session: AsyncSession) -> dict[str, int]:
        """Get distribution of users by dating goal."""
        result = await session.execute(
            select(ProfileModel.goal, func.count())
            .select_from(ProfileModel)
            .where(ProfileModel.goal.isnot(None))
            .group_by(ProfileModel.goal)
        )
        return {row[0]: row[1] for row in result.fetchall()}
    
    async def _get_matches_in_period(
        self, session: AsyncSession, cutoff_date: datetime
    ) -> int:
        """Get number of matches created after cutoff date.
        
        Note: This requires created_at field in MatchModel.
        """
        # Would need created_at field to filter properly
        return await self._get_total_matches(session)
    
    async def _get_interactions_in_period(
        self, session: AsyncSession, cutoff_date: datetime
    ) -> int:
        """Get number of interactions after cutoff date.
        
        Note: This requires created_at field in UserInteractionModel.
        """
        # Would need created_at field to filter properly
        return await self._get_total_interactions(session)
    
    async def _get_average_likes_received(self, session: AsyncSession) -> float:
        """Get average number of likes received per user."""
        subquery = (
            select(
                UserInteractionModel.to_user_id,
                func.count().label("likes_count"),
            )
            .where(UserInteractionModel.action == "like")
            .group_by(UserInteractionModel.to_user_id)
            .subquery()
        )
        
        result = await session.scalar(select(func.avg(subquery.c.likes_count)))
        return float(result) if result else 0.0


class MetricsCounter:
    """In-memory metrics counter for real-time tracking."""
    
    def __init__(self) -> None:
        """Initialize metrics counter."""
        self._counters: dict[str, int] = defaultdict(int)
        self._start_time = datetime.now()
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment a counter metric.
        
        Args:
            metric_name: Name of the metric.
            value: Value to increment by (default: 1).
        """
        self._counters[metric_name] += value
        LOGGER.debug("Metric %s incremented by %d", metric_name, value)
    
    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics.
        
        Returns:
            Dictionary with all metrics and metadata.
        """
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        return {
            "counters": dict(self._counters),
            "uptime_seconds": uptime,
            "start_time": self._start_time.isoformat(),
        }
    
    def reset(self) -> None:
        """Reset all counters."""
        self._counters.clear()
        self._start_time = datetime.now()
        LOGGER.info("Metrics counters reset")


# Global metrics counter instance
_metrics_counter = MetricsCounter()


def get_metrics_counter() -> MetricsCounter:
    """Get the global metrics counter instance.
    
    Returns:
        Global MetricsCounter instance.
    """
    return _metrics_counter


def track_command(command_name: str) -> None:
    """Track a bot command execution.
    
    Args:
        command_name: Name of the command (e.g., "start", "match", "stats").
    """
    _metrics_counter.increment(f"command_{command_name}")
    _metrics_counter.increment("commands_total")


def track_interaction(interaction_type: str) -> None:
    """Track a user interaction.
    
    Args:
        interaction_type: Type of interaction (e.g., "like", "dislike", "match").
    """
    _metrics_counter.increment(f"interaction_{interaction_type}")
    _metrics_counter.increment("interactions_total")


def track_profile_action(action: str) -> None:
    """Track a profile action.
    
    Args:
        action: Type of action (e.g., "create", "update", "delete").
    """
    _metrics_counter.increment(f"profile_{action}")
    _metrics_counter.increment("profiles_total")
