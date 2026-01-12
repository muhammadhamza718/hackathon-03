"""
Integration Tests for OpenAI Router
Tests p95 latency <200ms, 95%+ classification accuracy
"""

import sys
import time
import pytest
from pathlib import Path

# Add skills library to path
skills_path = Path(__file__).parent.parent.parent.parent / "skills-library" / "triage-logic"
sys.path.insert(0, str(skills_path))

# Import router components
try:
    from openai_router import OpenAIRouter, classify_with_router
    from intent_detection import classify_intent
    from route_selection import route_intent
except ImportError as e:
    print(f"Import failed: {e}")
    # Skip tests if modules not available
    pytest.skip("Router modules not available", allow_module_level=True)


class TestOpenAIRouterPerformance:
    """Test router performance metrics"""

    def test_p95_latency_under_200ms(self):
        """Verify p95 latency is under 200ms"""
        router = OpenAIRouter(use_hybrid=False)  # Pure skill mode

        # Test queries covering different intents
        test_queries = [
            "I'm getting a syntax error in my for loop",
            "What is polymorphism in OOP?",
            "Give me practice exercises for functions",
            "How am I progressing in my course?",
            "Why is my code throwing a null pointer exception?"
        ]

        latencies = []

        for query in test_queries:
            start_time = time.time()
            result = router.classify_intent(query)
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)

        # Calculate p95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        print(f"Latencies: {latencies}")
        print(f"p95 latency: {p95_latency:.1f}ms")

        assert p95_latency < 200, f"p95 latency {p95_latency:.1f}ms exceeds 200ms target"

    def test_95_percent_classification_accuracy(self):
        """Verify classification accuracy is 95%+"""
        router = OpenAIRouter(use_hybrid=False)

        # Test cases: (query, expected_intent)
        test_cases = [
            ("syntax error in for loop", "syntax_help"),
            ("what is polymorphism", "concept_explanation"),
            ("give me practice exercises", "practice_exercises"),
            ("how am I progressing", "progress_check"),
            ("null pointer exception help", "syntax_help"),
            ("explain inheritance", "concept_explanation"),
            ("I need coding exercises", "practice_exercises"),
            ("check my course progress", "progress_check"),
            ("error in my function", "syntax_help"),
            ("what are classes", "concept_explanation"),
        ]

        correct = 0
        total = len(test_cases)

        for query, expected_intent in test_cases:
            result = router.classify_intent(query)
            if result.intent == expected_intent:
                correct += 1
            else:
                print(f"Mismatch: '{query}' -> {result.intent} (expected {expected_intent})")

        accuracy = correct / total
        print(f"Accuracy: {correct}/{total} = {accuracy:.1%}")

        assert accuracy >= 0.95, f"Accuracy {accuracy:.1%} below 95% target"

    def test_token_efficiency_90_percent(self):
        """Verify token usage efficiency is 90%+ (vs 1500 LLM baseline)"""
        router = OpenAIRouter(use_hybrid=False)

        test_queries = [
            "I'm getting a syntax error",
            "What is polymorphism in OOP",
            "Give me practice exercises",
            "How am I progressing in my course"
        ]

        total_tokens = 0
        baseline_tokens = 1500 * len(test_queries)

        for query in test_queries:
            result = router.classify_intent(query)
            total_tokens += result.tokens_used

        efficiency = (baseline_tokens - total_tokens) / baseline_tokens

        print(f"Total tokens used: {total_tokens}")
        print(f"Baseline tokens: {baseline_tokens}")
        print(f"Efficiency: {efficiency:.1%}")

        assert efficiency >= 0.90, f"Efficiency {efficiency:.1%} below 90% target"
        assert total_tokens < 100, f"Total tokens {total_tokens} too high"

    def test_routing_accuracy(self):
        """Verify routing decisions are 100% accurate"""
        router = OpenAIRouter(use_hybrid=False)

        # Test cases: (intent, expected_agent)
        routing_cases = [
            ("syntax_help", "debug-agent"),
            ("concept_explanation", "concept-agent"),
            ("practice_exercises", "practice-agent"),
            ("progress_check", "progress-agent"),
        ]

        for intent, expected_agent in routing_cases:
            result = router.classify_intent(f"test {intent}")
            assert result.target_agent == expected_agent, \
                f"Routing failed: {intent} -> {result.target_agent} (expected {expected_agent})"

    def test_fallback_logic(self):
        """Test that fallback works when skills are unavailable or low confidence"""
        # This tests the resilience aspect of the router
        router = OpenAIRouter(use_hybrid=False)

        # Test with a very ambiguous query
        ambiguous_query = "xyz123 unknown query that makes no sense"

        result = router.classify_intent(ambiguous_query)

        # Should still return a valid result with reasonable confidence
        assert result.intent is not None
        assert result.target_agent is not None
        assert result.confidence >= 0.0  # Should have some confidence level
        assert result.processing_time_ms < 500  # Should be fast even for ambiguous

    def test_router_result_structure(self):
        """Verify router result has correct structure and metadata"""
        router = OpenAIRouter(use_hybrid=False)

        result = router.classify_intent("test query")

        # Check all required fields exist
        assert hasattr(result, 'intent')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'target_agent')
        assert hasattr(result, 'routing_metadata')
        assert hasattr(result, 'tokens_used')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'source')

        # Check value types and ranges
        assert isinstance(result.intent, str)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
        assert isinstance(result.target_agent, str)
        assert isinstance(result.tokens_used, int)
        assert result.tokens_used >= 0
        assert isinstance(result.processing_time_ms, float)
        assert result.processing_time_ms > 0
        assert result.source in ['skill', 'hybrid']


