"""Create moderation queue table

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-01-25 09:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "j0k1l2m3n4o5"
down_revision: str = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade():
    """Create moderation_queue table for content moderation."""

    # Create moderation_queue table
    op.create_table(
        "moderation_queue",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "content_type", sa.String(20), nullable=False
        ),  # 'photo' or 'profile'
        sa.Column("content_id", sa.String(36), nullable=False),  # photo_id or user_id
        sa.Column("user_id", sa.String(36), nullable=False),  # who submitted
        sa.Column(
            "status", sa.String(20), nullable=False, default="pending"
        ),  # pending, approved, rejected
        sa.Column(
            "priority", sa.Integer, nullable=False, default=1
        ),  # 1=normal, 2=high, 3=urgent
        sa.Column(
            "reason", sa.String(50), nullable=True
        ),  # 'upload', 'report', 'verification'
        sa.Column(
            "reported_by", sa.String(36), nullable=True
        ),  # if reported by another user
        sa.Column("moderator_id", sa.String(36), nullable=True),  # who moderated
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("moderation_notes", sa.Text, nullable=True),
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
    op.create_index("idx_moderation_queue_status", "moderation_queue", ["status"])
    op.create_index("idx_moderation_queue_priority", "moderation_queue", ["priority"])
    op.create_index("idx_moderation_queue_created", "moderation_queue", ["created_at"])
    op.create_index(
        "idx_moderation_queue_content",
        "moderation_queue",
        ["content_type", "content_id"],
    )
    op.create_index("idx_moderation_queue_user", "moderation_queue", ["user_id"])

    # Create unique constraint to prevent duplicates
    op.create_unique_constraint(
        "uq_moderation_queue_content",
        "moderation_queue",
        ["content_type", "content_id", "status"],
    )


def downgrade():
    """Drop moderation_queue table."""
    op.drop_table("moderation_queue")
