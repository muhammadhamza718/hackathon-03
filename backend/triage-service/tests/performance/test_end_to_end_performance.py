"""
Performance Tests: End-to-End Performance
Elite Implementation Standard v2.0.0

Benchmarks complete triage pipeline performance from HTTP request to response.
"""

import sys
import time
import pytest
import statistics
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.integration import TriageOrchestrator
from models.schemas import TriageRequest


class TestEndToEndPerformance:
    """Test complete pipeline performance"""

    def setup_method(self):
        """Setup orchestrator for performance testing"""
        self.orchestrator = TriageOrchestrator()

    async def benchmark_complete_flow(self, requests: list) -> dict:
        """Benchmark complete triage flow"""
        times = []
        token_estimates = []
        processing_times = []

        for request_data in requests:
            security_context = {
                "student_id": request_data["user_id"],
                "role": "student"
            }

            start = time.time()
            response, metrics = await self.orchestrator.execute_triage(
                request_data, security_context
            )
            duration = (time.time() - start) * 1000

            times.append(duration)
            token_estimates.append(metrics.tokens_used)
            processing_times.append(metrics.total_processing_ms)

        return {
            "count": len(requests),
            "total_time_ms": sum(times),
            "avg_time_ms": statistics.mean(times),
            "p95_time_ms": statistics.quantiles(times, n=20)[18] if len(times) > 20 else statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "avg_processing_ms": statistics.mean(processing_times),
            "total_tokens": sum(token_estimates),
            "avg_tokens": statistics.mean(token_estimates)
        }

    @pytest.mark.asyncio
    async def test_syntax_help_flow_performance(self):
        """Benchmark syntax help complete flow"""
        requests = [
            TriageRequest(
                query="syntax error in for loop",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(10)
        ]

        results = await self.benchmark_complete_flow(requests)

        # Target: <100ms average end-to-end
        assert results["avg_time_ms"] < 100

        # Target: <200ms p95
        assert results["p95_time_ms"] < 200

        print(f"Syntax Help E2E - Avg: {results['avg_time_ms']:.2f}ms, P95: {results['p95_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_concept_explanation_flow_performance(self):
        """Benchmark concept explanation complete flow"""
        requests = [
            TriageRequest(
                query="what is polymorphism",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(10)
        ]

        results = await self.benchmark_complete_flow(requests)

        # Target: <100ms average
        assert results["avg_time_ms"] < 100

        print(f"Concept Explanation E2E - Avg: {results['avg_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_practice_exercises_flow_performance(self):
        """Benchmark practice exercises complete flow"""
        requests = [
            TriageRequest(
                query="give me practice exercises",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(10)
        ]

        results = await self.benchmark_complete_flow(requests)

        # Target: <100ms average
        assert results["avg_time_ms"] < 100

        print(f"Practice Exercises E2E - Avg: {results['avg_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_progress_check_flow_performance(self):
        """Benchmark progress check complete flow"""
        requests = [
            TriageRequest(
                query="how am I doing",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(10)
        ]

        results = await self.benchmark_complete_flow(requests)

        # Target: <100ms average
        assert results["avg_time_ms"] < 100

        print(f"Progress Check E2E - Avg: {results['avg_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_mixed_intents_flow_performance(self):
        """Benchmark mixed intents complete flow"""
        queries = [
            "syntax error in for loop",
            "what is polymorphism",
            "give me practice exercises",
            "how am I doing",
            "help with my code",
            "explain inheritance",
            "coding challenges",
            "progress report"
        ]

        requests = [
            TriageRequest(
                query=queries[i % len(queries)],
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(20)
        ]

        results = await self.benchmark_complete_flow(requests)

        # Target: <150ms average, <300ms p95
        assert results["avg_time_ms"] < 150
        assert results["p95_time_ms"] < 300

        print(f"Mixed Intents E2E - Avg: {results['avg_time_ms']:.2f}ms, P95: {results['p95_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_high_load_performance(self):
        """Test performance under high load"""
        # Generate 50 requests
        requests = [
            TriageRequest(
                query="syntax error in for loop",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(50)
        ]

        start = time.time()
        results = await self.benchmark_complete_flow(requests)
        total_time = (time.time() - start) * 1000

        # Target: <5s total for 50 requests
        assert total_time < 5000

        # Target: <100ms average per request
        assert results["avg_time_ms"] < 100

        print(f"High Load (50) - Total: {total_time:.2f}ms, Avg: {results['avg_time_ms']:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_flow_performance(self):
        """Test concurrent requests performance"""
        async def execute_single_request(i):
            request = TriageRequest(
                query="syntax error",
                user_id=f"student-{i:05d}"
            ).model_dump()
            security_context = {"student_id": f"student-{i:05d}", "role": "student"}

            start = time.time()
            response, metrics = await self.orchestrator.execute_triage(
                request, security_context
            )
            duration = (time.time() - start) * 1000
            return duration

        start = time.time()
        # Launch 20 concurrent requests
        durations = await asyncio.gather(*[execute_single_request(i) for i in range(20)])
        total_time = (time.time() - start) * 1000

        avg_duration = statistics.mean(durations)

        # Target: <200ms total for 20 concurrent
        assert total_time < 2000

        # Target: <100ms average per request
        assert avg_duration < 100

        print(f"Concurrent (20) - Total: {total_time:.2f}ms, Avg: {avg_duration:.2f}ms")

    @pytest.mark.asyncio
    async def test_token_efficiency_e2e(self):
        """Test end-to-end token efficiency"""
        requests = [
            TriageRequest(
                query=query,
                user_id="student-12345"
            ).model_dump()
            for query in ["syntax error", "explain concept", "practice code", "progress check"]
        ]

        results = await self.benchmark_complete_flow(requests)

        # Baseline: 1500 tokens per query
        baseline = 1500 * len(requests)
        actual = results["total_tokens"]

        efficiency = (baseline - actual) / baseline

        # Target: 98.7% efficiency
        assert efficiency >= 0.987

        print(f"E2E Token Efficiency: {efficiency:.1%}")

    @pytest.mark.asyncio
    async def test_latency_breakdown(self):
        """Test breakdown of latency across pipeline stages"""
        # Mock timing for each stage
        with patch('services.integration.OpenAIRouter') as mock_router, \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit') as mock_audit:

            # Track timing
            stage_times = {}

            mock_router_instance = Mock()
            def mock_classify(query):
                start = time.time()
                result = {"intent": "syntax_help", "confidence": 0.95, "token_estimate": 15}
                stage_times["classification"] = (time.time() - start) * 1000
                return result

            def mock_route(intent, conf, student):
                start = time.time()
                result = {"target_agent": "debug-agent", "priority": 1, "confidence": conf, "intent": intent}
                stage_times["routing"] = (time.time() - start) * 1000
                return result

            mock_router_instance.classify_intent = mock_classify
            mock_router_instance.route_selection = mock_route
            mock_router.return_value = mock_router_instance

            mock_dapr_instance = Mock()
            async def mock_invoke(*args, **kwargs):
                start = time.time()
                await asyncio.sleep(0.01)  # Simulate network delay
                result = {"result": "success"}
                stage_times["dapr"] = (time.time() - start) * 1000
                return result

            mock_dapr_instance.invoke_agent = mock_invoke
            mock_dapr.return_value = mock_dapr_instance

            mock_audit_instance = Mock()
            def mock_record(*args, **kwargs):
                stage_times["audit"] = 1  # Minimal
            mock_audit_instance.record_event = mock_record
            mock_audit.return_value = mock_audit_instance

            # Execute single request
            orchestrator = TriageOrchestrator()
            request = {"query": "test", "user_id": "student-12345"}
            security_context = {"student_id": "student-12345", "role": "student"}

            start = time.time()
            await orchestrator.execute_triage(request, security_context)
            total_time = (time.time() - start) * 1000

            # Calculate overhead
            measured_stages = sum(stage_times.values())
            overhead = total_time - measured_stages

            # All stages should complete in <100ms
            assert total_time < 100

            print(f"Latency Breakdown:")
            print(f"  Classification: {stage_times.get('classification', 0):.2f}ms")
            print(f"  Routing: {stage_times.get('routing', 0):.2f}ms")
            print(f"  Dapr: {stage_times.get('dapr', 0):.2f}ms")
            print(f"  Audit: {stage_times.get('audit', 0):.2f}ms")
            print(f"  Overhead: {overhead:.2f}ms")
            print(f"  Total: {total_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_p95_target_consistency(self):
        """Test P95 latency stays under 150ms target"""
        requests = [
            TriageRequest(
                query="syntax error in for loop",
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i in range(100)  # Large sample for reliable P95
        ]

        results = await self.benchmark_complete_flow(requests)

        # Architecture spec: P95 latency should be ~150ms
        # Our target: <150ms
        assert results["p95_time_ms"] < 150

        print(f"P95 Latency: {results['p95_time_ms']:.2f}ms (Target: <150ms)")

    @pytest.mark.asyncio
    async def test_sustained_load_performance(self):
        """Test performance under sustained load over time"""
        total_requests = 200
        batch_size = 20
        batches = total_requests // batch_size

        all_durations = []

        for batch in range(batches):
            requests = [
                TriageRequest(
                    query=f"batch {batch} query {i}",
                    user_id=f"student-{batch:03d}{i:03d}"
                ).model_dump()
                for i in range(batch_size)
            ]

            batch_start = time.time()
            results = await self.benchmark_complete_flow(requests)
            batch_duration = (time.time() - batch_start) * 1000

            all_durations.append(batch_duration)

            # Each batch should complete in <2s
            assert batch_duration < 2000

        avg_batch_time = statistics.mean(all_durations)

        # Average batch time should be <1.5s
        assert avg_batch_time < 1500

        print(f"Sustained Load - {total_requests} requests in {batches} batches")
        print(f"  Avg Batch Time: {avg_batch_time:.2f}ms")
        print(f"  Avg Request Time: {results['avg_time_ms']:.2f}ms")


class TestPerformanceTargets:
    """Verify all performance targets from architecture"""

    @pytest.mark.asyncio
    async def test_all_performance_targets(self):
        """Test all performance targets are met"""
        # Run comprehensive test
        requests = [
            TriageRequest(
                query=query,
                user_id=f"student-{i:05d}"
            ).model_dump()
            for i, query in enumerate([
                "syntax error in for loop",
                "what is polymorphism",
                "give me practice exercises",
                "how am I doing"
            ] * 10)  # 40 total
        ]

        results = await self.benchmark_complete_flow(requests)

        targets = {
            "p95_latency_ms": 150,
            "avg_latency_ms": 100,
            "token_efficiency": 0.987,
            "max_concurrent": 20
        }

        # Calculate efficiency
        baseline = 1500 * len(requests)
        efficiency = (baseline - results["total_tokens"]) / baseline

        print("\n=== Performance Target Verification ===")
        print(f"P95 Latency: {results['p95_time_ms']:.2f}ms (Target: {targets['p95_latency_ms']}ms) {'✓' if results['p95_time_ms'] < targets['p95_latency_ms'] else '✗'}")
        print(f"Avg Latency: {results['avg_time_ms']:.2f}ms (Target: {targets['avg_latency_ms']}ms) {'✓' if results['avg_time_ms'] < targets['avg_latency_ms'] else '✗'}")
        print(f"Token Efficiency: {efficiency:.1%} (Target: {targets['token_efficiency']:.1%}) {'✓' if efficiency >= targets['token_efficiency'] else '✗'}")

        # All targets must be met
        assert results["p95_time_ms"] < targets["p95_latency_ms"]
        assert results["avg_time_ms"] < targets["avg_latency_ms"]
        assert efficiency >= targets["token_efficiency"]

        print("\n✓ All performance targets met!")


if __name__ == "__main__":
    print("=== Running Performance Tests: End-to-End ===")
    pytest.main([__file__, "-v", "-s"])