"""
Dapr Service Invocation Client
Elite Implementation Standard v2.0.0

Handles service-to-service calls with circuit breaker and retry policies.
Implements security context propagation (X-Student-ID).
"""

import asyncio
import time
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass

try:
    from dapr.clients import DaprClient
    from dapr.clients.grpc._request_util import DaprRequest
    HAS_DAPR = True
except ImportError:
    HAS_DAPR = False
    print("Dapr SDK not available - using mock client for development")

from models.errors import RoutingError, CircuitBreakerOpenError


@dataclass
class DaprResponse:
    """Unified Dapr response format"""
    success: bool
    data: Optional[Dict]
    target_agent: str
    latency_ms: float
    retry_count: int
    circuit_breaker_status: str


class CircuitBreaker:
    """Simple circuit breaker implementation"""

    def __init__(self, max_failures: int = 5, timeout_seconds: int = 30):
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        """Record a failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.max_failures:
            self.state = "OPEN"
            print(f"CIRCUIT BREAKER OPENED: {self.failure_count} failures")

    def record_success(self):
        """Record a successful request"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)

    def can_attempt(self) -> bool:
        """Check if we can attempt a request"""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "HALF_OPEN"
                print("CIRCUIT BREAKER: Half-open state")
                return True
            return False

        if self.state == "HALF_OPEN":
            return True

        return False

    def get_status(self) -> Dict:
        """Get current circuit breaker status"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "timeout_seconds": self.timeout_seconds,
            "can_attempt": self.can_attempt()
        }


class DaprResilientClient:
    """
    Dapr client with resilience patterns:
    - Circuit breaker (5 failures → 30s open)
    - Retry policy (3 attempts, exponential backoff)
    - Security context propagation (X-Student-ID)
    """

    def __init__(self, app_id: str = "triage-service"):
        self.app_id = app_id
        self.circuit_breakers = {}  # One per target agent
        self.max_retries = 3
        self.base_timeout = 2  # 2 seconds

        if HAS_DAPR:
            self.client = DaprClient()
        else:
            self.client = None  # Mock mode for development

    def _get_circuit_breaker(self, target_agent: str) -> CircuitBreaker:
        """Get or create circuit breaker for target agent"""
        if target_agent not in self.circuit_breakers:
            self.circuit_breakers[target_agent] = CircuitBreaker(max_failures=5, timeout_seconds=30)
        return self.circuit_breakers[target_agent]

    async def invoke_service(
        self,
        target_app_id: str,
        method: str,
        data: Dict,
        student_id: str,
        request_id: str,
        timeout: float = 2.0,
        max_retries: int = 3
    ) -> DaprResponse:
        """
        Invoke target service with resilience patterns

        Args:
            target_app_id: Dapr application ID (e.g., "debug-agent")
            method: Service method to call
            data: Request payload
            student_id: Student ID for security propagation
            request_id: Request ID for tracing
            timeout: Timeout in seconds
            max_retries: Maximum retry attempts
        """
        circuit_breaker = self._get_circuit_breaker(target_app_id)

        # Check circuit breaker
        if not circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError(
                target_agent=target_app_id,
                timeout_seconds=circuit_breaker.timeout_seconds
            )

        start_time = time.time()
        retry_count = 0

        # Security context headers
        metadata = {
            "X-Student-ID": student_id,
            "X-Request-ID": request_id,
            "X-Source": "triage-service",
            "X-Timestamp": str(int(time.time()))
        }

        # Exponential backoff for retries
        backoff_base = 0.1  # 100ms

        for attempt in range(max_retries + 1):
            try:
                if HAS_DAPR:
                    # Real Dapr invocation
                    response = self.client.invoke_method(
                        target_app_id=target_app_id,
                        method_name=method,
                        data=json.dumps(data).encode('utf-8'),
                        metadata=metadata,
                        timeout=timeout
                    )

                    result_data = json.loads(response.data.decode('utf-8'))

                    # Record success
                    circuit_breaker.record_success()

                    return DaprResponse(
                        success=True,
                        data=result_data,
                        target_agent=target_app_id,
                        latency_ms=(time.time() - start_time) * 1000,
                        retry_count=retry_count,
                        circuit_breaker_status=circuit_breaker.state
                    )

                else:
                    # Mock mode for development/testing
                    await asyncio.sleep(0.05)  # Simulate network delay

                    # Simulate random failures for testing circuit breaker
                    import random
                    if random.random() < 0.1:  # 10% failure rate
                        raise Exception("Mock service failure")

                    mock_response = {
                        "status": "success",
                        "target_agent": target_app_id,
                        "intent_processed": data.get("intent", "unknown"),
                        "student_context": student_id,
                        "timestamp": time.time()
                    }

                    circuit_breaker.record_success()

                    return DaprResponse(
                        success=True,
                        data=mock_response,
                        target_agent=target_app_id,
                        latency_ms=(time.time() - start_time) * 1000,
                        retry_count=retry_count,
                        circuit_breaker_status=circuit_breaker.state
                    )

            except Exception as e:
                retry_count += 1

                if attempt < max_retries:
                    # Calculate backoff delay
                    backoff_delay = backoff_base * (2 ** attempt)  # Exponential
                    print(f"Attempt {attempt + 1} failed for {target_app_id}: {e}")
                    print(f"Retrying in {backoff_delay}s...")

                    await asyncio.sleep(backoff_delay)
                    continue
                else:
                    # All retries exhausted
                    circuit_breaker.record_failure()

                    raise RoutingError(
                        message=f"All {max_retries + 1} attempts failed for {target_app_id}",
                        target_agent=target_app_id,
                        details={
                            "last_error": str(e),
                            "circuit_breaker_status": circuit_breaker.get_status(),
                            "student_id": student_id,
                            "request_id": request_id
                        }
                    )

        # Should never reach here
        raise RoutingError(
            message="Unexpected routing failure",
            target_agent=target_app_id
        )

    def get_circuit_breaker_status(self, target_agent: str) -> Dict:
        """Get current circuit breaker status for a target agent"""
        cb = self._get_circuit_breaker(target_agent)
        return cb.get_status()

    def get_all_circuit_breaker_status(self) -> Dict:
        """Get status of all circuit breakers"""
        return {
            agent: cb.get_status()
            for agent, cb in self.circuit_breakers.items()
        }


# Factory for easy integration
def create_dapr_client(app_id: str = "triage-service") -> DaprResilientClient:
    """Factory function to create Dapr client"""
    return DaprResilientClient(app_id=app_id)


if __name__ == "__main__":
    import asyncio

    async def test_dapr_client():
        print("=== Dapr Resilient Client Test ===")

        client = create_dapr_client()

        # Test basic invocation
        try:
            result = await client.invoke_service(
                target_app_id="debug-agent",
                method="process",
                data={"intent": "syntax_help", "query": "Test query"},
                student_id="student_123456",
                request_id="req_001"
            )

            print(f"✅ Success: {result.data}")
            print(f"   Target: {result.target_agent}")
            print(f"   Latency: {result.latency_ms:.2f}ms")
            print(f"   Retries: {result.retry_count}")
            print(f"   Circuit: {result.circuit_breaker_status}")

        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test circuit breaker with multiple failures
        print(f"\n=== Circuit Breaker Test ===")

        # Note: In mock mode, this will demonstrate the circuit breaker pattern
        for i in range(8):  # 8 attempts
            try:
                result = await client.invoke_service(
                    target_app_id="concepts-agent",
                    method="process",
                    data={"intent": "concept_explanation"},
                    student_id="student_789",
                    request_id=f"req_{i:03d}"
                )
                print(f"Attempt {i+1}: Success")
            except Exception as e:
                print(f"Attempt {i+1}: {e}")

            # Show circuit breaker status
            status = client.get_circuit_breaker_status("concepts-agent")
            print(f"  Circuit Status: {status}")

        print(f"\n=== Resilience Features ===")
        print(f"✅ Circuit Breaker: 5 failures → 30s open")
        print(f"✅ Retry Policy: 3 attempts, exponential backoff")
        print(f"✅ Security Context: X-Student-ID propagation")
        print(f"✅ Dapr Ready: Service invocation + metadata")

    asyncio.run(test_dapr_client())