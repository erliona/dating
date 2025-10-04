"""Telegram notification service implementation."""

from typing import Dict, Any
import logging

from aiogram import Bot

from core.interfaces import INotificationService

logger = logging.getLogger(__name__)


class TelegramNotificationService(INotificationService):
    """Telegram implementation of notification service.
    
    Sends notifications to users via Telegram bot messages.
    """
    
    def __init__(self, bot: Bot, tg_id_mapping: Dict[int, int]):
        """Initialize with Telegram bot instance.
        
        Args:
            bot: Aiogram Bot instance
            tg_id_mapping: Mapping from internal user_id to Telegram user_id
        """
        self.bot = bot
        self.tg_id_mapping = tg_id_mapping
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """Send notification to user via Telegram.
        
        Args:
            user_id: Internal user ID
            notification_type: Type of notification (new_match, new_message, etc.)
            data: Notification payload
            
        Returns:
            True if notification was sent successfully
        """
        # Get Telegram user ID
        tg_id = self.tg_id_mapping.get(user_id)
        if not tg_id:
            logger.warning(f"No Telegram ID found for user {user_id}")
            return False
        
        try:
            message = self._format_message(notification_type, data)
            await self.bot.send_message(chat_id=tg_id, text=message)
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
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
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.send_notification(
                user_id, notification_type, data
            )
        return results
    
    def _format_message(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Format notification message based on type."""
        messages = {
            'new_match': f"🎉 Новый матч! {data.get('name', 'Кто-то')} тоже лайкнул вас!",
            'new_message': f"💬 Новое сообщение от {data.get('name', 'пользователя')}",
            'new_like': f"❤️ {data.get('name', 'Кто-то')} лайкнул вас!",
            'super_like': f"⭐ {data.get('name', 'Кто-то')} поставил вам суперлайк!",
        }
        
        return messages.get(notification_type, f"Уведомление: {notification_type}")
