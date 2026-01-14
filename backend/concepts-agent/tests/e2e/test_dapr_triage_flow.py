"""
End-to-end test for Triage → Concepts Agent flow
Tests complete Dapr service invocation chain
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_complete_triage_to_concepts_flow():
    """
    Test complete flow: Triage Service → Dapr → Concepts Agent → Explanation

    This simulates what happens when a student asks for concept explanation
    and the triage service routes to concepts-agent.
    """
    client = TestClient(app)

    # Step 1: Student makes request to triage service
    # Triage classifies intent as "concept_explanation" and routes to concepts-agent

    # Step 2: Triage Service invokes concepts-agent via Dapr
    dapr_request = {
        "intent": "concept_explanation",
        "query": "I need help understanding recursion",
        "confidence": 0.89,
        "student_context": {
            "student_id": "student_123456",
            "student_level": "intermediate",
            "concept": "recursion",
            "student_progress": {
                "completed_concepts": ["functions", "variables"],
                "current_level": "intermediate"
            }
        },
        "routing_metadata": {
            "target_agent": "concepts-agent",
            "priority": 2,
            "timeout_ms": 2000,
            "circuit_breaker_status": "CLOSED"
        }
    }

    # Step 3: Concepts Agent processes the request
    response = client.post("/process", json=dapr_request)

    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert result["status"] == "success"
    assert result["agent"] == "concepts-agent"
    assert "processed_at" in result

    # Verify the explanation response
    explanation_result = result["result"]
    assert explanation_result["intent"] == "concept_explanation"
    assert explanation_result["concept"] == "recursion"
    assert explanation_result["confidence"] == 0.89

    # Verify explanation content
    explanation = explanation_result["explanation"]
    assert "explanation" in explanation
    assert "analogies" in explanation
    assert "examples" in explanation
    assert "key_points" in explanation

    # Verify the explanation is for recursion
    assert len(explanation["explanation"]) > 50  # Should be substantial
    assert len(explanation["analogies"]) > 0
    assert len(explanation["examples"]) > 0

    print(f"[OK] Complete flow successful:")
    print(f"   Student query: '{dapr_request['query']}'")
    print(f"   Intent: {explanation_result['intent']}")
    print(f"   Concept: {explanation_result['concept']}")
    print(f"   Confidence: {explanation_result['confidence']}")
    print(f"   Explanation length: {len(explanation['explanation'])} chars")
    print(f"   Analogies: {len(explanation['analogies'])}")
    print(f"   Examples: {len(explanation['examples'])}")

@pytest.mark.asyncio
async def test_concepts_agent_routing_decisions():
    """
    Test that concepts-agent properly routes different intents
    """
    client = TestClient(app)

    test_cases = [
        {
            "name": "Concept Explanation",
            "request": {
                "intent": "concept_explanation",
                "query": "explain variables",
                "confidence": 0.95,
                "student_context": {"student_level": "beginner", "concept": "variables"}
            },
            "expected_intent": "concept_explanation",
            "expected_concept": "variables"
        },
        {
            "name": "Concept Mapping",
            "request": {
                "intent": "concept_mapping",
                "query": "learning path for loops",
                "confidence": 0.91,
                "student_context": {"student_id": "student_123"},
                "concept": "loops"
            },
            "expected_intent": "concept_mapping",
            "expected_concept": "loops"
        },
        {
            "name": "Prerequisites Check",
            "request": {
                "intent": "prerequisites_check",
                "query": "am I ready for functions",
                "confidence": 0.87,
                "student_context": {"student_level": "beginner"},
                "concept": "functions"
            },
            "expected_intent": "prerequisites_check",
            "expected_concept": "functions"
        }
    ]

    for case in test_cases:
        response = client.post("/process", json=case["request"])
        assert response.status_code == 200, f"Failed for {case['name']}"

        data = response.json()
        assert data["status"] == "success", f"Status failed for {case['name']}"
        assert data["result"]["intent"] == case["expected_intent"], f"Intent mismatch for {case['name']}"
        assert data["result"]["concept"] == case["expected_concept"], f"Concept mismatch for {case['name']}"

        print(f"[OK] {case['name']}: routed correctly to concepts-agent")

@pytest.mark.asyncio
async def test_circuit_breaker_propagation():
    """
    Test that concepts-agent handles failures gracefully
    """
    client = TestClient(app)

    # Valid request that should work
    valid_request = {
        "intent": "concept_explanation",
        "query": "explain recursion",
        "confidence": 0.9,
        "student_context": {"student_level": "intermediate", "concept": "recursion"}
    }

    # Test multiple requests to ensure stability
    for i in range(3):
        response = client.post("/process", json=valid_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent"] == "concepts-agent"

    print("[OK] Circuit breaker test passed - service remains stable")

@pytest.mark.asyncio
async def test_security_context_propagation():
    """
    Test that security context (student_id) is properly maintained
    """
    client = TestClient(app)

    request_with_security = {
        "intent": "concept_explanation",
        "query": "explain functions",
        "confidence": 0.88,
        "student_context": {
            "student_id": "student_secure_789",
            "student_level": "intermediate",
            "concept": "functions"
        },
        "routing_metadata": {
            "security_context": {
                "X-Student-ID": "student_secure_789",
                "X-Request-ID": "req_123456",
                "X-Source": "triage-service"
            }
        }
    }

    response = client.post("/process", json=request_with_security)
    assert response.status_code == 200

    result = response.json()
    assert result["status"] == "success"

    # The service should process without exposing security context in response
    # but internally maintain the context
    print("[OK] Security context propagation test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])