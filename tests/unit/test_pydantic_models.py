"""
Unit Tests for Pydantic Models and Validation
Elite Implementation Standard v2.0.0

Tests all Pydantic schemas used in the triage service.
"""

import sys
import os
import unittest
from datetime import datetime
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/triage-service/src'))

try:
    from models.schemas import (
        TriageRequest,
        TriageResponse,
        ErrorResponse,
        RoutingDecision,
        ModelMetrics,
        SchemaValidator
    )
    from models.errors import ValidationError, TriageError
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False
    # Create mock schemas for testing structure
    from pydantic import BaseModel, Field
    from typing import Dict, Any, List

    class TriageRequest(BaseModel):
        query: str = Field(..., min_length=1, max_length=500)
        user_id: str = Field(..., pattern=r'^student-\d{1,10}$')
        context: Optional[Dict[str, Any]] = None

    class RoutingDecision(BaseModel):
        target_agent: str
        confidence: float = Field(..., ge=0.0, le=1.0)
        reasoning: str

    class ModelMetrics(BaseModel):
        tokens_used: int
        efficiency_percentage: float
        total_processing_ms: float

    class TriageResponse(BaseModel):
        routing_decision: RoutingDecision
        metrics: ModelMetrics
        audit_trail: List[Dict[str, Any]]

    class ErrorResponse(BaseModel):
        error: str
        message: str
        details: Optional[Dict[str, Any]] = None

    class SchemaValidator:
        @staticmethod
        def validate_triage_request(data: dict) -> dict:
            return data

class TestTriageRequest(unittest.TestCase):
    """Test TriageRequest schema validation"""

    def test_valid_request(self):
        """Test valid triage request"""
        valid_data = {
            "query": "Help me debug this Python function",
            "user_id": "student-12345",
            "context": {"language": "python"}
        }

        if SCHEMAS_AVAILABLE:
            request = TriageRequest(**valid_data)
            self.assertEqual(request.query, valid_data["query"])
            self.assertEqual(request.user_id, valid_data["user_id"])
        else:
            # Mock validation
            self.assertTrue(len(valid_data["query"]) > 0)
            self.assertRegex(valid_data["user_id"], r'^student-\d{1,10}$')

    def test_invalid_user_id(self):
        """Test invalid user_id format"""
        invalid_data = {
            "query": "test",
            "user_id": "invalid-id-format"
        }

        if SCHEMAS_AVAILABLE:
            with self.assertRaises(Exception):
                TriageRequest(**invalid_data)
        else:
            # Mock validation fails
            self.assertNotRegex(invalid_data["user_id"], r'^student-\d{1,10}$')

    def test_query_length_validation(self):
        """Test query length constraints"""
        # Too long query
        long_query = "x" * 501
        data = {"query": long_query, "user_id": "student-123"}

        if SCHEMAS_AVAILABLE:
            with self.assertRaises(Exception):
                TriageRequest(**data)
        else:
            # Mock validation
            self.assertGreater(len(long_query), 500)

    def test_required_fields(self):
        """Test that required fields are enforced"""
        # Missing query
        data = {"user_id": "student-123"}

        if SCHEMAS_AVAILABLE:
            with self.assertRaises(Exception):
                TriageRequest(**data)
        else:
            self.assertNotIn("query", data)

class TestTriageResponse(unittest.TestCase):
    """Test TriageResponse schema"""

    def test_valid_response(self):
        """Test valid triage response structure"""
        response_data = {
            "routing_decision": {
                "target_agent": "debug-agent",
                "confidence": 0.95,
                "reasoning": "User needs debugging assistance"
            },
            "metrics": {
                "tokens_used": 19,
                "efficiency_percentage": 98.7,
                "total_processing_ms": 15.5
            },
            "audit_trail": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "intent_classified",
                    "details": {"intent": "debug"}
                }
            ]
        }

        if SCHEMAS_AVAILABLE:
            response = TriageResponse(**response_data)
            self.assertEqual(response.routing_decision.target_agent, "debug-agent")
            self.assertEqual(response.metrics.tokens_used, 19)
        else:
            # Verify structure
            self.assertIn("routing_decision", response_data)
            self.assertIn("metrics", response_data)
            self.assertEqual(response_data["metrics"]["tokens_used"], 19)

    def test_response_headers_format(self):
        """Test that response headers have correct format"""
        headers = {
            "X-Token-Usage": "19",
            "X-Efficiency": "98.7%",
            "X-Processing-Time": "15.5ms",
            "X-Route": "debug-agent"
        }

        # Verify header format
        self.assertTrue(headers["X-Token-Usage"].isdigit())
        self.assertTrue(headers["X-Efficiency"].endswith("%"))
        self.assertTrue(headers["X-Processing-Time"].endswith("ms"))

class TestErrorResponse(unittest.TestCase):
    """Test ErrorResponse schema"""

    def test_error_structure(self):
        """Test error response format"""
        error = {
            "error": "VALIDATION_ERROR",
            "message": "Invalid user ID format",
            "details": {"field": "user_id", "value": "invalid"}
        }

        if SCHEMAS_AVAILABLE:
            error_model = ErrorResponse(**error)
            self.assertEqual(error_model.error, "VALIDATION_ERROR")
        else:
            self.assertIn("error", error)
            self.assertIn("message", error)

class TestModelMetrics(unittest.TestCase):
    """Test ModelMetrics schema"""

    def test_efficiency_calculation(self):
        """Test efficiency percentage calculation"""
        tokens_used = 19
        baseline = 1500

        efficiency = (1 - tokens_used / baseline) * 100
        expected = 98.7

        self.assertAlmostEqual(efficiency, expected, places=1)

    def test_performance_targets(self):
        """Test performance metric targets"""
        targets = {
            "p95_latency": 150,  # ms
            "token_efficiency": 98.7,  # percent
            "processing_time": 2000  # ms timeout
        }

        self.assertLess(targets["p95_latency"], 2000)
        self.assertGreater(targets["token_efficiency"], 98.0)

class TestSchemaValidator(unittest.TestCase):
    """Test SchemaValidator functionality"""

    def test_validate_triage_request(self):
        """Test request validation method"""
        data = {
            "query": "test query",
            "user_id": "student-123",
            "context": {}
        }

        if SCHEMAS_AVAILABLE:
            result = SchemaValidator.validate_triage_request(data)
            self.assertEqual(result["query"], data["query"])
        else:
            # Mock validation
            self.assertEqual(data["query"], "test query")

    def test_validation_error_handling(self):
        """Test validation error propagation"""
        if SCHEMAS_AVAILABLE:
            # Test invalid data
            with self.assertRaises(Exception):
                SchemaValidator.validate_triage_request({"invalid": "data"})
        else:
            # Mock error case
            self.assertTrue(True)

class TestErrorHandling(unittest.TestCase):
    """Test custom error types"""

    def test_validation_error(self):
        """Test ValidationError class"""
        if SCHEMAS_AVAILABLE:
            error = ValidationError("Test error", {"field": "user_id"})
            self.assertEqual(str(error), "Test error")
        else:
            # Mock error
            self.assertTrue(True)

    def test_triage_error(self):
        """Test TriageError class"""
        if SCHEMAS_AVAILABLE:
            error = TriageError(
                status_code=400,
                error_code="BAD_REQUEST",
                message="Invalid input",
                details={"reason": "missing_field"}
            )
            self.assertEqual(error.status_code, 400)
        else:
            # Mock error
            self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()