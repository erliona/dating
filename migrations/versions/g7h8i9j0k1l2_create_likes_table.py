"""Create likes table for tracking who liked whom.

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7h8i9j0k1l2"
down_revision: str | None = "f6g7h8i9j0k1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create likes table."""

    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("liker_id", sa.Integer(), nullable=False),
        sa.Column("liked_id", sa.Integer(), nullable=False),
        sa.Column(
            "like_type", sa.String(length=20), nullable=False, server_default="'like'"
        ),
        sa.Column("is_viewed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "like_type IN ('like', 'superlike')",
            name="valid_like_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("liker_id", "liked_id", name="unique_like_pair"),
    )
    op.create_index("idx_likes_liker_id", "likes", ["liker_id"])
    op.create_index("idx_likes_liked_id", "likes", ["liked_id"])
    op.create_index("idx_likes_created_at", "likes", ["created_at"])


def downgrade() -> None:
    """Drop likes table."""
    op.drop_table("likes")
