"""Fix admin timezone columns

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert admin timestamp columns to timezone-aware."""
    # Convert last_login to TIMESTAMPTZ
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN last_login TYPE TIMESTAMPTZ USING last_login AT TIME ZONE 'UTC'
        """
    )

    # Convert created_at to TIMESTAMPTZ
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'
        """
    )

    # Convert updated_at to TIMESTAMPTZ
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    """Convert admin timestamp columns back to timezone-naive."""
    # Convert last_login back to TIMESTAMP
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN last_login TYPE TIMESTAMP USING last_login AT TIME ZONE 'UTC'
        """
    )

    # Convert created_at back to TIMESTAMP
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'
        """
    )

    # Convert updated_at back to TIMESTAMP
    op.execute(
        """
        ALTER TABLE admins
        ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'
        """
    )
