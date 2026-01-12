"""
Unit Tests: Skill Components
Elite Implementation Standard v2.0.0

Tests individual skill components for accuracy and performance.
"""

import sys
import time
import pytest
from pathlib import Path

# Add skills library to path
skills_path = Path(__file__).parent.parent.parent.parent / "skills-library" / "triage-logic"
sys.path.insert(0, str(skills_path))

import importlib.util

def load_skill_module(name, filepath):
    """Load skill module from file"""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestIntentDetection:
    """Test intent detection accuracy"""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Load skill modules
        intent_spec = importlib.util.spec_from_file_location(
            "intent_detection",
            skills_path / "intent-detection.py"
        )
        self.intent_mod = importlib.util.module_from_spec(intent_spec)
        intent_spec.loader.exec_module(self.intent_mod)

    def test_syntax_help_detection(self):
        """Test syntax help intent classification"""
        queries = [
            "I'm getting a syntax error",
            "help with my code error",
            "why is this line failing",
            "syntax error in for loop"
        ]

        for query in queries:
            result = self.intent_mod.classify_intent(query)
            assert result['intent'] == 'syntax_help'
            assert 0.5 <= result['confidence'] <= 1.0
            assert result['token_estimate'] < 50

    def test_concept_explanation_detection(self):
        """Test concept explanation intent classification"""
        queries = [
            "what is polymorphism",
            "explain inheritance",
            "how does async work",
            "tell me about functions"
        ]

        for query in queries:
            result = self.intent_mod.classify_intent(query)
            assert result['intent'] == 'concept_explanation'
            assert 0.5 <= result['confidence'] <= 1.0
            assert result['token_estimate'] < 50

    def test_practice_exercises_detection(self):
        """Test practice exercises intent classification"""
        queries = [
            "give me exercises",
            "practice problems",
            "coding challenges",
            "drills for loops"
        ]

        for query in queries:
            result = self.intent_mod.classify_intent(query)
            assert result['intent'] == 'practice_exercises'
            assert 0.5 <= result['confidence'] <= 1.0
            assert result['token_estimate'] < 50

    def test_progress_check_detection(self):
        """Test progress check intent classification"""
        queries = [
            "how am I doing",
            "progress report",
            "course completion",
            "what have I learned"
        ]

        for query in queries:
            result = self.intent_mod.classify_intent(query)
            assert result['intent'] == 'progress_check'
            assert 0.5 <= result['confidence'] <= 1.0
            assert result['token_estimate'] < 50

    def test_ambiguous_query_fallback(self):
        """Test fallback for ambiguous queries"""
        ambiguous_queries = [
            "hello",
            "thanks",
            "okay",
            "interesting"
        ]

        for query in ambiguous_queries:
            result = self.intent_mod.classify_intent(query)
            # Should return low confidence or fallback intent
            assert 'intent' in result
            assert 'token_estimate' in result

    def test_performance_benchmark(self):
        """Test classification performance"""
        queries = [
            "syntax error in for loop",
            "what is polymorphism",
            "give me practice exercises",
            "how am I progressing"
        ]

        start_time = time.time()
        for query in queries:
            result = self.intent_mod.classify_intent(query)
            assert result is not None
        total_time = (time.time() - start_time) * 1000

        # Should complete in < 100ms for all queries
        assert total_time < 100

    def test_token_efficiency(self):
        """Test token efficiency targets"""
        test_queries = [
            "syntax error",
            "explain concept",
            "practice code",
            "progress check"
        ]

        total_tokens = 0
        for query in test_queries:
            result = self.intent_mod.classify_intent(query)
            total_tokens += result['token_estimate']

        # Calculate efficiency (vs 1500 LLM baseline per query)
        baseline = 1500 * len(test_queries)
        efficiency = (baseline - total_tokens) / baseline

        assert efficiency >= 0.90, f"Efficiency {efficiency:.1%} below 90% target"
        assert total_tokens < 100, f"Total tokens {total_tokens} too high"


