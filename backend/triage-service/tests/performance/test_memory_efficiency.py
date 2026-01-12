"""
Performance Tests: Memory Efficiency
Elite Implementation Standard v2.0.0

Tests memory usage patterns and resource efficiency across the pipeline.
"""

import sys
import pytest
import gc
import psutil
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.openai_router import OpenAIRouter
from services.dapr_client import DaprClient
from services.integration import TriageOrchestrator
from models.schemas import TriageRequest
from services.security_reporter import SecurityReporter
from services.audit_logger import TriageAudit


class TestMemoryUsage:
    """Test memory usage patterns"""

    def get_memory_usage(self):
        """Get current process memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def test_router_memory_efficiency(self):
        """Test OpenAI router memory efficiency"""
        baseline = self.get_memory_usage()

        router = OpenAIRouter()

        # Run 100 classifications
        for i in range(100):
            router.classify_intent(f"test query {i}")

        # Force garbage collection
        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <10MB increase for 100 operations
        assert increase < 10

        print(f"Router Memory - Baseline: {baseline:.2f}MB, Final: {final:.2f}MB, Increase: {increase:.2f}MB")

    def test_dapr_client_memory_efficiency(self):
        """Test Dapr client memory efficiency"""
        baseline = self.get_memory_usage()

        client = DaprClient()

        # Get status multiple times
        for i in range(100):
            client.get_circuit_breaker_status(f"agent-{i % 5}")

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <5MB increase
        assert increase < 5

        print(f"Dapr Client Memory - Increase: {increase:.2f}MB")

    def test_orchestrator_memory_efficiency(self):
        """Test orchestrator memory efficiency"""
        baseline = self.get_memory_usage()

        orchestrator = TriageOrchestrator()

        # Run multiple orchestrations (with mocked components)
        with patch('services.integration.OpenAIRouter') as mock_router, \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit'):

            mock_router_instance = Mock()
            mock_router_instance.classify_intent.return_value = {
                "intent": "syntax_help",
                "confidence": 0.95,
                "token_estimate": 15
            }
            mock_router_instance.route_selection.return_value = {
                "target_agent": "debug-agent",
                "priority": 1,
                "confidence": 0.95,
                "intent": "syntax_help"
            }
            mock_router.return_value = mock_router_instance

            mock_dapr_instance = Mock()
            mock_dapr_instance.invoke_agent = Mock(return_value={"result": "success"})
            mock_dapr_instance.get_circuit_breaker_status.return_value = {
                "can_attempt": True,
                "state": "CLOSED"
            }
            mock_dapr.return_value = mock_dapr_instance

            # Run orchestrations
            for i in range(50):
                request = {"query": f"test {i}", "user_id": f"student-{i:05d}"}
                security_context = {"student_id": f"student-{i:05d}", "role": "student"}

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        orchestrator.execute_triage(request, security_context)
                    )
                finally:
                    loop.close()

            # Mock audit
            mock_audit_instance = Mock()
            mock_audit.return_value = mock_audit_instance

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <20MB increase for 50 orchestrations
        assert increase < 20

        print(f"Orchestrator Memory - Increase: {increase:.2f}MB")

    def test_security_reporter_memory_efficiency(self):
        """Test security reporter memory efficiency"""
        baseline = self.get_memory_usage()

        reporter = SecurityReporter()

        # Generate many events
        for i in range(500):
            reporter.record_auth_failure(f"student-{i:03d}", "test", {"detail": "x" * 100})

        # Generate reports
        report = reporter.generate_compliance_report(hours=24)
        audit_trail = reporter.generate_audit_trail(hours=24)

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <20MB increase for 500 events + reports
        assert increase < 20

        print(f"Security Reporter Memory - Increase: {increase:.2f}MB")

    def test_audit_logger_memory_efficiency(self):
        """Test audit logger memory efficiency"""
        baseline = self.get_memory_usage()

        audit = TriageAudit()
        audit.kafka_enabled = False  # Mock mode

        # Generate many audit events
        for i in range(1000):
            audit.record_event(
                event_type="TRIAGE_COMPLETE",
                student_id=f"student-{i:05d}",
                routing_decision={"target_agent": "debug-agent"},
                metrics={"tokens_used": 19}
            )

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <25MB increase for 1000 events
        assert increase < 25

        print(f"Audit Logger Memory - Increase: {increase:.2f}MB")

    def test_model_object_efficiency(self):
        """Test Pydantic model memory efficiency"""
        baseline = self.get_memory_usage()

        # Create many model instances
        requests = []
        for i in range(1000):
            request = TriageRequest(
                query=f"Query {i} " * 10,  # 100 char query
                user_id=f"student-{i:05d}",
                context={"topic": "OOP", "difficulty": "intermediate", "index": i}
            )
            requests.append(request)

        # Serialize all
        serialized = [r.model_dump() for r in requests]

        # Estimate memory
        total_obj_size = sum(sys.getsizeof(r) for r in requests)
        total_serialized_size = sum(sys.getsizeof(str(s)) for s in serialized)

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Target: <30MB for 1000 complex requests
        assert increase < 30

        avg_obj_size = total_obj_size / len(requests)
        avg_serialized_size = total_serialized_size / len(requests)

        print(f"Model Memory - Total Increase: {increase:.2f}MB")
        print(f"  Per object: {avg_obj_size:.0f} bytes")
        print(f"  Per serialized: {avg_serialized_size:.0f} bytes")

    def test_leak_detection(self):
        """Test for memory leaks over time"""
        baseline = self.get_memory_usage()

        router = OpenAIRouter()

        # Run in cycles to detect leaks
        for cycle in range(5):
            for i in range(100):
                router.classify_intent(f"leak test {cycle}-{i}")

            # Check memory after each cycle
            current = self.get_memory_usage()
            increase = current - baseline

            # Should not grow excessively
            assert increase < 15, f"Memory leak detected at cycle {cycle}"

            # Force cleanup
            gc.collect()

        final = self.get_memory_usage()
        final_increase = final - baseline

        print(f"Leak Test - Final Increase: {final_increase:.2f}MB over 5 cycles")

    def test_large_batch_memory_stability(self):
        """Test memory stability with large batches"""
        baseline = self.get_memory_usage()

        router = OpenAIRouter()

        # Process large batch
        batch_size = 500
        for i in range(batch_size):
            router.classify_intent(f"large batch query {i} " * 20)

        # Check memory
        mid_memory = self.get_memory_usage()

        # Process second batch
        for i in range(batch_size):
            router.classify_intent(f"second batch {i} " * 20)

        final_memory = self.get_memory_usage()

        # Memory should stabilize (not grow linearly)
        first_batch_increase = mid_memory - baseline
        second_batch_increase = final_memory - mid_memory

        # Second batch should not use significantly more memory
        assert second_batch_increase < first_batch_increase * 1.5

        print(f"Large Batch Memory:")
        print(f"  First batch: {first_batch_increase:.2f}MB")
        print(f"  Second batch: {second_batch_increase:.2f}MB")
        print(f"  Ratio: {second_batch_increase/first_batch_increase:.2f}x")

    def test_resource_cleanup(self):
        """Test proper cleanup of resources"""
        baseline = self.get_memory_usage()

        # Create and use multiple instances
        for _ in range(10):
            router = OpenAIRouter()
            for i in range(10):
                router.classify_intent(f"test {i}")

        # Delete references
        router = None

        # Force cleanup
        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Should clean up most memory
        assert increase < 10

        print(f"Resource Cleanup - Remaining Increase: {increase:.2f}MB")


class TestMemoryPerformanceTargets:
    """Verify memory performance targets"""

    def test_all_memory_targets(self):
        """Test all memory targets are met"""
        baseline = self.get_memory_usage()

        # Run comprehensive memory test
        total_operations = 0

        # Router operations
        router = OpenAIRouter()
        for i in range(100):
            router.classify_intent(f"test {i}")
        total_operations += 100

        # Dapr client operations
        client = DaprClient()
        for i in range(50):
            client.get_circuit_breaker_status(f"agent-{i % 3}")
        total_operations += 50

        # Security events
        reporter = SecurityReporter()
        for i in range(50):
            reporter.record_auth_failure(f"student-{i:03d}", "test", {})
        total_operations += 50

        gc.collect()

        final = self.get_memory_usage()
        increase = final - baseline

        # Architecture spec: Memory efficient operations
        # Target: <20MB for 200+ operations
        assert increase < 20

        print("\n=== Memory Performance Targets ===")
        print(f"Total Operations: {total_operations}")
        print(f"Memory Increase: {increase:.2f}MB")
        print(f"Per Operation: {increase/total_operations:.2f}MB")
        print(f"Target: <20MB total, <0.1MB per operation")
        print(f"Result: {'✓ PASSED' if increase < 20 else '✗ FAILED'}")


if __name__ == "__main__":
    print("=== Running Performance Tests: Memory Efficiency ===")
    pytest.main([__file__, "-v", "-s"])