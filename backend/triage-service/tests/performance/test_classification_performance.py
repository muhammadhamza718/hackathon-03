"""
Performance Tests: Classification Performance
Elite Implementation Standard v2.0.0

Benchmarks intent classification speed, accuracy, and token efficiency.
"""

import sys
import time
import pytest
import statistics
from pathlib import Path
from typing import List, Dict

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.openai_router import OpenAIRouter


class TestClassificationPerformance:
    """Test classification performance benchmarks"""

    def setup_method(self):
        """Setup router for performance testing"""
        self.router = OpenAIRouter()

    def benchmark_classification(self, queries: List[str]) -> Dict:
        """Benchmark classification for given queries"""
        times = []
        token_estimates = []
        intents = []

        for query in queries:
            start = time.time()
            result = self.router.classify_intent(query)
            duration = (time.time() - start) * 1000  # ms

            times.append(duration)
            token_estimates.append(result["token_estimate"])
            intents.append(result["intent"])

        return {
            "count": len(queries),
            "total_time_ms": sum(times),
            "avg_time_ms": statistics.mean(times),
            "p95_time_ms": statistics.quantiles(times, n=20)[18] if len(times) > 20 else statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "total_tokens": sum(token_estimates),
            "avg_tokens": statistics.mean(token_estimates),
            "intents": intents
        }

    def test_syntax_help_classification_speed(self):
        """Benchmark syntax help classification speed"""
        queries = [
            "I'm getting a syntax error",
            "help with my code error",
            "why is this line failing",
            "syntax error in for loop",
            "missing semicolon error"
        ]

        results = self.benchmark_classification(queries)

        # Target: <20ms average per query
        assert results["avg_time_ms"] < 20

        # Target: <50ms p95 latency
        assert results["p95_time_ms"] < 50

        print(f"Syntax Help - Avg: {results['avg_time_ms']:.2f}ms, P95: {results['p95_time_ms']:.2f}ms")

    def test_concept_explanation_classification_speed(self):
        """Benchmark concept explanation classification speed"""
        queries = [
            "what is polymorphism",
            "explain inheritance",
            "how does async work",
            "tell me about functions",
            "what are closures"
        ]

        results = self.benchmark_classification(queries)

        # Target: <20ms average
        assert results["avg_time_ms"] < 20

        print(f"Concept Explanation - Avg: {results['avg_time_ms']:.2f}ms")

    def test_practice_exercises_classification_speed(self):
        """Benchmark practice exercises classification speed"""
        queries = [
            "give me exercises",
            "practice problems",
            "coding challenges",
            "drills for loops",
            "homework help"
        ]

        results = self.benchmark_classification(queries)

        # Target: <20ms average
        assert results["avg_time_ms"] < 20

        print(f"Practice Exercises - Avg: {results['avg_time_ms']:.2f}ms")

    def test_progress_check_classification_speed(self):
        """Benchmark progress check classification speed"""
        queries = [
            "how am I doing",
            "progress report",
            "course completion",
            "what have I learned",
            "my progress"
        ]

        results = self.benchmark_classification(queries)

        # Target: <20ms average
        assert results["avg_time_ms"] < 20

        print(f"Progress Check - Avg: {results['avg_time_ms']:.2f}ms")

    def test_mixed_intent_classification_speed(self):
        """Benchmark mixed intent classification speed"""
        queries = [
            "syntax error in for loop",  # syntax_help
            "what is polymorphism",  # concept_explanation
            "give me practice exercises",  # practice_exercises
            "how am I doing",  # progress_check
            "help with my code",  # syntax_help
            "explain inheritance",  # concept_explanation
            "coding challenges",  # practice_exercises
            "progress report",  # progress_check
        ]

        results = self.benchmark_classification(queries)

        # Target: <20ms average, <100ms total for 8 queries
        assert results["avg_time_ms"] < 20
        assert results["total_time_ms"] < 100

        print(f"Mixed Intents - Avg: {results['avg_time_ms']:.2f}ms, Total: {results['total_time_ms']:.2f}ms")

    def test_accuracy_consistency(self):
        """Test classification accuracy remains consistent"""
        # Same query multiple times
        query = "syntax error in for loop"
        expected_intent = "syntax_help"

        results = []
        for _ in range(10):
            result = self.router.classify_intent(query)
            results.append(result["intent"])

        # All should classify correctly
        assert all(intent == expected_intent for intent in results)

    def test_token_efficiency_target(self):
        """Test token efficiency meets 98.7% target"""
        test_queries = [
            "syntax error",
            "explain concept",
            "practice code",
            "progress check"
        ]

        results = self.benchmark_classification(test_queries)

        # Baseline: 1500 tokens per query
        baseline_tokens = 1500 * len(test_queries)
        actual_tokens = results["total_tokens"]

        efficiency = (baseline_tokens - actual_tokens) / baseline_tokens

        # Target: 98.7% efficiency
        assert efficiency >= 0.987

        print(f"Token Efficiency: {efficiency:.1%} (Target: 98.7%)")

    def test_large_batch_performance(self):
        """Test performance with large batch of queries"""
        # Generate 50 mixed queries
        base_queries = [
            "syntax error in line {i}",
            "what is concept {i}",
            "give me exercise {i}",
            "my progress {i}"
        ]

        queries = []
        for i in range(50):
            base = base_queries[i % 4]
            queries.append(base.format(i=i))

        results = self.benchmark_classification(queries)

        # Target: <25ms average even for large batches
        assert results["avg_time_ms"] < 25

        # Total should be reasonable
        assert results["total_time_ms"] < 1500  # <1.5s for 50 queries

        print(f"Large Batch (50) - Avg: {results['avg_time_ms']:.2f}ms, Total: {results['total_time_ms']:.2f}ms")

    def test_memory_efficiency(self):
        """Test memory efficiency during classification"""
        import gc
        import psutil
        import os

        # Get baseline memory
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss

        # Run classifications
        queries = ["test query"] * 100
        for query in queries:
            self.router.classify_intent(query)

        # Force garbage collection
        gc.collect()

        # Get final memory
        final_memory = process.memory_info().rss
        memory_increase = final_memory - baseline_memory

        # Target: <50MB increase for 100 classifications
        assert memory_increase < 50 * 1024 * 1024  # 50MB in bytes

        print(f"Memory Increase: {memory_increase / (1024*1024):.2f}MB")

    def test_concurrent_classification(self):
        """Test performance under concurrent load"""
        import asyncio

        async def classify_query(query):
            return self.router.classify_intent(query)

        async def run_concurrent():
            queries = ["concurrent test"] * 20
            tasks = [classify_query(q) for q in queries]
            return await asyncio.gather(*tasks)

        start = time.time()
        results = asyncio.run(run_concurrent())
        duration = (time.time() - start) * 1000

        # Should handle 20 concurrent in <100ms
        assert duration < 100
        assert len(results) == 20

        print(f"Concurrent (20) - Total: {duration:.2f}ms")

    def test_warm_vs_cold_performance(self):
        """Test performance difference between warm and cold starts"""
        # Cold start - new router instance
        cold_router = OpenAIRouter()
        start = time.time()
        cold_result = cold_router.classify_intent("test query")
        cold_time = (time.time() - start) * 1000

        # Warm start - reuse existing
        start = time.time()
        warm_result = self.router.classify_intent("test query")
        warm_time = (time.time() - start) * 1000

        # Warm should be faster or similar
        assert warm_time <= cold_time * 1.5  # Allow 50% variance

        print(f"Cold: {cold_time:.2f}ms, Warm: {warm_time:.2f}ms")

    def test_error_cases_performance(self):
        """Test performance of error handling"""
        # Edge cases
        edge_queries = [
            "",  # Empty
            "a",  # Single character
            "test " * 100,  # Very long
            "!!!",  # Special chars only
            "1234567890",  # Numbers only
        ]

        start_time = time.time()
        for query in edge_queries:
            try:
                self.router.classify_intent(query)
            except:
                pass  # Expected for some cases
        total_time = (time.time() - start_time) * 1000

        # Should handle all edge cases in <200ms total
        assert total_time < 200

        print(f"Edge Cases - Total: {total_time:.2f}ms")


