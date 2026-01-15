"""
Prediction Endpoints Integration Tests
=======================================

Integration tests for prediction and analytics endpoints.
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from src.main import app
from src.security import SecurityManager
from src.models.mastery import MasteryResult, MasteryLevel, ComponentScores, MasteryBreakdown


@pytest.fixture
def mock_security_manager():
    """Mock security manager with JWT validation"""
    security_manager = SecurityManager(jwt_secret="test-secret")

    # Create test tokens
    student_token = security_manager.create_jwt("student_123", "student")
    admin_token = security_manager.create_jwt("admin_123", "admin")

    return {
        "manager": security_manager,
        "tokens": {
            "student": student_token,
            "admin": admin_token
        }
    }


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing"""
    state_manager = Mock()

    # Mock current mastery
    current_mastery = MasteryResult(
        student_id="student_123",
        mastery_score=0.75,
        level=MasteryLevel.PROFICIENT,
        components=ComponentScores(0.8, 0.75, 0.8, 0.65),
        breakdown=MasteryBreakdown(
            completion=0.32, quiz=0.225, quality=0.16, consistency=0.065,
            weighted_sum=0.75,
            weights=Mock()
        )
    )
    state_manager.get_mastery_score = AsyncMock(return_value=current_mastery)

    # Mock historical data
    historical_data = []
    for i in range(10):
        score = 0.6 + (i * 0.02)  # Steady improvement
        mastery = MasteryResult(
            student_id="student_123",
            mastery_score=score,
            level=MasteryLevel.PROFICIENT,
            components=ComponentScores(score, score, score, score),
            breakdown=MasteryBreakdown(
                completion=score * 0.4, quiz=score * 0.3, quality=score * 0.2, consistency=score * 0.1,
                weighted_sum=score,
                weights=Mock()
            ),
            timestamp=datetime.utcnow() - timedelta(days=10-i)
        )
        historical_data.append(mastery)

    state_manager.get = AsyncMock(side_effect=lambda key: {
        f"student:student_123:mastery:{(datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')}": historical_data[i].model_dump()
        for i in range(10)
    }.get(key))

    state_manager.save = AsyncMock(return_value=True)
    state_manager.get_mastery_history = AsyncMock(return_value=historical_data)

    return state_manager


@pytest.fixture
def client(mock_security_manager, mock_state_manager):
    """Test client with mocked dependencies"""
    with patch('src.main.app_state') as mock_app_state:
        mock_app_state.__getitem__ = lambda self, key: {
            "security_manager": mock_security_manager["manager"],
            "state_manager": mock_state_manager,
            "ready": True,
            "health_report": {"state_store": True, "kafka": False, "dapr": True}
        }[key]

        return TestClient(app)


