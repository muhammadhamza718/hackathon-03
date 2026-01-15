"""
Security Unit Tests
===================

Comprehensive security tests for JWT validation, RBAC, audit logging, and GDPR compliance.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from jose import JWTError, jwt
from fastapi import HTTPException

from src.security import (
    SecurityManager, Role, Permission, AuditLog, ConsentRecord,
    ROLE_PERMISSIONS
)


class TestJWTValidation:
    """Test JWT token validation and generation"""

    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        manager = SecurityManager(jwt_secret="test-secret")

        token = manager.create_jwt(
            user_id="student_123",
            role="student",
            additional_claims={"custom": "value"}
        )

        assert token is not None
        assert isinstance(token, str)

    def test_jwt_token_validation_success(self):
        """Test successful JWT validation"""
        manager = SecurityManager(jwt_secret="test-secret")

        token = manager.create_jwt(user_id="student_123", role="student")
        claims = manager.validate_jwt(token)

        assert claims["sub"] == "student_123"
        assert claims["role"] == "student"
        assert "exp" in claims
        assert "iat" in claims

    def test_jwt_token_validation_expired(self):
        """Test expired JWT token"""
        manager = SecurityManager(jwt_secret="test-secret", expire_minutes=-1)

        token = manager.create_jwt(user_id="student_123", role="student")

        with pytest.raises(JWTError, match="expired"):
            manager.validate_jwt(token)

    def test_jwt_token_invalid_signature(self):
        """Test JWT token with wrong secret"""
        manager1 = SecurityManager(jwt_secret="secret1")
        manager2 = SecurityManager(jwt_secret="secret2")

        token = manager1.create_jwt(user_id="student_123", role="student")

        with pytest.raises(JWTError):
            manager2.validate_jwt(token)

    def test_jwt_token_missing_required_claims(self):
        """Test JWT token with missing claims"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Create malformed payload
        payload = {"sub": "student_123"}  # Missing role, exp
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        with pytest.raises(JWTError, match="Missing required claim"):
            manager.validate_jwt(token)

    def test_jwt_token_invalid_role(self):
        """Test JWT token with invalid role"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Create token with invalid role
        payload = {
            "sub": "student_123",
            "role": "superadmin",  # Invalid role
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")

        with pytest.raises(JWTError, match="Invalid role"):
            manager.validate_jwt(token)


class TestRBAC:
    """Test Role-Based Access Control"""

    def test_role_permissions_matrix_integrity(self):
        """Test that RBAC matrix is properly defined"""
        # Verify all roles exist in enum and matrix
        enum_roles = [role.value for role in Role]
        matrix_roles = list(ROLE_PERMISSIONS.keys())

        assert set(enum_roles) == set(matrix_roles)

        # Verify all roles have permissions
        for role, permissions in ROLE_PERMISSIONS.items():
            assert len(permissions) > 0
            for perm in permissions:
                assert perm in Permission

    def test_student_permissions(self):
        """Test student has correct permissions"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Students can read own data
        assert manager.check_permission(
            "student", Permission.READ_OWN_DATA, "student_123", "student_123"
        )

        # Students cannot read all data
        assert not manager.check_permission(
            "student", Permission.READ_ALL_DATA, "student_123"
        )

        # Students cannot delete data
        assert not manager.check_permission(
            "student", Permission.DELETE_DATA, "student_123"
        )

    def test_teacher_permissions(self):
        """Test teacher has correct permissions"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Teachers can read all data
        assert manager.check_permission(
            "teacher", Permission.READ_ALL_DATA, "teacher_123"
        )

        # Teachers cannot delete data
        assert not manager.check_permission(
            "teacher", Permission.DELETE_DATA, "teacher_123"
        )

    def test_admin_permissions(self):
        """Test admin has all permissions"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Admins can do everything
        assert manager.check_permission("admin", Permission.READ_OWN_DATA, "admin_123")
        assert manager.check_permission("admin", Permission.READ_ALL_DATA, "admin_123")
        assert manager.check_permission("admin", Permission.WRITE_DATA, "admin_123")
        assert manager.check_permission("admin", Permission.DELETE_DATA, "admin_123")
        assert manager.check_permission("admin", Permission.EXPORT_DATA, "admin_123")
        assert manager.check_permission("admin", Permission.MANAGE_USERS, "admin_123")

    def test_student_cannot_access_other_students_data(self):
        """Test student isolation"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Student A tries to access Student B's data
        assert not manager.check_permission(
            "student", Permission.READ_OWN_DATA, "student_a", "student_b"
        )

    def test_check_permission_invalid_role(self):
        """Test permission check with invalid role"""
        manager = SecurityManager(jwt_secret="test-secret")

        result = manager.check_permission(
            "invalid_role", Permission.READ_OWN_DATA, "user_123"
        )
        assert result is False

    def test_security_context_validation(self):
        """Test complete security context validation"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Create valid token
        token = manager.create_jwt(user_id="student_123", role="student")

        security_context = {"token": token}
        required_permissions = [Permission.READ_OWN_DATA]

        is_valid, error_msg = manager.validate_security_context(
            security_context, required_permissions
        )

        assert is_valid is True
        assert error_msg == ""

    def test_security_context_missing_token(self):
        """Test security context without token"""
        manager = SecurityManager(jwt_secret="test-secret")

        security_context = {}
        required_permissions = [Permission.READ_OWN_DATA]

        is_valid, error_msg = manager.validate_security_context(
            security_context, required_permissions
        )

        assert is_valid is False
        assert "Missing token" in error_msg

    def test_security_context_insufficient_permissions(self):
        """Test security context with insufficient permissions"""
        manager = SecurityManager(jwt_secret="test-secret")

        token = manager.create_jwt(user_id="student_123", role="student")
        security_context = {"token": token}
        required_permissions = [Permission.DELETE_DATA]  # Student doesn't have this

        is_valid, error_msg = manager.validate_security_context(
            security_context, required_permissions
        )

        assert is_valid is False
        assert "Insufficient permissions" in error_msg


