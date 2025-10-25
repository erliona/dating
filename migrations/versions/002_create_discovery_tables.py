"""Create interactions, matches and favorites tables.

Revision ID: 002_create_discovery_tables
Revises: 001_create_profile_tables
Create Date: 2024-10-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_create_discovery_tables"
down_revision: str | None = "001_create_profile_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create interactions, matches and favorites tables."""

    # Create interactions table
    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("interaction_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "interaction_type IN ('like', 'superlike', 'pass')",
            name="valid_interaction_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "target_id", name="unique_user_target_interaction"
        ),
    )
    op.create_index("idx_interactions_user_id", "interactions", ["user_id"])
    op.create_index("idx_interactions_target_id", "interactions", ["target_id"])
    op.create_index(
        "idx_interactions_user_target", "interactions", ["user_id", "target_id"]
    )

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user1_id", sa.Integer(), nullable=False),
        sa.Column("user2_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("user1_id < user2_id", name="user1_less_than_user2"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user1_id", "user2_id", name="unique_match_pair"),
    )
    op.create_index("idx_matches_user1", "matches", ["user1_id"])
    op.create_index("idx_matches_user2", "matches", ["user2_id"])

    # Create favorites table
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "target_id", name="unique_user_favorite"),
    )
    op.create_index("idx_favorites_user_id", "favorites", ["user_id"])
    op.create_index("idx_favorites_target_id", "favorites", ["target_id"])


def downgrade() -> None:
    """Drop interactions, matches and favorites tables."""
    op.drop_table("favorites")
    op.drop_table("matches")
    op.drop_table("interactions")
