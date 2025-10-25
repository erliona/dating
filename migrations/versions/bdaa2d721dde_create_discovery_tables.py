"""create discovery tables

Revision ID: bdaa2d721dde
Revises: dcaef3149a45
Create Date: 2025-10-25 22:47:46.236062

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bdaa2d721dde"
down_revision: str = "dcaef3149a45"
branch_labels: str = None
depends_on: str = None


def upgrade() -> None:
    """Create discovery and matching tables."""

    # Create interactions table
    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("target_id", sa.Integer(), nullable=False, index=True),
        sa.Column("interaction_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "target_id", name="unique_user_target_interaction"
        ),
        sa.CheckConstraint(
            "interaction_type IN ('like', 'superlike', 'pass')",
            name="valid_interaction_type",
        ),
    )

    # Create matches table
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user1_id", sa.Integer(), nullable=False, index=True),
        sa.Column("user2_id", sa.Integer(), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user1_id", "user2_id", name="unique_match_pair"),
        sa.CheckConstraint("user1_id < user2_id", name="user1_less_than_user2"),
    )

    # Create favorites table
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("target_id", sa.Integer(), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "target_id", name="unique_user_favorite"),
    )

    # Create admins table
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column(
            "username", sa.String(length=255), nullable=False, unique=True, index=True
        ),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "email", sa.String(length=255), nullable=True, unique=True, index=True
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop discovery and matching tables."""
    op.drop_table("admins")
    op.drop_table("favorites")
    op.drop_table("matches")
    op.drop_table("interactions")
