"""
End-to-end test for Triage → Exercise Agent flow
Tests complete Dapr service invocation chain
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_complete_triage_to_exercise_flow():
    """
    Test complete flow: Triage Service → Dapr → Exercise Agent → Problem

    This simulates what happens when a student asks for practice exercises
    and the triage service routes to exercise-agent.
    """
    client = TestClient(app)

    # Step 1: Student makes request to triage service
    # Triage classifies intent as "practice_exercises" and routes to exercise-agent

    # Step 2: Triage Service invokes exercise-agent via Dapr
    dapr_request = {
        "intent": "practice_exercises",
        "query": "I need practice with arrays and loops",
        "confidence": 0.89,
        "student_context": {
            "student_id": "student_123456",
            "student_level": "intermediate",
            "topic": "arrays",
            "difficulty": "auto",
            "mastery": 0.65,
            "success_rate": 0.72,
            "student_progress": {
                "completed_concepts": ["variables", "conditionals", "loops"],
                "current_level": "intermediate"
            }
        },
        "routing_metadata": {
            "target_agent": "exercise-agent",
            "priority": 3,
            "timeout_ms": 2000,
            "circuit_breaker_status": "CLOSED"
        }
    }

    # Step 3: Exercise Agent processes the request
    response = client.post("/process", json=dapr_request)

    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert result["status"] == "success"
    assert result["agent"] == "exercise-agent"
    assert "processed_at" in result

    # Verify the exercise response
    exercise_result = result["result"]
    assert exercise_result["intent"] == "practice_exercises"
    assert exercise_result["topic"] == "arrays"
    assert exercise_result["confidence"] == 0.89

    # Verify the generated exercise
    problem = exercise_result["problem"]
    assert "description" in problem
    assert "hints" in problem
    assert "test_cases" in problem
    assert "estimated_time" in problem

    # Verify the exercise is adaptive (difficulty should be intermediate based on mastery)
    assert exercise_result["difficulty"] in ["beginner", "intermediate"]  # Auto-calibrated

    print(f"[OK] Complete flow successful:")
    print(f"   Student query: '{dapr_request['query']}'")
    print(f"   Intent: {exercise_result['intent']}")
    print(f"   Topic: {exercise_result['topic']}")
    print(f"   Difficulty: {exercise_result['difficulty']}")
    print(f"   Problem: {len(problem['description'])} chars")
    print(f"   Hints: {len(problem['hints'])}")
    print(f"   Test cases: {len(problem['test_cases'])}")

@pytest.mark.asyncio
async def test_exercise_agent_routing_decisions():
    """
    Test that exercise-agent properly routes different intents
    """
    client = TestClient(app)

    test_cases = [
        {
            "name": "Practice Exercises",
            "request": {
                "intent": "practice_exercises",
                "query": "need loops practice",
                "confidence": 0.95,
                "student_context": {"topic": "loops", "student_level": "beginner", "difficulty": "auto"}
            },
            "expected_intent": "practice_exercises",
            "expected_topic": "loops"
        },
        {
            "name": "Difficulty Calibration",
            "request": {
                "intent": "difficulty_calibration",
                "query": "what level should I try",
                "confidence": 0.91,
                "student_context": {"mastery": 0.8, "success_rate": 0.85}
            },
            "expected_intent": "difficulty_calibration",
            "expected_difficulty": "advanced"  # Should be advanced based on high scores
        }
    ]

    for case in test_cases:
        response = client.post("/process", json=case["request"])
        assert response.status_code == 200, f"Failed for {case['name']}"

        data = response.json()
        assert data["status"] == "success", f"Status failed for {case['name']}"
        assert data["result"]["intent"] == case["expected_intent"], f"Intent mismatch for {case['name']}"

        if "expected_topic" in case:
            assert data["result"]["topic"] == case["expected_topic"], f"Topic mismatch for {case['name']}"
        if "expected_difficulty" in case:
            assert data["result"]["difficulty"] == case["expected_difficulty"], f"Difficulty mismatch for {case['name']}"

        print(f"[OK] {case['name']}: routed correctly to exercise-agent")

@pytest.mark.asyncio
async def test_adaptive_difficulty_calibration():
    """
    Test that exercise-agent calibrates difficulty adaptively
    """
    client = TestClient(app)

    # Test student with different performance levels
    profiles = [
        {
            "name": "Low performer",
            "mastery": 0.3,
            "success_rate": 0.4,
            "expected": "beginner"
        },
        {
            "name": "Medium performer",
            "mastery": 0.6,
            "success_rate": 0.7,
            "expected": "intermediate"
        },
        {
            "name": "High performer",
            "mastery": 0.85,
            "success_rate": 0.9,
            "expected": "advanced"
        }
    ]

    for profile in profiles:
        request = {
            "intent": "difficulty_calibration",
            "query": "difficulty assessment",
            "confidence": 0.9,
            "student_context": {
                "mastery": profile["mastery"],
                "success_rate": profile["success_rate"]
            }
        }

        response = client.post("/process", json=request)
        assert response.status_code == 200

        data = response.json()
        difficulty = data["result"]["difficulty"]

        assert difficulty == profile["expected"], f"Expected {profile['expected']} but got {difficulty} for {profile['name']}"
        print(f"[OK] {profile['name']}: correctly calibrated to {difficulty}")

@pytest.mark.asyncio
async def test_batch_problem_scenarios():
    """
    Test multiple problem generation scenarios in sequence
    """
    client = TestClient(app)

    scenarios = [
        {
            "topic": "loops",
            "difficulty": "beginner",
            "description": "Basic loop practice"
        },
        {
            "topic": "functions",
            "difficulty": "intermediate",
            "description": "Function complexity"
        },
        {
            "topic": "arrays",
            "difficulty": "beginner",
            "description": "Array fundamentals"
        }
    ]

    for scenario in scenarios:
        request = {
            "intent": "practice_exercises",
            "query": f"Practice {scenario['topic']}",
            "confidence": 0.9,
            "student_context": {
                "topic": scenario["topic"],
                "difficulty": scenario["difficulty"],
                "student_level": scenario["difficulty"]
            }
        }

        response = client.post("/process", json=request)
        assert response.status_code == 200

        data = response.json()
        problem = data["result"]["problem"]

        assert "description" in problem
        assert "hints" in problem
        assert len(problem["hints"]) > 0

        print(f"[OK] {scenario['description']}: Generated problem with {len(problem['hints'])} hints")

@pytest.mark.asyncio
async def test_performance_based_learning_path():
    """
    Test that exercise-agent suggests appropriate next steps based on performance
    """
    client = TestClient(app)

    # Student who just completed loops successfully
    request = {
        "intent": "practice_exercises",
        "query": "ready for next challenge",
        "confidence": 0.95,
        "student_context": {
            "student_id": "advancing_student",
            "topic": "functions",
            "difficulty": "auto",
            "mastery": 0.75,  # High mastery suggests readiness for challenge
            "success_rate": 0.85,
            "student_level": "intermediate"
        }
    }

    response = client.post("/process", json=request)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"

    # Should get intermediate or advanced difficulty based on high mastery
    difficulty = data["result"]["difficulty"]
    problem = data["result"]["problem"]

    assert difficulty in ["intermediate", "advanced"]
    assert len(problem["description"]) > 0  # Has a problem

    print(f"[OK] Advanced student: Got {difficulty} difficulty problem")
    print(f"   Problem: {problem['description'][:60]}...")

@pytest.mark.asyncio
async def test_error_recovery_and_fallbacks():
    """
    Test that exercise-agent handles various error conditions gracefully
    """
    client = TestClient(app)

    # Test with incomplete context
    minimal_request = {
        "intent": "practice_exercises",
        "confidence": 0.8
        # Missing most context fields
    }

    response = client.post("/process", json=minimal_request)
    assert response.status_code == 200  # Should not crash
    data = response.json()

    # Should provide some response, even if basic
    assert "status" in data
    print(f"[OK] Minimal context: Handled gracefully")

    # Test with unknown topic
    unknown_topic_request = {
        "intent": "practice_exercises",
        "query": "practice quantum physics",
        "confidence": 0.7,
        "student_context": {
            "topic": "quantum_physics",
            "difficulty": "beginner"
        }
    }

    response = client.post("/process", json=unknown_topic_request)
    assert response.status_code == 200
    data = response.json()

    # Should fallback to generic problem
    assert data["status"] == "success"
    print(f"[OK] Unknown topic: Fallback to generic problem")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])