"""Add user preferences and activity tracking tables.

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6g7h8i9j0k1"
down_revision: str | None = "e5f6g7h8i9j0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create user preferences and activity tables."""

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("max_age", sa.Integer(), nullable=False, server_default="55"),
        sa.Column(
            "preferred_gender",
            sa.String(length=20),
            nullable=False,
            server_default="'any'",
        ),
        sa.Column("max_distance_km", sa.Integer(), nullable=False, server_default="50"),
        sa.Column(
            "show_verified_only", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "show_active_only", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("min_age >= 18 AND min_age <= 100", name="valid_min_age"),
        sa.CheckConstraint("max_age >= 18 AND max_age <= 100", name="valid_max_age"),
        sa.CheckConstraint("min_age <= max_age", name="min_age_less_than_max_age"),
        sa.CheckConstraint(
            "max_distance_km >= 1 AND max_distance_km <= 1000",
            name="valid_max_distance",
        ),
        sa.CheckConstraint(
            "preferred_gender IN ('male', 'female', 'any')",
            name="valid_preferred_gender",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("idx_user_preferences_user_id", "user_preferences", ["user_id"])

    # Create user_activity table
    op.create_table(
        "user_activity",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column("last_location_update_at", sa.DateTime(), nullable=True),
        sa.Column("total_swipes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_likes_given", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "total_likes_received", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_matches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "daily_superlikes_used", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("last_superlike_reset_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("total_swipes >= 0", name="valid_total_swipes"),
        sa.CheckConstraint("total_likes_given >= 0", name="valid_likes_given"),
        sa.CheckConstraint("total_likes_received >= 0", name="valid_likes_received"),
        sa.CheckConstraint("total_matches >= 0", name="valid_total_matches"),
        sa.CheckConstraint(
            "daily_superlikes_used >= 0 AND daily_superlikes_used <= 5",
            name="valid_daily_superlikes",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("idx_user_activity_user_id", "user_activity", ["user_id"])
    op.create_index(
        "idx_user_activity_last_active", "user_activity", ["last_active_at"]
    )


def downgrade() -> None:
    """Drop user preferences and activity tables."""
    op.drop_table("user_activity")
    op.drop_table("user_preferences")
