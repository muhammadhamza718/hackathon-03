"""
Request Sanitization Middleware
Elite Implementation Standard v2.0.0

Protects against SQL injection, XSS, and malicious input patterns.
"""

import re
import html
from typing import Optional, List, Dict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from models.errors import ValidationError


class SanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitizes incoming requests to prevent injection attacks.
    """

    # Dangerous SQL patterns
    SQL_PATTERNS = [
        r"(?i)\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b",
        r"(?i)--|;--|;/\*",
        r"(?i)xp_cmdshell",
        r"(?i)information_schema",
        r"(?i)pg_sleep|sleep\(",
        r"(?i)waitfor delay",
        r"(?i)benchmark\(",
        r"(?i)char\([0-9]",
        r"(?i)concat\(",
    ]

    # Dangerous JavaScript/HTML patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"eval\(",
        r"execScript",
        r"document\.cookie",
        r"<svg[^>]*onload",
        r"<img[^>]*onerror",
    ]

    # Command injection patterns
    COMMAND_PATTERNS = [
        r";",
        r"&&",
        r"\|\|",
        r"`",
        r"\$\(",
        r"<\(",
        r">\(",
        r"wget|curl|nc|netcat",
        r"cat /etc/passwd",
        r"rm -rf",
        r"chmod",
        r"chown",
    ]

    # Dangerous file patterns
    PATH_TRAVERSAL = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/passwd",
        r"/etc/shadow",
        r"/etc/group",
        r"/proc/self",
        r"C:\\Windows\\",
        r"C:\\System32\\",
    ]

    def __init__(self, app, max_length: int = 500, strict_mode: bool = True):
        super().__init__(app)
        self.max_length = max_length
        self.strict_mode = strict_mode

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Sanitize request body and headers.

        Args:
            request: FastAPI request
            call_next: Next handler

        Returns:
            Response or error
        """
        # Only sanitize POST /api/v1/triage
        if request.method != "POST" or request.url.path != "/api/v1/triage":
            return await call_next(request)

        # Read request body
        try:
            body = await request.body()
            if not body:
                raise ValidationError("Empty request body")

            # Check content length
            if len(body) > 10000:  # 10KB max
                raise ValidationError("Request body too large")

            # Get JSON
            try:
                data = await request.json()
            except:
                raise ValidationError("Invalid JSON format")

            # Sanitize query field
            if "query" in data:
                query = data["query"]

                # Length check
                if len(query) > self.max_length:
                    raise ValidationError(f"Query exceeds maximum length of {self.max_length} characters")

                # Check for injections
                sanitized_query = self._sanitize_input(query)

                # If sanitization modified the input significantly, reject
                if self.strict_mode and len(sanitized_query) < len(query) * 0.5:
                    raise ValidationError("Input contains forbidden patterns")

                # Update sanitized query
                data["query"] = sanitized_query

            # Sanitize user_id
            if "user_id" in data:
                data["user_id"] = self._sanitize_identifier(data["user_id"])

            # Sanitize context
            if "context" in data and isinstance(data["context"], dict):
                data["context"] = self._sanitize_dict(data["context"])

            # Store sanitized data in request state
            request.state.sanitized_data = data

        except ValidationError as e:
            # Log security event
            self._log_security_event("sanitization_failed", request, str(e))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "SANITIZATION_FAILED",
                    "message": str(e)
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "BAD_REQUEST",
                    "message": "Invalid request format"
                }
            )

        return await call_next(request)

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize input text by removing dangerous patterns.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # HTML escape for XSS prevention
        text = html.escape(text, quote=True)

        # Remove dangerous SQL patterns
        for pattern in self.SQL_PATTERNS:
            text = re.sub(pattern, "", text)

        # Remove XSS patterns
        for pattern in self.XSS_PATTERNS:
            text = re.sub(pattern, "", text)

        # Remove command injection patterns
        for pattern in self.COMMAND_PATTERNS:
            text = re.sub(pattern, "", text)

        # Remove path traversal patterns
        for pattern in self.PATH_TRAVERSAL:
            text = re.sub(pattern, "", text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove null bytes and control characters
        text = text.replace('\x00', '').replace('\n', ' ').replace('\r', ' ')

        return text.strip()

    def _sanitize_identifier(self, identifier: str) -> str:
        """
        Sanitize identifiers (user_id, etc.).

        Args:
            identifier: Identifier to sanitize

        Returns:
            Sanitized identifier
        """
        if not identifier:
            raise ValidationError("Empty identifier")

        # Only allow student-#### format
        if not re.match(r'^student-\d{1,10}$', identifier):
            raise ValidationError("Invalid identifier format")

        return identifier

    def _sanitize_dict(self, data: dict) -> dict:
        """
        Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_input(str(v)) if isinstance(v, str) else v for v in value]
            else:
                sanitized[key] = value
        return sanitized

    def _log_security_event(self, event_type: str, request: Request, details: str):
        """
        Log security events for monitoring.

        Args:
            event_type: Type of security event
            request: Request object
            details: Event details
        """
        # In production, this would integrate with audit logging system
        print(f"[SECURITY] {event_type}: {details}")


# Helper functions for manual sanitization
def sanitize_text(text: str, max_length: int = 500) -> str:
    """
    Utility function to sanitize text outside middleware.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        ValidationError: If text is too long or contains forbidden patterns
    """
    if not text:
        raise ValidationError("Empty text")

    if len(text) > max_length:
        raise ValidationError(f"Text exceeds maximum length of {max_length}")

    sanitizer = SanitizationMiddleware(None)
    sanitized = sanitizer._sanitize_input(text)

    # If too much was stripped, reject
    if len(sanitized) < len(text) * 0.5:
        raise ValidationError("Text contains forbidden patterns")

    return sanitized


def validate_query(query: str) -> bool:
    """
    Validate query for safety.

    Args:
        query: Query string

    Returns:
        True if safe, False otherwise
    """
    try:
        sanitize_text(query, max_length=500)
        return True
    except ValidationError:
        return False


# Security monitoring functions
class SecurityMonitor:
    """
    Monitors for injection attempts and suspicious activity.
    """

    def __init__(self):
        self.suspicious_patterns: List[Dict] = []

    def analyze_request(self, raw_data: dict) -> Dict:
        """
        Analyze request for security risks.

        Args:
            raw_data: Raw request data

        Returns:
            Security analysis report
        """
        report = {
            "suspicious": False,
            "threats_detected": [],
            "confidence": 0.0
        }

        if not isinstance(raw_data, dict):
            return report

        # Check all string values
        def check_value(value, path=""):
            if isinstance(value, str):
                # Check SQL
                for pattern in SanitizationMiddleware.SQL_PATTERNS:
                    if re.search(pattern, value):
                        report["threats_detected"].append({
                            "type": "SQL_INJECTION",
                            "pattern": pattern,
                            "path": path
                        })

                # Check XSS
                for pattern in SanitizationMiddleware.XSS_PATTERNS:
                    if re.search(pattern, value):
                        report["threats_detected"].append({
                            "type": "XSS",
                            "pattern": pattern,
                            "path": path
                        })

                # Check command injection
                for pattern in SanitizationMiddleware.COMMAND_PATTERNS:
                    if re.search(pattern, value):
                        report["threats_detected"].append({
                            "type": "COMMAND_INJECTION",
                            "pattern": pattern,
                            "path": path
                        })

            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}" if path else k)

        check_value(raw_data)

        if report["threats_detected"]:
            report["suspicious"] = True
            report["confidence"] = min(1.0, len(report["threats_detected"]) * 0.3)

        return report


__all__ = [
    "SanitizationMiddleware",
    "sanitize_text",
    "validate_query",
    "SecurityMonitor"
]