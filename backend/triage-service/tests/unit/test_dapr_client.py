"""
Unit Tests: Dapr Client & Circuit Breaker
Elite Implementation Standard v2.0.0

Tests Dapr integration, circuit breaker pattern, and resilience features.
"""

import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.dapr_client import (
    DaprClient,
    CircuitBreaker,
    CircuitBreakerConfig,
    RetryPolicy
)
from models.errors import TriageError


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig validation"""

    def test_config_creation(self):
        """Test circuit breaker config creation"""
        config = CircuitBreakerConfig(
            max_failures=5,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff=[100, 200, 400]
        )

        assert config.max_failures == 5
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_backoff == [100, 200, 400]

    def test_config_defaults(self):
        """Test config with defaults"""
        config = CircuitBreakerConfig()

        assert config.max_failures == 5
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_backoff == [100, 200, 400]

    def test_config_validation(self):
        """Test config validation"""
        # Valid config
        config = CircuitBreakerConfig(max_failures=3, timeout_seconds=60)
        assert config.max_failures == 3
        assert config.timeout_seconds == 60

        # Should validate that max_failures > 0
        with pytest.raises(Exception):
            CircuitBreakerConfig(max_failures=0)


class TestRetryPolicy:
    """Test RetryPolicy calculation"""

    def test_retry_policy_creation(self):
        """Test retry policy creation"""
        policy = RetryPolicy(
            max_attempts=3,
            base_delay_ms=100,
            max_delay_ms=400
        )

        assert policy.max_attempts == 3
        assert policy.base_delay_ms == 100
        assert policy.max_delay_ms == 400

    def test_delay_calculation(self):
        """Test exponential backoff delay calculation"""
        policy = RetryPolicy(
            max_attempts=3,
            base_delay_ms=100,
            max_delay_ms=400
        )

        # Test exponential backoff
        delay1 = policy.calculate_delay(1)  # 100ms
        delay2 = policy.calculate_delay(2)  # 200ms
        delay3 = policy.calculate_delay(3)  # 400ms (capped)

        assert delay1 == 100
        assert delay2 == 200
        assert delay3 == 400

    def test_delay_cap(self):
        """Test delay is capped at max_delay"""
        policy = RetryPolicy(
            max_attempts=5,
            base_delay_ms=100,
            max_delay_ms=200
        )

        # Attempt 1: 100ms
        assert policy.calculate_delay(1) == 100

        # Attempt 2: 200ms (2*100)
        assert policy.calculate_delay(2) == 200

        # Attempt 3: 200ms (capped, would be 400)
        assert policy.calculate_delay(3) == 200

        # Attempt 4: 200ms (still capped)
        assert policy.calculate_delay(4) == 200


class TestCircuitBreaker:
    """Test CircuitBreaker state management"""

    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation"""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker("debug-agent", config)

        assert cb.agent_name == "debug-agent"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.next_retry_time is None

    def test_circuit_breaker_closed_state(self):
        """Test CLOSED state behavior"""
        config = CircuitBreakerConfig(max_failures=3)
        cb = CircuitBreaker("test-agent", config)

        assert cb.can_attempt() is True

        # Record successful attempt
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_circuit_breaker_failure_counting(self):
        """Test failure counting triggers open state"""
        config = CircuitBreakerConfig(max_failures=3)
        cb = CircuitBreaker("test-agent", config)

        # Fail up to threshold
        for i in range(3):
            assert cb.state == "CLOSED"
            cb.record_failure()
            assert cb.failure_count == i + 1

        # Third failure should open circuit
        assert cb.state == "OPEN"
        assert cb.can_attempt() is False

    def test_circuit_breaker_timeout(self):
        """Test circuit breaker timeout transition"""
        import time

        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=1)
        cb = CircuitBreaker("test-agent", config)

        # Trigger open state
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(1.1)

        # Should transition to HALF_OPEN
        assert cb.can_attempt() is True
        assert cb.state == "HALF_OPEN"

    def test_circuit_breaker_half_open_recovery(self):
        """Test HALF_OPEN state recovery"""
        import time

        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=0.5)
        cb = CircuitBreaker("test-agent", config)

        # Open circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(0.6)

        # Attempt should work
        assert cb.can_attempt() is True
        assert cb.state == "HALF_OPEN"

        # Success should close circuit
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_circuit_breaker_half_open_failure(self):
        """Test HALF_OPEN state failure reopens circuit"""
        import time

        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=0.5)
        cb = CircuitBreaker("test-agent", config)

        # Open and timeout
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.6)

        # Half-open attempt fails
        cb.record_failure()
        assert cb.state == "OPEN"  # Immediately reopens
        assert cb.failure_count == 1  # Reset to 1 (new failure sequence)


