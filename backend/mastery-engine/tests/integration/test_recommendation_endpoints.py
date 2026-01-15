"""
Recommendation Endpoints Integration Tests
==========================================

Integration tests for adaptive learning recommendation endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta
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

    # Mock current mastery with some weak areas
    current_mastery = MasteryResult(
        student_id="student_123",
        mastery_score=0.6,
        level=MasteryLevel.DEVELOPING,
        components=ComponentScores(0.5, 0.65, 0.7, 0.55),  # Completion and consistency below 0.7
        breakdown=MasteryBreakdown(
            completion=0.2, quiz=0.195, quality=0.14, consistency=0.065,
            weighted_sum=0.6,
            weights=Mock()
        )
    )
    state_manager.get_mastery_score = AsyncMock(return_value=current_mastery)

    # Mock save operation
    state_manager.save = AsyncMock(return_value=True)

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


class TestAdaptiveRecommendations:
    """Test adaptive recommendation endpoint functionality"""

    def test_adaptive_recommendations_success(self, client, mock_security_manager):
        """Test successful adaptive recommendation generation"""
        payload = {
            "student_id": "student_123",
            "limit": 5
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Should return a list of recommendations
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify recommendation structure
        recommendation = data[0]
        assert "action" in recommendation
        assert "area" in recommendation
        assert "priority" in recommendation
        assert "description" in recommendation
        assert "estimated_time" in recommendation
        assert "resources" in recommendation
        assert "confidence" in recommendation

        # Should have recommendations for weak components (completion, consistency)
        areas = [rec["area"] for rec in data]
        assert "completion" in areas or "consistency" in areas

    def test_adaptive_recommendations_with_filters(self, client, mock_security_manager):
        """Test recommendations with component and priority filters"""
        payload = {
            "student_id": "student_123",
            "limit": 3,
            "component_filter": ["completion"],
            "priority": "high"
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all recommendations match filters
        for rec in data:
            assert rec["area"] == "completion"
            assert rec["priority"] == "high"

    def test_adaptive_recommendations_student_access_denied(self, client, mock_security_manager):
        """Test that students cannot generate recommendations for others"""
        payload = {
            "student_id": "student_456",  # Different student
            "limit": 5
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 403

    def test_adaptive_recommendations_admin_access(self, client, mock_security_manager):
        """Test that admins can generate recommendations for any student"""
        payload = {
            "student_id": "student_456",  # Different student
            "limit": 5
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}  # Fixed: remove extra quote
        )

        # Should succeed or return 404 if student doesn't exist (but not 403)
        assert response.status_code in [200, 404]

    def test_adaptive_recommendations_missing_student_id(self, client, mock_security_manager):
        """Test missing student_id"""
        payload = {
            "limit": 5
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_adaptive_recommendations_invalid_priority(self, client, mock_security_manager):
        """Test invalid priority filter"""
        payload = {
            "student_id": "student_123",
            "priority": "invalid_priority"
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_adaptive_recommendations_invalid_component_filter(self, client, mock_security_manager):
        """Test invalid component filter"""
        payload = {
            "student_id": "student_123",
            "component_filter": ["invalid_component"]
        }

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400


class TestLearningPath:
    """Test learning path endpoint functionality"""

    def test_learning_path_success(self, client, mock_security_manager):
        """Test successful learning path generation"""
        payload = {
            "student_id": "student_123",
            "target_level": "proficient"
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify learning path structure
        assert "student_id" in data
        assert "path_id" in data
        assert "recommendations" in data
        assert "estimated_completion" in data
        assert "total_time_estimate" in data
        assert "priority_areas" in data
        assert "metadata" in data

        # Verify data types and values
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["total_time_estimate"], (int, float))
        assert data["total_time_estimate"] > 0
        assert isinstance(data["priority_areas"], list)
        assert len(data["recommendations"]) > 0

        # Verify metadata
        metadata = data["metadata"]
        assert "target_level" in metadata
        assert "current_level" in metadata
        assert metadata["target_level"] == "PROFICIENT"

    def test_learning_path_without_target_level(self, client, mock_security_manager):
        """Test learning path auto-detects target level"""
        payload = {
            "student_id": "student_123"
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Should auto-detect target level (DEVELOPING -> PROFICIENT)
        assert data["metadata"]["target_level"] == "PROFICIENT"

    def test_learning_path_with_duration_limit(self, client, mock_security_manager):
        """Test learning path with maximum duration"""
        payload = {
            "student_id": "student_123",
            "target_level": "master",
            "max_duration_minutes": 60
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Total time should be limited
        assert data["total_time_estimate"] <= 60

    def test_learning_path_invalid_target_level(self, client, mock_security_manager):
        """Test invalid target level"""
        payload = {
            "student_id": "student_123",
            "target_level": "invalid_level"
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_learning_path_missing_student_id(self, client, mock_security_manager):
        """Test missing student_id"""
        payload = {
            "target_level": "proficient"
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_learning_path_student_access_denied(self, client, mock_security_manager):
        """Test that students cannot generate paths for others"""
        payload = {
            "student_id": "student_456",
            "target_level": "proficient"
        }

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 403

    def test_learning_path_no_mastery_data(self, client, mock_security_manager):
        """Test learning path when student has no mastery data"""
        with patch('src.main.app_state') as mock_app_state:
            mock_state_manager = Mock()
            mock_state_manager.get_mastery_score = AsyncMock(return_value=None)

            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {
                "student_id": "nonexistent_student",
                "target_level": "proficient"
            }

            response = client.post(
                "/api/v1/recommendations/learning-path",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
            )

            assert response.status_code == 404


class TestMCPSkillRecommendations:
    """Test MCP skill recommendation endpoint"""

    def test_mcp_skill_recommendations_success(self, client, mock_security_manager):
        """Test successful MCP skill recommendations"""
        payload = {
            "student_id": "student_123"
        }

        response = client.post(
            "/api/v1/recommendations/mcp/skill-recommendations",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify MCP response structure
        assert "student_id" in data
        assert "timestamp" in data
        assert "priority_areas" in data
        assert "overall_score" in data
        assert "current_level" in data

        # Verify priority areas structure
        if data["priority_areas"]:
            area = data["priority_areas"][0]
            assert "component" in area
            assert "gap" in area
            assert "action" in area
            assert "priority" in area

    def test_mcp_skill_with_path_generation(self, client, mock_security_manager):
        """Test MCP skill with path generation enabled"""
        payload = {
            "student_id": "student_123",
            "use_path": True
        }

        response = client.post(
            "/api/v1/recommendations/mcp/skill-recommendations",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Should include path when use_path=True
        assert "path" in data
        assert "total_time" in data
        assert "daily_commitment" in data
        assert "estimated_completion_days" in data

        # Verify path structure
        if data["path"]:
            path_item = data["path"][0]
            assert "action" in path_item
            assert "area" in path_item
            assert "description" in path_item
            assert "time" in path_item

    def test_mcp_skill_missing_student_id(self, client, mock_security_manager):
        """Test MCP skill with missing student_id"""
        payload = {}

        response = client.post(
            "/api/v1/recommendations/mcp/skill-recommendations",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_mcp_skill_student_access_denied(self, client, mock_security_manager):
        """Test that students cannot use MCP skill for others"""
        payload = {
            "student_id": "student_456"
        }

        response = client.post(
            "/api/v1/recommendations/mcp/skill-recommendations",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 403

    def test_mcp_skill_no_mastery_data(self, client, mock_security_manager):
        """Test MCP skill when student has no mastery data"""
        with patch('src.main.app_state') as mock_app_state:
            mock_state_manager = Mock()
            mock_state_manager.get_mastery_score = AsyncMock(return_value=None)

            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {
                "student_id": "nonexistent_student"
            }

            response = client.post(
                "/api/v1/recommendations/mcp/skill-recommendations",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
            )

            assert response.status_code == 404


class TestRecommendationConfig:
    """Test recommendation configuration endpoint"""

    def test_get_config_success(self, client, mock_security_manager):
        """Test successful config retrieval"""
        response = client.get(
            "/api/v1/recommendations/config",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify config structure
        assert "model_version" in data
        assert "config" in data
        assert "notes" in data

        config = data["config"]
        assert "completion_threshold" in config
        assert "quiz_threshold" in config
        assert "quality_threshold" in config
        assert "consistency_threshold" in config
        assert "high_gap_threshold" in config
        assert "medium_gap_threshold" in config

    def test_get_config_requires_auth(self, client):
        """Test that config endpoint requires authentication"""
        response = client.get("/api/v1/recommendations/config")
        assert response.status_code == 401

    def test_get_config_different_roles(self, client, mock_security_manager):
        """Test that different roles can access config"""
        for role, token in mock_security_manager["tokens"].items():
            response = client.get(
                "/api/v1/recommendations/config",
                headers={"Authorization": f"Bearer {token}"}  # Fixed: remove extra quote
            )
            assert response.status_code == 200


class TestRecommendationFeedback:
    """Test recommendation feedback submission"""

    def test_submit_feedback_success(self, client, mock_security_manager):
        """Test successful feedback submission"""
        payload = {
            "recommendation_id": "rec_123",
            "completed": True,
            "time_taken": 25,
            "satisfaction_rating": 4,
            "improvement_score": 0.15
        }

        response = client.post(
            "/api/v1/recommendations/feedback",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["status"] == "received"
        assert "Thank you for your feedback" in data["message"]

    def test_submit_feedback_minimal(self, client, mock_security_manager):
        """Test feedback submission with minimal data"""
        payload = {
            "recommendation_id": "rec_123"
        }

        response = client.post(
            "/api/v1/recommendations/feedback",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200

    def test_submit_feedback_missing_recommendation_id(self, client, mock_security_manager):
        """Test feedback submission without recommendation_id"""
        payload = {
            "completed": True,
            "satisfaction_rating": 4
        }

        response = client.post(
            "/api/v1/recommendations/feedback",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_submit_feedback_invalid_satisfaction(self, client, mock_security_manager):
        """Test feedback with invalid satisfaction rating"""
        payload = {
            "recommendation_id": "rec_123",
            "satisfaction_rating": 6  # Should be 1-5
        }

        response = client.post(
            "/api/v1/recommendations/feedback",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 400

    def test_submit_feedback_student_access_only(self, client, mock_security_manager):
        """Test that only students can submit feedback for their own recommendations"""
        payload = {
            "recommendation_id": "rec_123",
            "completed": True,
            "satisfaction_rating": 4
        }

        # Admins should be able to submit feedback
        response = client.post(
            "/api/v1/recommendations/feedback",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}  # Fixed: remove extra quote
        )
        # Admins might not have sub claim matching student_id, but feedback doesn't validate student access
        assert response.status_code == 200


class TestRecommendationHistory:
    """Test recommendation history endpoint"""

    def test_get_history_success(self, client, mock_security_manager):
        """Test successful history retrieval"""
        response = client.get(
            "/api/v1/recommendations/recommendations/student_123/history",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "student_id" in data
        assert "days" in data
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_get_history_with_days_parameter(self, client, mock_security_manager):
        """Test history with custom days parameter"""
        response = client.get(
            "/api/v1/recommendations/recommendations/student_123/history?days=14",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 14

    def test_get_history_invalid_days_range(self, client, mock_security_manager):
        """Test history with invalid days parameter"""
        # Days must be between 1 and 30
        response = client.get(
            "/api/v1/recommendations/recommendations/student_123/history?days=31",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 422  # Validation error

    def test_get_history_student_access_denied(self, client, mock_security_manager):
        """Test that students cannot access others' history"""
        response = client.get(
            "/api/v1/recommendations/recommendations/student_456/history",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 403

    def test_get_history_admin_access(self, client, mock_security_manager):
        """Test that admins can access any history"""
        response = client.get(
            "/api/v1/recommendations/recommendations/student_456/history",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}  # Fixed: remove extra quote
        )

        assert response.status_code == 200