class TestAuditLogging:
    """Test audit logging functionality"""

    def test_audit_log_creation(self):
        """Test audit log entry creation"""
        log = AuditLog(
            user_id="user_123",
            action="READ",
            resource="student:123:data",
            details={"correlation_id": "abc123"}
        )

        assert log.user_id == "user_123"
        assert log.action == "READ"
        assert log.resource == "student:123:data"
        assert log.success is True
        assert log.correlation_id == "abc123"
        assert log.timestamp is not None

    def test_audit_log_to_dict(self):
        """Test audit log serialization"""
        log = AuditLog(
            user_id="user_123",
            action="DELETE",
            resource="student:123:data",
            success=False,
            details={"reason": "gdpr_request"}
        )

        log_dict = log.to_dict()

        assert log_dict["user_id"] == "user_123"
        assert log_dict["action"] == "DELETE"
        assert log_dict["resource"] == "student:123:data"
        assert log_dict["success"] is False
        assert log_dict["details"]["reason"] == "gdpr_request"

    def test_security_manager_audit_access(self):
        """Test security manager audit logging"""
        manager = SecurityManager(jwt_secret="test-secret")

        manager.audit_access(
            user_id="admin_123",
            action="EXPORT",
            resource="student:456",
            details={"format": "JSON"}
        )

        # Check that log was added
        assert len(manager.audit_logs) == 1
        log = manager.audit_logs[0]
        assert log.user_id == "admin_123"
        assert log.action == "EXPORT"
        assert log.resource == "student:456"

    def test_get_audit_logs_filtered(self):
        """Test retrieving filtered audit logs"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Add multiple logs
        manager.audit_access("user_1", "READ", "student:1")
        manager.audit_access("user_2", "WRITE", "student:2")
        manager.audit_access("user_1", "DELETE", "student:3")

        # Filter by user_id
        user1_logs = manager.get_audit_logs(user_id="user_1")
        assert len(user1_logs) == 2

        # Filter by resource_type
        read_logs = manager.get_audit_logs(resource_type="student")
        assert len(read_logs) == 3

        # Limit
        limited_logs = manager.get_audit_logs(limit=2)
        assert len(limited_logs) == 2


class TestConsentManagement:
    """Test GDPR consent tracking"""

    def test_consent_record_creation(self):
        """Test consent record creation"""
        consent = ConsentRecord(
            student_id="student_123",
            consent_type="data_processing",
            granted=True
        )

        assert consent.student_id == "student_123"
        assert consent.consent_type == "data_processing"
        assert consent.granted is True
        assert consent.withdrawn is False
        assert consent.timestamp is not None

    def test_consent_withdrawal(self):
        """Test consent withdrawal"""
        consent = ConsentRecord(
            student_id="student_123",
            consent_type="data_processing",
            granted=True
        )

        consent.withdraw()

        assert consent.withdrawn is True
        assert consent.withdrawn_at is not None

    def test_consent_to_dict(self):
        """Test consent serialization"""
        consent = ConsentRecord(
            student_id="student_123",
            consent_type="analytics",
            granted=True,
            version="2.0"
        )

        consent_dict = consent.to_dict()

        assert consent_dict["student_id"] == "student_123"
        assert consent_dict["consent_type"] == "analytics"
        assert consent_dict["granted"] is True
        assert consent_dict["version"] == "2.0"
        assert consent_dict["withdrawn"] is False
        assert consent_dict["withdrawn_at"] is None

    def test_security_manager_record_consent(self):
        """Test recording consent via SecurityManager"""
        manager = SecurityManager(jwt_secret="test-secret")

        consent = manager.record_consent(
            student_id="student_123",
            consent_type="data_processing",
            granted=True
        )

        assert consent.student_id == "student_123"
        assert consent.consent_type == "data_processing"

        # Check stored in consent_store
        key = "student_123:data_processing"
        assert key in manager.consent_store
        assert manager.consent_store[key] == consent

    def test_security_manager_withdraw_consent(self):
        """Test withdrawing consent via SecurityManager"""
        manager = SecurityManager(jwt_secret="test-secret")

        # Record consent first
        manager.record_consent("student_123", "data_processing", True)

        # Withdraw it
        success = manager.withdraw_consent("student_123", "data_processing")

        assert success is True
        consent = manager.consent_store["student_123:data_processing"]
        assert consent.withdrawn is True

    def test_withdraw_nonexistent_consent(self):
        """Test withdrawing nonexistent consent"""
        manager = SecurityManager(jwt_secret="test-secret")

        success = manager.withdraw_consent("student_123", "nonexistent")
        assert success is False

    def test_has_active_consent(self):
        """Test checking for active consent"""
        manager = SecurityManager(jwt_secret="test-secret")

        # No consent initially
        assert not manager.has_active_consent("student_123", "data_processing")

        # Record consent
        manager.record_consent("student_123", "data_processing", True)
        assert manager.has_active_consent("student_123", "data_processing")

        # Withdraw consent
        manager.withdraw_consent("student_123", "data_processing")
        assert not manager.has_active_consent("student_123", "data_processing")

    def test_has_active_consent_granted_false(self):
        """Test consent with granted=False"""
        manager = SecurityManager(jwt_secret="test-secret")

        manager.record_consent("student_123", "data_processing", False)
        assert not manager.has_active_consent("student_123", "data_processing")


class TestInputSanitization:
    """Test input sanitization against injection attacks"""

    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        manager = SecurityManager(jwt_secret="test-secret")

        clean_input = manager.sanitize_input("  hello world  ")
        assert clean_input == "hello world"

    def test_sanitize_input_xss_prevention(self):
        """Test XSS prevention"""
        manager = SecurityManager(jwt_secret="test-secret")

        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "onload=alert(1)",
            "onerror=alert(1)"
        ]

        for dangerous in dangerous_inputs:
            result = manager.sanitize_input(dangerous)
            assert result == "[BLOCKED]"

    def test_sanitize_input_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        manager = SecurityManager(jwt_secret="test-secret")

        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "union select * from passwords",
            "or 1=1 --",
            "and 1=1 --",
            "-- comment",
            ";--",
            "/* comment */"
        ]

        for dangerous in dangerous_inputs:
            result = manager.sanitize_input(dangerous)
            assert result == "[BLOCKED]"

    def test_sanitize_input_length_limit(self):
        """Test length limiting"""
        manager = SecurityManager(jwt_secret="test-secret")

        long_input = "a" * 2000
        result = manager.sanitize_input(long_input, max_length=1000)

        assert len(result) == 1003  # 1000 + "..." + "[TRUNCATED]"
        assert result.endswith("...[TRUNCATED]")

    def test_sanitize_input_non_string(self):
        """Test non-string input handling"""
        manager = SecurityManager(jwt_secret="test-secret")

        result = manager.sanitize_input(12345)
        assert result == ""

        result = manager.sanitize_input(None)
        assert result == ""

        result = manager.sanitize_input({"key": "value"})
        assert result == ""


class TestIntegrityHash:
    """Test data integrity hashing for GDPR exports"""

    def test_compute_data_hash_consistency(self):
        """Test hash computation is deterministic"""
        manager = SecurityManager(jwt_secret="test-secret")

        data = {
            "student_id": "student_123",
            "mastery_score": 0.85,
            "timestamp": "2024-01-01T12:00:00"
        }

        hash1 = manager.compute_data_hash(data)
        hash2 = manager.compute_data_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest

    def test_compute_data_hash_different_for_different_data(self):
        """Test different data produces different hashes"""
        manager = SecurityManager(jwt_secret="test-secret")

        data1 = {"value": 1}
        data2 = {"value": 2}

        hash1 = manager.compute_data_hash(data1)
        hash2 = manager.compute_data_hash(data2)

        assert hash1 != hash2

    def test_compute_data_hash_sorting(self):
        """Test hash is independent of key order"""
        manager = SecurityManager(jwt_secret="test-secret")

        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        hash1 = manager.compute_data_hash(data1)
        hash2 = manager.compute_data_hash(data2)

        assert hash1 == hash2


class TestSecurityManagerFactory:
    """Test SecurityManager factory function"""

    @patch.dict('os.environ', {
        'JWT_SECRET': 'env-secret',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRE_MINUTES': '120'
    })
    def test_create_security_manager_with_env(self):
        """Test factory uses environment variables"""
        from src.security import create_security_manager

        manager = create_security_manager()

        assert manager.jwt_secret == 'env-secret'
        assert manager.algorithm == 'HS256'
        assert manager.expire_minutes == 120

    @patch.dict('os.environ', {})
    def test_create_security_manager_with_defaults(self):
        """Test factory uses defaults when no env vars"""
        from src.security import create_security_manager

        manager = create_security_manager()

        assert manager.jwt_secret == 'dev-secret-change-in-production'
        assert manager.algorithm == 'HS256'
        assert manager.expire_minutes == 60