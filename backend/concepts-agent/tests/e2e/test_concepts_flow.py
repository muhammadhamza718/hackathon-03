"""
End-to-end tests for Concepts Agent
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

@pytest.mark.asyncio
async def test_concepts_api_endpoints():
    """Test Concepts Agent API endpoints"""
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
async def test_explanation_generation_flow():
    """Test explanation generation through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test explanation generation
    response = client.post("/explain/", json={
        "concept": "loops",
        "student_level": "beginner",
        "context": {},
        "preferred_style": "simple"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "loops"
    assert "explanation" in data
    assert isinstance(data["analogies"], list)
    assert isinstance(data["examples"], list)

@pytest.mark.asyncio
async def test_concept_mapping_flow():
    """Test concept mapping through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test concept mapping
    response = client.post("/mapping/", json={
        "concept": "loops",
        "depth": 2
    })

    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "loops"
    assert "prerequisites" in data
    assert "learning_path" in data

@pytest.mark.asyncio
async def test_prerequisites_check_flow():
    """Test prerequisites checking through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test prerequisites check
    response = client.post("/prerequisites/check", json={
        "concept": "loops",
        "student_level": "beginner"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "loops"
    assert "required_prerequisites" in data
    assert "readiness_score" in data

@pytest.mark.asyncio
async def test_concept_kafka_consumer():
    """Test Kafka consumer service"""
    from services.kafka_consumer import ConceptKafkaConsumer

    consumer = ConceptKafkaConsumer()
    consumer.kafka_enabled = False

    # Test event processing
    event = {
        "student_id": "test_student",
        "concept": "functions",
        "level": "intermediate",
        "timestamp": "2026-01-14T10:30:00Z"
    }

    result = consumer.process_concept_request(event)
    assert result is not None
    assert result["student_id"] == "test_student"
    assert "explanation" in result

    # Test mapping processing
    mapping_result = consumer.process_concept_mapping_request(event)
    assert mapping_result is not None
    assert "learning_path" in mapping_result

if __name__ == "__main__":
    pytest.main([__file__])