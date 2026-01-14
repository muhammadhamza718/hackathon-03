"""
Integration tests for Dapr service invocation
Concepts Agent
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from fastapi.testclient import TestClient

def test_dapr_process_concept_explanation():
    """Test Dapr service invocation for concept explanation"""
    client = TestClient(app)

    # Simulate what Triage Service would send via Dapr
    request_data = {
        "intent": "concept_explanation",
        "query": "explain loops",
        "confidence": 0.95,
        "student_context": {
            "student_id": "student_123456",
            "student_level": "beginner",
            "concept": "loops"
        },
        "routing_metadata": {
            "priority": 2,
            "timeout_ms": 2000
        }
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "concepts-agent"
    assert "result" in data
    assert data["result"]["intent"] == "concept_explanation"
    assert data["result"]["concept"] == "loops"
    assert "explanation" in data["result"]

    # Verify explanation structure
    explanation = data["result"]["explanation"]
    assert "explanation" in explanation
    assert "analogies" in explanation
    assert "examples" in explanation

def test_dapr_process_concept_mapping():
    """Test Dapr service invocation for concept mapping"""
    client = TestClient(app)

    request_data = {
        "intent": "concept_mapping",
        "query": "loops learning path",
        "confidence": 0.88,
        "student_context": {
            "student_id": "student_123456"
        },
        "concept": "loops"
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "concepts-agent"
    assert "result" in data
    assert data["result"]["intent"] == "concept_mapping"
    assert data["result"]["concept"] == "loops"
    assert "prerequisites" in data["result"]
    assert "learning_path" in data["result"]

def test_dapr_process_prerequisites_check():
    """Test Dapr service invocation for prerequisites check"""
    client = TestClient(app)

    request_data = {
        "intent": "prerequisites_check",
        "query": "do I know enough for loops",
        "confidence": 0.92,
        "student_context": {
            "student_id": "student_123456",
            "student_level": "beginner"
        },
        "concept": "loops"
    }

    response = client.post("/process", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "concepts-agent"
    assert "result" in data
    assert data["result"]["intent"] == "prerequisites_check"
    assert data["result"]["concept"] == "loops"
    assert "readiness" in data["result"]

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

def test_dapr_process_missing_fields():
    """Test Dapr service invocation with missing required fields"""
    client = TestClient(app)

    # Send minimal data
    request_data = {
        "intent": "concept_explanation"
        # Missing: query, student_context, etc.
    }

    response = client.post("/process", json=request_data)

    # Should still handle gracefully
    assert response.status_code == 200
    data = response.json()
    # May succeed with defaults or handle missing data
    assert "status" in data

if __name__ == "__main__":
    pytest.main([__file__])