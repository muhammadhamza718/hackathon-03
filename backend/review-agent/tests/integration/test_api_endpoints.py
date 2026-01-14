"""
Integration tests for Review Agent API endpoints
Tests endpoints with mocked services and real request/response flow
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime


@pytest.mark.integration
class TestAssessEndpoint:
    """Test the /review/assess endpoint"""

    def test_assess_endpoint_success(self, client, mock_validate_jwt, sample_assessment_request):
        """Test successful assessment request"""
        with patch('api.endpoints.assess.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.85,
                "factors": [{"name": "syntax", "score": 0.9, "weight": 0.15}],
                "strengths": ["Good structure"],
                "improvements": ["Add type hints"],
                "recommendations": ["Add docstrings"],
                "concept_score": 0.8,
                "structure_score": 0.85,
                "efficiency_score": 0.9,
                "category_scores": {"correctness": 0.9},
                "testing_suggestions": ["Test edge cases"],
                "optimization_suggestions": ["None needed"]
            }

            response = client.post(
                "/review/assess",
                json=sample_assessment_request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["score"] == 0.85
            assert "factors" in data
            assert "strengths" in data
            assert data["student_id"] == "test_student"

    def test_assess_endpoint_empty_code(self, client, mock_validate_jwt):
        """Test assessment with empty code"""
        request = {"student_code": "", "problem_context": {}}

        response = client.post(
            "/review/assess",
            json=request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_assess_endpoint_large_code(self, client, mock_validate_jwt):
        """Test assessment with code exceeding size limit"""
        large_code = "x = 1\n" * 30000  # Exceeds 50,000 characters
        request = {"student_code": large_code, "problem_context": {}}

        response = client.post(
            "/review/assess",
            json=request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 413  # Payload too large

    def test_assess_endpoint_batch_success(self, client, mock_validate_jwt, sample_assessment_request):
        """Test batch assessment endpoint"""
        batch_request = [sample_assessment_request] * 3

        with patch('api.endpoints.assess.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.8,
                "factors": [],
                "strengths": [],
                "improvements": [],
                "recommendations": [],
                "concept_score": 0.8,
                "structure_score": 0.8,
                "efficiency_score": 0.8,
                "category_scores": {},
                "testing_suggestions": [],
                "optimization_suggestions": []
            }

            response = client.post(
                "/review/assess/batch",
                json=batch_request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert all(item["status"] == "success" for item in data)

    def test_assess_endpoint_batch_too_many(self, client, mock_validate_jwt, sample_assessment_request):
        """Test batch assessment with too many requests"""
        batch_request = [sample_assessment_request] * 21  # Exceeds limit

        response = client.post(
            "/review/assess/batch",
            json=batch_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "Maximum 20" in response.json()["detail"]

    def test_assess_health_check(self, client, mock_validate_jwt):
        """Test assessment health endpoint"""
        with patch('api.endpoints.assess.check_mcp_connection') as mock_check:
            mock_check.return_value = True

            response = client.get(
                "/review/assess/health",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "assessment"
            assert data["mcp_connected"] is True

    def test_assess_validate_endpoint(self, client, mock_validate_jwt, sample_assessment_request):
        """Test validation endpoint"""
        response = client.post(
            "/review/assess/validate",
            json=sample_assessment_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data


@pytest.mark.integration
class TestHintsEndpoint:
    """Test the /review/hints endpoint"""

    def test_hints_endpoint_success(self, client, mock_validate_jwt, sample_hint_request):
        """Test successful hint generation"""
        with patch('api.endpoints.hints.generate_hint_with_mcp') as mock_hint:
            mock_hint.return_value = {
                "text": "Check your loop boundaries",
                "level": "medium",
                "estimated_time": 10,
                "category": "off_by_one",
                "next_steps": ["Test with small inputs"],
                "student_mastery": 0.6
            }

            response = client.post(
                "/review/hints",
                json=sample_hint_request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["text"]) > 10
            assert data["level"] == "medium"
            assert data["estimated_time"] == 10

    def test_hints_endpoint_invalid_level(self, client, mock_validate_jwt, sample_hint_request):
        """Test hint with invalid level"""
        invalid_request = sample_hint_request.copy()
        invalid_request["hint_level"] = "invalid"

        response = client.post(
            "/review/hints",
            json=invalid_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "Invalid hint level" in response.json()["detail"]

    def test_hints_suggest_endpoint(self, client, mock_validate_jwt, sample_hint_request):
        """Test hint suggestion endpoint"""
        response = client.post(
            "/review/hints/suggest",
            json=sample_hint_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "available_categories" in data
        assert "estimated_hint_count" in data
        assert "recommended_approach" in data

    def test_hints_batch_endpoint(self, client, mock_validate_jwt, sample_hint_request):
        """Test batch hint generation"""
        batch_request = [sample_hint_request] * 2

        with patch('api.endpoints.hints.generate_hint_with_mcp') as mock_hint:
            mock_hint.return_value = {
                "text": "Hint text",
                "level": "medium",
                "estimated_time": 5,
                "category": "general",
                "next_steps": ["Step 1"],
                "student_mastery": 0.5
            }

            response = client.post(
                "/review/hints/batch",
                json=batch_request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(item["status"] == "success" for item in data)

    def test_hints_health_check(self, client, mock_validate_jwt):
        """Test hints health endpoint"""
        with patch('api.endpoints.hints.check_mcp_connection') as mock_check:
            mock_check.return_value = True

            response = client.get(
                "/review/hints/health",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "hints"
            assert data["mcp_connected"] is True


@pytest.mark.integration
class TestFeedbackEndpoint:
    """Test the /review/feedback endpoint"""

    def test_feedback_endpoint_success(self, client, mock_validate_jwt, sample_feedback_request):
        """Test successful feedback generation"""
        with patch('api.endpoints.feedback.assess_code_quality_with_mcp') as mock_assess:
            with patch('api.endpoints.feedback.generate_hint_with_mcp') as mock_hint:
                mock_assess.return_value = {
                    "score": 0.8,
                    "factors": [],
                    "strengths": ["Good naming"],
                    "improvements": ["Add error handling"],
                    "recommendations": [],
                    "concept_score": 0.8,
                    "structure_score": 0.8,
                    "efficiency_score": 0.8,
                    "category_scores": {},
                    "testing_suggestions": [],
                    "optimization_suggestions": []
                }

                mock_hint.return_value = {
                    "text": "Consider error handling",
                    "level": "medium",
                    "estimated_time": 15,
                    "category": "error_handling",
                    "next_steps": ["Add try-catch"],
                    "student_mastery": 0.6
                }

                response = client.post(
                    "/review/feedback",
                    json=sample_feedback_request,
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "summary" in data
                assert "quality_score" in data
                assert "strengths" in data
                assert "improvements" in data
                assert "detailed_feedback" in data

    def test_feedback_quick_endpoint(self, client, mock_validate_jwt, sample_feedback_request):
        """Test quick feedback endpoint"""
        with patch('api.endpoints.feedback.assess_code_quality_with_mcp') as mock_assess:
            with patch('api.endpoints.feedback.generate_hint_with_mcp') as mock_hint:
                mock_assess.return_value = {
                    "score": 0.7,
                    "improvements": ["Issue 1", "Issue 2"]
                }
                mock_hint.return_value = {
                    "text": "Quick hint",
                    "level": "direct",
                    "estimated_time": 5
                }

                response = client.post(
                    "/review/feedback/quick",
                    json=sample_feedback_request,
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "quick_hint" in data
                assert "key_issues" in data

    def test_feedback_batch_endpoint(self, client, mock_validate_jwt, sample_feedback_request):
        """Test batch feedback generation"""
        batch_request = {"submissions": [sample_feedback_request, sample_feedback_request]}

        with patch('api.endpoints.feedback.assess_code_quality_with_mcp') as mock_assess:
            with patch('api.endpoints.feedback.generate_hint_with_mcp') as mock_hint:
                mock_assess.return_value = {
                    "score": 0.8,
                    "factors": [],
                    "strengths": ["Good"],
                    "improvements": ["Improve"],
                    "recommendations": [],
                    "concept_score": 0.8,
                    "structure_score": 0.8,
                    "efficiency_score": 0.8,
                    "category_scores": {},
                    "testing_suggestions": [],
                    "optimization_suggestions": []
                }

                mock_hint.return_value = {
                    "text": "Hint",
                    "level": "medium",
                    "estimated_time": 10,
                    "category": "general",
                    "next_steps": ["Step 1"],
                    "student_mastery": 0.5
                }

                response = client.post(
                    "/review/feedback/batch",
                    json=batch_request,
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["results"]) == 2
                assert "summary" in data
                assert data["summary"]["total_submissions"] == 2

    def test_feedback_health_check(self, client, mock_validate_jwt):
        """Test feedback health endpoint"""
        with patch('api.endpoints.feedback.check_assessment_mcp') as mock_assess:
            with patch('api.endpoints.feedback.check_hint_mcp') as mock_hint:
                mock_assess.return_value = True
                mock_hint.return_value = True

                response = client.get(
                    "/review/feedback/health",
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["service"] == "feedback"
                assert data["mcp_connected"] is True

    def test_feedback_validate_endpoint(self, client, mock_validate_jwt, sample_feedback_request):
        """Test feedback validation endpoint"""
        response = client.post(
            "/review/feedback/validate",
            json=sample_feedback_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "errors" in data


@pytest.mark.integration
class TestDaprIntegration:
    """Test Dapr service invocation endpoint"""

    def test_dapr_process_quality_assessment(self, client, mock_validate_jwt):
        """Test Dapr intent routing for quality assessment"""
        dapr_data = {
            "intent": "quality_assessment",
            "student_code": "def func(): return 42",
            "problem_context": {"topic": "functions"},
            "confidence": 0.9
        }

        with patch('main.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.9,
                "factors": [],
                "strengths": ["Good"],
                "improvements": [],
                "recommendations": []
            }

            response = client.post(
                "/process",
                json=dapr_data,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["result"]["intent"] == "quality_assessment"
            assert "quality_score" in data["result"]

    def test_dapr_process_hint_generation(self, client, mock_validate_jwt):
        """Test Dapr intent routing for hint generation"""
        dapr_data = {
            "intent": "hint_generation",
            "student_code": "x = 5",
            "error_type": "syntax",
            "confidence": 0.8
        }

        with patch('main.generate_hint_with_mcp') as mock_hint:
            mock_hint.return_value = {
                "text": "Check syntax",
                "level": "medium",
                "estimated_time": 5
            }

            response = client.post(
                "/process",
                json=dapr_data,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["result"]["intent"] == "hint_generation"
            assert "hint" in data["result"]

    def test_dapr_process_detailed_feedback(self, client, mock_validate_jwt):
        """Test Dapr intent routing for detailed feedback"""
        dapr_data = {
            "intent": "detailed_feedback",
            "student_code": "def func(): return 42",
            "error_type": "general",
            "confidence": 0.7
        }

        with patch('main.assess_code_quality_with_mcp') as mock_assess:
            with patch('main.generate_hint_with_mcp') as mock_hint:
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

                response = client.post(
                    "/process",
                    json=dapr_data,
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["result"]["intent"] == "detailed_feedback"
                assert "feedback" in data["result"]

    def test_dapr_process_unknown_intent(self, client, mock_validate_jwt):
        """Test Dapr processing with unknown intent"""
        dapr_data = {
            "intent": "unknown_intent",
            "student_code": "x = 5"
        }

        response = client.post(
            "/process",
            json=dapr_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Unknown intent" in data["error"]

    def test_dapr_process_empty_code(self, client, mock_validate_jwt):
        """Test Dapr processing with empty code"""
        dapr_data = {
            "intent": "quality_assessment",
            "student_code": ""
        }

        response = client.post(
            "/process",
            json=dapr_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "No student code" in data["error"]


@pytest.mark.integration
class TestSecurityMiddleware:
    """Test security middleware and authentication"""

    def test_missing_auth_token(self, client):
        """Test endpoint access without auth token"""
        response = client.post(
            "/review/assess",
            json={"student_code": "x = 1", "problem_context": {}}
        )

        assert response.status_code == 403  # FastAPI HTTPBearer raises 403

    def test_invalid_auth_token(self, client):
        """Test endpoint access with invalid token"""
        response = client.post(
            "/review/assess",
            json={"student_code": "x = 1", "problem_context": {}},
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    def test_input_sanitization_middleware(self, client, mock_validate_jwt):
        """Test input sanitization for dangerous patterns"""
        dangerous_requests = [
            {"student_code": "drop table users", "problem_context": {}},
            {"student_code": "<script>alert('xss')</script>", "problem_context": {}},
            {"student_code": "sudo rm -rf /", "problem_context": {}},
            {"student_code": "SELECT * FROM users --", "problem_context": {}}
        ]

        for request in dangerous_requests:
            response = client.post(
                "/review/assess",
                json=request,
                headers={"Authorization": "Bearer test-token"}
            )

            # Should be blocked by middleware
            assert response.status_code in [400, 422]

    def test_security_headers_added(self, client, mock_validate_jwt, sample_assessment_request):
        """Test that security headers are added to responses"""
        with patch('api.endpoints.assess.assess_code_quality_with_mcp') as mock_assess:
            mock_assess.return_value = {
                "score": 0.8,
                "factors": [],
                "strengths": [],
                "improvements": [],
                "recommendations": [],
                "concept_score": 0.8,
                "structure_score": 0.8,
                "efficiency_score": 0.8,
                "category_scores": {},
                "testing_suggestions": [],
                "optimization_suggestions": []
            }

            response = client.post(
                "/review/assess",
                json=sample_assessment_request,
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_on_health_endpoint(self, client, mock_validate_jwt):
        """Test rate limiting on health endpoints"""
        # This would need actual rate limiting to be enabled in test
        # For now, we've mocked it out in conftest
        for _ in range(15):  # Make more requests than the limit
            response = client.get(
                "/review/health",
                headers={"Authorization": "Bearer test-token"}
            )
            # Should always succeed since we've disabled rate limiting in tests
            assert response.status_code == 200


@pytest.mark.integration
class TestRootEndpoints:
    """Test root level endpoints"""

    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "review-agent"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "review-agent"

    def test_ready_endpoint(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "review-agent"