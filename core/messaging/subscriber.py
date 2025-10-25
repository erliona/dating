from __future__ import annotations

"""Event subscriber for RabbitMQ."""
import json
import logging
from collections.abc import Callable

import aio_pika
from aio_pika import ExchangeType, IncomingMessage

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Subscribes to events from RabbitMQ."""

    def __init__(self, rabbitmq_url: str, service_name: str):
        """Initialize subscriber.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            service_name: Name of the service (for queue naming)
        """
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self.handlers: dict[str, Callable] = {}

    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "dating.events", ExchangeType.TOPIC, durable=True
            )

            # Create service-specific queue
            queue_name = f"{self.service_name}.events"
            self.queue = await self.channel.declare_queue(queue_name, durable=True)

            logger.info(f"Connected to RabbitMQ, queue: {queue_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise

    def register_handler(self, event_pattern: str, handler: Callable):
        """Register handler for event pattern.

        Args:
            event_pattern: Routing key pattern (e.g., "match.*", "message.sent")
            handler: Async function to handle event
        """
        self.handlers[event_pattern] = handler
        logger.info(f"Registered handler for pattern: {event_pattern}")

    async def start_consuming(self):
        """Start consuming events from queue."""
        if not self.queue:
            logger.error("Subscriber not connected")
            return

        # Bind queue to patterns
        for pattern in self.handlers.keys():
            await self.queue.bind(self.exchange, routing_key=pattern)
            logger.info(f"Bound queue to pattern: {pattern}")

        # Start consuming
        await self.queue.consume(self._process_message)
        logger.info("Started consuming events")

    async def _process_message(self, message: IncomingMessage):
        """Process incoming message."""
        async with message.process():
            try:
                # Parse message
                data = json.loads(message.body.decode())
                routing_key = message.routing_key
                correlation_id = message.headers.get("correlation_id")

                logger.info(
                    f"Received event: {routing_key}",
                    extra={"event_type": routing_key, "correlation_id": correlation_id},
                )

                # Find and call handler
                handler = self._find_handler(routing_key)
                if handler:
                    await handler(data, correlation_id=correlation_id)
                else:
                    logger.warning(f"No handler for event: {routing_key}")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Message will be requeued by aio_pika

    def _find_handler(self, routing_key: str) -> Callable | None:
        """Find handler matching routing key."""
        # Exact match first
        if routing_key in self.handlers:
            return self.handlers[routing_key]

        # Pattern match (e.g., "match.*" matches "match.created")
        for pattern, handler in self.handlers.items():
            if self._matches_pattern(routing_key, pattern):
                return handler

        return None

    def _matches_pattern(self, routing_key: str, pattern: str) -> bool:
        """Check if routing key matches pattern."""
        pattern_parts = pattern.split(".")
        key_parts = routing_key.split(".")

        if len(pattern_parts) != len(key_parts):
            return False

        for p, k in zip(pattern_parts, key_parts, strict=False):
            if p != "*" and p != k:
                return False

        return True

    async def close(self):
        """Close connection."""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
