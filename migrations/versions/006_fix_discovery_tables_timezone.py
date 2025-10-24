"""Fix timezone columns for interactions, matches and favorites tables

Revision ID: 006
Revises: 005
Create Date: 2025-01-15 14:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_fix_discovery_tables_timezone"
down_revision: Union[str, None] = "005_fix_profile_tables_timezone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert timestamp columns to timezone-aware for interactions, matches, and favorites tables."""

    # Fix interactions table
    op.execute(
        """
        ALTER TABLE interactions
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE interactions
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Fix matches table
    op.execute(
        """
        ALTER TABLE matches
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )

    # Fix favorites table
    op.execute(
        """
        ALTER TABLE favorites
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    """Convert timestamp columns back to timezone-naive for interactions, matches, and favorites tables."""

    # Revert interactions table
    op.execute(
        """
        ALTER TABLE interactions
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE interactions
        ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'
        """
    )

    # Revert matches table
    op.execute(
        """
        ALTER TABLE matches
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )

    # Revert favorites table
    op.execute(
        """
        ALTER TABLE favorites
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )
