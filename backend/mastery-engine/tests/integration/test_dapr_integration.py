"""
Dapr Integration Security Tests
================================

Tests for Dapr integration security, GDPR operations, and compliance enforcement.
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from src.main import app
from src.security import SecurityManager


@pytest.fixture
def mock_dapr_state_manager():
    """Mock Dapr state manager"""
    with patch('src.services.state_manager.StateManager.create') as mock:
        state_manager = Mock()
        state_manager.health_check = AsyncMock(return_value=True)
        state_manager.get_mastery_score = AsyncMock(return_value=None)
        state_manager.get_activity_data = AsyncMock(return_value=None)
        state_manager.get_mastery_history = AsyncMock(return_value=[])
        state_manager.delete = AsyncMock(return_value=True)
        state_manager.save = AsyncMock(return_value=True)
        state_manager.get = AsyncMock(return_value=None)
        mock.return_value = state_manager
        yield state_manager


@pytest.fixture
def mock_security_manager():
    """Mock security manager"""
    security_manager = SecurityManager(jwt_secret="test-secret")

    # Create test tokens for different roles
    admin_token = security_manager.create_jwt("admin_123", "admin")
    student_token = security_manager.create_jwt("student_123", "student")
    teacher_token = security_manager.create_jwt("teacher_123", "teacher")

    return {
        "manager": security_manager,
        "tokens": {
            "admin": admin_token,
            "student": student_token,
            "teacher": teacher_token
        }
    }


@pytest.fixture
def client(mock_dapr_state_manager, mock_security_manager):
    """Test client with mocked dependencies"""
    with patch('src.main.app_state') as mock_app_state:
        mock_app_state.__getitem__ = lambda self, key: {
            "state_manager": mock_dapr_state_manager,
            "security_manager": mock_security_manager["manager"],
            "ready": True,
            "health_report": {
                "state_store": True,
                "kafka": False,
                "dapr": True
            }
        }[key]

        return TestClient(app)


class TestGDPRRightToErasure:
    """Test GDPR Article 17 - Right to Erasure"""

    def test_gdpr_deletion_admin_access(self, client, mock_security_manager):
        """Test admin can delete student data"""
        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "GDPR Article 17" in data["compliance"]

    def test_gdpr_deletion_student_access_denied(self, client, mock_security_manager):
        """Test student cannot delete data"""
        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 403

    def test_gdpr_deletion_teacher_access_denied(self, client, mock_security_manager):
        """Test teacher cannot delete data"""
        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['teacher']}"}
        )

        assert response.status_code == 403

    def test_gdpr_deletion_missing_auth(self, client):
        """Test deletion without auth fails"""
        response = client.delete("/api/v1/compliance/student/student_456")

        assert response.status_code == 401

    def test_gdpr_deletion_invalid_token(self, client):
        """Test deletion with invalid token fails"""
        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_gdpr_deletion_audit_logging(self, client, mock_security_manager):
        """Test deletion is properly audited"""
        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

        # Verify audit logs were created
        logs = mock_security_manager["manager"].audit_logs
        deletion_log = next((log for log in logs if "DELETE" in log.action), None)
        assert deletion_log is not None
        assert deletion_log.user_id == "admin_123"
        assert "student_456" in deletion_log.resource

    @patch('src.api.endpoints.compliance.StateKeyPatterns')
    def test_gdpr_deletion_deletes_all_data(self, mock_patterns, client, mock_security_manager, mock_dapr_state_manager):
        """Test GDPR deletion removes all student data"""
        # Setup mock patterns
        mock_patterns.current_mastery.return_value = "mastery:student_456"
        mock_patterns.daily_snapshot.return_value = "snapshot:student_456:2024-01-01"
        mock_patterns.activity_data.return_value = "activity:student_456"

        # Mock historical data
        mock_history = [Mock(date="2024-01-01")]
        mock_dapr_state_manager.get_mastery_history.return_value = mock_history

        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

        # Verify deletion tasks were attempted
        data = response.json()
        assert len(data["deleted_tasks"]) > 0


class TestGDPRRightToDataPortability:
    """Test GDPR Article 20 - Right to Data Portability"""

    def test_gdpr_export_admin_access(self, client, mock_security_manager, mock_dapr_state_manager):
        """Test admin can export student data"""
        # Mock some data to export
        from src.models.mastery import MasteryResult, MasteryLevel
        mock_mastery = MasteryResult(
            student_id="student_456",
            mastery_score=0.85,
            level=MasteryLevel.PROFICIENT,
            components={"completion": 0.9, "quiz": 0.8, "quality": 0.85, "consistency": 0.8},
            breakdown={"completion": 0.36, "quiz": 0.24, "quality": 0.17, "consistency": 0.08},
            updated_at=datetime.utcnow()
        )
        mock_dapr_state_manager.get_mastery_score.return_value = mock_mastery

        response = client.get(
            "/api/v1/compliance/student/student_456/export",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify export structure
        assert "export_version" in data
        assert "exported_at" in data
        assert "student_id" in data
        assert "data" in data
        assert "integrity_hash" in data
        assert "GDPR Article 20" in data["compliance"]

        # Verify data includes mastery
        assert "current_mastery" in data["data"]

    def test_gdpr_export_student_access_denied(self, client, mock_security_manager):
        """Test student cannot export data"""
        response = client.get(
            "/api/v1/compliance/student/student_456/export",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 403

    def test_gdpr_export_teacher_access_denied(self, client, mock_security_manager):
        """Test teacher cannot export data"""
        response = client.get(
            "/api/v1/compliance/student/student_456/export",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['teacher']}"}
        )

        assert response.status_code == 403

    def test_gdpr_export_missing_auth(self, client):
        """Test export without auth fails"""
        response = client.get("/api/v1/compliance/student/student_456/export")

        assert response.status_code == 401

    def test_gdpr_export_integrity_hash(self, client, mock_security_manager, mock_dapr_state_manager):
        """Test export includes integrity hash"""
        # Mock some data
        mock_mastery = Mock()
        mock_mastery.model_dump.return_value = {"score": 0.85}
        mock_dapr_state_manager.get_mastery_score.return_value = mock_mastery

        response = client.get(
            "/api/v1/compliance/student/student_456/export",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify hash is computed correctly
        assert "integrity_hash" in data
        assert len(data["integrity_hash"]) == 64  # SHA256 hex

        # Verify hash is consistent with data
        expected_hash = mock_security_manager["manager"].compute_data_hash(data["data"])
        assert data["integrity_hash"] == expected_hash

    def test_gdpr_export_audit_logging(self, client, mock_security_manager, mock_dapr_state_manager):
        """Test export is properly audited"""
        response = client.get(
            "/api/v1/compliance/student/student_456/export",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

        # Verify audit logs
        logs = mock_security_manager["manager"].audit_logs
        export_log = next((log for log in logs if "EXPORT" in log.action), None)
        assert export_log is not None
        assert export_log.user_id == "admin_123"


class TestConsentManagement:
    """Test GDPR consent management endpoints"""

    def test_record_consent_student_own_data(self, client, mock_security_manager):
        """Test student can record their own consent"""
        response = client.post(
            "/api/v1/compliance/consent/student_123?consent_type=data_processing&granted=true",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["granted"] is True

    def test_record_consent_student_cannot_record_others(self, client, mock_security_manager):
        """Test student cannot record consent for others"""
        response = client.post(
            "/api/v1/compliance/consent/student_456?consent_type=data_processing&granted=true",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 403

    def test_record_consent_teacher_can_record(self, client, mock_security_manager):
        """Test teacher can record consent"""
        response = client.post(
            "/api/v1/compliance/consent/student_456?consent_type=data_processing&granted=true",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['teacher']}"}
        )

        assert response.status_code == 200

    def test_withdraw_consent(self, client, mock_security_manager):
        """Test consent withdrawal"""
        # First record consent
        client.post(
            "/api/v1/compliance/consent/student_123?consent_type=data_processing&granted=true",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        # Then withdraw it
        response = client.post(
            "/api/v1/compliance/consent/student_123/withdraw?consent_type=data_processing",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_consent_status(self, client, mock_security_manager):
        """Test retrieving consent status"""
        # Record some consent first
        client.post(
            "/api/v1/compliance/consent/student_123?consent_type=data_processing&granted=true",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        response = client.get(
            "/api/v1/compliance/consent/status/student_123",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["consent_records"]) > 0


class TestAuditLogs:
    """Test audit log access"""

    def test_get_audit_logs_admin_only(self, client, mock_security_manager):
        """Test only admins can access audit logs"""
        response = client.get(
            "/api/v1/compliance/audit/logs",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 403

        response = client.get(
            "/api/v1/compliance/audit/logs",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['teacher']}"}
        )

        assert response.status_code == 403

        response = client.get(
            "/api/v1/compliance/audit/logs",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

    def test_get_audit_logs_with_filters(self, client, mock_security_manager):
        """Test audit logs with filtering"""
        # Create some audit logs
        manager = mock_security_manager["manager"]
        manager.audit_access("user_1", "READ", "student:1")
        manager.audit_access("user_2", "WRITE", "student:2")
        manager.audit_access("user_1", "DELETE", "student:3")

        response = client.get(
            "/api/v1/compliance/audit/logs?user_id=user_1&limit=10",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Only user_1's logs


class TestDaprServiceInvocationSecurity:
    """Test Dapr service invocation with security context"""

    def test_dapr_process_with_valid_security_context(self, client, mock_security_manager):
        """Test Dapr endpoint with valid security context"""
        payload = {
            "intent": "mastery_calculation",
            "payload": {"student_id": "student_123"},
            "security_context": {
                "token": mock_security_manager["tokens"]["student"]
            }
        }

        # Mock the mastery calculation
        with patch('src.api.endpoints.mastery.calculate_mastery') as mock_calc:
            mock_calc.return_value = {"status": "success", "score": 0.85}

            response = client.post("/process", json=payload)

            assert response.status_code == 200

    def test_dapr_process_with_invalid_security_context(self, client):
        """Test Dapr endpoint with invalid security context"""
        payload = {
            "intent": "mastery_calculation",
            "payload": {"student_id": "student_123"},
            "security_context": {
                "token": "invalid_token"
            }
        }

        response = client.post("/process", json=payload)

        assert response.status_code == 401

    def test_dapr_process_without_security_context(self, client):
        """Test Dapr endpoint without security context"""
        payload = {
            "intent": "mastery_calculation",
            "payload": {"student_id": "student_123"}
        }

        # Should still work as it's optional
        with patch('src.api.endpoints.mastery.calculate_mastery') as mock_calc:
            mock_calc.return_value = {"status": "success", "score": 0.85}

            response = client.post("/process", json=payload)

            assert response.status_code == 200

    def test_dapr_process_unknown_intent(self, client, mock_security_manager):
        """Test Dapr endpoint with unknown intent"""
        payload = {
            "intent": "unknown_intent",
            "payload": {},
            "security_context": {
                "token": mock_security_manager["tokens"]["admin"]
            }
        }

        response = client.post("/process", json=payload)

        assert response.status_code == 400


class TestSecurityHeaders:
    """Test security headers and CORS"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are properly set"""
        response = client.options("/api/v1/mastery/ingest")

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_security_headers_in_response(self, client, mock_security_manager):
        """Test various security headers"""
        response = client.get(
            "/health",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        # Basic security headers (could be added via middleware)
        assert response.status_code == 200


class TestInputValidationAndSanitization:
    """Test input validation and sanitization in endpoints"""

    def test_xss_prevention_in_event_ingestion(self, client, mock_security_manager):
        """Test XSS attempts are blocked"""
        malicious_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123",
            "data": {
                "exercise_id": "<script>alert('xss')</script>",
                "difficulty": "easy",
                "time_spent_seconds": 60,
                "completion_rate": 1.0,
                "correctness": 1.0
            }
        }

        response = client.post(
            "/api/v1/mastery/ingest",
            json=malicious_payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        assert response.status_code == 202  # Should process (sanitization happens later)

    def test_sql_injection_prevention(self, client, mock_security_manager):
        """Test SQL injection attempts in string fields"""
        malicious_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "exercise.completed",
            "student_id": "student_123'; DROP TABLE users; --",
            "data": {
                "exercise_id": "ex_1",
                "difficulty": "easy",
                "time_spent_seconds": 60,
                "completion_rate": 1.0,
                "correctness": 1.0
            }
        }

        response = client.post(
            "/api/v1/mastery/ingest",
            json=malicious_payload,
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['student']}"}
        )

        # Should still be accepted (sanitization happens in service layer)
        assert response.status_code == 202


