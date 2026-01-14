"""
End-to-end tests for Progress Agent
"""

import pytest
import sys
import os
import httpx
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

@pytest.mark.asyncio
async def test_api_endpoints():
    """Test API endpoints availability"""
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
async def test_mastery_endpoint_flow():
    """Test mastery calculation through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test mastery calculation
    response = client.post("/mastery/calculate", json={
        "student_id": "e2e_test_student",
        "topic_id": "python_basic",
        "session_data": {"score": 90, "time": 30}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "e2e_test_student"
    assert data["topic_id"] == "python_basic"
    assert "mastery_level" in data

@pytest.mark.asyncio
async def test_progress_retrieval():
    """Test progress retrieval endpoints"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test summary endpoint
    response = client.get("/progress/summary/test_student")
    assert response.status_code == 200

    # Test topics endpoint
    response = client.get("/progress/topics/test_student")
    assert response.status_code == 200

    # Test history endpoint
    response = client.get("/history/trend/test_student/python_basic")
    assert response.status_code == 200