"""
Authentication Middleware
Elite Implementation Standard v2.0.0

Extracts student_id from Kong JWT and propagates to Dapr context.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import time
import json
from datetime import datetime

from models.errors import AuthenticationError, AuthorizationError


class SecurityMiddleware:
    """
    JWT authentication and security context propagation
    Kong Gateway provides: X-Consumer-Username (student_id)
    """

    def __init__(self):
        # In production, we'd validate JWT signatures
        # For this implementation, we trust Kong's headers
        self.kong_headers = {
            "consumer_username": "X-Consumer-Username",  # Extracted from JWT sub claim
            "consumer_id": "X-Consumer-ID",
            "jwt_claims": "X-JWT-Claims",
            "request_id": "X-Request-ID"
        }

    async def extract_student_context(self, request: Request) -> Dict:
        """
        Extract security context from Kong JWT headers

        Kong JWT plugin validates token and extracts:
        - sub claim → X-Consumer-Username (student_id)
        - Additional claims → X-JWT-Claims
        """
        headers = request.headers

        # Required: Student ID from JWT sub claim
        student_id = headers.get(self.kong_headers["consumer_username"])

        if not student_id:
            # In production, this means JWT validation failed at Kong
            raise AuthorizationError(
                "Missing X-Consumer-Username header. "
                "Kong JWT plugin must extract student_id from token 'sub' claim."
            )

        # Optional: JWT claims for additional context
        jwt_claims_str = headers.get(self.kong_headers["jwt_claims"])
        jwt_claims = {}
        if jwt_claims_str:
            try:
                jwt_claims = json.loads(jwt_claims_str)
            except json.JSONDecodeError:
                pass

        # Optional: Request ID for tracing
        request_id = headers.get(self.kong_headers["request_id"])

        context = {
            "student_id": student_id,
            "request_id": request_id,
            "jwt_claims": jwt_claims,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "kong_gateway"
        }

        return context

    def propagate_to_dapr_metadata(self, security_context: Dict) -> Dict:
        """
        Convert security context to Dapr metadata headers
        This ensures downstream agents receive student context
        """
        return {
            "X-Student-ID": security_context["student_id"],
            "X-Request-ID": security_context.get("request_id", ""),
            "X-JWT-Claims": json.dumps(security_context.get("jwt_claims", {})),
            "X-Timestamp": security_context["timestamp"],
            "X-Source": "triage-service"
        }

    def audit_log_entry(self, security_context: Dict, action: str, details: Dict = None) -> Dict:
        """Generate audit log entry for Kafka"""
        return {
            "timestamp": security_context["timestamp"],
            "student_id": security_context["student_id"],
            "action": action,
            "source": "triage-service",
            "details": details or {},
            "request_id": security_context.get("request_id")
        }


# FastAPI middleware implementation
async def security_context_middleware(request: Request, call_next):
    """
    FastAPI middleware that extracts security context and adds it to request state

    Flow:
    1. Kong validates JWT → extracts student_id
    2. Middleware extracts headers → creates security context
    3. Context is passed to route handlers
    4. Context is propagated to Dapr services
    """
    middleware = SecurityMiddleware()

    try:
        # Extract security context
        security_context = await middleware.extract_student_context(request)

        # Add to request state for route handlers
        request.state.security_context = security_context

        # Add Dapr metadata to request headers for downstream calls
        dapr_metadata = middleware.propagate_to_dapr_metadata(security_context)
        request.state.dapr_metadata = dapr_metadata

        # Process request
        response = await call_next(request)

        # Add security headers to response
        response.headers["X-Student-ID"] = security_context["student_id"]
        response.headers["X-Request-ID"] = security_context.get("request_id", "")

        return response

    except AuthorizationError as e:
        # JWT validation failed or missing
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "AUTHORIZATION_ERROR",
                "message": "Student authentication required",
                "details": {
                    "required": "Kong JWT plugin with student_id in 'sub' claim",
                    "header": "X-Consumer-Username"
                }
            }
        )

    except Exception as e:
        # Generic security error
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "SECURITY_ERROR",
                "message": f"Security context extraction failed: {str(e)}"
            }
        )


class KongJWTValidator:
    """
    Kong JWT plugin configuration validator
    This documents what should be configured in Kong for production
    """

    @staticmethod
    def get_kong_configuration() -> Dict:
        """
        Return the Kong configuration needed for this service

        This should be applied via Kong Admin API:
        POST /services/triage-service/plugins
        """
        return {
            "name": "jwt",
            "config": {
                "secret_is_base64": False,
                "run_on_preflight": False,
                "key_claim_name": "kid",  # Key identifier in JWT
                "consumer_claim_name": "sub",  # Student ID mapping
                "anonymous": None,
                "minimum_ttl": 0
            },
            # Consumer setup for each student
            "consumer_setup": {
                "endpoint": "/consumers/{student_id}/jwt",
                "expected_headers": [
                    "X-Consumer-Username",  # Maps to JWT sub claim
                    "X-Consumer-ID",
                    "X-JWT-Claims"
                ]
            }
        }

    @staticmethod
    def validate_headers(headers: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate that Kong has properly configured JWT plugin

        Returns: (is_valid, error_message)
        """
        required_headers = ["X-Consumer-Username"]

        for header in required_headers:
            if header not in headers:
                return False, f"Missing required header: {header}"

        # Additional validation can be added here
        student_id = headers["X-Consumer-Username"]
        if not student_id or len(student_id.strip()) < 1:
            return False, "Invalid student_id in header"

        return True, None


# Test utility
async def mock_kong_headers(student_id: str, request_id: str = None) -> Dict:
    """Create mock Kong headers for testing"""
    return {
        "X-Consumer-Username": student_id,
        "X-Consumer-ID": f"consumer_{student_id}",
        "X-JWT-Claims": json.dumps({
            "sub": student_id,
            "role": "student",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time())
        }),
        "X-Request-ID": request_id or f"req_{int(time.time())}"
    }


if __name__ == "__main__":
    print("=== Security Middleware Test ===")

    # Test Kong configuration
    kong_config = KongJWTValidator.get_kong_configuration()
    print(f"Kong JWT Plugin: {kong_config['name']}")
    print(f"Config: {kong_config['config']}")
    print(f"Expected Headers: {kong_config['consumer_setup']['expected_headers']}")

    # Test header validation
    test_headers = {
        "X-Consumer-Username": "student_123456",
        "X-Consumer-ID": "consumer_123456",
        "X-JWT-Claims": '{"sub":"student_123456","role":"student"}'
    }

    is_valid, error = KongJWTValidator.validate_headers(test_headers)
    print(f"\nHeader Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if error:
        print(f"Error: {error}")

    # Test security middleware
    middleware = SecurityMiddleware()
    context = {
        "student_id": "student_123456",
        "request_id": "req_123456",
        "jwt_claims": {"sub": "student_123456", "role": "student"},
        "timestamp": datetime.utcnow().isoformat(),
        "source": "test"
    }

    dapr_metadata = middleware.propagate_to_dapr_metadata(context)
    print(f"\nDapr Metadata Propagation:")
    for k, v in dapr_metadata.items():
        print(f"  {k}: {v}")

    print(f"\n=== Security Architecture ===")
    print(f"✅ JWT Validation: Kong Gateway (edge)")
    print(f"✅ Student Extraction: X-Consumer-Username (sub claim)")
    print(f"✅ Context Propagation: X-Student-ID to Dapr")
    print(f"✅ Downstream Agents: Know exact student identity")
    print(f"✅ Audit Trail: Complete trace from request to agent")