"""Chat protocol improvements

Revision ID: 012_chat_protocol_improvements
Revises: 011_create_likes_table
Create Date: 2025-01-24 10:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_chat_protocol_improvements"
down_revision: str = "011_create_likes_table"
branch_labels = None
depends_on = None


def upgrade():
    """Add chat protocol improvements."""

    # Add idempotency support to messages
    op.add_column(
        "messages", sa.Column("idempotency_key", postgresql.UUID(), nullable=True)
    )
    op.add_column(
        "messages", sa.Column("idempotency_expires_at", sa.TIMESTAMP(), nullable=True)
    )

    # Add unique constraint for idempotency
    op.create_unique_constraint(
        "unique_message_idempotency",
        "messages",
        ["conversation_id", "sender_id", "idempotency_key"],
    )

    # Create participant_read_state table
    op.create_table(
        "participant_read_state",
        sa.Column("conversation_id", postgresql.UUID(), nullable=False),
        sa.Column("user_id", postgresql.UUID(), nullable=False),
        sa.Column("last_read_message_id", postgresql.UUID(), nullable=False),
        sa.Column(
            "last_read_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("conversation_id", "user_id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["last_read_message_id"], ["messages.id"], ondelete="CASCADE"
        ),
    )

    # Create chat_blocks table
    op.create_table(
        "chat_blocks",
        sa.Column("blocker_id", postgresql.UUID(), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("blocker_id", "target_user_id"),
        sa.ForeignKeyConstraint(["blocker_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create chat_reports table
    op.create_table(
        "chat_reports",
        sa.Column(
            "id",
            postgresql.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("reporter_id", postgresql.UUID(), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(), nullable=False),
        sa.Column("message_id", postgresql.UUID(), nullable=True),
        sa.Column("reason", sa.VARCHAR(50), nullable=False),
        sa.Column("comment", sa.TEXT(), nullable=True),
        sa.Column("status", sa.VARCHAR(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("reviewed_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )

    # Add indexes for performance
    op.create_index(
        "idx_messages_conversation_time",
        "messages",
        ["conversation_id", "created_at", "id"],
        postgresql_using="btree",
    )

    op.create_index(
        "idx_messages_idempotency",
        "messages",
        ["idempotency_key"],
        postgresql_using="btree",
    )

    op.create_index(
        "idx_chat_reports_status",
        "chat_reports",
        ["status", "created_at"],
        postgresql_using="btree",
    )


def downgrade():
    """Remove chat protocol improvements."""

    # Remove indexes
    op.drop_index("idx_chat_reports_status", table_name="chat_reports")
    op.drop_index("idx_messages_idempotency", table_name="messages")
    op.drop_index("idx_messages_conversation_time", table_name="messages")

    # Remove tables
    op.drop_table("chat_reports")
    op.drop_table("chat_blocks")
    op.drop_table("participant_read_state")

    # Remove unique constraint
    op.drop_constraint("unique_message_idempotency", "messages", type_="unique")

    # Remove columns
    op.drop_column("messages", "idempotency_expires_at")
    op.drop_column("messages", "idempotency_key")
