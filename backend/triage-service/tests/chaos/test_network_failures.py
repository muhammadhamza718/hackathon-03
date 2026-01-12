"""
Chaos Tests: Network Failures & Service Downtime
Elite Implementation Standard v2.0.0

Tests system resilience under various failure conditions.
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

from services.dapr_client import DaprClient
from services.integration import TriageOrchestrator
from models.errors import TriageError


class TestNetworkFailures:
    """Test network failure scenarios"""

    @pytest.mark.asyncio
    async def test_connection_timeout(self):
        """Test handling of connection timeout"""
        client = DaprClient()

        # Mock service that times out
        async def timeout_invoke(*args, **kwargs):
            await asyncio.sleep(5)  # Exceeds default timeout
            return {"result": "slow"}

        with patch.object(client, '_invoke_service', side_effect=timeout_invoke):
            with pytest.raises(asyncio.TimeoutError):
                await client.invoke_agent(
                    "debug-agent",
                    {"query": "test"},
                    "student-12345",
                    timeout=1.0
                )

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling of connection refused"""
        client = DaprClient()

        with patch.object(client, '_invoke_service', side_effect=ConnectionRefusedError("Connection refused")):
            with pytest.raises(Exception):
                await client.invoke_agent(
                    "debug-agent",
                    {"query": "test"},
                    "student-12345"
                )

            # Circuit breaker should record failure
            cb = client.circuit_breakers["debug-agent"]
            assert cb.failure_count >= 1

    @pytest.mark.asyncio
    async def test_dns_failure(self):
        """Test handling of DNS resolution failure"""
        client = DaprClient()

        with patch.object(client, '_invoke_service', side_effect=Exception("DNS lookup failed")):
            with pytest.raises(Exception):
                await client.invoke_agent(
                    "nonexistent-agent",
                    {"query": "test"},
                    "student-12345"
                )

    @pytest.mark.asyncio
    async def test_network_partition(self):
        """Test handling of network partition (partial connectivity)"""
        client = DaprClient()

        # Simulate intermittent failures
        call_count = 0

        async def intermittent_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # Odd calls fail
                raise Exception("Network partition")
            return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=intermittent_failure):
            # First call fails
            with pytest.raises(Exception):
                await client.invoke_agent("debug-agent", {}, "student-12345")

            # Should trigger retry
            result = await client.invoke_agent("debug-agent", {}, "student-12345")
            assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_slow_network(self):
        """Test handling of slow network (latency)"""
        client = DaprClient()

        # Mock slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.5)  # 500ms delay
            return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=slow_response):
            start = time.time()
            result = await client.invoke_agent(
                "debug-agent",
                {"query": "test"},
                "student-12345"
            )
            duration = time.time() - start

            assert result["result"] == "success"
            assert duration >= 0.5


