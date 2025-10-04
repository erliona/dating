"""Create admin table

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create admin table."""
    op.create_table(
        'admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_admins_username', 'admins', ['username'], unique=True)
    op.create_index('idx_admins_email', 'admins', ['email'], unique=True)
    
    # Create default admin user (username: admin, password: admin123)
    # Password hash for "admin123" using SHA-256
    op.execute(
        """
        INSERT INTO admins (username, password_hash, full_name, is_active, is_super_admin)
        VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Super Admin', true, true)
        """
    )


def downgrade() -> None:
    """Drop admin table."""
    op.drop_index('idx_admins_email', table_name='admins')
    op.drop_index('idx_admins_username', table_name='admins')
    op.drop_table('admins')