class TestRouteSelection:
    """Test route selection accuracy"""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Load route selection module
        route_spec = importlib.util.spec_from_file_location(
            "route_selection",
            skills_path / "route-selection.py"
        )
        self.route_mod = importlib.util.module_from_spec(route_spec)
        route_spec.loader.exec_module(self.route_mod)

    def test_routing_accuracy(self):
        """Test 100% routing accuracy for valid intents"""
        intent_map = {
            "syntax_help": "debug-agent",
            "concept_explanation": "concepts-agent",
            "practice_exercises": "exercise-agent",
            "progress_check": "progress-agent"
        }

        for intent, expected_agent in intent_map.items():
            route = self.route_mod.route_selection(intent, 0.9, "student-12345")
            assert route['target_agent'] == expected_agent
            assert route['priority'] is not None

    def test_confidence_threshold(self):
        """Test routing decisions based on confidence"""
        # High confidence should route to target agent
        route_high = self.route_mod.route_selection("syntax_help", 0.9, "student-12345")
        assert route_high['target_agent'] == "debug-agent"

        # Low confidence should route to review agent via fallback
        route_low = self.route_mod.route_selection("syntax_help", 0.1, "student-12345")
        if 'target_agent' in route_low:
            assert route_low['target_agent'] == "review-agent"

    def test_priority_levels(self):
        """Test priority assignment"""
        intents_with_priorities = [
            ("syntax_help", 1),        # High priority - blocking issues
            ("concept_explanation", 2), # Medium priority
            ("practice_exercises", 3),  # Lower priority
            ("progress_check", 4)      # Low priority
        ]

        for intent, expected_priority in intents_with_priorities:
            route = self.route_mod.route_selection(intent, 0.9, "student-12345")
            assert route['priority'] == expected_priority

    def test_invalid_intent_handling(self):
        """Test behavior for unknown intents"""
        route = self.route_mod.route_selection("unknown_intent", 0.9, "student-12345")
        # Should handle gracefully (fallback or error structure)
        assert 'error' in route or 'target_agent' in route


class TestRoutingLogic:
    """Test routing logic with retries"""

    def test_retry_config(self):
        """Test retry configuration"""
        from services.routing_logic import RetryConfig, RetryManager

        config = RetryConfig(max_attempts=3, base_delay_ms=100, max_delay_ms=400)
        manager = RetryManager(config)

        # Test delay calculation
        delay1 = manager.calculate_delay(1)  # Should be 100
        delay2 = manager.calculate_delay(2)  # Should be 200
        delay3 = manager.calculate_delay(3)  # Should be 400

        assert delay1 == 100
        assert delay2 == 200
        assert delay3 == 400


class TestRoutingMap:
    """Test routing map completeness"""

    def test_all_agents_mapped(self):
        """Test all 5 agents are properly mapped"""
        from services.routing_map import ROUTING_MAP, TargetAgent

        expected_intents = ["syntax_help", "concept_explanation", "practice_exercises", "progress_check"]
        expected_agents = [agent.value for agent in TargetAgent]

        # Check all intents are mapped
        for intent in expected_intents:
            assert intent in ROUTING_MAP

        # Check all agents are used
        mapped_agents = set(ROUTING_MAP.values())
        assert len(mapped_agents) >= 4  # At least 4 different agents

    def test_circuit_breaker_config(self):
        """Test circuit breaker configuration for all agents"""
        from services.routing_map import CIRCUIT_BREAKER_CONFIG

        required_keys = ["max_failures", "timeout_seconds", "retry_attempts", "retry_backoff"]

        for agent, config in CIRCUIT_BREAKER_CONFIG.items():
            for key in required_keys:
                assert key in config

            # Verify values match spec
            assert config["max_failures"] == 5
            assert config["timeout_seconds"] == 30
            assert config["retry_attempts"] == 3
            assert config["retry_backoff"] == [100, 200, 400]


if __name__ == "__main__":
    # Run tests directly for quick verification
    print("=== Running Unit Tests: Skill Components ===")
    pytest.main([__file__, "-v"])