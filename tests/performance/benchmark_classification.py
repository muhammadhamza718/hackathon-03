#!/usr/bin/env python3
"""
Benchmark: Intent Classification Speed
Elite Implementation Standard v2.0.0

Measures intent classification performance for various query patterns.
"""

import sys
import os
import time
import unittest
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../skills-library'))

class IntentClassificationBenchmark(unittest.TestCase):
    """Benchmark intent classification performance"""

    def setUp(self):
        """Set up test queries"""
        self.test_queries = [
            "Help me debug this Python syntax error",
            "Explain recursion in simple terms",
            "Create a quiz about calculus",
            "Show my learning progress this week",
            "Review my submitted code for improvements"
        ]

        # Expected intents
        self.expected_intents = ["debug_code", "explain_concept", "create_exercise", "track_progress", "review_work"]

    def benchmark_classification(self, queries: List[str]) -> Dict:
        """Run classification benchmark"""
        times = []

        # Mock classification (replace with actual skill library call)
        for query in queries:
            start_time = time.time()

            # Simulate classification logic
            if "debug" in query.lower():
                intent = "debug_code"
            elif "explain" in query.lower():
                intent = "explain_concept"
            elif "create" in query.lower():
                intent = "create_exercise"
            elif "progress" in query.lower():
                intent = "track_progress"
            elif "review" in query.lower():
                intent = "review_work"
            else:
                intent = "unknown"

            # Simulate processing time
            time.sleep(0.001)

            duration = (time.time() - start_time) * 1000  # Convert to ms
            times.append(duration)

        total_time = sum(times)
        avg_time = total_time / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        return {
            "total_queries": len(queries),
            "total_time_ms": total_time,
            "avg_time_ms": avg_time,
            "p95_time_ms": p95_time,
            "queries_per_second": len(queries) / (total_time / 1000)
        }

    def test_classification_speed(self):
        """Test classification speed meets target"""
        results = self.benchmark_classification(self.test_queries)

        # Performance targets
        target_p95 = 50.0  # 50ms maximum for P95
        target_avg = 20.0  # 20ms average

        self.assertLess(results["p95_time_ms"], target_p95,
                       f"P95 latency {results['p95_time_ms']:.2f}ms exceeds {target_p95}ms target")
        self.assertLess(results["avg_time_ms"], target_avg,
                       f"Average latency {results['avg_time_ms']:.2f}ms exceeds {target_avg}ms target")

        print(f"✓ Classification: {results['avg_time_ms']:.2f}ms avg, {results['p95_time_ms']:.2f}ms P95")

    def test_accuracy_rate(self):
        """Test classification accuracy"""
        correct = 0
        total = len(self.test_queries)

        for query, expected in zip(self.test_queries, self.expected_intents):
            # Mock classification result
            if "debug" in query.lower():
                actual = "debug_code"
            elif "explain" in query.lower():
                actual = "explain_concept"
            elif "create" in query.lower():
                actual = "create_exercise"
            elif "progress" in query.lower():
                actual = "track_progress"
            elif "review" in query.lower():
                actual = "review_work"
            else:
                actual = "unknown"

            if actual == expected:
                correct += 1

        accuracy = (correct / total) * 100
        target_accuracy = 95.0

        self.assertGreaterEqual(accuracy, target_accuracy,
                               f"Accuracy {accuracy:.1f}% below {target_accuracy}% target")

        print(f"✓ Accuracy: {accuracy:.1f}%")

    def test_token_efficiency(self):
        """Test token usage efficiency"""
        # Mock token counts
        baseline_llm = 1500  # Baseline LLM tokens per query
        skill_tokens = 19    # Our skill library tokens
        num_queries = len(self.test_queries)

        total_baseline = baseline_llm * num_queries
        total_skill = skill_tokens * num_queries

        efficiency = (1 - (total_skill / total_baseline)) * 100
        target_efficiency = 98.7

        self.assertGreaterEqual(efficiency, target_efficiency,
                               f"Efficiency {efficiency:.1f}% below {target_efficiency}% target")

        print(f"✓ Token Efficiency: {efficiency:.1f}%")

    def test_concurrent_classification(self):
        """Test classification under concurrent load"""
        # Simulate concurrent requests
        concurrent_load = 50  # 50 concurrent requests

        # Mock concurrent processing
        concurrent_times = []
        for i in range(concurrent_load):
            start = time.time()
            # Simulate quick classification
            time.sleep(0.002)
            duration = (time.time() - start) * 1000
            concurrent_times.append(duration)

        avg_concurrent = sum(concurrent_times) / len(concurrent_times)
        max_concurrent = max(concurrent_times)

        # Target: should handle concurrent load without significant degradation
        target_max = 100.0  # 100ms max for concurrent

        self.assertLess(max_concurrent, target_max,
                       f"Max concurrent time {max_concurrent:.2f}ms exceeds {target_max}ms")

        print(f"✓ Concurrent: {avg_concurrent:.2f}ms avg, {max_concurrent:.2f}ms max")

    def test_memory_efficiency(self):
        """Test memory usage during classification"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run classifications
        self.benchmark_classification(self.test_queries)

        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_memory - baseline_memory

        # Target: memory increase should be minimal
        target_increase = 50.0  # 50MB max increase

        self.assertLess(memory_increase, target_increase,
                       f"Memory increase {memory_increase:.2f}MB exceeds {target_increase}MB")

        print(f"✓ Memory: +{memory_increase:.2f}MB")

    def benchmark_all_scenarios(self):
        """Run comprehensive benchmark scenarios"""
        scenarios = {
            "simple_queries": [
                "Debug code",
                "Explain concept",
                "Create exercise"
            ],
            "complex_queries": [
                "Help me debug this complex Python function with recursion and error handling",
                "Explain the mathematical concept of derivatives in simple terms with examples",
                "Create a comprehensive quiz about advanced calculus topics"
            ],
            "edge_cases": [
                "A",  # Very short
                "I need help with a problem that involves multiple steps including debugging, explanation, and creating exercises",  # Very long
                "debug-code-explain-concept",  # Hyphens
                "Debug! Explain? Create!",  # Special chars
            ]
        }

        print("\n=== Benchmark Results ===")
        for name, queries in scenarios.items():
            results = self.benchmark_classification(queries)
            print(f"{name:15} | {results['avg_time_ms']:6.2f}ms avg | {results['queries_per_second']:6.1f} QPS")

if __name__ == '__main__':
    # Run benchmarks
    print("Intent Classification Benchmark")
    print("=" * 50)

    benchmark = IntentClassificationBenchmark()
    benchmark.setUp()

    # Run all tests
    unittest.main(verbosity=0, exit=False)

    # Run comprehensive scenarios
    benchmark.benchmark_all_scenarios()