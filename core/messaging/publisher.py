"""Event publisher for RabbitMQ."""
import logging
import json
from typing import Dict, Any
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to RabbitMQ."""
    
    def __init__(self, rabbitmq_url: str):
        """Initialize publisher.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.exchange = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Create events exchange (topic exchange for routing)
            self.exchange = await self.channel.declare_exchange(
                "dating.events",
                ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}", exc_info=True)
            raise
    
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: str = None
    ) -> bool:
        """Publish event to exchange.
        
        Args:
            event_type: Event routing key (e.g., "match.created")
            data: Event payload
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            True if published successfully
        """
        if not self.exchange:
            logger.error("Publisher not connected to RabbitMQ")
            return False
        
        try:
            # Prepare message
            message_body = json.dumps(data).encode()
            headers = {}
            if correlation_id:
                headers["correlation_id"] = correlation_id
            
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                headers=headers,
                content_type="application/json"
            )
            
            # Publish to exchange with routing key
            await self.exchange.publish(
                message,
                routing_key=event_type
            )
            
            logger.info(
                f"Published event: {event_type}",
                extra={
                    "event_type": event_type,
                    "correlation_id": correlation_id,
                    "data": data
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish event {event_type}: {e}",
                exc_info=True
            )
            return False
    
    async def close(self):
        """Close connection."""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
