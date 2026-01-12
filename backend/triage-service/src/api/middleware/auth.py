"""
Authentication Middleware - Student ID Extraction
Elite Implementation Standard v2.0.0

Security Handshake: Extracts student_id from Kong JWT headers and validates claims.
Implements the X-Student-ID propagation pattern for downstream agents.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import time
import json
import base64
from datetime import datetime

from models.errors import AuthenticationError, AuthorizationError


class AuthMiddleware:
    """
    JWT Authentication via Kong Gateway

    Kong JWT Plugin Flow:
    1. Validates JWT signature and expiration
    2. Extracts 'sub' claim → X-Consumer-Username header
    3. Forwards full claims to X-JWT-Claims header
    """

    def __init__(self):
        # Kong standard headers
        self.kong_headers = {
            "consumer_username": "X-Consumer-Username",  # student_id from JWT 'sub' claim
            "consumer_id": "X-Consumer-ID",
            "jwt_claims": "X-JWT-Claims",  # Base64 encoded JSON of all claims
            "request_id": "X-Request-ID"
        }

        # Required JWT claims
        self.required_claims = ["sub", "exp", "role"]

    async def extract_student_context(self, request: Request) -> Dict:
        """
        Extract and validate security context from Kong JWT headers

        Returns:
            {
                "student_id": "student-123",
                "consumer_id": "uuid",
                "claims": {...},
                "expires_at": 1234567890,
                "role": "student",
                "validated_at": "ISO timestamp"
            }

        Raises:
            AuthorizationError: If required headers missing or invalid
        """
        headers = dict(request.headers)

        # 1. Extract student_id from X-Consumer-Username (from JWT 'sub' claim)
        student_id = headers.get(self.kong_headers["consumer_username"])
        if not student_id:
            raise AuthorizationError(
                message="Missing X-Consumer-Username header",
                details={
                    "error_code": "JWT_VALIDATION_FAILED",
                    "reason": "Kong did not extract 'sub' claim",
                    "required_claim": "sub"
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Extract consumer_id
        consumer_id = headers.get(self.kong_headers["consumer_id"])

        # 3. Extract and decode JWT claims
        jwt_claims_encoded = headers.get(self.kong_headers["jwt_claims"])
        if not jwt_claims_encoded:
            raise AuthorizationError(
                message="Missing X-JWT-Claims header",
                details={
                    "error_code": "JWT_CLAIMS_MISSING",
                    "reason": "Kong did not forward JWT claims"
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Kong sends claims as base64 encoded JSON
            jwt_claims = json.loads(base64.b64decode(jwt_claims_encoded).decode('utf-8'))
        except Exception as e:
            raise AuthorizationError(
                message="Invalid JWT claims format",
                details={
                    "error_code": "JWT_CLAIMS_INVALID",
                    "reason": f"Failed to parse claims: {str(e)}"
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # 4. Validate required claims
        for claim in self.required_claims:
            if claim not in jwt_claims:
                raise AuthorizationError(
                    message=f"Missing required JWT claim: {claim}",
                    details={
                        "error_code": "JWT_CLAIM_MISSING",
                        "missing_claim": claim,
                        "available_claims": list(jwt_claims.keys())
                    },
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

        # 5. Validate expiration (Kong should handle this, but double-check)
        exp = jwt_claims.get("exp")
        if exp and exp < time.time():
            raise AuthorizationError(
                message="JWT token expired",
                details={
                    "error_code": "JWT_EXPIRED",
                    "exp": exp,
                    "now": int(time.time())
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # 6. Validate role
        role = jwt_claims.get("role")
        if role not in ["student", "admin", "instructor"]:
            raise AuthorizationError(
                message="Invalid role in JWT",
                details={
                    "error_code": "INVALID_ROLE",
                    "role": role,
                    "allowed_roles": ["student", "admin", "instructor"]
                },
                status_code=status.HTTP_403_FORBIDDEN
            )

        # 7. Construct security context
        security_context = {
            "student_id": student_id,
            "consumer_id": consumer_id,
            "claims": jwt_claims,
            "role": role,
            "expires_at": exp,
            "validated_at": datetime.utcnow().isoformat(),
            "headers": {
                "X-Consumer-Username": student_id,
                "X-Consumer-ID": consumer_id,
                "X-JWT-Claims": jwt_claims_encoded
            }
        }

        return security_context

    def generate_dapr_context(self, security_context: Dict) -> Dict[str, str]:
        """
        Generate Dapr context headers for service-to-service calls

        This implements the Zero-Trust Security Handshake:
        - X-Student-ID: Propagates identity to downstream agents
        - X-Role: Propagates permissions
        - X-Auth-Source: Identifies authentication method
        """
        return {
            "X-Student-ID": security_context["student_id"],
            "X-Role": security_context["role"],
            "X-Auth-Source": "kong-jwt",
            "X-Consumer-ID": security_context.get("consumer_id", ""),
            "X-Request-Timestamp": str(int(time.time()))
        }


class RateLimitMiddleware:
    """
    Rate limiting per student (100 req/min)

    This would typically be handled by Kong, but we implement a secondary
    layer here as defense-in-depth and for audit logging.
    """

    def __init__(self):
        # In production, use Redis with atomic operations
        # For this implementation, we'll simulate rate limiting
        self.requests = {}  # student_id: [(timestamp, ...)]
        self.max_requests = 100
        self.window_seconds = 60

    def is_rate_limited(self, student_id: str) -> tuple[bool, Optional[Dict]]:
        """
        Check if student has exceeded rate limit

        Returns:
            (is_limited: bool, metadata: Dict)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Initialize student record if needed
        if student_id not in self.requests:
            self.requests[student_id] = []

        # Clean old requests outside window
        self.requests[student_id] = [
            ts for ts in self.requests[student_id] if ts > window_start
        ]

        # Check limit
        current_count = len(self.requests[student_id])
        is_limited = current_count >= self.max_requests

        if not is_limited:
            # Record this request
            self.requests[student_id].append(now)

        remaining = self.max_requests - current_count
        reset_time = window_start + self.window_seconds

        metadata = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": int(reset_time),
            "current_count": current_count
        }

        return is_limited, metadata


