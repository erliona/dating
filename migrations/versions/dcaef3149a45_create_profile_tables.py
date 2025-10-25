"""create profile tables

Revision ID: dcaef3149a45
Revises: 8b74e0367a99
Create Date: 2025-10-25 22:47:43.779206

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dcaef3149a45"
down_revision: str = None
branch_labels: str = None
depends_on: str = None


def upgrade() -> None:
    """Create users and profiles tables."""

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("tg_id", sa.BigInteger(), nullable=False, unique=True, index=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=10), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_banned", sa.Boolean(), nullable=False, default=False),
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

    # Create profiles table
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("orientation", sa.String(length=20), nullable=False),
        sa.Column("goal", sa.String(length=50), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("interests", sa.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column("height_cm", sa.SmallInteger(), nullable=True),
        sa.Column("education", sa.String(length=50), nullable=True),
        sa.Column("has_children", sa.Boolean(), nullable=True),
        sa.Column("wants_children", sa.Boolean(), nullable=True),
        sa.Column("smoking", sa.Boolean(), nullable=True),
        sa.Column("drinking", sa.Boolean(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("geohash", sa.String(length=20), nullable=True, index=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("hide_distance", sa.Boolean(), nullable=False, default=False),
        sa.Column("hide_online", sa.Boolean(), nullable=False, default=False),
        sa.Column("hide_age", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "allow_messages_from",
            sa.String(length=20),
            nullable=False,
            default="matches",
        ),
        sa.Column("is_visible", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_complete", sa.Boolean(), nullable=False, default=False),
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
        sa.CheckConstraint("birth_date <= CURRENT_DATE", name="birth_date_not_future"),
        sa.CheckConstraint(
            "height_cm IS NULL OR (height_cm >= 100 AND height_cm <= 250)",
            name="height_cm_range",
        ),
        sa.CheckConstraint(
            "gender IN ('male', 'female', 'other')", name="valid_gender"
        ),
        sa.CheckConstraint(
            "orientation IN ('male', 'female', 'any')", name="valid_orientation"
        ),
        sa.CheckConstraint(
            "goal IN ('friendship', 'dating', 'relationship', 'networking', 'serious', 'casual')",
            name="valid_goal",
        ),
        sa.CheckConstraint(
            "allow_messages_from IN ('matches', 'anyone')",
            name="valid_allow_messages_from",
        ),
    )

    # Create photos table
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, default=0),
        sa.Column("safe_score", sa.Float(), nullable=False, default=1.0),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop users, profiles, and photos tables."""
    op.drop_table("photos")
    op.drop_table("profiles")
    op.drop_table("users")