class TestPredictionEndpoints:
    """Test prediction endpoint functionality"""

    def test_next_week_prediction_success(self, client, mock_security_manager):
        """Test successful next week prediction"""
        payload = {
            "student_id": "student_123"
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify prediction structure
        assert "predicted_score" in data
        assert "confidence" in data
        assert "trend" in data
        assert "intervention_needed" in data
        assert "predicted_level" in data
        assert "components_projection" in data

        # Verify reasonable values
        assert 0.0 <= data["predicted_score"] <= 1.0
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["trend"] in ["improving", "declining", "stable"]

    def test_next_week_prediction_student_access_denied(self, client, mock_security_manager):
        """Test that students cannot predict for others"""
        payload = {
            "student_id": "student_456"  # Different student
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 403

    def test_next_week_prediction_admin_access(self, client, mock_security_manager):
        """Test that admins can predict for any student"""
        payload = {
            "student_id": "student_456"  # Different student
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

    def test_next_week_prediction_missing_student_id(self, client, mock_security_manager):
        """Test missing student_id"""
        payload = {}

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 400

    def test_trajectory_prediction_success(self, client, mock_security_manager):
        """Test successful trajectory prediction"""
        payload = {
            "student_id": "student_123"
        }

        response = client.post(
            "/api/v1/analytics/predictions/trajectory",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify trajectory structure
        assert "trajectory" in data
        assert "confidence_over_time" in data
        assert "intervention_points" in data
        assert "overall_trend" in data

        # Should have 14 days of trajectory
        assert len(data["trajectory"]) == 14

        # Verify trajectory point structure
        first_point = data["trajectory"][0]
        assert "days_from_now" in first_point
        assert "predicted_score" in first_point
        assert "confidence" in first_point
        assert "level" in first_point

    def test_trajectory_prediction_insufficient_history(self, mock_security_manager):
        """Test trajectory with insufficient history"""
        # Create client with mock that returns no history
        with patch('src.main.app_state') as mock_app_state:
            mock_state_manager = Mock()
            mock_state_manager.get_mastery_score = AsyncMock(
                return_value=MasteryResult(
                    student_id="test",
                    mastery_score=0.5,
                    level=MasteryLevel.DEVELOPING,
                    components=ComponentScores(0.5, 0.5, 0.5, 0.5),
                    breakdown=MasteryBreakdown(
                        completion=0.2, quiz=0.15, quality=0.1, consistency=0.05,
                        weighted_sum=0.5,
                        weights=Mock()
                    )
                )
            )
            mock_state_manager.get = AsyncMock(return_value=None)
            mock_state_manager.save = AsyncMock()

            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": SecurityManager(jwt_secret="test-secret"),
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            response = client.post(
                "/api/v1/analytics/predictions/trajectory",
                json={"student_id": "test"},
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
            )

            assert response.status_code == 200
            data = response.json()
            # Should still return trajectory with low confidence
            assert len(data["trajectory"]) == 14
            assert data["trajectory"][0]["confidence"] < 0.2

    def test_intervention_prediction_success(self, client, mock_security_manager):
        """Test intervention-aware prediction"""
        payload = {
            "student_id": "student_123",
            "intervention_type": "tutoring"
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week/intervention",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have intervention metadata
        assert "intervention_impact" in data["metadata"]
        assert data["metadata"]["intervention_type"] == "tutoring"
        assert data["predicted_score"] >= 0.75  # Should be higher than base

    def test_intervention_prediction_invalid_type(self, client, mock_security_manager):
        """Test with invalid intervention type"""
        payload = {
            "student_id": "student_123",
            "intervention_type": "invalid_type"
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week/intervention",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 400

    def test_intervention_prediction_missing_type(self, client, mock_security_manager):
        """Test with missing intervention type"""
        payload = {
            "student_id": "student_123"
        }

        response = client.post(
            "/api/v1/analytics/predictions/next-week/intervention",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 400

    def test_mastery_history_endpoint(self, client, mock_security_manager, mock_state_manager):
        """Test mastery history endpoint"""
        payload = {
            "student_id": "student_123",
            "start_date": "2026-01-01",
            "end_date": "2026-01-14",
            "aggregation": "daily"
        }

        response = client.post(
            "/api/v1/analytics/mastery-history",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "student_id" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "data" in data

    def test_mastery_history_invalid_dates(self, client, mock_security_manager):
        """Test with invalid date format"""
        payload = {
            "student_id": "student_123",
            "start_date": "not-a-date",
            "end_date": "2026-01-14"
        }

        response = client.post(
            "/api/v1/analytics/mastery-history",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 400

    def test_mastery_history_reversed_dates(self, client, mock_security_manager):
        """Test with reversed date range"""
        payload = {
            "student_id": "student_123",
            "start_date": "2026-01-14",
            "end_date": "2026-01-01"  # End before start
        }

        response = client.post(
            "/api/v1/analytics/mastery-history",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 400

    def test_accuracy_metrics_endpoint(self, client, mock_security_manager):
        """Test prediction accuracy metrics endpoint"""
        response = client.get(
            "/api/v1/analytics/predictions/accuracy/student_123",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return accuracy structure
        assert "student_id" in data
        assert "metrics" in data
        assert data["student_id"] == "student_123"

    def test_prediction_config_endpoint(self, client, mock_security_manager):
        """Test prediction configuration endpoint"""
        response = client.get(
            "/api/v1/analytics/predictions/config",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return config
        assert "config" in data
        assert "model_version" in data
        assert "min_history_days" in data["config"]
        assert "intervention_threshold" in data["config"]


class TestAnalyticsErrorHandling:
    """Test error handling for analytics endpoints"""

    def test_prediction_service_failure(self, client, mock_security_manager):
        """Test when predictor service fails"""
        with patch('src.services.predictor.PredictorService.predict_next_week') as mock_predict:
            mock_predict.side_effect = Exception("Service failure")

            payload = {"student_id": "student_123"}

            response = client.post(
                "/api/v1/analytics/predictions/next-week",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
            )

            assert response.status_code == 500
            assert "prediction failed" in response.json()["message"].lower()

    def test_authentication_failure(self, client):
        """Test missing authentication"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload
            # No Authorization header
        )

        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test invalid JWT token"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_exposed_exception_details_production(self, client, mock_security_manager):
        """Test that production mode doesn't expose sensitive error details"""
        with patch('os.getenv') as mock_env:
            mock_env.return_value = "production"

            with patch('src.services.predictor.PredictorService.predict_next_week') as mock_predict:
                mock_predict.side_effect = Exception("Sensitive database error: password mismatch")

                payload = {"student_id": "student_123"}

                response = client.post(
                    "/api/v1/analytics/predictions/next-week",
                    json=payload,
                    headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
                )

                assert response.status_code == 500
                # Should not contain sensitive details
                assert "password" not in response.json()["message"].lower()


class TestAnalyticsAuditLogging:
    """Test audit logging for analytics operations"""

    @pytest.mark.asyncio
    async def test_prediction_audit_log_created(self, mock_security_manager, mock_state_manager):
        """Test that prediction requests are audited"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {"student_id": "student_123"}

            response = client.post(
                "/api/v1/analytics/predictions/next-week",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
            )

            assert response.status_code == 200

            # Check audit logs
            audit_logs = mock_security_manager["manager"].audit_logs
            prediction_log = next((log for log in audit_logs if log.action == "PREDICT"), None)

            assert prediction_log is not None
            assert prediction_log.user_id == "student_123"
            assert "student_123" in prediction_log.resource

    @pytest.mark.asyncio
    async def test_intervention_prediction_audit_log(self, mock_security_manager, mock_state_manager):
        """Test intervention prediction audit logging"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {"student_id": "student_123", "intervention_type": "tutoring"}

            response = client.post(
                "/api/v1/analytics/predictions/next-week/intervention",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
            )

            assert response.status_code == 200

            # Check audit logs
            audit_logs = mock_security_manager["manager"].audit_logs
            intervention_log = next((log for log in audit_logs if log.action == "PREDICT_INTERVENTION"), None)

            assert intervention_log is not None
            assert "intervention" in intervention_log.resource
            assert intervention_log.details["intervention_type"] == "tutoring"


class TestPerformanceAndEdgeCases:
    """Test performance characteristics and edge cases"""

    def test_prediction_response_time_estimate(self, client, mock_security_manager):
        """Test that predictions complete within reasonable time"""
        import time

        payload = {"student_id": "student_123"}

        start_time = time.time()
        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )
        end_time = time.time()

        assert response.status_code == 200
        # Should complete within 2 seconds (including overhead)
        assert (end_time - start_time) < 2.0

    def test_trajectory_completeness(self, client, mock_security_manager):
        """Test trajectory contains all required data points"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/analytics/predictions/trajectory",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        data = response.json()

        # Verify trajectory integrity
        trajectory = data["trajectory"]
        assert len(trajectory) == 14

        # Verify each point has required fields
        for point in trajectory:
            required_fields = ["days_from_now", "predicted_score", "confidence", "level"]
            for field in required_fields:
                assert field in point

        # Verify chronological order
        days = [point["days_from_now"] for point in trajectory]
        assert days == list(range(1, 15))

        # Verify scores are within bounds
        scores = [point["predicted_score"] for point in trajectory]
        assert all(0.0 <= score <= 1.0 for score in scores)

    def test_prediction_with_zero_historical_data(self, client, mock_security_manager):
        """Test prediction when student has no historical data at all"""
        with patch('src.main.app_state') as mock_app_state:
            mock_state_manager = Mock()
            mock_state_manager.get_mastery_score = AsyncMock(return_value=None)
            mock_state_manager.get = AsyncMock(return_value=None)
            mock_state_manager.save = AsyncMock()

            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {"student_id": "student_999"}

            response = client.post(
                "/api/v1/analytics/predictions/next-week",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
            )

            # Should still return a prediction (with low confidence)
            assert response.status_code == 200
            data = response.json()
            assert data["confidence"] < 0.3
            assert "insufficient_history" in data["metadata"].get("warning", "")


class TestAnalyticsAPIContracts:
    """Test that analytics endpoints adhere to expected contracts"""

    def test_prediction_result_contract(self, client, mock_security_manager):
        """Test PredictionResult structure is correctly returned"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/analytics/predictions/next-week",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        data = response.json()

        # Required fields from PredictionResult model
        required_fields = [
            "student_id", "predicted_score", "confidence", "trend",
            "intervention_needed", "timeframe_days", "predicted_level",
            "components_projection"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(data["predicted_score"], (int, float))
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["trend"], str)
        assert isinstance(data["intervention_needed"], bool)
        assert isinstance(data["timeframe_days"], int)
        assert isinstance(data["predicted_level"], str)
        assert isinstance(data["components_projection"], dict)

    def test_trajectory_result_contract(self, client, mock_security_manager):
        """Test TrajectoryResult structure is correctly returned"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/analytics/predictions/trajectory",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        data = response.json()

        # Required fields from TrajectoryResult model
        required_fields = [
            "student_id", "trajectory", "confidence_over_time",
            "intervention_points", "overall_trend"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify trajectory point structure
        if data["trajectory"]:
            point = data["trajectory"][0]
            point_fields = ["days_from_now", "predicted_score", "confidence", "level"]
            for field in point_fields:
                assert field in point