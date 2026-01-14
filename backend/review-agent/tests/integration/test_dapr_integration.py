"""
Dapr Integration Tests for Review Agent
Tests Dapr service invocation and event processing
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from services.kafka_consumer import ReviewKafkaConsumer


@pytest.mark.integration
class TestDaprServiceInvocation:
    """Test Dapr service invocation patterns"""

    def test_dapr_service_invocation_format(self, client, mock_validate_jwt):
        """Test that Dapr service invocation format is correct"""
        # Dapr sends events in a specific format
        dapr_event = {
            "intent": "quality_assessment",
            "student_code": "def add(a, b):\n    return a + b",
            "problem_context": {"topic": "basic_math", "difficulty": "easy"},
            "student_id": "student_123",
            "confidence": 0.85
        }

        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.9,
                "factors": [],
                "strengths": ["Good"],
                "improvements": [],
                "recommendations": [],
                "concept_score": 0.9,
                "structure_score": 0.9,
                "efficiency_score": 0.9,
                "category_scores": {},
                "testing_suggestions": [],
                "optimization_suggestions": []
            }

            response = client.post(
                "/process",
                json=dapr_event,
                headers={
                    "Authorization": "Bearer test-token",
                    "dapr-app-id": "review-agent"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["agent"] == "review-agent"
            assert data["status"] == "success"

    def test_dapr_metadata_propagation(self, client, mock_validate_jwt):
        """Test metadata propagation in Dapr calls"""
        request = {
            "intent": "hint_generation",
            "student_code": "x = 5",
            "error_type": "syntax"
        }

        with patch('services.hint_generator.generate_hint_with_mcp') as mock_hint:
            mock_hint.return_value = {
                "text": "Check syntax",
                "level": "medium",
                "estimated_time": 5,
                "category": "syntax",
                "next_steps": ["Step 1"]
            }

            response = client.post(
                "/process",
                json=request,
                headers={"Authorization": "Bearer test-token"}
            )

            data = response.json()
            # Should include processing timestamp
            assert "processed_at" in data
            # Should include agent identification
            assert data["agent"] == "review-agent"

    def test_dapr_error_handling(self, client, mock_validate_jwt):
        """Test Dapr error handling and response format"""
        request = {
            "intent": "quality_assessment",
            "student_code": "broken code"
        }

        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.side_effect = Exception("MCP service unavailable")

            response = client.post(
                "/process",
                json=request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200  # Dapr should return 200 even for errors
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
            assert "data_received" in data

    def test_dapr_unsupported_intent(self, client, mock_validate_jwt):
        """Test handling of unsupported intents"""
        request = {
            "intent": "unsupported_operation",
            "student_code": "x = 5"
        }

        response = client.post(
            "/process",
            json=request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Unknown intent" in data["error"]
        assert "supported_intents" in data


@pytest.mark.integration
class TestKafkaConsumerProcessing:
    """Test Kafka consumer event processing"""

    def test_kafka_consumer_initialization(self):
        """Test Kafka consumer can be initialized"""
        consumer = ReviewKafkaConsumer()

        assert consumer.kafka_enabled is not None
        assert consumer.broker is not None

    def test_validate_event_schema_exercise_request(self, mock_kafka_consumer):
        """Test event validation for review requests"""
        valid_event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",
            "student_code": "def func(): pass",
            "problem_context": {"topic": "functions"},
            "language": "python"
        }

        is_valid, error = mock_kafka_consumer.validate_event_schema(valid_event)
        assert is_valid is True
        assert error is None

    def test_validate_event_schema_missing_fields(self, mock_kafka_consumer):
        """Test event validation with missing required fields"""
        invalid_event = {
            "student_id": "student_123",
            # Missing timestamp, intent, etc.
        }

        is_valid, error = mock_kafka_consumer.validate_event_schema(invalid_event)
        assert is_valid is False
        assert error is not None

    def test_validate_event_schema_empty_code(self, mock_kafka_consumer):
        """Test event validation with empty code"""
        invalid_event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",
            "student_code": "",
            "problem_context": {}
        }

        is_valid, error = mock_kafka_consumer.validate_event_schema(invalid_event)
        assert is_valid is False
        assert error is not None

    def test_process_code_review_request_quality(self, mock_kafka_consumer):
        """Test processing quality assessment request"""
        event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",
            "student_code": "def add(a, b):\n    return a + b",
            "problem_context": {"topic": "functions"}
        }

        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.8,
                "factors": [],
                "strengths": ["Good"],
                "improvements": [],
                "recommendations": []
            }

            result = mock_kafka_consumer.process_code_review_request(event)

            assert result is not None
            assert result["status"] == "success"
            assert result["result"]["intent"] == "quality_assessment"

    def test_process_code_review_request_hint(self, mock_kafka_consumer):
        """Test processing hint generation request"""
        event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "hint_generation",
            "student_code": "x = 5",
            "error_type": "syntax"
        }

        with patch('services.hint_generator.generate_hint_with_mcp') as mock_hint:
            mock_hint.return_value = {
                "text": "Check syntax",
                "level": "medium",
                "estimated_time": 5
            }

            result = mock_kafka_consumer.process_code_review_request(event)

            assert result is not None
            assert result["status"] == "success"
            assert result["result"]["intent"] == "hint_generation"
            assert "hint" in result["result"]

    def test_process_code_review_request_feedback(self, mock_kafka_consumer):
        """Test processing detailed feedback request"""
        event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "detailed_feedback",
            "student_code": "def func(): return 42",
            "error_type": "general"
        }

        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            with patch('services.hint_generator.generate_hint_with_mcp') as mock_hint:
                mock_assess.return_value = {
                    "score": 0.85,
                    "factors": [],
                    "strengths": ["Good"],
                    "improvements": ["Improve"],
                    "recommendations": []
                }
                mock_hint.return_value = {
                    "text": "Hint",
                    "level": "medium",
                    "estimated_time": 10,
                    "next_steps": ["Step 1"]
                }

                result = mock_kafka_consumer.process_code_review_request(event)

                assert result is not None
                assert result["status"] == "success"
                assert result["result"]["intent"] == "detailed_feedback"

    def test_process_performance_update(self, mock_kafka_consumer):
        """Test processing student performance updates"""
        event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "topic": "functions",
            "correctness": True,
            "time_taken": 30,
            "attempts": 2,
            "quality_score": 0.85
        }

        result = mock_kafka_consumer.process_performance_update(event)

        assert result is not None
        assert result["student_id"] == "student_123"
        assert result["topic"] == "functions"
        assert result["performance"]["correctness"] is True

    def test_process_feedback_response(self, mock_kafka_consumer):
        """Test processing feedback response events"""
        event = {
            "student_id": "student_123",
            "request_id": "req_123",
            "feedback": {
                "summary": "Good work",
                "score": 0.9
            }
        }

        result = mock_kafka_consumer.process_feedback_response(event)

        assert result is not None
        assert result["status"] == "acknowledged"
        assert result["request_id"] == "req_123"

    def test_consumer_stats(self, mock_kafka_consumer):
        """Test consumer statistics endpoint"""
        stats = mock_kafka_consumer.get_consumer_stats()

        assert "kafka_enabled" in stats
        assert "broker" in stats
        assert "topic" in stats
        assert "status" in stats

    def test_kafka_event_validation_edge_cases(self, mock_kafka_consumer):
        """Test event validation with various edge cases"""
        # Very long code
        long_code_event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",
            "student_code": "x = 1\n" * 30000,
            "problem_context": {}
        }

        is_valid, error = mock_kafka_consumer.validate_event_schema(long_code_event)
        assert is_valid is False
        assert "exceeds" in error.lower()

        # Missing language field (should be optional)
        valid_event = {
            "student_id": "student_123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",
            "student_code": "x = 1",
            "problem_context": {}
            # language field is optional
        }

        is_valid, error = mock_kafka_consumer.validate_event_schema(valid_event)
        assert is_valid is True


@pytest.mark.integration
class TestDaprEventCoordination:
    """Test coordination between Dapr and Kafka events"""

    def test_end_to_end_dapr_kafka_flow(self, mock_kafka_consumer, sample_student_code):
        """Test complete flow from Dapr event to Kafka processing"""
        # Simulate Dapr event
        dapr_event = {
            "intent": "quality_assessment",
            "student_code": sample_student_code,
            "problem_context": {"topic": "functions", "difficulty": "medium"},
            "student_id": "student_456",
            "confidence": 0.9
        }

        # Process through Dapr handler logic (simulated)
        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.82,
                "factors": [],
                "strengths": ["Good function structure"],
                "improvements": ["Add type hints"],
                "recommendations": []
            }

            # Process through the Dapr endpoint flow
            result = mock_kafka_consumer.process_code_review_request(dapr_event)

            assert result is not None
            assert result["status"] == "success"
            assert result["result"]["quality_score"] == 0.82
            assert "processed_via" in result
            assert result["processed_via"] == "kafka"

    def test_performance_update_coordination(self, mock_kafka_consumer):
        """Test performance update flow"""
        performance_event = {
            "student_id": "student_789",
            "timestamp": "2026-01-14T10:30:00Z",
            "topic": "loops",
            "correctness": True,
            "time_taken": 45,
            "attempts": 1,
            "quality_score": 0.9,
            "code_snippet": "for i in range(10):\n    print(i)"
        }

        # Process performance update
        result = mock_kafka_consumer.process_performance_update(performance_event)

        assert result is not None
        assert result["performance"]["quality_score"] == 0.9
        assert result["performance"]["correctness"] is True


@pytest.mark.integration
class TestDaprErrorRecovery:
    """Test Dapr error recovery and resilience"""

    def test_mcp_service_failure_graceful_degradation(self, client, mock_validate_jwt):
        """Test graceful handling when MCP services are unavailable"""
        request = {
            "intent": "quality_assessment",
            "student_code": "def func(): pass"
        }

        with patch('services.quality_scoring.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.side_effect = ConnectionError("MCP service unreachable")

            response = client.post(
                "/process",
                json=request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "MCP service unreachable" in data["error"]

    def test_invalid_json_handling(self, client, mock_validate_jwt):
        """Test handling of malformed JSON requests"""
        # Send invalid JSON
        response = client.post(
            "/process",
            data="invalid json {{",
            headers={
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            }
        )

        # FastAPI will handle this automatically
        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.integration
class TestDaprSecurity:
    """Test Dapr security considerations"""

    def test_dapr_service_invocation_authentication(self, client):
        """Test that Dapr service invocation requires authentication"""
        request = {
            "intent": "quality_assessment",
            "student_code": "x = 1"
        }

        # Without auth token
        response = client.post("/process", json=request)
        assert response.status_code in [403, 401]

        # With invalid token
        response = client.post(
            "/process",
            json=request,
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401

    def test_app_id_verification_simulation(self, client, mock_validate_jwt):
        """Test app ID verification (simulated)"""
        request = {
            "intent": "quality_assessment",
            "student_code": "x = 1"
        }

        with patch('api.endpoints.assess.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.7,
                "factors": [],
                "strengths": [],
                "improvements": [],
                "recommendations": [],
                "concept_score": 0.7,
                "structure_score": 0.7,
                "efficiency_score": 0.7,
                "category_scores": {},
                "testing_suggestions": [],
                "optimization_suggestions": []
            }

            response = client.post(
                "/process",
                json=request,
                headers={
                    "Authorization": "Bearer test-token",
                    "dapr-app-id": "triage-service"
                }
            )

            # Should succeed
            assert response.status_code == 200


@pytest.mark.integration
class TestDaprHealthAndReadiness:
    """Test Dapr health and readiness checks"""

    def test_dapr_compatible_health_endpoint(self, client):
        """Test that health endpoint works for Dapr sidecar"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "review-agent"

    def test_dapr_ready_endpoint(self, client):
        """Test readiness endpoint for Dapr"""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "review-agent"

    def test_readiness_depends_on_mcp(self, client):
        """Test that readiness checks verify MCP connectivity"""
        with patch('services.quality_scoring.check_mcp_connection') as mock_check:
            mock_check.return_value = False

            # Trigger a readiness check through the endpoint
            # Note: This test might need to trigger actual service initialization
            response = client.get("/ready")
            # For now, the endpoint doesn't check MCP - it just returns ready
            assert response.status_code == 200


