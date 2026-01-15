"""
Circuit Breaker Pattern Implementation
======================================

Implements circuit breaker pattern for external dependencies with automatic
fallback mechanisms and health monitoring.

Based on the pattern described by Michael Nygard in "Release It!"
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field

from src.main import circuit_breaker_state

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, requests rejected immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds to wait before trying again
    half_open_max_calls: int = 3  # Max calls in half-open state
    expected_exception: Exception = Exception  # Exception type to catch


@dataclass
class CircuitStats:
    """Circuit breaker statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation with Prometheus metrics integration

    Usage:
        async with CircuitBreaker("redis", config) as cb:
            result = await cb.call(lambda: await redis_client.ping())

    Or:
        breaker = CircuitBreaker("redis")
        result = await breaker.execute(redis_client.ping)
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.state_changed_at = datetime.utcnow()
        self.half_open_failures = 0
        self.half_open_successes = 0

        # Prometheus metrics for this circuit
        self.metrics = {
            "state": circuit_breaker_state.labels(service=name),
            "calls": None,  # Will be created in execute
        }

    async def execute(self, func: Callable, fallback: Optional[Callable] = None) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Async function to execute
            fallback: Optional fallback function if circuit is open

        Returns:
            Function result or fallback result

        Raises:
            CircuitOpenError: If circuit is open and no fallback provided
            Exception: If function fails and no fallback provided
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if datetime.utcnow() - self.state_changed_at > timedelta(seconds=self.config.recovery_timeout):
                logger.info(f"Circuit '{self.name}' attempting recovery", extra={
                    "circuit_state": self.state.value,
                    "service": self.name
                })
                self._transition_to_half_open()
            else:
                if fallback:
                    logger.warning(f"Circuit '{self.name}' is OPEN, using fallback", extra={
                        "service": self.name
                    })
                    return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
                else:
                    raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        # Execute function
        self.stats.total_calls += 1

        try:
            result = await func() if asyncio.iscoroutine(func) else func()

            # Success
            self._record_success()
            return result

        except Exception as e:
            # Failure
            self._record_failure()

            if fallback:
                logger.warning(f"Circuit '{self.name}' function failed, using fallback: {e}", extra={
                    "service": self.name,
                    "error": str(e)
                })
                return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
            else:
                logger.error(f"Circuit '{self.name}' function failed: {e}", extra={
                    "service": self.name,
                    "error": str(e)
                })
                raise

    def _record_success(self):
        """Record successful call"""
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1

            # If we have enough successes in half-open, close the circuit
            if self.half_open_successes >= self.config.half_open_max_calls:
                logger.info(f"Circuit '{self.name}' recovered, closing circuit", extra={
                    "service": self.name,
                    "half_open_successes": self.half_open_successes
                })
                self._transition_to_closed()
                self.half_open_successes = 0
                self.half_open_failures = 0

    def _record_failure(self):
        """Record failed call"""
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_failures += 1

            # If we fail in half-open, go back to open
            logger.warning(f"Circuit '{self.name}' failed in half-open state", extra={
                "service": self.name,
                "half_open_failures": self.half_open_failures
            })
            self._transition_to_open()
            self.half_open_successes = 0
            self.half_open_failures = 0

        elif self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.stats.consecutive_failures >= self.config.failure_threshold:
                logger.error(f"Circuit '{self.name}' opening due to consecutive failures", extra={
                    "service": self.name,
                    "consecutive_failures": self.stats.consecutive_failures,
                    "threshold": self.config.failure_threshold
                })
                self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.state_changed_at = datetime.utcnow()
        self.stats.state_changes += 1
        self.metrics["state"].set(1)  # 1 = OPEN

        logger.critical(f"Circuit '{self.name}' state changed to OPEN", extra={
            "service": self.name,
            "state": "OPEN",
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful": self.stats.successful_calls,
                "failed": self.stats.failed_calls,
                "consecutive_failures": self.stats.consecutive_failures
            }
        })

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.state_changed_at = datetime.utcnow()
        self.stats.state_changes += 1
        self.metrics["state"].set(2)  # 2 = HALF_OPEN

        logger.info(f"Circuit '{self.name}' state changed to HALF_OPEN", extra={
            "service": self.name,
            "state": "half_open"
        })

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.state_changed_at = datetime.utcnow()
        self.stats.state_changes += 1
        self.metrics["state"].set(0)  # 0 = CLOSED

        logger.info(f"Circuit '{self.name}' state changed to CLOSED", extra={
            "service": self.name,
            "state": "closed"
        })

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "state_changed_at": self.state_changed_at.isoformat(),
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "last_failure": self.stats.last_failure.isoformat() if self.stats.last_failure else None,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
            },
            "half_open_progress": {
                "successes": self.half_open_successes,
                "failures": self.half_open_failures,
            } if self.state == CircuitState.HALF_OPEN else None
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers (for testing/debugging)"""
        for name, breaker in self._breakers.items():
            breaker._transition_to_closed()
            logger.warning(f"Reset circuit breaker '{name}' to CLOSED state")


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


# Convenience functions for common services
def get_redis_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Redis operations"""
    config = CircuitBreakerConfig(
        failure_threshold=3,  # Redis failures should be caught quickly
        recovery_timeout=30,  # 30 seconds recovery timeout
        half_open_max_calls=2
    )
    return circuit_breaker_manager.get_or_create("redis", config)


def get_kafka_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Kafka operations"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,  # Longer timeout for Kafka
        half_open_max_calls=3
    )
    return circuit_breaker_manager.get_or_create("kafka", config)


def get_dapr_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Dapr operations"""
    config = CircuitBreakerConfig(
        failure_threshold=4,
        recovery_timeout=45,
        half_open_max_calls=2
    )
    return circuit_breaker_manager.get_or_create("dapr", config)


# Service-specific circuit breaker usage examples
async def safe_redis_operation(operation: Callable, fallback: Optional[Callable] = None):
    """Execute Redis operation with circuit breaker"""
    breaker = get_redis_circuit_breaker()
    return await breaker.execute(operation, fallback)


async def safe_kafka_operation(operation: Callable, fallback: Optional[Callable] = None):
    """Execute Kafka operation with circuit breaker"""
    breaker = get_kafka_circuit_breaker()
    return await breaker.execute(operation, fallback)


async def safe_dapr_operation(operation: Callable, fallback: Optional[Callable] = None):
    """Execute Dapr operation with circuit breaker"""
    breaker = get_dapr_circuit_breaker()
    return await breaker.execute(operation, fallback)