"""Fix timezone columns for users, profiles and photos tables

Revision ID: 005
Revises: 004
Create Date: 2025-01-15 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_fix_profile_tables_timezone"
down_revision: Union[str, None] = "004_fix_admin_timezone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert timestamp columns to timezone-aware for users, profiles, and photos tables."""

    # Fix users table
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Fix profiles table
    op.execute(
        """
        ALTER TABLE profiles
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE profiles
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Fix photos table
    op.execute(
        """
        ALTER TABLE photos
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    """Convert timestamp columns back to timezone-naive for users, profiles, and photos tables."""

    # Revert users table
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Revert profiles table
    op.execute(
        """
        ALTER TABLE profiles
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE profiles
        ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Revert photos table
    op.execute(
        """
        ALTER TABLE photos
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )
