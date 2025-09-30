"""Create interactions, matches, and user_settings tables

Revision ID: 20241201_0002
Revises: 20240611_0001
Create Date: 2024-12-01 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241201_0002"
down_revision = "20240611_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_settings table
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("lang", sa.String(length=10), nullable=False, server_default="ru"),
        sa.Column("show_location", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("show_age", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_matches", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_messages", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        op.f("ix_user_settings_user_id"), "user_settings", ["user_id"], unique=True
    )

    # Create user_interactions table for likes/dislikes
    op.create_table(
        "user_interactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("from_user_id", sa.BigInteger(), nullable=False),
        sa.Column("to_user_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),  # 'like' or 'dislike'
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        op.f("ix_user_interactions_from_user_id"), "user_interactions", ["from_user_id"]
    )
    op.create_index(
        op.f("ix_user_interactions_to_user_id"), "user_interactions", ["to_user_id"]
    )
    # Compound index for efficient lookups
    op.create_index(
        "ix_user_interactions_from_to", "user_interactions", ["from_user_id", "to_user_id"], unique=True
    )

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user1_id", sa.BigInteger(), nullable=False),
        sa.Column("user2_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        op.f("ix_matches_user1_id"), "matches", ["user1_id"]
    )
    op.create_index(
        op.f("ix_matches_user2_id"), "matches", ["user2_id"]
    )
    # Compound index for efficient lookups, ensure user1_id < user2_id
    op.create_index(
        "ix_matches_users", "matches", ["user1_id", "user2_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_matches_users", table_name="matches")
    op.drop_index(op.f("ix_matches_user2_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_user1_id"), table_name="matches")
    op.drop_table("matches")
    
    op.drop_index("ix_user_interactions_from_to", table_name="user_interactions")
    op.drop_index(op.f("ix_user_interactions_to_user_id"), table_name="user_interactions")
    op.drop_index(op.f("ix_user_interactions_from_user_id"), table_name="user_interactions")
    op.drop_table("user_interactions")
    
    op.drop_index(op.f("ix_user_settings_user_id"), table_name="user_settings")
    op.drop_table("user_settings")