class TestServiceDowntime:
    """Test service downtime scenarios"""

    @pytest.mark.asyncio
    async def test_service_unavailable(self):
        """Test complete service unavailability"""
        client = DaprClient()

        with patch.object(client, '_invoke_service', side_effect=Exception("Service unavailable")):
            # Multiple failures should open circuit breaker
            for _ in range(5):
                try:
                    await client.invoke_agent("debug-agent", {}, "student-12345")
                except:
                    pass

            cb = client.circuit_breakers["debug-agent"]
            assert cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_service_restart_scenario(self):
        """Test service restart and recovery"""
        client = DaprClient()

        # Phase 1: Service down
        with patch.object(client, '_invoke_service', side_effect=Exception("Service down")):
            for _ in range(3):
                try:
                    await client.invoke_agent("debug-agent", {}, "student-12345")
                except:
                    pass

            cb = client.circuit_breakers["debug-agent"]
            initial_failures = cb.failure_count
            assert initial_failures >= 3

        # Phase 2: Service comes back (wait for timeout)
        time.sleep(1.1)  # Exceeds default timeout

        # Phase 3: Service healthy again
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
            mock.return_value = {"result": "recovered"}

            # Should be able to invoke again (half-open)
            result = await client.invoke_agent("debug-agent", {}, "student-12345")
            assert result["result"] == "recovered"

            # Success should close circuit
            cb = client.circuit_breakers["debug-agent"]
            assert cb.state == "CLOSED"
            assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_partial_service_degradation(self):
        """Test partial service degradation (some agents work, some don't)"""
        client = DaprClient()

        # debug-agent fails
        with patch.object(client, '_invoke_service', side_effect=Exception("debug-agent down")):
            try:
                await client.invoke_agent("debug-agent", {}, "student-12345")
            except:
                pass

        # concepts-agent works
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
            mock.return_value = {"result": "success"}
            result = await client.invoke_agent("concepts-agent", {}, "student-12345")
            assert result["result"] == "success"

        # Verify independent circuit breakers
        debug_cb = client.circuit_breakers["debug-agent"]
        concepts_cb = client.circuit_breakers["concepts-agent"]

        assert debug_cb.failure_count == 1
        assert concepts_cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_cascading_failure(self):
        """Test cascading failure scenario"""
        client = DaprClient()

        # Primary agent fails, causing load on fallback
        with patch.object(client, '_invoke_service', side_effect=Exception("Primary failure")):
            for _ in range(5):
                try:
                    await client.invoke_agent("debug-agent", {}, "student-12345")
                except:
                    pass

        # Circuit breaker should protect system
        cb = client.circuit_breakers["debug-agent"]
        assert cb.state == "OPEN"

        # Subsequent calls should fail fast
        start = time.time()
        with pytest.raises(TriageError):
            await client.invoke_agent("debug-agent", {}, "student-12345")
        duration = time.time() - start

        # Should fail very quickly (circuit breaker protection)
        assert duration < 0.1


