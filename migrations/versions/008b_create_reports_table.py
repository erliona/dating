"""Create reports table for user reports and moderation.

Revision ID: 008b_create_reports_table
Revises: 008_create_notifications_table
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008b_create_reports_table"
down_revision: str | None = "008_create_notifications_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create reports table."""

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("reported_user_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "context", sa.String(length=20), nullable=False, server_default="'profile'"
        ),
        sa.Column("context_id", sa.Integer(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="'pending'"
        ),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("action_taken", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "report_type IN ('spam', 'inappropriate_content', 'fake_profile', 'harassment', 'underage', 'other')",
            name="valid_report_type",
        ),
        sa.CheckConstraint(
            "context IN ('profile', 'chat', 'photo')",
            name="valid_context",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'investigating', 'resolved', 'dismissed')",
            name="valid_status",
        ),
        sa.CheckConstraint(
            "action_taken IN ('warned', 'banned_1d', 'banned_7d', 'banned_permanent', 'profile_hidden', 'photo_removed', 'no_action')",
            name="valid_action_taken",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reporter_id",
            "reported_user_id",
            "context",
            "context_id",
            name="unique_report",
        ),
    )
    op.create_index("idx_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("idx_reports_reported_user_id", "reports", ["reported_user_id"])
    op.create_index("idx_reports_status", "reports", ["status"])
    op.create_index("idx_reports_created_at", "reports", ["created_at"])


def downgrade() -> None:
    """Drop reports table."""
    op.drop_table("reports")
