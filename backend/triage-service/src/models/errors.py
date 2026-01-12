"""
Custom Error Classes
Elite Implementation Standard v2.0.0
"""

from fastapi import HTTPException, status
from typing import Optional, Dict


class TriageError(HTTPException):
    """Base error for triage service"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict] = None, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail={
            "error": error_code,
            "message": message,
            "details": details
        })


class ValidationError(TriageError):
    """Schema validation failed"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(TriageError):
    """JWT authentication failed"""
    def __init__(self, message: str):
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(TriageError):
    """Student ID extraction failed or missing"""
    def __init__(self, message: str):
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class RoutingError(TriageError):
    """Dapr service invocation failed"""
    def __init__(self, message: str, target_agent: str, details: Optional[Dict] = None):
        super().__init__(
            error_code="ROUTING_ERROR",
            message=message,
            details={"target_agent": target_agent, **(details or {})},
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class IntentClassificationError(TriageError):
    """Intent detection failed"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            error_code="INTENT_CLASSIFICATION_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CircuitBreakerOpenError(TriageError):
    """Circuit breaker is open - service unavailable"""
    def __init__(self, target_agent: str, timeout_seconds: int):
        super().__init__(
            error_code="CIRCUIT_BREAKER_OPEN",
            message=f"Service {target_agent} is temporarily unavailable. Please try again in {timeout_seconds} seconds.",
            details={
                "target_agent": target_agent,
                "timeout_seconds": timeout_seconds,
                "retry_after": timeout_seconds
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class SchemaMismatchError(TriageError):
    """Data doesn't match M1 contract schemas"""
    def __init__(self, schema_name: str, issues: list):
        super().__init__(
            error_code="SCHEMA_MISMATCH",
            message=f"Data does not match {schema_name} schema",
            details={"schema": schema_name, "issues": issues},
            status_code=status.HTTP_400_BAD_REQUEST
        )


# Error factory for consistent error responses
def create_error_response(error_type: str, message: str, details: Dict = None):
    """Factory method for consistent error responses"""
    error_map = {
        "validation": ValidationError,
        "auth": AuthenticationError,
        "authorization": AuthorizationError,
        "routing": RoutingError,
        "classification": IntentClassificationError,
        "circuit_breaker": CircuitBreakerOpenError,
        "schema": SchemaMismatchError,
    }

    error_class = error_map.get(error_type, TriageError)
    return error_class(message, details)


if __name__ == "__main__":
    print("=== Error System Tests ===")

    # Test error creation
    errors = [
        ValidationError("Invalid request format", {"field": "query", "issue": "too_short"}),
        AuthenticationError("Invalid JWT token"),
        AuthorizationError("Student ID not found in token"),
        RoutingError("Service timeout", "debug-agent"),
        CircuitBreakerOpenError("concepts-agent", 30),
    ]

    for error in errors:
        print(f"✅ {error.error_code}: {error.message}")
        if error.details:
            print(f"   Details: {error.details}")

    print(f"\nError system ready for production use ✅")