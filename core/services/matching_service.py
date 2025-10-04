"""Matching service - core business logic for discovery and matching."""

from datetime import datetime
from typing import List, Optional

from ..interfaces import IProfileRepository
from ..models import UserProfile, UserSettings


class MatchingService:
    """Service for matching and discovery - platform independent.

    This service contains all business logic for finding and matching profiles,
    independent of any platform (Telegram, mobile, etc.).
    """

    def __init__(self, profile_repository: IProfileRepository):
        """Initialize service with repository interface."""
        self.profile_repository = profile_repository

    async def get_recommendations(
        self, user_id: int, settings: UserSettings, limit: int = 10
    ) -> List[UserProfile]:
        """Get profile recommendations for user.

        Business logic:
        - Apply user preferences (age, distance, orientation)
        - Filter out already seen profiles
        - Apply matching algorithm
        - Return sorted list
        """
        profiles = await self.profile_repository.search_profiles(
            user_id=user_id, settings=settings, limit=limit
        )

        return profiles

    def calculate_compatibility_score(
        self, profile1: UserProfile, profile2: UserProfile
    ) -> float:
        """Calculate compatibility score between two profiles.

        Business logic:
        - Compare interests
        - Compare goals
        - Compare education levels
        - Calculate distance
        - Return score 0-100
        """
        score = 0.0

        # Common interests (up to 40 points)
        if profile1.interests and profile2.interests:
            common_interests = set(profile1.interests) & set(profile2.interests)
            interest_score = min(len(common_interests) * 8, 40)
            score += interest_score

        # Same goal (20 points)
        if profile1.goal and profile2.goal and profile1.goal == profile2.goal:
            score += 20

        # Similar education level (20 points)
        if profile1.education and profile2.education:
            if profile1.education == profile2.education:
                score += 20
            elif (
                abs(
                    self._education_level(profile1.education)
                    - self._education_level(profile2.education)
                )
                <= 1
            ):
                score += 10

        # Common languages (20 points)
        if profile1.languages and profile2.languages:
            common_languages = set(profile1.languages) & set(profile2.languages)
            language_score = min(len(common_languages) * 10, 20)
            score += language_score

        return min(score, 100.0)

    def _education_level(self, education) -> int:
        """Convert education enum to numeric level for comparison."""
        education_levels = {
            "high_school": 1,
            "bachelor": 2,
            "master": 3,
            "phd": 4,
            "other": 0,
        }
        return education_levels.get(
            education.value if hasattr(education, "value") else education, 0
        )

    async def apply_filters(
        self,
        profiles: List[UserProfile],
        settings: UserSettings,
        user_location: Optional[tuple[float, float]] = None,
    ) -> List[UserProfile]:
        """Apply user preference filters to profile list.

        Business logic:
        - Filter by age range
        - Filter by distance (if location available)
        - Filter by orientation
        - Sort by compatibility
        """
        filtered = []

        for profile in profiles:
            # Age filter
            if not (settings.min_age <= profile.age <= settings.max_age):
                continue

            # Orientation filter
            if settings.show_me != "any":
                if profile.gender.value != settings.show_me.value:
                    continue

            # Distance filter (if location available)
            if user_location and profile.latitude and profile.longitude:
                distance = self._calculate_distance(
                    user_location[0],
                    user_location[1],
                    profile.latitude,
                    profile.longitude,
                )
                if distance > settings.max_distance:
                    continue

            # Profile must be visible
            if not profile.is_visible:
                continue

            filtered.append(profile)

        return filtered

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates in km (Haversine formula)."""
        from math import atan2, cos, radians, sin, sqrt

        R = 6371  # Earth radius in km

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c
