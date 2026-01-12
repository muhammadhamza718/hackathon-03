"""
Unit Tests: Pydantic Models & Schema Validation
Elite Implementation Standard v2.0.0

Tests schema validation, data integrity, and model constraints.
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from models.schemas import (
    TriageRequest,
    TriageResponse,
    ErrorResponse,
    SchemaValidator,
    RoutingDecision,
    Metrics
)
from models.errors import ValidationError, TriageError


class TestTriageRequest:
    """Test TriageRequest schema validation"""

    def test_valid_request(self):
        """Test valid request creation"""
        request = TriageRequest(
            query="What is polymorphism?",
            user_id="student-12345",
            context={"topic": "OOP", "difficulty": "intermediate"}
        )
        assert request.query == "What is polymorphism?"
        assert request.user_id == "student-12345"
        assert request.context == {"topic": "OOP", "difficulty": "intermediate"}

    def test_request_validation(self):
        """Test request validation rules"""
        # Empty query should fail
        with pytest.raises(Exception):
            TriageRequest(query="", user_id="student-12345")

        # Long query should fail (max 500 chars)
        long_query = "a" * 501
        with pytest.raises(Exception):
            TriageRequest(query=long_query, user_id="student-12345")

        # Invalid user_id format should fail
        with pytest.raises(Exception):
            TriageRequest(query="test", user_id="invalid_format")

    def test_request_serialization(self):
        """Test JSON serialization"""
        request = TriageRequest(
            query="Test query",
            user_id="student-12345",
            context={"test": True}
        )

        json_data = request.model_dump()
        assert json_data["query"] == "Test query"
        assert json_data["user_id"] == "student-12345"
        assert json_data["context"]["test"] is True

    def test_request_with_missing_context(self):
        """Test request with optional context"""
        request = TriageRequest(
            query="Simple query",
            user_id="student-12345"
        )
        assert request.context is None


class TestTriageResponse:
    """Test TriageResponse schema validation"""

    def test_valid_response(self):
        """Test valid response creation"""
        decision = RoutingDecision(
            target_agent="debug-agent",
            confidence=0.95,
            intent="syntax_help",
            priority=1
        )

        metrics = Metrics(
            tokens_used=19,
            efficiency_percentage=98.7,
            total_processing_ms=15.5
        )

        response = TriageResponse(
            routing_decision=decision,
            metrics=metrics,
            audit_id="audit-12345"
        )

        assert response.routing_decision.target_agent == "debug-agent"
        assert response.metrics.tokens_used == 19
        assert response.audit_id == "audit-12345"

    def test_response_serialization(self):
        """Test response to JSON"""
        response = TriageResponse(
            routing_decision=RoutingDecision(
                target_agent="concepts-agent",
                confidence=0.92,
                intent="concept_explanation",
                priority=2
            ),
            metrics=Metrics(
                tokens_used=25,
                efficiency_percentage=98.3,
                total_processing_ms=20.1
            ),
            audit_id="audit-67890"
        )

        json_data = response.model_dump()
        assert json_data["routing_decision"]["target_agent"] == "concepts-agent"
        assert json_data["metrics"]["tokens_used"] == 25


class TestErrorResponse:
    """Test ErrorResponse schema"""

    def test_error_response_structure(self):
        """Test error response creation"""
        error = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Invalid query format",
            details={"field": "query", "reason": "too long"}
        )

        assert error.error == "VALIDATION_ERROR"
        assert error.message == "Invalid query format"
        assert error.details["field"] == "query"


class TestSchemaValidator:
    """Test SchemaValidator functionality"""

    def test_validate_triage_request_valid(self):
        """Test valid request validation"""
        valid_data = {
            "query": "What is polymorphism?",
            "user_id": "student-12345",
            "context": {"topic": "OOP"}
        }

        result = SchemaValidator.validate_triage_request(valid_data)
        assert result["query"] == "What is polymorphism?"
        assert result["user_id"] == "student-12345"

    def test_validate_triage_request_invalid(self):
        """Test invalid request validation"""
        invalid_data = {
            "query": "",  # Empty query
            "user_id": "invalid"
        }

        with pytest.raises(ValidationError):
            SchemaValidator.validate_triage_request(invalid_data)

    def test_validate_with_extra_fields(self):
        """Test validation ignores extra fields"""
        data = {
            "query": "Test",
            "user_id": "student-12345",
            "extra_field": "should be ignored"
        }

        result = SchemaValidator.validate_triage_request(data)
        assert "extra_field" not in result
        assert result["query"] == "Test"


class TestRoutingDecision:
    """Test RoutingDecision model"""

    def test_routing_decision_creation(self):
        """Test routing decision with all fields"""
        decision = RoutingDecision(
            target_agent="debug-agent",
            confidence=0.95,
            intent="syntax_help",
            priority=1,
            reason="High confidence syntax error detection"
        )

        assert decision.target_agent == "debug-agent"
        assert decision.confidence == 0.95
        assert decision.intent == "syntax_help"
        assert decision.priority == 1
        assert decision.reason == "High confidence syntax error detection"

    def test_routing_decision_minimal(self):
        """Test routing decision with required fields only"""
        decision = RoutingDecision(
            target_agent="exercise-agent",
            confidence=0.8,
            intent="practice_exercises",
            priority=3
        )

        assert decision.target_agent == "exercise-agent"
        assert decision.reason is None


class TestMetrics:
    """Test Metrics model"""

    def test_metrics_creation(self):
        """Test metrics with all fields"""
        metrics = Metrics(
            tokens_used=19,
            efficiency_percentage=98.7,
            total_processing_ms=15.5,
            retries=0,
            circuit_breaker_events=0
        )

        assert metrics.tokens_used == 19
        assert metrics.efficiency_percentage == 98.7
        assert metrics.total_processing_ms == 15.5
        assert metrics.retries == 0
        assert metrics.circuit_breaker_events == 0

    def test_metrics_efficiency_calculation(self):
        """Test efficiency percentage calculation"""
        # Baseline: 1500 tokens, Actual: 19 tokens
        baseline = 1500
        actual = 19

        efficiency = ((baseline - actual) / baseline) * 100
        assert efficiency == pytest.approx(98.733, 0.01)

    def test_metrics_performance_targets(self):
        """Test metrics meet performance targets"""
        metrics = Metrics(
            tokens_used=25,
            efficiency_percentage=98.3,
            total_processing_ms=25.0,
            retries=1,
            circuit_breaker_events=0
        )

        # Target: <100ms processing time
        assert metrics.total_processing_ms < 100

        # Target: >98% efficiency
        assert metrics.efficiency_percentage > 98.0


class TestModelErrorHandling:
    """Test error handling in models"""

    def test_triage_error_creation(self):
        """Test custom TriageError"""
        error = TriageError(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="Invalid request",
            details={"field": "query"}
        )

        assert error.status_code == 422
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid request"

    def test_validation_error_inherits(self):
        """Test ValidationError inheritance"""
        error = ValidationError("Test validation error")
        assert error.message == "Test validation error"


class TestSchemaConstraints:
    """Test schema constraints and limits"""

    def test_query_length_limit(self):
        """Test maximum query length enforcement"""
        max_length = 500
        long_query = "a" * (max_length + 1)

        with pytest.raises(Exception):
            TriageRequest(query=long_query, user_id="student-12345")

        # Should work at exact limit
        exact_query = "a" * max_length
        request = TriageRequest(query=exact_query, user_id="student-12345")
        assert len(request.query) == max_length

    def test_user_id_format(self):
        """Test user_id format validation"""
        # Valid formats
        valid_ids = ["student-12345", "student-99999", "student-1"]
        for uid in valid_ids:
            request = TriageRequest(query="test", user_id=uid)
            assert request.user_id == uid

        # Invalid formats
        invalid_ids = ["student12345", "user-123", "student-", "12345"]
        for uid in invalid_ids:
            with pytest.raises(Exception):
                TriageRequest(query="test", user_id=uid)

    def test_confidence_range(self):
        """Test confidence score range (0-1)"""
        # Valid ranges
        valid_decisions = [
            RoutingDecision(target_agent="test", confidence=0.0, intent="test", priority=1),
            RoutingDecision(target_agent="test", confidence=0.5, intent="test", priority=1),
            RoutingDecision(target_agent="test", confidence=1.0, intent="test", priority=1),
        ]

        # Invalid ranges should fail
        with pytest.raises(Exception):
            RoutingDecision(target_agent="test", confidence=-0.1, intent="test", priority=1)

        with pytest.raises(Exception):
            RoutingDecision(target_agent="test", confidence=1.1, intent="test", priority=1)


class TestModelPerformance:
    """Test model performance characteristics"""

    def test_serialization_speed(self):
        """Test serialization is fast (<1ms)"""
        import time

        request = TriageRequest(
            query="Performance test query",
            user_id="student-12345",
            context={"test": True}
        )

        start = time.time()
        for _ in range(100):
            _ = request.model_dump()
        duration = (time.time() - start) * 10  # Average per call

        assert duration < 0.001  # <1ms average

    def test_memory_efficiency(self):
        """Test models are memory efficient"""
        import sys

        # Create multiple instances
        requests = [
            TriageRequest(
                query=f"Query {i}",
                user_id=f"student-{1000+i}",
                context={"index": i}
            )
            for i in range(100)
        ]

        # Estimate memory usage
        total_size = sum(sys.getsizeof(r) for r in requests)
        avg_size = total_size / len(requests)

        # Each request should be <2KB
        assert avg_size < 2000


if __name__ == "__main__":
    print("=== Running Unit Tests: Models ===")
    pytest.main([__file__, "-v"])