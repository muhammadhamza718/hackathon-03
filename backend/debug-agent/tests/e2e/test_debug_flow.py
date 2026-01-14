"""
End-to-end tests for Debug Agent
"""

import pytest
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

@pytest.mark.asyncio
async def test_debug_api_endpoints():
    """Test Debug Agent API endpoints"""
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
async def test_code_analysis_flow():
    """Test code analysis through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test analyze endpoint
    response = client.post("/analyze/", json={
        "code": "print('Hello World')",
        "language": "python",
        "student_id": "test_student"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "test_student"
    assert "lines_of_code" in data
    assert "syntax_errors" in data

@pytest.mark.asyncio
async def test_pattern_detection_flow():
    """Test pattern detection through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test pattern detection
    response = client.post("/patterns/detect", json={
        "error_message": "IndexError: list index out of range",
        "stack_trace": "File \"test.py\", line 5, in <module>",
        "student_id": "test_student"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["pattern_id"] == "ERR-001"
    assert len(data["common_fixes"]) > 0

@pytest.mark.asyncio
async def test_suggestions_flow():
    """Test fix suggestions through API"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test suggestions endpoint
    response = client.post("/suggestions/", json={
        "code": "print('Hello",
        "error_message": "SyntaxError: EOL while scanning string literal"
    })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "suggested_fix" in data[0]

if __name__ == "__main__":
    pytest.main([__file__])