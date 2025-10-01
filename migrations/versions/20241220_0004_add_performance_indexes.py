"""Add performance indexes for query optimization

Revision ID: 20241220_0004
Revises: 20241215_0003
Create Date: 2024-12-20 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241220_0004"
down_revision = "20241215_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add index on age for age-based filtering
    op.create_index(
        op.f("ix_profiles_age"), "profiles", ["age"]
    )
    
    # Add index on location for geographic filtering
    op.create_index(
        op.f("ix_profiles_location"), "profiles", ["location"]
    )
    
    # Add composite index for common matching queries (gender + preference)
    op.create_index(
        "ix_profiles_gender_preference", "profiles", ["gender", "preference"]
    )
    
    # Add composite index for filtering by preference and age (common in recommendations)
    op.create_index(
        "ix_profiles_preference_age", "profiles", ["preference", "age"]
    )


def downgrade() -> None:
    op.drop_index("ix_profiles_preference_age", table_name="profiles")
    op.drop_index("ix_profiles_gender_preference", table_name="profiles")
    op.drop_index(op.f("ix_profiles_location"), table_name="profiles")
    op.drop_index(op.f("ix_profiles_age"), table_name="profiles")
