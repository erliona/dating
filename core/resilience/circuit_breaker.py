"""Circuit breaker implementation for service-to-service calls."""
import logging
from typing import Callable, Any, Optional
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiohttp import ClientError, ClientTimeout
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Circuit breaker metrics
CIRCUIT_BREAKER_CALLS = Counter(
    'circuit_breaker_calls_total',
    'Total circuit breaker calls',
    ['service', 'target', 'state', 'result']
)

CIRCUIT_BREAKER_STATE = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service', 'target']
)


class ServiceCircuitBreaker:
    """Circuit breaker wrapper for microservice calls."""
    
    def __init__(
        self,
        service_name: str,
        fail_max: int = 5,
        timeout_duration: int = 60,
        expected_exception: type = ClientError
    ):
        """Initialize circuit breaker for a service.
        
        Args:
            service_name: Name of the service (for logging)
            fail_max: Maximum failures before opening circuit
            timeout_duration: Seconds to wait before half-open state
            expected_exception: Exception type to catch
        """
        self.service_name = service_name
        self.breaker = CircuitBreaker(
            fail_max=fail_max,
            timeout_duration=timeout_duration,
            name=service_name
        )
        
        # Register event listeners
        self.breaker.add_listeners(self._on_open, self._on_close, self._on_half_open)
    
    def _on_open(self, breaker):
        """Called when circuit opens."""
        logger.error(
            f"Circuit breaker OPENED for {self.service_name}",
            extra={"event_type": "circuit_opened", "service": self.service_name}
        )
    
    def _on_close(self, breaker):
        """Called when circuit closes."""
        logger.info(
            f"Circuit breaker CLOSED for {self.service_name}",
            extra={"event_type": "circuit_closed", "service": self.service_name}
        )
    
    def _on_half_open(self, breaker):
        """Called when circuit enters half-open state."""
        logger.warning(
            f"Circuit breaker HALF-OPEN for {self.service_name}",
            extra={"event_type": "circuit_half_open", "service": self.service_name}
        )
    
    async def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            fallback: Optional fallback function if circuit is open
            *args, **kwargs: Arguments to pass to func
            
        Returns:
            Result from func or fallback
            
        Raises:
            CircuitBreakerError: If circuit is open and no fallback provided
        """
        # Get current state for metrics
        current_state = self.breaker.current_state
        state_name = current_state.name.lower()
        
        try:
            result = await self.breaker.call(func, *args, **kwargs)
            
            # Record successful call
            CIRCUIT_BREAKER_CALLS.labels(
                service=self.service_name,
                target=self.service_name,
                state=state_name,
                result='success'
            ).inc()
            
            return result
            
        except Exception as e:
            # Record failed call
            CIRCUIT_BREAKER_CALLS.labels(
                service=self.service_name,
                target=self.service_name,
                state=state_name,
                result='failure'
            ).inc()
            
            # Check if it's a circuit breaker error or the expected exception
            if isinstance(e, CircuitBreakerError) or isinstance(e, self.expected_exception):
                logger.warning(
                    f"Circuit open for {self.service_name}, using fallback",
                    extra={"event_type": "circuit_fallback", "service": self.service_name}
                )
                if fallback:
                    return await fallback(*args, **kwargs)
                raise
            else:
                # Re-raise unexpected exceptions
                raise
        finally:
            # Update state metric
            CIRCUIT_BREAKER_STATE.labels(
                service=self.service_name,
                target=self.service_name
            ).set(current_state.value)


# Global circuit breakers for each service
data_service_breaker = ServiceCircuitBreaker("data-service", fail_max=5, timeout_duration=60)
bot_service_breaker = ServiceCircuitBreaker("telegram-bot", fail_max=3, timeout_duration=30)
