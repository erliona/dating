"""fix_migration_chain_integrity

Revision ID: 8b74e0367a99
Revises: 7f665aef7e3d
Create Date: 2025-10-25 15:36:32.862886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b74e0367a99'
down_revision: str = '7f665aef7e3d'
branch_labels: str = None
depends_on: str = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