class TestRecommendationAuditLogging:
    """Test audit logging for recommendation operations"""

    @pytest.mark.asyncio
    async def test_adaptive_recommendations_audit_log(self, mock_security_manager, mock_state_manager):
        """Test that adaptive recommendations are audited"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {
                "student_id": "student_123",
                "limit": 3
            }

            response = client.post(
                "/api/v1/recommendations/adaptive",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
            )

            assert response.status_code == 200

            # Check audit logs
            audit_logs = mock_security_manager["manager"].audit_logs
            recommendation_log = next((log for log in audit_logs if log.action == "GENERATE_RECOMMENDATIONS"), None)

            assert recommendation_log is not None
            assert recommendation_log.user_id == "student_123"
            assert "recommendations:student_123" in recommendation_log.resource

    @pytest.mark.asyncio
    async def test_learning_path_audit_log(self, mock_security_manager, mock_state_manager):
        """Test that learning path generation is audited"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "security_manager": mock_security_manager["manager"],
                "state_manager": mock_state_manager,
                "ready": True
            }[key]

            client = TestClient(app)

            payload = {
                "student_id": "student_123",
                "target_level": "proficient"
            }

            response = client.post(
                "/api/v1/recommendations/learning-path",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
            )

            assert response.status_code == 200

            # Check audit logs
            audit_logs = mock_security_manager["manager"].audit_logs
            path_log = next((log for log in audit_logs if log.action == "GENERATE_LEARNING_PATH"), None)

            assert path_log is not None
            assert path_log.user_id == "student_123"
            assert "learning_path:student_123" in path_log.resource