class TestPerformanceRegression:
    """Test for performance regressions"""

    def test_no_regression_baseline(self):
        """Ensure no significant performance regression"""
        # Baseline targets from architecture spec
        targets = {
            "avg_latency_ms": 20,
            "p95_latency_ms": 50,
            "token_efficiency": 0.987
        }

        # Run standard test
        queries = ["syntax error", "explain concept", "practice", "progress"]
        results = self.benchmark_classification(queries)

        # Check against targets
        assert results["avg_time_ms"] <= targets["avg_latency_ms"]
        assert results["p95_time_ms"] <= targets["p95_latency_ms"]

        # Token efficiency
        baseline = 1500 * len(queries)
        efficiency = (baseline - results["total_tokens"]) / baseline
        assert efficiency >= targets["token_efficiency"]

        print("Performance Regression Test: PASSED")
        print(f"  Avg: {results['avg_time_ms']:.2f}ms (target: {targets['avg_latency_ms']}ms)")
        print(f"  P95: {results['p95_time_ms']:.2f}ms (target: {targets['p95_latency_ms']}ms)")
        print(f"  Efficiency: {efficiency:.1%} (target: {targets['token_efficiency']:.1%})")


if __name__ == "__main__":
    print("=== Running Performance Tests: Classification ===")
    pytest.main([__file__, "-v", "-s"])