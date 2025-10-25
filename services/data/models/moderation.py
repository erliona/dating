"""Moderation queue models for content moderation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ModerationQueue(Base):
    """Moderation queue for content review."""
    
    __tablename__ = 'moderation_queue'
    
    id = Column(String(36), primary_key=True)
    content_type = Column(String(20), nullable=False)  # 'photo' or 'profile'
    content_id = Column(String(36), nullable=False)    # photo_id or user_id
    user_id = Column(String(36), nullable=False)       # who submitted
    status = Column(String(20), nullable=False, default='pending')  # pending, approved, rejected
    priority = Column(Integer, nullable=False, default=1)  # 1=normal, 2=high, 3=urgent
    reason = Column(String(50), nullable=True)         # 'upload', 'report', 'verification'
    reported_by = Column(String(36), nullable=True)    # if reported by another user
    moderator_id = Column(String(36), nullable=True)   # who moderated
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'user_id': self.user_id,
            'status': self.status,
            'priority': self.priority,
            'reason': self.reason,
            'reported_by': self.reported_by,
            'moderator_id': self.moderator_id,
            'moderated_at': self.moderated_at.isoformat() if self.moderated_at else None,
            'moderation_notes': self.moderation_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_photo_moderation(
        cls,
        photo_id: str,
        user_id: str,
        reason: str = 'upload',
        priority: int = 1
    ) -> 'ModerationQueue':
        """Create photo moderation entry."""
        return cls(
            id=f"mod_{photo_id}_{int(datetime.utcnow().timestamp())}",
            content_type='photo',
            content_id=photo_id,
            user_id=user_id,
            reason=reason,
            priority=priority
        )
    
    @classmethod
    def create_profile_moderation(
        cls,
        user_id: str,
        reason: str = 'verification',
        priority: int = 1
    ) -> 'ModerationQueue':
        """Create profile moderation entry."""
        return cls(
            id=f"mod_profile_{user_id}_{int(datetime.utcnow().timestamp())}",
            content_type='profile',
            content_id=user_id,
            user_id=user_id,
            reason=reason,
            priority=priority
        )
    
    @classmethod
    def create_report_moderation(
        cls,
        content_type: str,
        content_id: str,
        reported_by: str,
        reason: str = 'report',
        priority: int = 2
    ) -> 'ModerationQueue':
        """Create report moderation entry."""
        return cls(
            id=f"mod_report_{content_type}_{content_id}_{int(datetime.utcnow().timestamp())}",
            content_type=content_type,
            content_id=content_id,
            user_id=reported_by,
            reason=reason,
            priority=priority,
            reported_by=reported_by
        )
