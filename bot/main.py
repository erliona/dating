"""Minimal bot entry point - infrastructure only."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Bootstrap the bot."""
    config = load_config()
    LOGGER.info("Configuration loaded successfully")
    
    bot = Bot(token=config.token)
    dp = Dispatcher(storage=MemoryStorage())
    
    LOGGER.info("Starting polling")
    try:
        await dp.start_polling(bot)
    finally:
        LOGGER.info("Shutting down bot")


if __name__ == "__main__":
    asyncio.run(main())
