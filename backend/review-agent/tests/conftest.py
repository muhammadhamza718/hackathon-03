"""
Pytest configuration and shared fixtures for Review Agent tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app, validate_jwt
from services.quality_scoring import QualityScoringEngine
from services.hint_generator import HintGenerator


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_env():
    """Set up test environment variables"""
    os.environ["KAFKA_ENABLED"] = "false"
    os.environ["KAFKA_BROKER"] = "localhost:9092"
    os.environ["JWT_SECRET"] = "test-secret-key"
    yield
    # Cleanup
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


@pytest.fixture
def mock_security_context():
    """Mock JWT security context"""
    from main import SecurityContext
    return SecurityContext(
        student_id="test_student_123",
        role="student",
        request_id="test_req_001"
    )


@pytest.fixture
def sample_student_code():
    """Sample student code for testing"""
    return """
def calculate_sum(a, b):
    total = a + b
    return total

def find_max(numbers):
    max_num = 0
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num
"""


@pytest.fixture
def sample_problem_context():
    """Sample problem context"""
    return {
        "topic": "basic_functions",
        "difficulty": "easy",
        "problem_statement": "Write functions to perform basic operations"
    }


@pytest.fixture
def mock_quality_engine():
    """Mock quality scoring engine"""
    engine = QualityScoringEngine()
    engine.mcp_connected = False  # Use algorithmic mode only
    return engine


@pytest.fixture
def mock_hint_generator():
    """Mock hint generator"""
    generator = HintGenerator()
    generator.mcp_connected = False  # Use algorithmic mode only
    return generator


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_mcp_response():
    """Mock MCP response for testing"""
    return {
        "score": 0.75,
        "factors": [{"name": "syntax", "score": 0.9, "weight": 0.15}],
        "strengths": ["Good function structure"],
        "improvements": ["Add type hints"],
        "recommendations": ["Add type hints and docstrings"]
    }


@pytest.fixture
def sample_assessment_request():
    """Sample assessment request"""
    return {
        "student_code": "def add(a, b):\n    return a + b",
        "problem_context": {"topic": "functions"},
        "language": "python"
    }


@pytest.fixture
def sample_hint_request():
    """Sample hint request"""
    return {
        "student_code": "for i in range(5):\n    print(i)",
        "error_type": "logic",
        "hint_level": "medium",
        "previous_hints": 0
    }


@pytest.fixture
def sample_feedback_request():
    """Sample feedback request"""
    return {
        "student_code": "def max(a, b):\n    if a > b:\n        return a\n    else:\n        return b",
        "error_type": "edge_cases",
        "request_level": "comprehensive"
    }


@pytest.fixture
def mock_kafka_consumer():
    """Mock Kafka consumer"""
    from services.kafka_consumer import ReviewKafkaConsumer
    consumer = ReviewKafkaConsumer()
    consumer.kafka_enabled = False
    return consumer


@pytest.fixture
def valid_jwt_token():
    """Generate a valid-looking JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdHVkZW50X2lkIjoidGVzdF9zdHVkZW50In0.test"


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable rate limiting during tests"""
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    # Mock the rate limiter to always pass
    original_limit = app.state.limiter.limit

    def mock_limit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    app.state.limiter.limit = mock_limit


@pytest.fixture
def mock_validate_jwt(monkeypatch):
    """Mock JWT validation to always pass"""
    async def mock_validator(credentials=None):
        from main import SecurityContext
        return SecurityContext(
            student_id="test_student",
            role="student",
            request_id="test_req"
        )

    monkeypatch.setattr("main.validate_jwt", mock_validator)


# Async test utilities
@pytest.fixture
def async_test_helper():
    """Helper for running async tests"""
    def run_async(coro):
        return asyncio.run(coro)
    return run_async


# Test data factories
@pytest.fixture
def create_test_code():
    """Factory to create test code snippets"""
    def _create(kind="valid"):
        codes = {
            "valid": "def func(x):\n    return x * 2",
            "syntax_error": "def func(x\n    return x",
            "logic_error": "def max(a, b):\n    if a > b:\n        return b\n    else:\n        return a",
            "empty_function": "def func():\n    pass",
            "nested_loops": "for i in range(5):\n    for j in range(3):\n        print(i, j)"
        }
        return codes.get(kind, codes["valid"])
    return _create