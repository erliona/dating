"""Notification preferences models for user notification settings."""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from sqlalchemy import Column, String, Boolean, Time, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class NotificationPreferences(Base):
    """User notification preferences."""
    
    __tablename__ = 'notification_preferences'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    push_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=False)
    telegram_enabled = Column(Boolean, nullable=False, default=True)
    new_matches = Column(Boolean, nullable=False, default=True)
    new_messages = Column(Boolean, nullable=False, default=True)
    super_likes = Column(Boolean, nullable=False, default=True)
    likes = Column(Boolean, nullable=False, default=True)
    profile_views = Column(Boolean, nullable=False, default=False)
    verification_updates = Column(Boolean, nullable=False, default=True)
    marketing = Column(Boolean, nullable=False, default=False)
    reminders = Column(Boolean, nullable=False, default=True)
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)
    timezone = Column(String(50), nullable=True, default='UTC')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'push_enabled': self.push_enabled,
            'email_enabled': self.email_enabled,
            'telegram_enabled': self.telegram_enabled,
            'new_matches': self.new_matches,
            'new_messages': self.new_messages,
            'super_likes': self.super_likes,
            'likes': self.likes,
            'profile_views': self.profile_views,
            'verification_updates': self.verification_updates,
            'marketing': self.marketing,
            'reminders': self.reminders,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_default(cls, user_id: str) -> 'NotificationPreferences':
        """Create default notification preferences for a user."""
        return cls(
            id=f"notif_prefs_{user_id}_{int(datetime.utcnow().timestamp())}",
            user_id=user_id,
            push_enabled=True,
            email_enabled=False,
            telegram_enabled=True,
            new_matches=True,
            new_messages=True,
            super_likes=True,
            likes=True,
            profile_views=False,
            verification_updates=True,
            marketing=False,
            reminders=True,
            quiet_hours_start=None,
            quiet_hours_end=None,
            timezone='UTC'
        )
    
    def is_quiet_hours(self, current_time: Optional[time] = None) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        if current_time is None:
            current_time = datetime.now().time()
        
        # Handle quiet hours that cross midnight
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
    
    def should_send_notification(self, notification_type: str) -> bool:
        """Check if notification should be sent based on preferences."""
        # Check if push notifications are enabled
        if not self.push_enabled:
            return False
        
        # Check quiet hours
        if self.is_quiet_hours():
            return False
        
        # Check specific notification type
        type_mapping = {
            'new_match': self.new_matches,
            'new_message': self.new_messages,
            'super_like': self.super_likes,
            'like': self.likes,
            'profile_view': self.profile_views,
            'verification_update': self.verification_updates,
            'marketing': self.marketing,
            'reminder': self.reminders
        }
        
        return type_mapping.get(notification_type, True)
