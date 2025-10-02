"""Create users, profiles and photos tables.

Revision ID: 001_create_profile_tables
Revises: 
Create Date: 2024-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_create_profile_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users, profiles and photos tables."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tg_id')
    )
    op.create_index('ix_users_tg_id', 'users', ['tg_id'])
    
    # Create profiles table
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('orientation', sa.String(length=20), nullable=False),
        sa.Column('goal', sa.String(length=50), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('interests', sa.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column('height_cm', sa.SmallInteger(), nullable=True),
        sa.Column('education', sa.String(length=50), nullable=True),
        sa.Column('has_children', sa.Boolean(), nullable=True),
        sa.Column('wants_children', sa.Boolean(), nullable=True),
        sa.Column('smoking', sa.Boolean(), nullable=True),
        sa.Column('drinking', sa.Boolean(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('geohash', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('hide_distance', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hide_online', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('hide_age', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allow_messages_from', sa.String(length=20), nullable=False, server_default="'matches'"),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('birth_date <= CURRENT_DATE', name='birth_date_not_future'),
        sa.CheckConstraint('height_cm IS NULL OR (height_cm >= 100 AND height_cm <= 250)', 
                          name='height_cm_range'),
        sa.CheckConstraint("gender IN ('male', 'female', 'other')", name='valid_gender'),
        sa.CheckConstraint("orientation IN ('male', 'female', 'any')", name='valid_orientation'),
        sa.CheckConstraint(
            "goal IN ('friendship', 'dating', 'relationship', 'networking', 'serious', 'casual')",
            name='valid_goal'
        ),
        sa.CheckConstraint(
            "allow_messages_from IN ('matches', 'anyone')", 
            name='valid_allow_messages_from'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_profiles_user_id', 'profiles', ['user_id'])
    op.create_index('idx_profiles_geohash', 'profiles', ['geohash'])
    
    # Create photos table
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('safe_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=50), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('sort_order >= 0 AND sort_order <= 2', name='sort_order_range'),
        sa.CheckConstraint('safe_score >= 0.0 AND safe_score <= 1.0', name='safe_score_range'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_photos_user_id', 'photos', ['user_id'])
    op.create_index('idx_photos_user_id_sort', 'photos', ['user_id', 'sort_order'])


def downgrade() -> None:
    """Drop users, profiles and photos tables."""
    op.drop_table('photos')
    op.drop_table('profiles')
    op.drop_table('users')
