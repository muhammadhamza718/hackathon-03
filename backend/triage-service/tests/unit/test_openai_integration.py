"""
Unit Tests: OpenAI Integration & Skills Router
Elite Implementation Standard v2.0.0

Tests OpenAI SDK wrapper, skills-first routing, and token efficiency.
"""

import sys
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.openai_router import OpenAIRouter, RouterConfig
from models.schemas import TriageRequest, RoutingDecision


class TestOpenAIRouterConfig:
    """Test RouterConfig validation"""

    def test_config_creation(self):
        """Test router config creation"""
        config = RouterConfig(
            model="gpt-4o-mini",
            max_tokens=150,
            temperature=0.1,
            timeout=2.0,
            skills_first=True,
            efficiency_target=0.98
        )

        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 150
        assert config.temperature == 0.1
        assert config.timeout == 2.0
        assert config.skills_first is True
        assert config.efficiency_target == 0.98

    def test_config_defaults(self):
        """Test config with defaults"""
        config = RouterConfig()

        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 150
        assert config.temperature == 0.1
        assert config.timeout == 2.0
        assert config.skills_first is True


class TestOpenAIRouterInitialization:
    """Test OpenAIRouter initialization"""

    def test_router_creation_with_config(self):
        """Test router creation with custom config"""
        config = RouterConfig(
            model="gpt-4",
            max_tokens=200,
            skills_first=True
        )

        router = OpenAIRouter(config)

        assert router.config.model == "gpt-4"
        assert router.config.max_tokens == 200
        assert router.skills_first is True

    def test_router_creation_default(self):
        """Test router creation with defaults"""
        router = OpenAIRouter()

        assert router.config.model == "gpt-4o-mini"
        assert router.skills_first is True
        assert router.client is not None

    def test_skills_library_path(self):
        """Test skills library path resolution"""
        router = OpenAIRouter()

        # Should find skills library
        skills_path = router.skills_path
        assert skills_path is not None
        assert skills_path.exists()

        # Should contain expected skill files
        intent_file = skills_path / "intent-detection.py"
        route_file = skills_path / "route-selection.py"

        assert intent_file.exists()
        assert route_file.exists()


class TestSkillsClassification:
    """Test skills-based intent classification"""

    def test_classify_intent_syntax_help(self):
        """Test syntax help intent classification"""
        router = OpenAIRouter()

        queries = [
            "I'm getting a syntax error",
            "help with my code error",
            "why is this line failing"
        ]

        for query in queries:
            result = router.classify_intent(query)
            assert result["intent"] == "syntax_help"
            assert result["confidence"] >= 0.5
            assert result["token_estimate"] < 50

    def test_classify_intent_concept_explanation(self):
        """Test concept explanation intent classification"""
        router = OpenAIRouter()

        queries = [
            "what is polymorphism",
            "explain inheritance",
            "how does async work"
        ]

        for query in queries:
            result = router.classify_intent(query)
            assert result["intent"] == "concept_explanation"
            assert result["confidence"] >= 0.5
            assert result["token_estimate"] < 50

    def test_classify_intent_practice_exercises(self):
        """Test practice exercises intent classification"""
        router = OpenAIRouter()

        queries = [
            "give me exercises",
            "practice problems",
            "coding challenges"
        ]

        for query in queries:
            result = router.classify_intent(query)
            assert result["intent"] == "practice_exercises"
            assert result["confidence"] >= 0.5
            assert result["token_estimate"] < 50

    def test_classify_intent_progress_check(self):
        """Test progress check intent classification"""
        router = OpenAIRouter()

        queries = [
            "how am I doing",
            "progress report",
            "course completion"
        ]

        for query in queries:
            result = router.classify_intent(query)
            assert result["intent"] == "progress_check"
            assert result["confidence"] >= 0.5
            assert result["token_estimate"] < 50

    def test_classify_intent_ambiguous_fallback(self):
        """Test ambiguous query handling"""
        router = OpenAIRouter()

        ambiguous_queries = ["hello", "thanks", "okay", "interesting"]

        for query in ambiguous_queries:
            result = router.classify_intent(query)
            # Should return something, even if low confidence
            assert "intent" in result
            assert "token_estimate" in result


class TestSkillsRouting:
    """Test skills-based routing"""

    def test_route_selection(self):
        """Test route selection for all intents"""
        router = OpenAIRouter()

        intent_map = {
            "syntax_help": "debug-agent",
            "concept_explanation": "concepts-agent",
            "practice_exercises": "exercise-agent",
            "progress_check": "progress-agent"
        }

        for intent, expected_agent in intent_map.items():
            result = router.route_selection(intent, 0.9, "student-12345")
            assert result["target_agent"] == expected_agent
            assert result["priority"] is not None

    def test_route_selection_low_confidence(self):
        """Test routing with low confidence"""
        router = OpenAIRouter()

        result = router.route_selection("syntax_help", 0.1, "student-12345")
        # Low confidence should route to review agent
        if "target_agent" in result:
            assert result["target_agent"] == "review-agent"

    def test_route_selection_invalid_intent(self):
        """Test routing with unknown intent"""
        router = OpenAIRouter()

        result = router.route_selection("unknown_intent", 0.9, "student-12345")
        # Should handle gracefully
        assert "error" in result or "target_agent" in result


