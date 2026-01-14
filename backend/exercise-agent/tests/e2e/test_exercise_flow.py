"""
End-to-end tests for Exercise Agent flow
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import app
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_exercise_api_endpoints():
    """Test Exercise Agent API endpoints"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Test readiness
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

@pytest.mark.asyncio
async def test_problem_generation_flow():
    """Test problem generation through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test problem generation
    response = client.post("/generate/", json={
        "topic": "loops",
        "difficulty": "beginner",
        "context": {},
        "student_level": "beginner"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "loops"
    assert data["difficulty"] == "beginner"
    assert "problem" in data
    assert "hints" in data
    assert "test_cases" in data
    assert isinstance(data["hints"], list)
    assert isinstance(data["test_cases"], list)

@pytest.mark.asyncio
async def test_difficulty_calibration_flow():
    """Test difficulty calibration through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test difficulty calibration
    response = client.post("/calibrate/", json={
        "student_id": "test_student",
        "concept": "loops",
        "recent_performance": [0.6, 0.7, 0.8, 0.75],
        "student_history": {}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "test_student"
    assert data["concept"] == "loops"
    assert "recommended_difficulty" in data
    assert "confidence" in data
    assert "estimated_mastery" in data
    assert data["estimated_mastery"] > 0.6  # Based on recent performance

@pytest.mark.asyncio
async def test_batch_problem_generation():
    """Test batch generation of multiple problems"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test batch generation
    response = client.post("/generate/batch", json=[
        {"topic": "loops", "difficulty": "beginner", "context": {}},
        {"topic": "functions", "difficulty": "intermediate", "context": {}},
        {"topic": "arrays", "difficulty": "beginner", "context": {}}
    ])

    assert response.status_code == 200
    data = response.json()
    assert "problems" in data
    assert len(data["problems"]) == 3

    # Check each problem
    for problem in data["problems"]:
        if problem["status"] == "success":
            assert "problem" in problem
            assert "hints" in problem
            assert "test_cases" in problem

@pytest.mark.asyncio
async def test_dapr_process_endpoint():
    """Test Dapr service invocation handler"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test practice exercises intent
    dapr_request = {
        "intent": "practice_exercises",
        "query": "I need practice with loops",
        "confidence": 0.9,
        "student_context": {
            "student_id": "student_123",
            "topic": "loops",
            "student_level": "intermediate",
            "difficulty": "auto"
        }
    }

    response = client.post("/process", json=dapr_request)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["agent"] == "exercise-agent"
    assert "result" in data
    assert data["result"]["intent"] == "practice_exercises"
    assert "problem" in data["result"]

@pytest.mark.asyncio
async def test_difficulty_calibration_intent():
    """Test Dapr difficulty calibration intent"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test difficulty calibration intent
    dapr_request = {
        "intent": "difficulty_calibration",
        "query": "what difficulty should I try",
        "confidence": 0.85,
        "student_context": {
            "student_id": "student_456",
            "mastery": 0.7,
            "success_rate": 0.8
        }
    }

    response = client.post("/process", json=dapr_request)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["intent"] == "difficulty_calibration"
    assert data["result"]["difficulty"] in ["beginner", "intermediate", "advanced"]

@pytest.mark.asyncio
async def test_visual_problem_generation():
    """Test visual problem generation endpoint"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post("/generate/with-visual", json={
        "topic": "functions",
        "difficulty": "intermediate",
        "context": {}
    })

    assert response.status_code == 200
    data = response.json()
    assert "problem" in data
    assert "visual_elements" in data
    assert data["visual_elements"]["diagram_type"] == "flowchart"

@pytest.mark.asyncio
async def test_available_topics():
    """Test getting available topics"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/generate/topics")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert isinstance(data["topics"], list)
    assert "loops" in data["topics"]
    assert "functions" in data["topics"]

if __name__ == "__main__":
    pytest.main([__file__])