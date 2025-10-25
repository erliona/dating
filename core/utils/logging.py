from __future__ import annotations

"""Shared structured JSON logging configuration for all services."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
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
        for field in [
            "user_id",
            "event_type",
            "service_name",
            "request_id",
            "correlation_id",
            "trace_id",
            "span_id",
            "parent_span_id",
            "duration_ms",
            "status_code",
            "method",
            "path",
            "remote_addr",
            "user_agent",
            "error_type",
            "error_message",
        ]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        return json.dumps(log_data)


def configure_logging(service_name: str, log_level: str = "INFO") -> None:
    """Configure JSON logging for a service.

    Args:
        service_name: Name of the service (e.g., "auth-service", "profile-service")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Add service name to all logs from this logger
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    # Configure noisy library loggers
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    # Log initialization
    logger = logging.getLogger(service_name)
    logger.info(
        f"{service_name} logging initialized",
        extra={"event_type": "logging_initialized"},
    )
