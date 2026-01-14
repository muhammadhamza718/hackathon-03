"""
Security utilities for Review Agent
Extracted to avoid circular imports
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from jose import JWTError, jwt
import re
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

class SecurityContext(BaseModel):
    """Security context from JWT token"""
    student_id: str
    role: str = "student"
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

async def validate_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> SecurityContext:
    """
    Validate JWT token and extract security context

    Args:
        credentials: HTTP Bearer token

    Returns:
        SecurityContext: Validated security context

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # In production, this would validate against real JWT secret
        # For now, we'll use a mock validation that accepts any valid-looking token
        token = credentials.credentials

        # Basic validation
        if not token or len(token) < 10:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Mock extraction - in production: jwt.decode(token, SECRET, algorithms=["HS256"])
        # Extract student_id from token pattern (mock)
        student_id_match = re.search(r'student_id[:\s]*([a-zA-Z0-9_]+)', token)
        student_id = student_id_match.group(1) if student_id_match else "mock_student"

        return SecurityContext(
            student_id=student_id,
            role="student",
            request_id=f"req_{datetime.utcnow().timestamp()}"
        )

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")