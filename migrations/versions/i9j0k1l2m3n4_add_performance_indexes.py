"""Add performance indexes

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-01-24 11:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: str = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for query optimization."""

    # Profiles table indexes - using actual column names
    op.create_index("idx_profiles_city", "profiles", ["city"])

    op.create_index("idx_profiles_created_at", "profiles", ["created_at"])

    op.create_index("idx_profiles_geohash", "profiles", ["geohash"])

    # Interactions table indexes - using actual column names
    op.create_index(
        "idx_interactions_target_type",
        "interactions",
        ["target_id", "interaction_type"],
    )

    op.create_index(
        "idx_interactions_user_type", "interactions", ["user_id", "interaction_type"]
    )

    op.create_index("idx_interactions_created_at", "interactions", ["created_at"])

    # Messages table indexes (additional to existing)
    op.create_index(
        "idx_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at", "id"],
    )

    op.create_index(
        "idx_messages_sender_created", "messages", ["sender_id", "created_at"]
    )

    # Conversations table indexes
    op.create_index(
        "idx_conversations_users", "conversations", ["user1_id", "user2_id"]
    )

    op.create_index("idx_conversations_updated_at", "conversations", ["updated_at"])

    # Likes table indexes (additional to existing)
    op.create_index("idx_likes_liked_created", "likes", ["liked_id", "created_at"])

    op.create_index("idx_likes_liker_created", "likes", ["liker_id", "created_at"])

    # Photos table indexes
    op.create_index("idx_photos_created_at", "photos", ["created_at"])

    op.create_index("idx_photos_user_id", "photos", ["user_id"])

    # Notifications table indexes (additional to existing)
    op.create_index(
        "idx_notifications_user_type", "notifications", ["user_id", "notification_type"]
    )

    op.create_index(
        "idx_notifications_read_created", "notifications", ["is_read", "created_at"]
    )

    # Reports table indexes (additional to existing)
    op.create_index(
        "idx_reports_reported_status", "reports", ["reported_user_id", "status"]
    )

    op.create_index("idx_reports_created_status", "reports", ["created_at", "status"])

    # Chat blocks indexes
    op.create_index("idx_chat_blocks_blocker", "chat_blocks", ["blocker_id"])

    op.create_index("idx_chat_blocks_target", "chat_blocks", ["target_user_id"])

    # Chat reports indexes (additional to existing)
    op.create_index("idx_chat_reports_reporter", "chat_reports", ["reporter_id"])

    op.create_index(
        "idx_chat_reports_conversation", "chat_reports", ["conversation_id"]
    )

    # Participant read state indexes
    op.create_index(
        "idx_participant_read_state_user", "participant_read_state", ["user_id"]
    )

    op.create_index(
        "idx_participant_read_state_message",
        "participant_read_state",
        ["last_read_message_id"],
    )


def downgrade():
    """Remove performance indexes."""

    # Remove all indexes in reverse order
    op.drop_index(
        "idx_participant_read_state_message", table_name="participant_read_state"
    )
    op.drop_index(
        "idx_participant_read_state_user", table_name="participant_read_state"
    )
    op.drop_index("idx_chat_reports_conversation", table_name="chat_reports")
    op.drop_index("idx_chat_reports_reporter", table_name="chat_reports")
    op.drop_index("idx_chat_blocks_target", table_name="chat_blocks")
    op.drop_index("idx_chat_blocks_blocker", table_name="chat_blocks")
    op.drop_index("idx_reports_created_status", table_name="reports")
    op.drop_index("idx_reports_reported_status", table_name="reports")
    op.drop_index("idx_notifications_read_created", table_name="notifications")
    op.drop_index("idx_notifications_user_type", table_name="notifications")
    op.drop_index("idx_photos_user_id", table_name="photos")
    op.drop_index("idx_photos_created_at", table_name="photos")
    op.drop_index("idx_likes_liker_created", table_name="likes")
    op.drop_index("idx_likes_liked_created", table_name="likes")
    op.drop_index("idx_conversations_updated_at", table_name="conversations")
    op.drop_index("idx_conversations_users", table_name="conversations")
    op.drop_index("idx_messages_sender_created", table_name="messages")
    op.drop_index("idx_messages_conversation_created", table_name="messages")
    op.drop_index("idx_interactions_created_at", table_name="interactions")
    op.drop_index("idx_interactions_user_type", table_name="interactions")
    op.drop_index("idx_interactions_target_type", table_name="interactions")
    op.drop_index("idx_profiles_geohash", table_name="profiles")
    op.drop_index("idx_profiles_created_at", table_name="profiles")
    op.drop_index("idx_profiles_city", table_name="profiles")