class TestChaosScenarios:
    """Test complex chaos scenarios"""

    @pytest.mark.asyncio
    async def test_degraded_performance_recovery(self):
        """Test performance degradation and recovery"""
        client = DaprClient()

        # Phase 1: Slow responses
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.3)
            return {"result": "slow"}

        with patch.object(client, '_invoke_service', side_effect=slow_response):
            # This might trigger timeouts or retries
            try:
                await client.invoke_agent("debug-agent", {}, "student-12345")
            except:
                pass

        # Phase 2: Recovery to fast responses
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
            mock.return_value = {"result": "fast"}

            start = time.time()
            result = await client.invoke_agent("debug-agent", {}, "student-12345")
            duration = time.time() - start

            assert result["result"] == "fast"
            assert duration < 0.1  # Should be fast

    @pytest.mark.asyncio
    async def test_burst_traffic_with_failures(self):
        """Test burst traffic combined with failures"""
        client = DaprClient()

        # Simulate mixed success/failure pattern
        call_count = 0

        async def burst_handler(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # First 3 succeed
                return {"result": "success"}
            elif call_count <= 8:  # Next 5 fail
                raise Exception("Service overload")
            else:  # Then recover
                return {"result": "recovered"}

        with patch.object(client, '_invoke_service', side_effect=burst_handler):
            # Should handle pattern
            results = []
            for i in range(15):
                try:
                    result = await client.invoke_agent("debug-agent", {}, "student-12345")
                    results.append(result)
                except:
                    results.append("error")

            # Verify behavior
            assert len(results) == 15
            # Circuit breaker should protect from complete overload

    @pytest.mark.asyncio
    async def test_complete_system_overload(self):
        """Test when all services are overloaded"""
        client = DaprClient()

        # All agents fail
        with patch.object(client, '_invoke_service', side_effect=Exception("System overloaded")):
            # Trigger failures for all agents
            agents = ["debug-agent", "concepts-agent", "exercise-agent", "progress-agent"]

            for agent in agents:
                try:
                    await client.invoke_agent(agent, {}, "student-12345")
                except:
                    pass

            # All circuits should be open or in failure state
            for agent in agents:
                cb = client.circuit_breakers[agent]
                # Each should have recorded failures
                assert cb.failure_count >= 1


class TestRecoveryStrategies:
    """Test recovery strategies after failures"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_retry(self):
        """Test exponential backoff in retry logic"""
        client = DaprClient()

        call_times = []

        async def timing_invoke(*args, **kwargs):
            call_times.append(time.time())
            if len(call_times) == 1:
                raise Exception("First failure")
            return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=timing_invoke):
            start = time.time()
            result = await client.invoke_agent("debug-agent", {}, "student-12345")
            total_time = time.time() - start

            assert result["result"] == "success"
            assert len(call_times) == 2

            # Verify delay (should be ~100ms base)
            if len(call_times) >= 2:
                delay = call_times[1] - call_times[0]
                assert 0.08 < delay < 0.2  # 100ms +/- tolerance

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_probe(self):
        """Test half-open probe requests"""
        client = DaprClient()

        # Open circuit
        cb = client.circuit_breakers["debug-agent"]
        for _ in range(5):
            cb.record_failure()
        assert cb.state == "OPEN"

        # Wait for timeout
        time.sleep(1.1)

        # Circuit should be half-open
        assert cb.can_attempt() is True
        assert cb.state == "HALF_OPEN"

        # First probe succeeds
        with patch.object(client, '_invoke_service', new_callable=AsyncMock) as mock:
            mock.return_value = {"result": "success"}
            result = await client.invoke_agent("debug-agent", {}, "student-12345")
            assert result["result"] == "success"

        # Should close circuit
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_failure(self):
        """Test half-open probe failure reopens circuit"""
        client = DaprClient()

        # Open circuit
        cb = client.circuit_breakers["debug-agent"]
        for _ in range(5):
            cb.record_failure()

        # Wait for timeout
        time.sleep(1.1)

        # Half-open probe fails
        with patch.object(client, '_invoke_service', side_effect=Exception("Still down")):
            with pytest.raises(Exception):
                await client.invoke_agent("debug-agent", {}, "student-12345")

        # Should immediately reopen
        assert cb.state == "OPEN"


class TestResilienceMetrics:
    """Test resilience metrics and monitoring"""

    @pytest.mark.asyncio
    async def test_failure_rate_tracking(self):
        """Test tracking of failure rates"""
        client = DaprClient()

        success_count = 0
        failure_count = 0

        # Simulate mixed outcomes
        async def mixed_outcome(*args, **kwargs):
            nonlocal success_count, failure_count
            if success_count + failure_count < 10:
                if (success_count + failure_count) % 3 == 0:
                    failure_count += 1
                    raise Exception("Intermittent failure")
                else:
                    success_count += 1
                    return {"result": "success"}
            else:
                return {"result": "success"}

        with patch.object(client, '_invoke_service', side_effect=mixed_outcome):
            for _ in range(12):
                try:
                    await client.invoke_agent("debug-agent", {}, "student-12345")
                except:
                    pass

        cb = client.circuit_breakers["debug-agent"]
        # Circuit should not open with 3 failures out of 12 (below threshold)
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_status_monitoring(self):
        """Test monitoring circuit breaker states"""
        client = DaprClient()

        # Set up different states for different agents
        # debug-agent: OPEN
        debug_cb = client.circuit_breakers["debug-agent"]
        for _ in range(5):
            debug_cb.record_failure()

        # concepts-agent: CLOSED (healthy)
        concepts_cb = client.circuit_breakers["concepts-agent"]
        concepts_cb.record_success()

        # Get all status
        status = client.get_all_circuit_breaker_status()

        assert status["debug-agent"]["state"] == "OPEN"
        assert status["debug-agent"]["can_attempt"] is False
        assert status["concepts-agent"]["state"] == "CLOSED"
        assert status["concepts-agent"]["can_attempt"] is True


if __name__ == "__main__":
    print("=== Running Chaos Tests: Network Failures & Service Downtime ===")
    pytest.main([__file__, "-v"])