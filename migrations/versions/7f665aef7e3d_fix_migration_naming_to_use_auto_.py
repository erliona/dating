"""fix_migration_naming_to_use_auto_generated_hashes

Revision ID: 7f665aef7e3d
Revises: 7530ba8052bd
Create Date: 2025-10-25 15:33:10.698336

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f665aef7e3d'
down_revision: str = '7530ba8052bd'
branch_labels: str = None
depends_on: str = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
