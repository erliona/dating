"""Example handler demonstrating WebApp authentication with Epic A2.

DEPRECATED: This example shows the OLD architecture where bot had command handlers.

After refactoring, the bot only receives notifications from the notification service.
All user interactions happen in the WebApp which communicates directly with API Gateway.
The bot no longer has /start command or WebApp buttons.

This file is kept for reference only.
"""

import logging
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from bot.config import load_config
from bot.security import ValidationError, validate_jwt_token

logger = logging.getLogger(__name__)
router = Router()

# In-memory storage for user sessions (in production, use database)
user_sessions: dict[int, dict[str, Any]] = {}


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Send welcome message with WebApp button."""
    config = load_config()

    if not config.webapp_url:
        await message.answer(
            "⚠️ WebApp is not configured. " "Please set WEBAPP_URL environment variable."
        )
        return

    # Create keyboard with WebApp button
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Открыть Mini App",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "👋 Добро пожаловать в Dating Mini App!\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение и создать свою анкету.",
        reply_markup=keyboard,
    )


if __name__ == "__main__":
    import asyncio

    async def main():
        logging.basicConfig(level=logging.INFO)
        config = load_config()
        bot = Bot(token=config.token)
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)
        await dp.start_polling(bot)

    asyncio.run(main())
