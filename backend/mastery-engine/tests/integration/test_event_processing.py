"""
Event Processing Integration Tests
===================================

Tests for event ingestion, validation, and state updates.
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from src.main import app
from src.models.events import ExerciseCompletedEvent, QuizCompletedEvent
from src.services.event_validator import EventValidationService


@pytest.fixture
def mock_security():
    """Mock JWT security"""
    with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock:
        security_manager = Mock()
        security_manager.validate_jwt.return_value = {
            "sub": "student_123",
            "role": "student",
            "exp": 9999999999
        }
        mock.return_value = security_manager
        yield security_manager


@pytest.fixture
def mock_state_manager():
    """Mock state manager"""
    with patch('src.api.endpoints.mastery.StateManager.create') as mock:
        state_manager = Mock()
        state_manager.health_check = AsyncMock(return_value=True)
        state_manager.is_event_processed = AsyncMock(return_value=False)
        state_manager.save_learning_event = AsyncMock(return_value=True)
        state_manager.append_event_log = AsyncMock(return_value=True)
        mock.return_value = state_manager
        yield state_manager


@pytest.fixture
def client(mock_security, mock_state_manager):
    """Test client with mocked dependencies"""
    return TestClient(app)


class TestEventValidation:
    """Test event validation service"""

    def test_validate_exercise_completed_event(self):
        """Test validation of exercise completed event"""
        validator = EventValidationService()

        event_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "exercise_id": "ex_123",
                "difficulty": "medium",
                "time_spent_seconds": 120,
                "completion_rate": 0.9,
                "correctness": 0.85,
                "topic_ids": ["math", "algebra"],
                "hints_used": 2,
                "retries": 1
            }
        }

        # Structure validation
        result = validator.validate_event_structure(event_data)
        assert result.valid is True
        assert len(result.errors) == 0

        # Business rule validation
        result = validator.validate_event_business_rules(event_data)
        assert result.valid is True

    def test_validate_quiz_completed_event(self):
        """Test validation of quiz completed event"""
        validator = EventValidationService()

        event_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "quiz.completed",
            "student_id": "student_123",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "quiz_id": "quiz_456",
                "score": 0.9,
                "questions_total": 10,
                "questions_correct": 9,
                "time_spent_seconds": 300,
                "topic_ids": ["science"]
            }
        }

        result = validator.validate_event_structure(event_data)
        assert result.valid is True

        result = validator.validate_event_business_rules(event_data)
        assert result.valid is True

    def test_invalid_event_data(self):
        """Test validation catches invalid event data"""
        validator = EventValidationService()

        # Missing required fields
        invalid_data = {
            "event_type": "exercise.completed",
            "student_id": "student_123"
            # Missing event_id, timestamp
        }

        result = validator.validate_event_structure(invalid_data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_suspicious_pattern_detection(self):
        """Test detection of suspicious event patterns"""
        validator = EventValidationService()

        # High completion but very low correctness (potential gaming)
        event_data = {
            "event_type": "exercise.completed",
            "data": {
                "completion_rate": 0.95,
                "correctness": 0.1
            }
        }

        # Mock current mastery state
        current_mastery = {"mastery_score": 0.7}

        result = validator.validate_against_mastery_state(event_data, current_mastery)
        assert len(result.warnings) > 0
        assert any("suspicious" in w.lower() for w in result.warnings)

    def test_data_sanitization(self):
        """Test sanitization of potentially malicious data"""
        validator = EventValidationService()

        dirty_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "exercise_id": "ex_123",
                "difficulty": "<script>alert('xss')</script>",
                "time_spent_seconds": 120,
                "completion_rate": 0.9,
                "correctness": 0.85
            }
        }

        sanitized = validator.sanitize_event_data(dirty_data)

        assert "<script>" not in sanitized["data"]["difficulty"]
        assert "javascript:" not in str(sanitized)


class TestEventIngestionEndpoint:
    """Test the /api/v1/mastery/ingest endpoint"""

    def test_successful_event_ingestion(self, client):
        """Test successful event ingestion"""
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "data": {
                "exercise_id": "ex_123",
                "difficulty": "medium",
                "time_spent_seconds": 120,
                "completion_rate": 0.9,
                "correctness": 0.85
            }
        }

        response = client.post(
            "/api/v1/mastery/ingest",
            json=event_payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "event_id" in data
        assert data["event_id"] == event_payload["event_id"]

    def test_duplicate_event_rejection(self, client, mock_state_manager):
        """Test idempotency - duplicate events are handled gracefully"""
        event_id = str(uuid.uuid4())

        # First request
        event_payload = {
            "event_id": event_id,
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "data": {"exercise_id": "ex_1", "difficulty": "easy", "time_spent_seconds": 60, "completion_rate": 1.0, "correctness": 1.0}
        }

        response1 = client.post(
            "/api/v1/mastery/ingest",
            json=event_payload,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response1.status_code == 202

        # Simulate event already processed
        mock_state_manager.is_event_processed.return_value = True

        # Second request with same event_id
        response2 = client.post(
            "/api/v1/mastery/ingest",
            json=event_payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response2.status_code == 202
        data = response2.json()
        assert "already processed" in data["message"]

    def test_missing_required_fields(self, client):
        """Test validation rejects events with missing fields"""
        invalid_payload = {
            "event_type": "exercise.completed",
            # Missing event_id, student_id
            "data": {"exercise_id": "ex_1"}
        }

        response = client.post(
            "/api/v1/mastery/ingest",
            json=invalid_payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert len(data["errors"]) > 0

    def test_invalid_business_rules(self, client):
        """Test validation rejects events violating business rules"""
        invalid_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "data": {
                "exercise_id": "ex_1",
                "difficulty": "invalid_difficulty",  # Invalid
                "time_spent_seconds": -60,  # Invalid
                "completion_rate": 1.5,  # Invalid
                "correctness": 0.8
            }
        }

        response = client.post(
            "/api/v1/mastery/ingest",
            json=invalid_payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert any("difficulty" in error.lower() or "completion" in error.lower() for error in data["errors"])

    def test_student_cannot_ingest_for_others(self, client):
        """Test security: students can only ingest events for themselves"""
        # Mock student A trying to ingest event for student B
        with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock_security:
            security_manager = Mock()
            security_manager.validate_jwt.return_value = {
                "sub": "student_a",
                "role": "student"
            }
            mock_security.return_value = security_manager

            event_payload = {
                "event_id": str(uuid.uuid4()),
                "event_type": "exercise.completed",
                "student_id": "student_b",  # Different from JWT sub
                "data": {"exercise_id": "ex_1", "difficulty": "easy", "time_spent_seconds": 60, "completion_rate": 1.0, "correctness": 1.0}
            }

            response = client.post(
                "/api/v1/mastery/ingest",
                json=event_payload,
                headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 403
            data = response.json()
            assert "Cannot ingest events for other students" in data["message"]

    def test_student_id_injection(self, client):
        """Test that student_id is set from JWT if not provided"""
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            # student_id not provided
            "data": {"exercise_id": "ex_1", "difficulty": "easy", "time_spent_seconds": 60, "completion_rate": 1.0, "correctness": 1.0}
        }

        with patch('src.api.endpoints.mastery.StateManager.create') as mock_state:
            state_manager = Mock()
            state_manager.is_event_processed = AsyncMock(return_value=False)
            state_manager.save_learning_event = AsyncMock(return_value=True)
            state_manager.append_event_log = AsyncMock(return_value=True)
            mock_state.return_value = state_manager

            response = client.post(
                "/api/v1/mastery/ingest",
                json=event_payload,
                headers={"Authorization": "Bearer test_token"}
            )

            assert response.status_code == 202

            # Verify that append_event_log was called with JWT user_id
            call_args = state_manager.append_event_log.call_args
            assert call_args[0][0] == "student_123"  # From JWT mock

    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/api/v1/mastery/ingest",
            data="invalid json",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid JSON" in data["message"]


class TestEventToStateMapping:
    """Test that events correctly update student state"""

    @pytest.mark.asyncio
    async def test_exercise_event_updates_mastery(self):
        """Test that exercise completion can trigger mastery recalculation"""
        # This would be tested via the Kafka consumer, but we can test the logic
        from src.skills.calculator import MasteryCalculator
        from src.models.mastery import ComponentScores

        # Simulate: Student had 0.7 mastery, completed exercise with high quality
        # Expected: Slight improvement in completion and consistency components

        calculator = MasteryCalculator()
        old_components = ComponentScores(0.7, 0.7, 0.7, 0.7)
        old_result = calculator.execute_calculation("student", old_components)

        # New event: High completion, high quality
        new_completion = 0.85  # Improved
        new_quality = 0.9      # High quality work

        new_components = ComponentScores(
            completion=new_completion,
            quiz=0.7,
            quality=new_quality,
            consistency=0.75  # Slight improvement
        )

        new_result = calculator.execute_calculation("student", new_components)

        assert new_result.mastery_score > old_result.mastery_score
        assert new_result.level.value >= old_result.level.value

    def test_quiz_event_affects_quiz_component(self):
        """Test that quiz events primarily affect quiz component"""
        calculator = MasteryCalculator()

        # High quiz score
        components = ComponentScores(
            completion=0.5,
            quiz=0.95,
            quality=0.5,
            consistency=0.5
        )

        result = calculator.execute_calculation("student", components)

        # Quiz contributes 30% to score
        expected_quiz_contribution = 0.95 * 0.3  # 0.285
        actual_quiz_contribution = result.breakdown.quiz

        assert abs(actual_quiz_contribution - expected_quiz_contribution) < 0.001


class TestEventBatchProcessing:
    """Test batch event processing capabilities"""

    def test_batch_events_consistency_validation(self):
        """Test validation of batch events for consistency"""
        from src.services.event_validator import EventValidationService

        validator = EventValidationService()

        batch = [
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "exercise.completed",
                "student_id": "student_123",
                "timestamp": "2024-01-01T12:00:00",
                "data": {"exercise_id": "ex_1", "difficulty": "easy", "time_spent_seconds": 60, "completion_rate": 1.0, "correctness": 1.0}
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "quiz.completed",
                "student_id": "student_123",
                "timestamp": "2024-01-01T12:05:00",
                "data": {"quiz_id": "quiz_1", "score": 0.8, "questions_total": 10, "questions_correct": 8, "time_spent_seconds": 300}
            }
        ]

        valid, errors = validator.validate_batch_consistency(batch)
        assert valid is True

    def test_duplicate_event_ids_in_batch(self):
        """Test detection of duplicate event IDs in batch"""
        from src.services.event_validator import EventValidationService

        validator = EventValidationService()

        event_id = str(uuid.uuid4())
        batch = [
            {
                "event_id": event_id,
                "event_type": "exercise.completed",
                "student_id": "student_123",
                "timestamp": "2024-01-01T12:00:00",
                "data": {"exercise_id": "ex_1", "difficulty": "easy", "time_spent_seconds": 60, "completion_rate": 1.0, "correctness": 1.0}
            },
            {
                "event_id": event_id,  # Same ID
                "event_type": "quiz.completed",
                "student_id": "student_123",
                "timestamp": "2024-01-01T12:05:00",
                "data": {"quiz_id": "quiz_1", "score": 0.8, "questions_total": 10, "questions_correct": 8, "time_spent_seconds": 300}
            }
        ]

        valid, errors = validator.validate_batch_consistency(batch)
        assert valid is False
        assert len(errors) > 0


class TestComplexityScoring:
    """Test event complexity scoring for monitoring"""

    def test_event_complexity_scoring(self):
        """Test that events are scored by complexity"""
        validator = EventValidationService()

        events = [
            {"event_type": "lesson.viewed", "data": {}},
            {"event_type": "exercise.completed", "data": {}},
            {"event_type": "quiz.completed", "data": {}},
            {"event_type": "milestone.reached", "data": {}},
            {"event_type": "exercise.completed", "data": {"topic_ids": ["a", "b", "c", "d"]}}  # More complex
        ]

        scores = [validator.get_event_complexity_score(e) for e in events]

        # Should be ordered by complexity
        assert scores[0] < scores[1]
        assert scores[1] < scores[2]
        assert scores[2] < scores[3]
        assert scores[4] > scores[1]  # Exercise with topics > exercise without


# End of TestEventProcessing