class TestTokenEfficiency:
    """Test token efficiency metrics"""

    def test_token_estimates(self):
        """Test token estimates are accurate"""
        router = OpenAIRouter()

        test_queries = [
            ("syntax error", "syntax_help"),
            ("explain concept", "concept_explanation"),
            ("practice code", "practice_exercises"),
            ("progress check", "progress_check")
        ]

        total_tokens = 0
        for query, expected_intent in test_queries:
            result = router.classify_intent(query)
            assert result["intent"] == expected_intent
            total_tokens += result["token_estimate"]

        # Should be <100 total tokens for 4 queries
        assert total_tokens < 100

    def test_efficiency_vs_baseline(self):
        """Test efficiency improvement vs LLM baseline"""
        router = OpenAIRouter()

        test_queries = [
            "syntax error",
            "explain concept",
            "practice code",
            "progress check"
        ]

        total_tokens = 0
        for query in test_queries:
            result = router.classify_intent(query)
            total_tokens += result["token_estimate"]

        # Baseline: 1500 tokens per query
        baseline = 1500 * len(test_queries)
        efficiency = (baseline - total_tokens) / baseline

        assert efficiency >= 0.90  # 90% efficiency target
        assert total_tokens < 100  # Absolute token limit

    def test_skills_first_efficiency(self):
        """Test skills-first approach efficiency"""
        config = RouterConfig(skills_first=True)
        router = OpenAIRouter(config)

        start_time = time.time()
        for _ in range(10):
            router.classify_intent("test query")
        duration = time.time() - start_time

        # Should be very fast (<100ms for 10 calls)
        assert duration < 0.1


class TestPerformanceBenchmark:
    """Test router performance benchmarks"""

    def test_classification_speed(self):
        """Test classification is fast"""
        router = OpenAIRouter()

        queries = [
            "syntax error in for loop",
            "what is polymorphism",
            "give me practice exercises",
            "how am I progressing"
        ]

        start_time = time.time()
        for query in queries:
            result = router.classify_intent(query)
            assert result is not None
        total_time = (time.time() - start_time) * 1000

        # Should complete in <100ms for all queries
        assert total_time < 100

    def test_routing_speed(self):
        """Test routing is fast"""
        router = OpenAIRouter()

        start_time = time.time()
        for _ in range(20):
            result = router.route_selection("syntax_help", 0.9, "student-12345")
            assert result is not None
        total_time = (time.time() - start_time) * 1000

        # Should complete in <50ms for 20 calls
        assert total_time < 50

    def test_memory_usage(self):
        """Test router memory efficiency"""
        import sys

        router = OpenAIRouter()

        # Create multiple request objects
        results = []
        for i in range(50):
            result = router.classify_intent(f"query {i}")
            results.append(result)

        # Estimate memory
        total_size = sum(sys.getsizeof(r) for r in results)
        avg_size = total_size / len(results)

        # Each result should be <500 bytes
        assert avg_size < 500


class TestIntegrationCompatibility:
    """Test compatibility with integration layer"""

    def test_enriched_metadata_structure(self):
        """Test router provides integration-compatible metadata"""
        router = OpenAIRouter()

        # Mock a full routing flow
        intent_result = router.classify_intent("syntax error in for loop")
        route_result = router.route_selection(
            intent_result["intent"],
            intent_result["confidence"],
            "student-12345"
        )

        # Should have all required fields for integration
        assert "target_agent" in route_result
        assert "priority" in route_result
        assert "intent" in intent_result
        assert "confidence" in intent_result
        assert "token_estimate" in intent_result

    def test_routing_decision_format(self):
        """Test routing decision matches expected format"""
        router = OpenAIRouter()

        result = router.route_selection("syntax_help", 0.95, "student-12345")

        # Should have expected structure
        assert isinstance(result, dict)
        assert result["target_agent"] == "debug-agent"
        assert result["priority"] == 1  # Highest priority for syntax issues
        assert result["confidence"] == 0.95
        assert result["intent"] == "syntax_help"


class TestErrorHandling:
    """Test error handling in router"""

    @patch('services.openai_router.importlib.util.spec_from_file_location')
    def test_skills_library_failure(self, mock_spec):
        """Test graceful handling of missing skills library"""
        mock_spec.return_value = None

        router = OpenAIRouter()

        # Should fall back gracefully
        result = router.classify_intent("test query")
        # Should still return a valid structure
        assert "intent" in result
        assert "token_estimate" in result

    def test_invalid_student_id(self):
        """Test handling of invalid student IDs"""
        router = OpenAIRouter()

        # Should handle invalid formats
        result = router.route_selection("syntax_help", 0.9, "invalid_id")
        # Should not crash
        assert isinstance(result, dict)


if __name__ == "__main__":
    print("=== Running Unit Tests: OpenAI Integration ===")
    pytest.main([__file__, "-v"])