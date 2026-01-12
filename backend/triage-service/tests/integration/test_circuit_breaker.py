"""
Integration Tests: Circuit Breaker Pattern
Elite Implementation Standard v2.0.0

Tests circuit breaker behavior across service boundaries.
"""

import sys
import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.dapr_client import DaprClient, CircuitBreakerConfig
from models.errors import TriageError


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with service calls"""

    def setup_method(self):
        """Setup test fixtures"""
        self.dapr_client = DaprClient()

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit opens after configured failures"""
        agent_name = "test-agent"
        config = CircuitBreakerConfig(max_failures=3, timeout_seconds=1)

        # Create isolated circuit breaker for testing
        cb = self.dapr_client._get_or_create_circuit_breaker(agent_name, config)

        # Record failures up to threshold
        for i in range(3):
            cb.record_failure()
            if i < 2:
                assert cb.state == "CLOSED"
                assert cb.can_attempt() is True

        # After 3 failures, should be OPEN
        assert cb.state == "OPEN"
        assert cb.can_attempt() is False

    def test_circuit_breaker_timeout_transition(self):
        """Test OPEN → HALF_OPEN → CLOSED transitions"""
        agent_name = "test-agent-timeout"
        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=0.5)

        cb = self.dapr_client._get_or_create_circuit_breaker(agent_name, config)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(0.6)

        # Should transition to HALF_OPEN
        assert cb.can_attempt() is True
        assert cb.state == "HALF_OPEN"

        # Success should close it
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_circuit_breaker_half_open_failure_reopens(self):
        """Test HALF_OPEN failure immediately reopens circuit"""
        agent_name = "test-agent-halfopen"
        config = CircuitBreakerConfig(max_failures=2, timeout_seconds=0.3)

        cb = self.dapr_client._get_or_create_circuit_breaker(agent_name, config)

        # Open and timeout
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.35)

        # Half-open attempt fails
        cb.record_failure()

        # Should immediately reopen
        assert cb.state == "OPEN"
        assert cb.failure_count == 1  # New failure sequence

    def test_circuit_breaker_status_reporting(self):
        """Test circuit breaker status API"""
        agent_name = "test-agent-status"

        status = self.dapr_client.get_circuit_breaker_status(agent_name)

        assert "can_attempt" in status
        assert "state" in status
        assert "failure_count" in status
        assert "config" in status

    def test_multiple_agents_circuit_breakers(self):
        """Test independent circuit breakers per agent"""
        agents = ["debug-agent", "concepts-agent", "exercise-agent"]

        # Open one circuit
        cb_debug = self.dapr_client._get_or_create_circuit_breaker("debug-agent")
        cb_debug.record_failure()
        cb_debug.record_failure()
        cb_debug.record_failure()

        # Check all agents status
        all_status = self.dapr_client.get_all_circuit_breaker_status()

        # debug-agent should be OPEN
        assert all_status["debug-agent"]["state"] == "OPEN"
        assert all_status["debug-agent"]["can_attempt"] is False

        # Others should still be CLOSED (if not affected)
        if "concepts-agent" in all_status:
            assert all_status["concepts-agent"]["state"] == "CLOSED"


