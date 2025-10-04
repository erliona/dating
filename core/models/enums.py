"""Core enumerations for domain models."""

from enum import Enum


class Gender(str, Enum):
    """Gender enum."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Orientation(str, Enum):
    """Orientation enum."""

    MALE = "male"
    FEMALE = "female"
    ANY = "any"


class Goal(str, Enum):
    """Relationship goal enum."""

    FRIENDSHIP = "friendship"
    DATING = "dating"
    RELATIONSHIP = "relationship"
    NETWORKING = "networking"
    SERIOUS = "serious"
    CASUAL = "casual"


class Education(str, Enum):
    """Education level enum."""

    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    OTHER = "other"
