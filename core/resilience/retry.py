"""Retry logic with exponential backoff."""
import logging
from typing import Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from aiohttp import ClientError, ServerTimeoutError

logger = logging.getLogger(__name__)


def retry_on_service_error(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10
):
    """Decorator for retrying service calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((ClientError, ServerTimeoutError, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


# Specific retry decorators for different scenarios
def retry_data_service():
    """Retry decorator for Data Service calls."""
    return retry_on_service_error(max_attempts=3, min_wait=1, max_wait=5)


def retry_notification():
    """Retry decorator for notification calls (more lenient)."""
    return retry_on_service_error(max_attempts=5, min_wait=2, max_wait=30)