class TestDaprClient:
    """Test Dapr client functionality"""

    def test_client_creation(self):
        """Test Dapr client creation"""
        client = DaprClient()
        assert client is not None
        assert isinstance(client.circuit_breakers, dict)

    def test_get_circuit_breaker_status(self):
        """Test getting circuit breaker status"""
        client = DaprClient()

        status = client.get_circuit_breaker_status("debug-agent")
        assert status is not None
        assert "can_attempt" in status
        assert "state" in status
        assert "failure_count" in status

    def test_get_all_circuit_breaker_status(self):
        """Test getting all circuit breaker statuses"""
        client = DaprClient()

        all_status = client.get_all_circuit_breaker_status()
        assert isinstance(all_status, dict)
        assert len(all_status) > 0

        # Check each agent has proper structure
        for agent, status in all_status.items():
            assert "can_attempt" in status
            assert "state" in status
            assert status["state"] in ["CLOSED", "OPEN", "HALF_OPEN"]

    @pytest.mark.asyncio
    async def test_invoke_agent_success(self):
        """Test successful agent invocation"""
        client = DaprClient()

        # Mock successful response
        mock_response = {"result": "success", "data": {"answer": "test"}}

        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response

            result = await client.invoke_agent(
                "debug-agent",
                {"query": "test query"},
                "student-12345"
            )

            assert result == mock_response
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_invoke_agent_with_retry(self):
        """Test agent invocation with retry logic"""
        client = DaprClient()

        # Mock responses: first fails, second succeeds
        responses = [
            Exception("Connection timeout"),
            {"result": "success", "data": {"answer": "retried"}}
        ]

        call_count = 0

        async def mock_invoke(*args, **kwargs):
            nonlocal call_count
            response = responses[call_count]
            call_count += 1
            if isinstance(response, Exception):
                raise response
            return response

        with patch.object(client, '_invoke_service', side_effect=mock_invoke):
            result = await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

            assert result["result"] == "success"
            assert call_count == 2  # One failure, one success

    @pytest.mark.asyncio
    async def test_invoke_agent_circuit_breaker_open(self):
        """Test invocation fails when circuit breaker is open"""
        client = DaprClient()

        # Open the circuit breaker
        cb = client.circuit_breakers["debug-agent"]
        for _ in range(cb.config.max_failures):
            cb.record_failure()
        assert cb.state == "OPEN"

        # Should fail immediately without attempting invoke
        with pytest.raises(TriageError) as exc_info:
            await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

        assert "circuit breaker" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invoke_agent_timeout(self):
        """Test timeout handling"""
        client = DaprClient()

        async def slow_invoke(*args, **kwargs):
            await asyncio.sleep(3)  # Longer than timeout
            return {"result": "slow"}

        with patch.object(client, '_invoke_service', side_effect=slow_invoke):
            with pytest.raises(asyncio.TimeoutError):
                await client.invoke_agent(
                    "debug-agent",
                    {"query": "test"},
                    "student-12345",
                    timeout=1.0
                )

    @pytest.mark.asyncio
    async def test_invoke_with_dapr_headers(self):
        """Test proper Dapr headers are included"""
        client = DaprClient()

        captured_headers = {}

        async def mock_invoke(app_id, method, data, metadata=None):
            captured_headers.update(metadata or {})
            return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=mock_invoke):
            await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

        # Check trace context headers
        assert "traceparent" in captured_headers
        assert "student_id" in captured_headers
        assert captured_headers["student_id"] == "student-12345"


class TestResiliencePatterns:
    """Test resilience patterns"""

    def test_retry_backoff_sequence(self):
        """Test retry backoff follows correct sequence"""
        policy = RetryPolicy(max_attempts=3, base_delay_ms=100, max_delay_ms=400)

        delays = []
        for attempt in range(1, 4):
            delays.append(policy.calculate_delay(attempt))

        # Exponential: 100, 200, 400
        assert delays == [100, 200, 400]

    def test_circuit_breaker_state_transitions(self):
        """Test complete state transition flow"""
        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=0.1)
        cb = CircuitBreaker("test", config)

        # Initial: CLOSED
        assert cb.state == "CLOSED"
        assert cb.can_attempt() is True

        # Failures: CLOSED -> OPEN
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_attempt() is False

        # Wait timeout: OPEN -> HALF_OPEN
        import time
        time.sleep(0.15)
        assert cb.can_attempt() is True
        assert cb.state == "HALF_OPEN"

        # Success: HALF_OPEN -> CLOSED
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_failure_reset_on_success(self):
        """Test failure count resets on success"""
        config = CircuitBreakerConfig(max_failures=5)
        cb = CircuitBreaker("test", config)

        # Record some failures
        for _ in range(3):
            cb.record_failure()

        assert cb.failure_count == 3

        # Record success
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"


class TestPerformance:
    """Test performance characteristics"""

    def test_circuit_breaker_speed(self):
        """Test circuit breaker operations are fast"""
        import time

        config = CircuitBreakerConfig()
        cb = CircuitBreaker("test", config)

        start = time.time()
        for _ in range(1000):
            cb.can_attempt()
            cb.record_success()
        duration = time.time() - start

        # Should handle 1000 operations in <100ms
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_dapr_client_overhead(self):
        """Test Dapr client overhead is minimal"""
        client = DaprClient()

        start = time.time()
        for _ in range(100):
            client.get_circuit_breaker_status("debug-agent")
        duration = time.time() - start

        # Should handle 100 status checks in <50ms
        assert duration < 0.05


if __name__ == "__main__":
    print("=== Running Unit Tests: Dapr Client ===")
    pytest.main([__file__, "-v"])