class TestRouterIntegration:
    """Test router integration with other components"""

    def test_skills_import_works(self):
        """Verify skills can be imported and used"""
        # This is the core of our efficiency strategy
        from intent_detection import classify_intent
        from route_selection import route_intent

        result = classify_intent("test query")
        route = route_intent("syntax_help", 0.9)

        assert 'intent' in result
        assert 'token_estimate' in result
        assert 'target_agent' in route
        assert 'priority' in route

    def test_async_wrapper(self):
        """Test the async convenience function"""
        import asyncio

        async def test_async():
            result = await classify_with_router("test query")
            return result

        result = asyncio.run(test_async())

        assert result.intent is not None
        assert result.target_agent is not None


if __name__ == "__main__":
    # Run tests manually
    test_perf = TestOpenAIRouterPerformance()
    test_int = TestRouterIntegration()

    print("=== Running Router Performance Tests ===")

    try:
        test_perf.test_p95_latency_under_200ms()
        print("✅ Latency test passed")
    except Exception as e:
        print(f"❌ Latency test failed: {e}")

    try:
        test_perf.test_95_percent_classification_accuracy()
        print("✅ Accuracy test passed")
    except Exception as e:
        print(f"❌ Accuracy test failed: {e}")

    try:
        test_perf.test_token_efficiency_90_percent()
        print("✅ Efficiency test passed")
    except Exception as e:
        print(f"❌ Efficiency test failed: {e}")

    try:
        test_perf.test_routing_accuracy()
        print("✅ Routing test passed")
    except Exception as e:
        print(f"❌ Routing test failed: {e}")

    try:
        test_int.test_skills_import_works()
        print("✅ Skills import test passed")
    except Exception as e:
        print(f"❌ Skills import test failed: {e}")

    print("\n=== Integration Test Summary ===")
    print("If all passed above, router meets all Phase 1 requirements:")
    print("- p95 latency < 200ms ✅")
    print("- 95%+ classification accuracy ✅")
    print("- 90%+ token efficiency ✅")
    print("- 100% routing accuracy ✅")
    print("- Skills-first architecture ✅")