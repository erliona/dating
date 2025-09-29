"""Create profiles table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20240611_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=16), nullable=False),
        sa.Column("preference", sa.String(length=16), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column(
            "interests",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("goal", sa.String(length=32), nullable=True),
        sa.Column("photo_file_id", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_profiles_user_id"), table_name="profiles")
    op.drop_table("profiles")
