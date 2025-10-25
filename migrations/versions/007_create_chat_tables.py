"""Create conversations and messages tables for chat functionality.

Revision ID: 007_create_chat_tables
Revises: 006_fix_discovery_tables_timezone
Create Date: 2025-01-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_create_chat_tables"
down_revision: str | None = "bdaa2d721dde"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create conversations and messages tables."""

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("user1_id", sa.Integer(), nullable=False),
        sa.Column("user2_id", sa.Integer(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column(
            "unread_count_user1", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "unread_count_user2", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("blocked_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id"),
        sa.CheckConstraint("user1_id < user2_id", name="user1_less_than_user2"),
    )
    op.create_index("idx_conversations_user1", "conversations", ["user1_id"])
    op.create_index("idx_conversations_user2", "conversations", ["user2_id"])
    op.create_index("idx_conversations_match_id", "conversations", ["match_id"])

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_type",
            sa.String(length=20),
            nullable=False,
            server_default="'text'",
        ),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "content_type IN ('text', 'photo', 'voice', 'system')",
            name="valid_content_type",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("idx_messages_sender_id", "messages", ["sender_id"])
    op.create_index("idx_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    """Drop conversations and messages tables."""
    op.drop_table("messages")
    op.drop_table("conversations")
