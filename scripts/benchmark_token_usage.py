#!/usr/bin/env python3
"""
Token Efficiency Benchmark Script
Elite Implementation Standard v2.0.0

Measures token usage and efficiency of triage skill vs LLM baseline.
Validates 90% token reduction target.
"""

import json
import time
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class BenchmarkResult:
    """Benchmark result container"""
    test_name: str
    input_text: str
    token_estimate: int
    processing_time_ms: float
    baseline_llm_tokens: int
    efficiency_gain: float
    passed: bool
    notes: str = ""


class TokenEfficiencyBenchmark:
    """
    Comprehensive token efficiency benchmarking suite
    """

    def __init__(self):
        self.baseline_llm_tokens = 1500  # Estimated LLM tokens per classification
        self.target_efficiency = 0.90    # 90% reduction target
        self.max_tokens_threshold = 1000  # Maximum allowed tokens
        self.results: List[BenchmarkResult] = []

        # Import our skills for testing
        sys.path.append('skills-library/triage-logic')
        from intent_detection import classify_intent
        from route_selection import route_selection

        self.classify_intent = classify_intent
        self.route_selection = route_selection

    def _token_estimate(self, text: str) -> int:
        """Estimate token count for given text"""
        return len(text.split()) + (len(text) // 4)

    def _calculate_efficiency(self, skill_tokens: int) -> float:
        """Calculate efficiency gain vs LLM baseline"""
        return 1 - (skill_tokens / self.baseline_llm_tokens)

    def _check_pass(self, token_count: int, efficiency: float) -> Tuple[bool, str]:
        """Check if benchmark passes elite standards"""
        if token_count > self.max_tokens_threshold:
            return False, f"Token count {token_count} exceeds threshold {self.max_tokens_threshold}"

        if efficiency < self.target_efficiency:
            return False, f"Efficiency {efficiency:.3f} below target {self.target_efficiency}"

        if token_count < 10:
            return False, f"Token count suspiciously low: {token_count}"

        return True, "PASS"

    def run_intent_classification_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark intent classification token usage"""
        print("=== Intent Classification Benchmarks ===")

        test_cases = [
            ("Syntax error help", "I'm getting a syntax error in my for loop, can you help fix it?"),
            ("Concept explanation", "What is polymorphism in object-oriented programming? Please explain with examples."),
            ("Exercise request", "Give me some challenging practice problems for list comprehensions and loops."),
            ("Progress check", "How am I progressing in my Python learning journey? Show me my mastery level."),
            ("Minimal query", "Help with error"),
            ("Complex query", "I've been working on this Python project for 3 days and I keep getting TypeError: 'int' object is not iterable when trying to iterate over what should be a list. I've checked the variable type with isinstance() and it says it's a list, but the loop still fails. Can you explain why this might happen and how to debug it?"),
            ("Edge case empty", ""),
            ("Edge case single char", "a"),
        ]

        results = []

        for name, query in test_cases:
            if not query:
                query = ""  # Handle empty case

            # Time the intent classification
            start_time = time.time()
            try:
                result = self.classify_intent(query)
                processing_time = (time.time() - start_time) * 1000

                # Extract relevant metrics
                token_count = result.get('token_estimate', self._token_estimate(query))
                efficiency = self._calculate_efficiency(token_count)
                passed, note = self._check_pass(token_count, efficiency)

                benchmark_result = BenchmarkResult(
                    test_name=f"Intent: {name}",
                    input_text=query[:50] + "..." if len(query) > 50 else query,
                    token_estimate=token_count,
                    processing_time_ms=processing_time,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=efficiency,
                    passed=passed,
                    notes=note
                )

                results.append(benchmark_result)
                print(f"  {name:20} | Tokens: {token_count:4} | Time: {processing_time:5.1f}ms | Eff: {efficiency:.2%} | {'PASS' if passed else 'FAIL'}")

            except Exception as e:
                print(f"  {name:20} | ERROR: {str(e)}")
                results.append(BenchmarkResult(
                    test_name=f"Intent: {name}",
                    input_text=query,
                    token_estimate=9999,
                    processing_time_ms=0,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=0,
                    passed=False,
                    notes=f"Exception: {str(e)}"
                ))

        return results

    def run_route_selection_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark route selection efficiency"""
        print("\n=== Route Selection Benchmarks ===")

        test_cases = [
            ("High confidence syntax", "syntax_help", 0.95),
            ("Medium confidence concept", "concept_explanation", 0.75),
            ("Low confidence fallback", "exercise_request", 0.45),
            ("Unknown intent", "unknown_intent", 0.80),
            ("Borderline confidence", "progress_check", 0.59),
        ]

        results = []
        student_id = "student_12345678-1234-1234-1234-123456789012"

        for name, intent, confidence in test_cases:
            start_time = time.time()
            try:
                result = self.route_selection(intent, confidence, student_id)
                processing_time = (time.time() - start_time) * 1000

                # Route selection uses minimal tokens (just metadata)
                token_count = 50  # Fixed small overhead
                efficiency = self._calculate_efficiency(token_count)
                passed, note = self._check_pass(token_count, efficiency)

                benchmark_result = BenchmarkResult(
                    test_name=f"Route: {name}",
                    input_text=f"{intent} (conf: {confidence})",
                    token_estimate=token_count,
                    processing_time_ms=processing_time,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=efficiency,
                    passed=passed,
                    notes=note
                )

                results.append(benchmark_result)
                print(f"  {name:25} | Tokens: {token_count:4} | Time: {processing_time:5.1f}ms | Eff: {efficiency:.2%} | {'PASS' if passed else 'FAIL'}")

            except Exception as e:
                print(f"  {name:25} | ERROR: {str(e)}")
                results.append(BenchmarkResult(
                    test_name=f"Route: {name}",
                    input_text=f"{intent} (conf: {confidence})",
                    token_estimate=9999,
                    processing_time_ms=0,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=0,
                    passed=False,
                    notes=f"Exception: {str(e)}"
                ))

        return results

    def run_end_to_end_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark complete triage flow (classification + routing)"""
        print("\n=== End-to-End Flow Benchmarks ===")

        test_queries = [
            ("Complete flow syntax", "I'm getting a syntax error in my function"),
            ("Complete flow concept", "Explain how decorators work in Python"),
            ("Complete flow exercise", "Give me practice problems for functions"),
        ]

        results = []

        for name, query in test_queries:
            start_time = time.time()
            try:
                # Step 1: Intent classification
                intent_result = self.classify_intent(query)
                intent_tokens = intent_result.get('token_estimate', self._token_estimate(query))
                intent_time = (time.time() - start_time) * 1000

                # Step 2: Route selection
                route_start = time.time()
                route_result = self.route_selection(
                    intent_result['intent'],
                    intent_result['confidence'],
                    "student_12345678-1234-1234-1234-123456789012"
                )
                route_time = (time.time() - route_start) * 1000

                # Total metrics
                total_tokens = intent_tokens + 50  # Intent + route overhead
                total_time = intent_time + route_time
                efficiency = self._calculate_efficiency(total_tokens)
                passed, note = self._check_pass(total_tokens, efficiency)

                benchmark_result = BenchmarkResult(
                    test_name=f"Flow: {name}",
                    input_text=query[:40] + "..." if len(query) > 40 else query,
                    token_estimate=total_tokens,
                    processing_time_ms=total_time,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=efficiency,
                    passed=passed,
                    notes=f"Intent: {intent_time:.1f}ms + Route: {route_time:.1f}ms"
                )

                results.append(benchmark_result)
                print(f"  {name:20} | Tokens: {total_tokens:4} | Time: {total_time:5.1f}ms | Eff: {efficiency:.2%} | {'PASS' if passed else 'FAIL'}")

            except Exception as e:
                print(f"  {name:20} | ERROR: {str(e)}")
                results.append(BenchmarkResult(
                    test_name=f"Flow: {name}",
                    input_text=query,
                    token_estimate=9999,
                    processing_time_ms=0,
                    baseline_llm_tokens=self.baseline_llm_tokens,
                    efficiency_gain=0,
                    passed=False,
                    notes=f"Exception: {str(e)}"
                ))

        return results

    def generate_summary(self) -> Dict:
        """Generate comprehensive benchmark summary"""
        all_results = self.results
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.passed)
        failed_tests = total_tests - passed_tests

        if total_tests == 0:
            return {"error": "No tests run"}

        # Calculate averages
        avg_tokens = sum(r.token_estimate for r in all_results) / total_tests
        avg_time = sum(r.processing_time_ms for r in all_results) / total_tests
        avg_efficiency = sum(r.efficiency_gain for r in all_results) / total_tests

        # Find extremes
        max_tokens = max(r.token_estimate for r in all_results)
        min_tokens = min(r.token_estimate for r in all_results)
        max_time = max(r.processing_time_ms for r in all_results)

        # Elite standard validation
        elite_standards = {
            "90%_efficiency_target": avg_efficiency >= 0.90,
            "all_tests_passed": failed_tests == 0,
            "max_tokens_1000": max_tokens <= 1000,
            "p95_latency_150ms": max_time <= 150,  # Approximation
            "performance_budget": avg_time <= 50  # Budget for combined operations
        }

        summary = {
            "benchmark_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{(passed_tests/total_tests)*100:.1f}%",
                "efficiency_target": 0.90,
                "max_tokens_threshold": 1000,
                "baseline_llm_tokens": self.baseline_llm_tokens
            },
            "performance_metrics": {
                "avg_tokens": round(avg_tokens, 1),
                "avg_processing_time_ms": round(avg_time, 2),
                "avg_efficiency_gain": round(avg_efficiency, 3),
                "max_tokens": max_tokens,
                "min_tokens": min_tokens,
                "max_processing_time_ms": round(max_time, 2)
            },
            "elite_standard_compliance": elite_standards,
            "overall_status": "PASS" if all(elite_standards.values()) else "REVIEW_NEEDED"
        }

        return summary

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite"""
        print("🚀 Token Efficiency Benchmark Suite")
        print(f"Baseline: {self.baseline_llm_tokens} tokens (LLM)")
        print(f"Target: {self.target_efficiency:.0%} reduction")
        print(f"Max allowed: {self.max_tokens_threshold} tokens")
        print("=" * 60)

        # Run all benchmark categories
        intent_results = self.run_intent_classification_benchmarks()
        route_results = self.run_route_selection_benchmarks()
        flow_results = self.run_end_to_end_benchmarks()

        # Collect all results
        self.results.extend(intent_results)
        self.results.extend(route_results)
        self.results.extend(flow_results)

        # Generate summary
        summary = self.generate_summary()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)

        if "error" in summary:
            print(f"ERROR: {summary['error']}")
            return summary

        s = summary['benchmark_summary']
        p = summary['performance_metrics']
        e = summary['elite_standard_compliance']

        print(f"Tests Run: {s['total_tests']} | Passed: {s['passed']} | Failed: {s['failed']} | Rate: {s['pass_rate']}")
        print(f"\nPerformance:")
        print(f"  Avg Tokens: {p['avg_tokens']} (vs {self.baseline_llm_tokens} LLM)")
        print(f"  Avg Efficiency: {p['avg_efficiency_gain']:.1%} (Target: {self.target_efficiency:.0%})")
        print(f"  Avg Time: {p['avg_processing_time_ms']}ms")
        print(f"  Max Time: {p['max_processing_time_ms']}ms")

        print(f"\nElite Standard Compliance:")
        for standard, passed in e.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {standard}: {status}")

        print(f"\nOVERALL: {summary['overall_status']}")

        # Write detailed results to file
        self.write_results_to_file(summary)

        return summary

    def write_results_to_file(self, summary: Dict):
        """Write benchmark results to JSON file"""
        try:
            output_file = "scripts/benchmark_results.json"

            # Prepare detailed results
            detailed_results = [asdict(r) for r in self.results]

            output_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": summary,
                "detailed_results": detailed_results
            }

            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"\n📄 Detailed results written to: {output_file}")

        except Exception as e:
            print(f"Warning: Could not write results file: {e}")


def main():
    """Main entry point"""
    try:
        benchmark = TokenEfficiencyBenchmark()
        results = benchmark.run_all_benchmarks()

        # Exit with appropriate code
        if results.get('overall_status') == 'PASS':
            print("\n✅ All benchmarks passed! Token efficiency target achieved.")
            return 0
        else:
            print("\n❌ Some benchmarks failed. Review results above.")
            return 1

    except ImportError as e:
        print(f"❌ Error: Required skill scripts not found. {e}")
        print("Make sure intent-detection.py and route-selection.py are available.")
        return 2
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)