class TestDaprServiceInvocationWithCircuitBreaker:
    """Test Dapr service invocation with circuit breaker protection"""

    @pytest.mark.asyncio
    async def test_successful_invocation_with_metrics(self):
        """Test successful Dapr call updates circuit breaker"""
        client = DaprClient()

        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {"result": "success", "answer": "test"}

            result = await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

            assert result["result"] == "success"

            # Circuit should remain closed
            cb = client.circuit_breakers["debug-agent"]
            assert cb.state == "CLOSED"
            assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_increments_counter(self):
        """Test failed invocation increments failure counter"""
        client = DaprClient()

        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Service error")

            # Should raise but increment counter
            with pytest.raises(Exception):
                await client.invoke_agent(
                    "debug-agent",
                    {"query": "test"},
                    "student-12345"
                )

            cb = client.circuit_breakers["debug-agent"]
            assert cb.failure_count == 1
            assert cb.state == "CLOSED"  # Not yet open

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_invocation(self):
        """Test circuit breaker prevents calls when open"""
        client = DaprClient()

        # Manually open the circuit
        cb = client._get_or_create_circuit_breaker("debug-agent")
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "OPEN"

        # Should not attempt invoke, should raise immediately
        with pytest.raises(TriageError) as exc_info:
            await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

        assert "circuit breaker" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry policy with exponential backoff"""
        client = DaprClient()

        call_times = []

        async def mock_invoke_with_timing(*args, **kwargs):
            call_times.append(time.time())
            if len(call_times) == 1:
                raise Exception("First failure")
            return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=mock_invoke_with_timing):
            start_time = time.time()
            result = await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )

            assert result["result"] == "success"
            assert len(call_times) == 2  # First failure, then success

            # Check timing (approximate exponential backoff)
            if len(call_times) >= 2:
                delay = call_times[1] - call_times[0]
                # Should be around 100ms base delay
                assert 0.08 < delay < 0.2  # Allow some variance


class TestEndToEndResilienceScenario:
    """Test complete resilience scenario"""

    @pytest.mark.asyncio
    async def test_degraded_service_recovery(self):
        """Test service degradation and recovery"""
        client = DaprClient()

        # Step 1: Service is working
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {"result": "success"}
            result = await client.invoke_agent("test-agent", {}, "student-12345")
            assert result["result"] == "success"

        # Step 2: Service starts failing (5 failures opens circuit)
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Service down")

            for _ in range(5):
                try:
                    await client.invoke_agent("test-agent", {}, "student-12345")
                except:
                    pass

        # Step 3: Circuit should be open
        cb = client.circuit_breakers["test-agent"]
        assert cb.state == "OPEN"

        # Step 4: Service recovers (wait for timeout)
        time.sleep(1.1)  # Wait for timeout

        # Step 5: Circuit breaker allows one test call
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {"result": "recovered"}
            result = await client.invoke_agent("test-agent", {}, "student-12345")
            assert result["result"] == "recovered"

        # Step 6: Circuit should be closed again
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0


class TestPerformanceUnderLoad:
    """Test circuit breaker performance under load"""

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_operations(self):
        """Test circuit breaker handles concurrent operations"""
        client = DaprClient()
        agent_name = "concurrent-agent"

        # Create multiple concurrent operations
        async def attempt_invoke(success):
            if success:
                with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
                    mock.return_value = {"result": "success"}
                    return await client.invoke_agent(agent_name, {}, "student-12345")
            else:
                with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
                    mock.side_effect = Exception("fail")
                    try:
                        await client.invoke_agent(agent_name, {}, "student-12345")
                    except:
                        return "failed"

        # Run concurrent successes and failures
        tasks = []
        for i in range(10):
            tasks.append(attempt_invoke(i % 2 == 0))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Circuit breaker should handle this gracefully
        cb = client._get_or_create_circuit_breaker(agent_name)
        # State might be any due to concurrency, but should not crash
        assert cb.state in ["CLOSED", "OPEN", "HALF_OPEN"]

    def test_circuit_breaker_overhead(self):
        """Test circuit breaker adds minimal overhead"""
        client = DaprClient()

        start = time.time()
        for _ in range(1000):
            client.get_circuit_breaker_status("test-agent")
        duration = time.time() - start

        # Should handle 1000 status checks in <100ms
        assert duration < 0.1


class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration validation"""

    def test_config_validation(self):
        """Test configuration parameters are validated"""
        from services.dapr_client import CircuitBreakerConfig

        # Valid config
        config = CircuitBreakerConfig(
            max_failures=5,
            timeout_seconds=30,
            retry_attempts=3,
            retry_backoff=[100, 200, 400]
        )

        assert config.max_failures == 5
        assert config.timeout_seconds == 30

        # Test invalid configs
        with pytest.raises(Exception):
            CircuitBreakerConfig(max_failures=0)

        with pytest.raises(Exception):
            CircuitBreakerConfig(timeout_seconds=-1)

    def test_default_config_matches_spec(self):
        """Test default config matches architecture spec"""
        config = CircuitBreakerConfig()

        # Spec requirements
        assert config.max_failures == 5
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_backoff == [100, 200, 400]


if __name__ == "__main__":
    print("=== Running Integration Tests: Circuit Breaker ===")
    pytest.main([__file__, "-v"])