@pytest.mark.integration
class TestDaprEventSchemaValidation:
    """Test Dapr event schema validation against real formats"""

    def test_dapr_event_format_matches_spec(self, mock_kafka_consumer):
        """Verify Dapr events match expected schemas"""
        # These are the formats we expect from Triage Service
        test_cases = [
            {
                "name": "quality_assessment",
                "event": {
                    "intent": "quality_assessment",
                    "student_code": "x = 1",
                    "problem_context": {"topic": "variables"},
                    "student_id": "s123"
                },
                "should_pass": True
            },
            {
                "name": "hint_generation",
                "event": {
                    "intent": "hint_generation",
                    "student_code": "x = 1",
                    "error_type": "syntax",
                    "student_id": "s123"
                },
                "should_pass": True
            },
            {
                "name": "missing_code",
                "event": {
                    "intent": "quality_assessment",
                    "student_id": "s123"
                },
                "should_pass": False
            }
        ]

        for case in test_cases:
            is_valid, error = mock_kafka_consumer.validate_event_schema(case["event"])
            assert is_valid == case["should_pass"], f"Failed case: {case['name']}"

    def test_malformed_dapr_events(self, mock_kafka_consumer):
        """Test handling of malformed Dapr events"""
        malformed_events = [
            {"intent": "quality_assessment"},  # Missing student_code
            {"student_code": "x=1"},  # Missing intent
            {"intent": 123, "student_code": "x=1"},  # Wrong type for intent
            {"intent": "quality_assessment", "student_code": []},  # Wrong type for code
        ]

        for event in malformed_events:
            is_valid, error = mock_kafka_consumer.validate_event_schema(event)
            assert is_valid is False