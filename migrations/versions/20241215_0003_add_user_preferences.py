"""Add age and distance preferences to user_settings

Revision ID: 20241215_0003
Revises: 20241201_0002
Create Date: 2024-12-15 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241215_0003"
down_revision = "20241201_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add age preference columns to user_settings table
    op.add_column("user_settings", sa.Column("age_min", sa.Integer(), nullable=True))
    op.add_column("user_settings", sa.Column("age_max", sa.Integer(), nullable=True))
    
    # Add distance preference (in km, null means no limit)
    op.add_column("user_settings", sa.Column("max_distance", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "max_distance")
    op.drop_column("user_settings", "age_max")
    op.drop_column("user_settings", "age_min")
