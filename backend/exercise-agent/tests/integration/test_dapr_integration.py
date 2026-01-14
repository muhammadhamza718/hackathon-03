"""
Integration tests for Dapr service invocation
Exercise Agent
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from fastapi.testclient import TestClient

def test_dapr_process_practice_exercises():
    """Test Dapr service invocation for practice exercises"""
    client = TestClient(app)

    # Simulate what Triage Service would send via Dapr
    request_data = {
        "intent": "practice_exercises",
        "query": "I need practice with loops and functions",
        "confidence": 0.95,
        "student_context": {
            "student_id": "student_123456",
            "topic": "loops",
            "student_level": "intermediate",
            "difficulty": "auto",
            "mastery": 0.6,
            "success_rate": 0.7
        },
        "routing_metadata": {
            "priority": 3,
            "timeout_ms": 2000
        }
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "exercise-agent"
    assert "result" in data
    assert data["result"]["intent"] == "practice_exercises"
    assert data["result"]["topic"] == "loops"
    assert "problem" in data["result"]
    assert "difficulty" in data["result"]

    # Verify the problem structure
    problem = data["result"]["problem"]
    assert "description" in problem
    assert "hints" in problem
    assert "test_cases" in problem

def test_dapr_process_difficulty_calibration():
    """Test Dapr service invocation for difficulty calibration"""
    client = TestClient(app)

    request_data = {
        "intent": "difficulty_calibration",
        "query": "what difficulty should I try for functions",
        "confidence": 0.88,
        "student_context": {
            "student_id": "student_789",
            "mastery": 0.75,
            "success_rate": 0.82
        }
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "exercise-agent"
    assert data["result"]["intent"] == "difficulty_calibration"
    assert data["result"]["difficulty"] in ["beginner", "intermediate", "advanced"]
    assert "mastery" in data["result"]
    assert "success_rate" in data["result"]

def test_dapr_process_unknown_intent():
    """Test Dapr service invocation with unknown intent"""
    client = TestClient(app)

    request_data = {
        "intent": "unknown_intent",
        "query": "some query",
        "confidence": 0.5,
        "student_context": {}
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "error" in data
    assert "supported_intents" in data

def test_dapr_process_with_auto_difficulty():
    """Test Dapr service with auto difficulty calibration"""
    client = TestClient(app)

    request_data = {
        "intent": "practice_exercises",
        "query": "practice arrays",
        "confidence": 0.9,
        "student_context": {
            "student_id": "student_auto",
            "topic": "arrays",
            "student_level": "beginner",
            "difficulty": "auto"
        }
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "difficulty" in data["result"]

def test_dapr_security_context_propagation():
    """Test that Dapr handles security context properly"""
    client = TestClient(app)

    request_data = {
        "intent": "practice_exercises",
        "query": "loops practice",
        "confidence": 0.85,
        "student_context": {
            "student_id": "student_secure_123",
            "topic": "loops",
            "student_level": "intermediate"
        },
        "routing_metadata": {
            "security_context": {
                "X-Student-ID": "student_secure_123",
                "X-Request-ID": "req_789012",
                "X-Source": "triage-service"
            }
        }
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_dapr_error_handling():
    """Test Dapr service handles errors gracefully"""
    client = TestClient(app)

    # Test with completely malformed data
    request_data = {
        # Missing everything - should be handled gracefully
    }

    response = client.post("/process", json=request_data)

    # Should return error but not crash
    assert response.status_code == 200
    data = response.json()
    assert "error" in data

    # Test with valid intent but missing context
    request_data2 = {
        "intent": "practice_exercises"
        # Missing student_context
    }

    response2 = client.post("/process", json=request_data2)
    assert response2.status_code == 200
    data2 = response2.json()
    # May succeed with defaults or return error
    assert "status" in data2

if __name__ == "__main__":
    pytest.main([__file__])