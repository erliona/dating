"""Create likes table for tracking who liked whom.

Revision ID: 011_create_likes_table
Revises: 010_add_user_preferences_activity
Create Date: 2025-01-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_create_likes_table"
down_revision: Union[str, None] = "010_add_user_preferences_activity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create likes table."""
    
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("liker_id", sa.Integer(), nullable=False),
        sa.Column("liked_id", sa.Integer(), nullable=False),
        sa.Column("like_type", sa.String(length=20), nullable=False, server_default="'like'"),
        sa.Column("is_viewed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
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
