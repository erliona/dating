"""Add Telegram metadata fields to users table for admin panel and anti-fraud.

Revision ID: 009b_add_telegram_metadata
Revises: 009_add_verification_fields
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009b_add_telegram_metadata"
down_revision: str | None = "009_add_verification_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Telegram metadata fields to users table."""

    # Telegram Profile Info
    op.add_column(
        "users", sa.Column("tg_username", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("tg_first_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("tg_last_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users", sa.Column("tg_language_code", sa.String(length=10), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "tg_is_premium", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "users", sa.Column("tg_photo_url", sa.String(length=500), nullable=True)
    )
    op.add_column("users", sa.Column("tg_bio", sa.Text(), nullable=True))

    # Device & Location Info
    op.add_column(
        "users", sa.Column("tg_platform", sa.String(length=50), nullable=True)
    )
    op.add_column("users", sa.Column("tg_version", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("ip_address", sa.String(length=45), nullable=True))
    op.add_column(
        "users", sa.Column("ip_country", sa.String(length=100), nullable=True)
    )
    op.add_column("users", sa.Column("ip_city", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("user_agent", sa.Text(), nullable=True))

    # Anti-Fraud Metadata
    op.add_column(
        "users", sa.Column("tg_account_created_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("tg_has_phone", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column(
            "tg_has_username", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "users",
        sa.Column("tg_is_bot", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("tg_is_scam", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("tg_is_fake", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column(
            "tg_is_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "tg_added_to_attachment_menu",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # Referral & UTM
    op.add_column(
        "users", sa.Column("referral_source", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "users", sa.Column("referral_campaign", sa.String(length=100), nullable=True)
    )
    op.add_column("users", sa.Column("invited_by_user_id", sa.Integer(), nullable=True))

    # Risk Scoring
    op.add_column(
        "users",
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column("users", sa.Column("risk_flags", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("admin_notes", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_flagged_for_review",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    # Timestamps
    op.add_column("users", sa.Column("first_login_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users", sa.Column("registration_completed_at", sa.DateTime(), nullable=True)
    )

    # Add indexes
    op.create_index("idx_users_tg_username", "users", ["tg_username"])
    op.create_index("idx_users_ip_address", "users", ["ip_address"])
    op.create_index("idx_users_risk_score", "users", ["risk_score"])
    op.create_index("idx_users_flagged", "users", ["is_flagged_for_review"])

    # Add check constraints
    op.create_check_constraint(
        "valid_risk_score", "users", "risk_score >= 0.0 AND risk_score <= 1.0"
    )


def downgrade() -> None:
    """Remove Telegram metadata fields from users table."""
    op.drop_constraint("valid_risk_score", "users", type_="check")
    op.drop_index("idx_users_flagged", "users")
    op.drop_index("idx_users_risk_score", "users")
    op.drop_index("idx_users_ip_address", "users")
    op.drop_index("idx_users_tg_username", "users")

    op.drop_column("users", "registration_completed_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "first_login_at")
    op.drop_column("users", "is_flagged_for_review")
    op.drop_column("users", "admin_notes")
    op.drop_column("users", "risk_flags")
    op.drop_column("users", "risk_score")
    op.drop_column("users", "invited_by_user_id")
    op.drop_column("users", "referral_campaign")
    op.drop_column("users", "referral_source")
    op.drop_column("users", "tg_added_to_attachment_menu")
    op.drop_column("users", "tg_is_verified")
    op.drop_column("users", "tg_is_fake")
    op.drop_column("users", "tg_is_scam")
    op.drop_column("users", "tg_is_bot")
    op.drop_column("users", "tg_has_username")
    op.drop_column("users", "tg_has_phone")
    op.drop_column("users", "tg_account_created_at")
    op.drop_column("users", "user_agent")
    op.drop_column("users", "ip_city")
    op.drop_column("users", "ip_country")
    op.drop_column("users", "ip_address")
    op.drop_column("users", "tg_version")
    op.drop_column("users", "tg_platform")
    op.drop_column("users", "tg_bio")
    op.drop_column("users", "tg_photo_url")
    op.drop_column("users", "tg_is_premium")
    op.drop_column("users", "tg_language_code")
    op.drop_column("users", "tg_last_name")
    op.drop_column("users", "tg_first_name")
    op.drop_column("users", "tg_username")
