"""
Security Manager and Compliance Utilities
==========================================

JWT validation, RBAC, audit logging, and GDPR compliance for the Mastery Engine.
"""

import os
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from uuid import uuid4
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class Role(Enum):
    """User roles for RBAC"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class Permission(Enum):
    """Available permissions"""
    READ_OWN_DATA = "read_own_data"
    READ_ALL_DATA = "read_all_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    EXPORT_DATA = "export_data"
    MANAGE_USERS = "manage_users"


# RBAC Matrix
ROLE_PERMISSIONS = {
    Role.STUDENT.value: [
        Permission.READ_OWN_DATA,
        Permission.WRITE_DATA,
        Permission.EXPORT_DATA
    ],
    Role.TEACHER.value: [
        Permission.READ_OWN_DATA,
        Permission.READ_ALL_DATA,
        Permission.WRITE_DATA
    ],
    Role.ADMIN.value: [
        Permission.READ_OWN_DATA,
        Permission.READ_ALL_DATA,
        Permission.WRITE_DATA,
        Permission.DELETE_DATA,
        Permission.EXPORT_DATA,
        Permission.MANAGE_USERS
    ]
}


class AuditLog:
    """Audit log entry for tracking data access and changes"""

    def __init__(self, user_id: str, action: str, resource: str,
                 timestamp: Optional[datetime] = None,
                 success: bool = True,
                 details: Optional[Dict[str, Any]] = None):
        self.id = str(uuid4())
        self.user_id = user_id
        self.action = action
        self.resource = resource
        self.timestamp = timestamp or datetime.utcnow()
        self.success = success
        self.details = details or {}
        self.correlation_id = self.details.get("correlation_id", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "details": self.details,
            "correlation_id": self.correlation_id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ConsentRecord:
    """GDPR consent tracking record"""

    def __init__(self, student_id: str, consent_type: str,
                 granted: bool, timestamp: Optional[datetime] = None,
                 version: str = "1.0"):
        self.student_id = student_id
        self.consent_type = consent_type  # e.g., "data_processing", "analytics", "sharing"
        self.granted = granted
        self.timestamp = timestamp or datetime.utcnow()
        self.version = version
        self.withdrawn = False
        self.withdrawn_at = None

    def withdraw(self):
        """Withdraw consent"""
        self.withdrawn = True
        self.withdrawn_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "consent_type": self.consent_type,
            "granted": self.granted,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "withdrawn": self.withdrawn,
            "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None
        }


class SecurityManager:
    """
    Handles JWT validation, RBAC, audit logging, and security operations
    """

    def __init__(self, jwt_secret: str, algorithm: str = "HS256", expire_minutes: int = 60):
        self.jwt_secret = jwt_secret
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.audit_logs: List[AuditLog] = []  # In production, store in persistent storage
        self.consent_store: Dict[str, ConsentRecord] = {}

    def validate_jwt(self, token: str) -> Dict[str, any]:
        """
        Validate JWT token and return claims
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm]
            )

            # Validate required claims
            required_claims = ["sub", "role", "exp"]
            for claim in required_claims:
                if claim not in payload:
                    raise JWTError(f"Missing required claim: {claim}")

            # Check expiration
            exp = datetime.fromtimestamp(payload["exp"])
            if datetime.utcnow() >= exp:
                raise JWTError("Token has expired")

            # Validate role
            valid_roles = [role.value for role in Role]
            if payload["role"] not in valid_roles:
                raise JWTError(f"Invalid role: {payload['role']}")

            return payload

        except JWTError as e:
            logger.error(f"JWT validation failed: {e}")
            raise

    def check_permission(self, user_role: str, permission: Permission,
                        user_id: str, target_user_id: Optional[str] = None) -> bool:
        """
        RBAC: Check if user has permission for action
        """
        if user_role not in ROLE_PERMISSIONS:
            return False

        user_permissions = ROLE_PERMISSIONS[user_role]

        if permission not in user_permissions:
            return False

        # Special case: Students can only access their own data
        if permission == Permission.READ_OWN_DATA and user_role == Role.STUDENT.value:
            if target_user_id and target_user_id != user_id:
                return False

        return True

    def create_jwt(self, user_id: str, role: str, additional_claims: Optional[Dict[str, any]] = None) -> str:
        """
        Create a new JWT token (for testing/demo purposes)
        """
        payload = {
            "sub": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            "iat": datetime.utcnow(),
            **(additional_claims or {})
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)
        return token

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    def audit_access(self, user_id: str, action: str, resource: str,
                     success: bool = True, details: Optional[Dict[str, Any]] = None):
        """
        Log audit trail for data access and changes
        """
        log_entry = AuditLog(user_id, action, resource, success=success, details=details)
        self.audit_logs.append(log_entry)

        # In production, this would write to persistent storage
        logger.info(
            f"AUDIT: {user_id} {action} {resource} {'SUCCESS' if success else 'FAILED'}",
            extra=log_entry.to_dict()
        )

    def get_audit_logs(self, user_id: Optional[str] = None,
                      resource_type: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering
        """
        logs = self.audit_logs

        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        if resource_type:
            logs = [log for log in logs if log.resource.startswith(resource_type)]

        return [log.to_dict() for log in logs[-limit:]]

    def record_consent(self, student_id: str, consent_type: str, granted: bool) -> ConsentRecord:
        """
        Record GDPR consent for a student
        """
        consent = ConsentRecord(student_id, consent_type, granted)
        key = f"{student_id}:{consent_type}"
        self.consent_store[key] = consent

        logger.info(f"Consent recorded for {student_id}: {consent_type} = {granted}")
        return consent

    def withdraw_consent(self, student_id: str, consent_type: str):
        """
        Withdraw GDPR consent
        """
        key = f"{student_id}:{consent_type}"
        if key in self.consent_store:
            self.consent_store[key].withdraw()
            logger.info(f"Consent withdrawn for {student_id}: {consent_type}")
            return True
        return False

    def has_active_consent(self, student_id: str, consent_type: str) -> bool:
        """
        Check if student has active consent
        """
        key = f"{student_id}:{consent_type}"
        consent = self.consent_store.get(key)
        return consent is not None and consent.granted and not consent.withdrawn

    def sanitize_input(self, value: str, max_length: int = 1000) -> str:
        """
        Sanitize user input to prevent injection attacks
        """
        if not isinstance(value, str):
            return ""

        # Remove dangerous patterns
        dangerous_patterns = [
            "<script", "javascript:", "onload=", "onerror=",
            "drop table", "--", ";--", "/*", "*/",
            "union select", "or 1=1", "and 1=1"
        ]

        sanitized = value.lower()
        for pattern in dangerous_patterns:
            if pattern in sanitized:
                logger.warning(f"Input sanitization blocked pattern: {pattern}")
                return "[BLOCKED]"

        # Limit length
        if len(value) > max_length:
            value = value[:max_length] + "...[TRUNCATED]"

        # Remove extra whitespace
        return value.strip()

    def compute_data_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute hash of data for integrity verification
        """
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def validate_security_context(self, security_context: Optional[Dict[str, Any]],
                                  required_permissions: List[Permission]) -> tuple[bool, str]:
        """
        Validate security context and permissions
        Returns (is_valid, error_message)
        """
        if not security_context:
            return False, "Missing security context"

        token = security_context.get("token")
        if not token:
            return False, "Missing token in security context"

        try:
            claims = self.validate_jwt(token)
            user_role = claims.get("role")
            user_id = claims.get("sub")

            for permission in required_permissions:
                if not self.check_permission(user_role, permission, user_id):
                    return False, f"Insufficient permissions for {permission.value}"

            return True, ""

        except JWTError as e:
            return False, f"Token validation failed: {e}"


# Factory function
def create_security_manager() -> SecurityManager:
    """
    Create SecurityManager with environment configuration
    """
    jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    return SecurityManager(
        jwt_secret=jwt_secret,
        algorithm=algorithm,
        expire_minutes=expire_minutes
    )