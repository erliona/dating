"""Notification service interface - platform agnostic."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class INotificationService(ABC):
    """Interface for sending notifications to users.
    
    Platform adapters (Telegram, mobile push, email, etc.) implement this interface.
    """
    
    @abstractmethod
    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send notification to user.
        
        Args:
            user_id: Internal user ID
            notification_type: Type of notification (new_match, new_message, etc.)
            data: Notification payload
            
        Returns:
            True if notification was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_batch_notifications(
        self,
        user_ids: list[int],
        notification_type: str,
        data: Dict[str, Any]
    ) -> Dict[int, bool]:
        """Send notifications to multiple users.
        
        Returns:
            Dictionary mapping user_id to success status
        """
        pass