class TestRecommendationErrorHandling:
    """Test error handling for recommendation endpoints"""

    def test_recommendation_service_failure(self, client, mock_security_manager):
        """Test when recommendation service fails"""
        with patch('src.services.recommendation_engine.RecommendationEngine.generate_adaptive_recommendations') as mock_gen:
            mock_gen.side_effect = Exception("Service failure")

            payload = {"student_id": "student_123"}

            response = client.post(
                "/api/v1/recommendations/adaptive",
                json=payload,
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
            )

            assert response.status_code == 500
            assert "recommendation generation failed" in response.json()["detail"].lower()

    def test_authentication_failure(self, client):
        """Test missing authentication"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload
            # No Authorization header
        )

        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Test invalid JWT token"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": "Bearer invalid.token.here"}  # Fixed: remove extra quote
        )

        assert response.status_code == 401


class TestRecommendationAPIContracts:
    """Test that recommendation endpoints adhere to expected contracts"""

    def test_adaptive_recommendations_contract(self, client, mock_security_manager):
        """Test AdaptiveRecommendation structure is correctly returned"""
        payload = {"student_id": "student_123"}

        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        data = response.json()

        # Required fields from AdaptiveRecommendation model
        required_fields = [
            "action", "area", "priority", "description", "resources", "confidence"
        ]

        if data:  # If we have recommendations
            for field in required_fields:
                assert field in data[0], f"Missing required field: {field}"

            # Verify data types
            assert isinstance(data[0]["action"], str)
            assert isinstance(data[0]["area"], str)
            assert isinstance(data[0]["priority"], str)
            assert isinstance(data[0]["description"], str)
            assert isinstance(data[0]["resources"], list)
            assert isinstance(data[0]["confidence"], (int, float))

    def test_learning_path_contract(self, client, mock_security_manager):
        """Test LearningPath structure is correctly returned"""
        payload = {"student_id": "student_123", "target_level": "proficient"}

        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )

        data = response.json()

        # Required fields from LearningPath model
        required_fields = [
            "student_id", "path_id", "recommendations", "estimated_completion",
            "total_time_estimate", "priority_areas"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify data types
        assert isinstance(data["student_id"], str)
        assert isinstance(data["path_id"], str)
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["total_time_estimate"], (int, float))
        assert isinstance(data["priority_areas"], list)


class TestRecommendationPerformance:
    """Test performance characteristics of recommendation endpoints"""

    def test_adaptive_recommendations_response_time(self, client, mock_security_manager):
        """Test that recommendations complete within reasonable time"""
        import time

        payload = {"student_id": "student_123", "limit": 5}

        start_time = time.time()
        response = client.post(
            "/api/v1/recommendations/adaptive",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )
        end_time = time.time()

        assert response.status_code == 200
        # Should complete within 2 seconds
        assert (end_time - start_time) < 2.0

    def test_learning_path_response_time(self, client, mock_security_manager):
        """Test that learning path generation completes within reasonable time"""
        import time

        payload = {"student_id": "student_123", "target_level": "proficient"}

        start_time = time.time()
        response = client.post(
            "/api/v1/recommendations/learning-path",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )
        end_time = time.time()

        assert response.status_code == 200
        # Should complete within 3 seconds (path generation is more complex)
        assert (end_time - start_time) < 3.0

    def test_mcp_skill_response_time(self, client, mock_security_manager):
        """Test that MCP skill recommendations are fast"""
        import time

        payload = {"student_id": "student_123"}

        start_time = time.time()
        response = client.post(
            "/api/v1/recommendations/mcp/skill-recommendations",
            json=payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}  # Fixed: remove extra quote
        )
        end_time = time.time()

        assert response.status_code == 200
        # MCP should be very fast (under 1 second)
        assert (end_time - start_time) < 1.0