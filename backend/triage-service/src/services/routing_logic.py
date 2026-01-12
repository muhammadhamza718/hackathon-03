"""
Routing Logic with Retry and Exponential Backoff
Elite Implementation Standard v2.0.0

Handles retry logic with exponential backoff: 100ms → 200ms → 400ms
Implements the retry pattern for resilience.
"""

import asyncio
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 400
    backoff_factor: float = 2.0
    exponential: bool = True


class RetryManager:
    """
    Implements retry logic with exponential backoff

    Retry pattern: 100ms → 200ms → 400ms
    Total attempts: 3
    Total time: ~700ms worst case
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Dict:
        """
        Execute operation with retry logic and exponential backoff

        Args:
            operation: Async function to execute
            *args, **kwargs: Arguments to pass to operation

        Returns:
            Dict with operation result and retry metadata
        """
        last_exception = None
        total_time = 0

        for attempt in range(1, self.config.max_attempts + 1):
            start_time = time.time()

            try:
                # Attempt the operation
                result = await operation(*args, **kwargs)

                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time

                # Success! Return immediately
                return {
                    "success": True,
                    "data": result,
                    "attempts": attempt,
                    "total_time_ms": total_time,
                    "retry_policy": "exponential"
                }

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                total_time += execution_time
                last_exception = e

                # Log the failure
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed "
                    f"after {execution_time:.1f}ms: {str(e)}"
                )

                # If this was the last attempt, don't delay
                if attempt == self.config.max_attempts:
                    break

                # Calculate exponential backoff delay
                delay_ms = min(
                    self.config.base_delay_ms * (self.config.backoff_factor ** (attempt - 1)),
                    self.config.max_delay_ms
                )

                logger.info(f"Retrying in {delay_ms:.1f}ms...")
                await asyncio.sleep(delay_ms / 1000)

        # All attempts failed
        return {
            "success": False,
            "error": str(last_exception),
            "attempts": self.config.max_attempts,
            "total_time_ms": total_time,
            "retry_policy": "exponential"
        }

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt using exponential backoff"""
        if attempt == 1:
            return self.config.base_delay_ms

        delay = self.config.base_delay_ms * (self.config.backoff_factor ** (attempt - 2))
        return min(delay, self.config.max_delay_ms)


# Default retry manager instance
default_retry_manager = RetryManager()


async def execute_with_default_retry(operation: Callable, *args, **kwargs) -> Dict:
    """
    Convenience function using default retry configuration

    Pattern: 100ms → 200ms → 400ms (3 attempts total)
    """
    retry_manager = RetryManager()
    return await retry_manager.execute_with_retry(operation, *args, **kwargs)


if __name__ == "__main__":
    # Test retry logic
    import asyncio

    async def failing_operation(attempt_count: list):
        attempt_count[0] += 1
        if attempt_count[0] < 3:  # Fail first 2 attempts
            raise Exception(f"Simulated failure on attempt {attempt_count[0]}")
        return {"result": "success", "attempt": attempt_count[0]}

    async def test():
        print("=== Retry Logic Test ===")
        print("Expecting: 100ms delay after attempt 1, 200ms after attempt 2")

        attempt_count = [0]
        result = await execute_with_default_retry(failing_operation, attempt_count)

        print(f"Result: {result}")
        print(f"Success: {result['success']}")
        print(f"Attempts: {result['attempts']}")
        print(f"Total time: {result['total_time_ms']:.1f}ms")

    asyncio.run(test())