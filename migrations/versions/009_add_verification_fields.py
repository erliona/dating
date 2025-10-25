"""Add verification fields to profiles table.

Revision ID: 009_add_verification_fields
Revises: 008b_create_reports_table
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009_add_verification_fields"
down_revision: str | None = "008b_create_reports_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add verification fields to profiles table."""

    op.add_column(
        "profiles",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "verification_status",
            sa.String(length=20),
            nullable=False,
            server_default="'none'",
        ),
    )
    op.add_column(
        "profiles",
        sa.Column("verification_photo_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "profiles", sa.Column("verification_requested_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "profiles", sa.Column("verification_completed_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "profiles", sa.Column("verified_by_admin_id", sa.Integer(), nullable=True)
    )

    # Add check constraints
    op.create_check_constraint(
        "valid_verification_status",
        "profiles",
        "verification_status IN ('none', 'pending', 'verified', 'rejected')",
    )


def downgrade() -> None:
    """Remove verification fields from profiles table."""
    op.drop_constraint("valid_verification_status", "profiles", type_="check")
    op.drop_column("profiles", "verified_by_admin_id")
    op.drop_column("profiles", "verification_completed_at")
    op.drop_column("profiles", "verification_requested_at")
    op.drop_column("profiles", "verification_photo_url")
    op.drop_column("profiles", "verification_status")
    op.drop_column("profiles", "is_verified")
