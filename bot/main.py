"""Minimal bot entry point - infrastructure only."""

import asyncio
import json
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from .config import load_config

# Create router for handlers
router = Router()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        
        return json.dumps(log_data)


def configure_logging():
    """Configure JSON logging for structured logs."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Configure aiogram loggers to reduce noise
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Send welcome message with WebApp button."""
    config = load_config()
    
    if not config.webapp_url:
        await message.answer(
            "⚠️ WebApp is not configured. "
            "Please set WEBAPP_URL environment variable."
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


async def main() -> None:
    """Bootstrap the bot."""
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Bot initialization started", extra={"event_type": "startup"})
    
    try:
        config = load_config()
        logger.info(
            "Configuration loaded successfully",
            extra={
                "event_type": "config_loaded",
                "webapp_url": config.webapp_url,
                "database_configured": bool(config.database_url),
            }
        )
    except Exception as exc:
        logger.error(
            f"Failed to load configuration: {exc}",
            exc_info=True,
            extra={"event_type": "config_error"}
        )
        raise
    
    try:
        bot = Bot(token=config.token)
        logger.info("Bot instance created", extra={"event_type": "bot_created"})
        
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)
        logger.info(
            "Dispatcher initialized with MemoryStorage",
            extra={"event_type": "dispatcher_initialized"}
        )
        
        logger.info("Starting polling", extra={"event_type": "polling_start"})
        await dp.start_polling(bot)
    except Exception as exc:
        logger.error(
            f"Error during bot execution: {exc}",
            exc_info=True,
            extra={"event_type": "bot_error"}
        )
        raise
    finally:
        logger.info("Shutting down bot", extra={"event_type": "shutdown"})


if __name__ == "__main__":
    asyncio.run(main())
