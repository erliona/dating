"""Create notification_preferences table

Revision ID: 015_create_notification_preferences
Revises: 014_create_moderation_queue
Create Date: 2025-01-25 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "015_create_notification_preferences"
down_revision = "014_create_moderation_queue"
branch_labels = None
depends_on = None


def upgrade():
    """Create notification_preferences table for user notification settings."""

    # Create notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("push_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("email_enabled", sa.Boolean, nullable=False, default=False),
        sa.Column("telegram_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("new_matches", sa.Boolean, nullable=False, default=True),
        sa.Column("new_messages", sa.Boolean, nullable=False, default=True),
        sa.Column("super_likes", sa.Boolean, nullable=False, default=True),
        sa.Column("likes", sa.Boolean, nullable=False, default=True),
        sa.Column("profile_views", sa.Boolean, nullable=False, default=False),
        sa.Column("verification_updates", sa.Boolean, nullable=False, default=True),
        sa.Column("marketing", sa.Boolean, nullable=False, default=False),
        sa.Column("reminders", sa.Boolean, nullable=False, default=True),
        sa.Column("quiet_hours_start", sa.Time, nullable=True),
        sa.Column("quiet_hours_end", sa.Time, nullable=True),
        sa.Column("timezone", sa.String(50), nullable=True, default="UTC"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes for performance
    op.create_index(
        "idx_notification_preferences_user", "notification_preferences", ["user_id"]
    )
    op.create_index(
        "idx_notification_preferences_push",
        "notification_preferences",
        ["push_enabled"],
    )
    op.create_index(
        "idx_notification_preferences_telegram",
        "notification_preferences",
        ["telegram_enabled"],
    )

    # Create unique constraint to prevent duplicates
    op.create_unique_constraint(
        "uq_notification_preferences_user", "notification_preferences", ["user_id"]
    )


def downgrade():
    """Drop notification_preferences table."""
    op.drop_table("notification_preferences")
