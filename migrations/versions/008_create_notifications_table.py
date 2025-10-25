"""Create notifications table for push notifications.

Revision ID: 008_create_notifications_table
Revises: 007_create_chat_tables
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_create_notifications_table"
down_revision: str | None = "007_create_chat_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create notifications table."""

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "notification_type IN ('new_match', 'new_message', 'new_like', 'verification_complete', 'verification_rejected')",
            name="valid_notification_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_type", "notifications", ["notification_type"])
    op.create_index("idx_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    """Drop notifications table."""
    op.drop_table("notifications")
