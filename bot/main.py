"""Minimal bot entry point - infrastructure only."""

import asyncio
import json
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import load_config


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


# Configure JSON logging for structured logs
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

LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Bootstrap the bot."""
    LOGGER.info("Bot initialization started", extra={"event_type": "startup"})
    
    try:
        config = load_config()
        LOGGER.info(
            "Configuration loaded successfully",
            extra={
                "event_type": "config_loaded",
                "webapp_url": config.webapp_url,
                "database_configured": bool(config.database_url),
            }
        )
    except Exception as exc:
        LOGGER.error(
            f"Failed to load configuration: {exc}",
            exc_info=True,
            extra={"event_type": "config_error"}
        )
        raise
    
    try:
        bot = Bot(token=config.token)
        LOGGER.info("Bot instance created", extra={"event_type": "bot_created"})
        
        dp = Dispatcher(storage=MemoryStorage())
        LOGGER.info(
            "Dispatcher initialized with MemoryStorage",
            extra={"event_type": "dispatcher_initialized"}
        )
        
        LOGGER.info("Starting polling", extra={"event_type": "polling_start"})
        await dp.start_polling(bot)
    except Exception as exc:
        LOGGER.error(
            f"Error during bot execution: {exc}",
            exc_info=True,
            extra={"event_type": "bot_error"}
        )
        raise
    finally:
        LOGGER.info("Shutting down bot", extra={"event_type": "shutdown"})


if __name__ == "__main__":
    asyncio.run(main())