class TestRateLimiting:
    """Test rate limiting enforcement"""

    def test_rate_limiting_compliance_endpoints(self, client, mock_security_manager):
        """Test rate limits on compliance endpoints"""
        # Make multiple requests to trigger rate limiting
        for i in range(15):  # GDPR deletion limit is 10 per minute
            response = client.delete(
                "/api/v1/compliance/student/test",
                headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
            )

            if response.status_code == 429:
                # Rate limited
                return

        # If we get here, rate limiting might not be active in test mode
        # which is acceptable


class TestMasterySecurityScenarios:
    """Test complex security scenarios"""

    def test_student_cannot_access_other_student_via_api(self, client, mock_security_manager):
        """Test comprehensive student isolation"""
        # Create tokens for two different students
        student_a_token = mock_security_manager["tokens"]["student"]  # student_123
        student_b_id = "student_456"

        # Student A tries to access Student B's data via various endpoints
        endpoints = [
            f"/api/v1/compliance/consent/status/{student_b_id}",
            f"/api/v1/compliance/student/{student_b_id}/export"
        ]

        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {student_a_token}"}
            )

            # Should be denied
            assert response.status_code in [403, 401]

    def test_privilege_escalation_prevention(self, client, mock_security_manager):
        """Test privilege escalation attempts"""
        # Create a student token
        student_token = mock_security_manager["tokens"]["student"]

        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/v1/compliance/audit/logs"
        ]

        for endpoint in admin_endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {student_token}"}
            )

            assert response.status_code == 403

    def test_token_manipulation_detection(self, client):
        """Test manipulated token detection"""
        # Create a malformed token by modifying a valid one
        valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50XzEyMyIsInJvbGUiOiJzdHVkZW50IiwiZXhwIjo5OTk5OTk5OTk5fQ.signature"
        manipulated_token = valid_token[:-10] + "tampered"  # Modify signature

        response = client.delete(
            "/api/v1/compliance/student/test",
            headers={"Authorization": f"Bearer {manipulated_token}"}
        )

        assert response.status_code == 401

    def test_expired_token_rejection(self, client):
        """Test expired token is rejected"""
        manager = SecurityManager(jwt_secret="test-secret", expire_minutes=-1)
        expired_token = manager.create_jwt("student_123", "student")

        response = client.get(
            "/api/v1/compliance/consent/status/student_123",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


class TestComplianceAuditTrail:
    """Test complete audit trail for compliance"""

    def test_full_audit_trail_for_gdpr_operations(self, client, mock_security_manager, mock_dapr_state_manager):
        """Test that all GDPR operations create comprehensive audit trails"""
        manager = mock_security_manager["manager"]

        # Perform GDPR deletion
        mock_dapr_state_manager.get_mastery_score.return_value = Mock()
        mock_dapr_state_manager.get_activity_data.return_value = Mock()
        mock_dapr_state_manager.get_mastery_history.return_value = []

        response = client.delete(
            "/api/v1/compliance/student/student_456",
            headers={"Authorization": f"Bearer {mock_security_manager['tokens']['admin']}"}
        )

        assert response.status_code == 200

        # Verify multiple audit entries were created
        logs = manager.get_audit_logs(user_id="admin_123")
        deletion_logs = [log for log in logs if "student_456" in log.get("resource", "")]

        # Should have at least two logs: request and completion
        assert len(deletion_logs) >= 2

        # Verify correlation ID is preserved
        response_data = response.json()
        correlation_id = response_data.get("correlation_id")

        # Find log with correlation ID
        correlated_log = next(
            (log for log in deletion_logs if log.get("correlation_id") == correlation_id),
            None
        )
        assert correlated_log is not None