class SanitizationMiddleware:
    """
    Input sanitization for security
    - SQL injection prevention
    - XSS prevention
    - Command injection prevention
    """

    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize user query input

        Returns cleaned query or raises ValidationError
        """
        if not query or len(query.strip()) == 0:
            raise AuthenticationError(
                message="Empty query",
                details={"error_code": "INVALID_INPUT"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if len(query) > 1000:
            raise AuthenticationError(
                message="Query too long",
                details={"error_code": "INPUT_TOO_LONG", "max_length": 1000},
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )

        # Basic sanitization - remove obviously dangerous patterns
        dangerous_patterns = [
            "DROP TABLE", "DELETE FROM", "UPDATE SET",
            "<script>", "</script>", "javascript:",
            "bash -c", "python -c", "exec(",
            "__import__", "eval(", "os.system"
        ]

        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if pattern.upper() in query_upper:
                raise AuthenticationError(
                    message="Potentially dangerous input detected",
                    details={
                        "error_code": "DANGEROUS_INPUT",
                        "pattern_detected": pattern,
                        "input_sample": query[:100]
                    },
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

        return query.strip()


# Global middleware instances
auth_middleware = AuthMiddleware()
rate_limit_middleware = RateLimitMiddleware()
sanitization_middleware = SanitizationMiddleware()


async def security_context_middleware(request: Request, call_next):
    """
    Main security middleware function for FastAPI

    Flow:
    1. Extract student_id from Kong JWT headers
    2. Validate JWT claims
    3. Check rate limits (secondary layer)
    4. Attach security context to request state
    5. Continue to endpoint handler
    """
    try:
        # Extract security context
        security_context = await auth_middleware.extract_student_context(request)

        # Apply rate limiting (defense-in-depth)
        is_limited, rate_meta = rate_limit_middleware.is_rate_limited(
            security_context["student_id"]
        )

        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {rate_meta['limit']} requests per minute exceeded",
                    "retry_after": rate_meta['reset'] - int(time.time()),
                    "request_id": request.headers.get("X-Request-ID")
                },
                headers={
                    "X-RateLimit-Limit": str(rate_meta["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_meta["reset"])
                }
            )

        # Store security context in request state for endpoint access
        request.state.security_context = security_context

        # Add security headers to response
        response = await call_next(request)

        # Propagate security headers to client
        response.headers["X-Student-ID"] = security_context["student_id"]
        response.headers["X-Role"] = security_context["role"]
        response.headers["X-Auth-Method"] = "kong-jwt"

        return response

    except (AuthenticationError, AuthorizationError) as e:
        # Return structured security error
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )

    except Exception as e:
        # Catch-all for unexpected errors
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SECURITY_ERROR",
                "message": "Security validation failed",
                "details": {"exception": str(e)}
            }
        )