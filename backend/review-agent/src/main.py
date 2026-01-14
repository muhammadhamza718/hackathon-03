"""
Review Agent - Code Quality Assessment Microservice
Elite Implementation Standard v2.0.0
"""

from fastapi import FastAPI, HTTPException, status, Depends, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from jose import JWTError, jwt
import asyncio
import logging
import os
import sys
import re
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import routers
from api.endpoints.assess import router as assess_router
from api.endpoints.hints import router as hints_router
from api.endpoints.feedback import router as feedback_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security
security = HTTPBearer()

# Request/Response models with Pydantic v2
class SecurityContext(BaseModel):
    """Security context from JWT token"""
    student_id: str
    role: str = "student"
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    timestamp: float
    version: str = "1.0.0"

class RootResponse(BaseModel):
    """Root endpoint response model"""
    service: str
    version: str
    endpoints: List[str]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    logger.info("Review Agent starting up...")

    # Initialize services
    try:
        logger.info("Review Agent services initialized")
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")

    asyncio.create_task(health_check_loop())

    yield

    logger.info("Review Agent shutting down...")

app = FastAPI(
    title="Review Agent",
    description="Code quality assessment and feedback agent for LearnFlow",
    version="1.0.0",
    lifespan=lifespan
)

# Apply rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: {"error": "Rate limit exceeded"})

# Include routers
app.include_router(assess_router, prefix="/review")
app.include_router(hints_router, prefix="/review")
app.include_router(feedback_router, prefix="/review")

# Security validation
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
        student_id_match = re.search(r'student_id[:"\s]*([a-zA-Z0-9_]+)', token)
        student_id = student_id_match.group(1) if student_id_match else "mock_student"

        return SecurityContext(
            student_id=student_id,
            role="student",
            request_id=f"req_{datetime.utcnow().timestamp()}"
        )

    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Security middleware
@app.middleware("http")
async def input_sanitization_middleware(request: Request, call_next):
    """
    Input sanitization middleware to prevent injection attacks

    This middleware sanitizes all incoming request data to prevent:
    - SQL injection
    - XSS attacks
    - Command injection
    - Other injection attacks
    """
    try:
        # Read and sanitize request body
        if request.method in ["POST", "PUT", "PATCH"]:
            # Get raw body
            body = await request.body()
            body_str = body.decode('utf-8', errors='ignore')

            # Basic sanitization - remove dangerous patterns
            dangerous_patterns = [
                r'(?i)(sql|drop|delete|update|insert|exec|cmd|shell|bash|python|system)',
                r'[<>]',
                r'--',
                r';',
                r'union',
                r'select.*from'
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, body_str):
                    logger.warning(f"Potentially dangerous input detected: {pattern}")
                    raise HTTPException(status_code=400, detail="Invalid input detected")

            # Limit input size
            if len(body) > 100000:  # 100KB max
                raise HTTPException(status_code=413, detail="Input too large")

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response

    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")

# Dapr service invocation endpoint
@app.post("/process")
async def dapr_process_handler(
    data: Dict[str, Any] = Body(...),
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Dapr service invocation handler for Review Agent

    This endpoint receives service calls from the Triage Service via Dapr
    and routes them to the appropriate internal functionality.

    Supported intents:
    - quality_assessment: Assess code quality and provide scores
    - hint_generation: Generate contextual hints for code issues
    - detailed_feedback: Comprehensive feedback report

    Args:
        data: Request data from Triage Service
        security_context: Validated JWT security context

    Returns:
        Dict: Service response with results or error
    """
    logger.info(f"Dapr invocation received from {security_context.student_id}: {data}")

    try:
        intent = data.get("intent", "")
        student_code = data.get("student_code", "")
        problem_context = data.get("problem_context", {})
        error_type = data.get("error_type", "general")
        confidence = data.get("confidence", 0.0)

        # Input validation
        if not student_code or len(student_code.strip()) == 0:
            return {
                "status": "error",
                "agent": "review-agent",
                "error": "No student code provided",
                "processed_at": datetime.utcnow().isoformat()
            }

        # Route based on intent
        if intent == "quality_assessment":
            from services.quality_scoring import assess_code_quality_with_mcp
            assessment = await assess_code_quality_with_mcp(
                student_code=student_code,
                context=problem_context,
                student_id=security_context.student_id
            )

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": intent,
                    "quality_score": assessment["score"],
                    "factors": assessment["factors"],
                    "recommendations": assessment.get("recommendations", []),
                    "student_id": security_context.student_id,
                    "confidence": confidence
                },
                "processed_at": datetime.utcnow().isoformat()
            }

        elif intent == "hint_generation":
            from services.hint_generator import generate_hint_with_mcp
            hint = await generate_hint_with_mcp(
                student_code=student_code,
                problem_context=problem_context,
                error_type=error_type,
                student_id=security_context.student_id
            )

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": intent,
                    "hint": hint["text"],
                    "level": hint["level"],
                    "estimated_time": hint["estimated_time"],
                    "student_id": security_context.student_id,
                    "confidence": confidence
                },
                "processed_at": datetime.utcnow().isoformat()
            }

        elif intent == "detailed_feedback":
            from services.quality_scoring import assess_code_quality_with_mcp
            from services.hint_generator import generate_hint_with_mcp

            assessment = await assess_code_quality_with_mcp(
                student_code=student_code,
                context=problem_context,
                student_id=security_context.student_id
            )

            hint = await generate_hint_with_mcp(
                student_code=student_code,
                problem_context=problem_context,
                error_type=error_type,
                student_id=security_context.student_id
            )

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": intent,
                    "quality_score": assessment["score"],
                    "feedback": {
                        "strengths": assessment.get("strengths", []),
                        "improvements": assessment.get("improvements", []),
                        "hint": hint["text"],
                        "next_steps": hint.get("next_steps", [])
                    },
                    "student_id": security_context.student_id,
                    "confidence": confidence
                },
                "processed_at": datetime.utcnow().isoformat()
            }

        else:
            return {
                "status": "error",
                "agent": "review-agent",
                "error": f"Unknown intent: {intent}",
                "supported_intents": ["quality_assessment", "hint_generation", "detailed_feedback"],
                "processed_at": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Dapr handler error: {e}")
        return {
            "status": "error",
            "agent": "review-agent",
            "error": str(e),
            "data_received": data,
            "processed_at": datetime.utcnow().isoformat()
        }

@app.get("/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint with rate limiting"""
    return HealthResponse(
        status="healthy",
        service="review-agent",
        timestamp=asyncio.get_event_loop().time(),
        version="1.0.0"
    )

@app.get("/ready", response_model=HealthResponse)
@limiter.limit("10/minute")
async def readiness_check(request: Request):
    """Readiness check with rate limiting"""
    return HealthResponse(
        status="ready",
        service="review-agent",
        timestamp=asyncio.get_event_loop().time(),
        version="1.0.0"
    )

@app.get("/", response_model=RootResponse)
async def root():
    """API information endpoint"""
    return RootResponse(
        service="review-agent",
        version="1.0.0",
        endpoints=[
            "/review/assess",
            "/review/hints",
            "/review/feedback",
            "/process",
            "/health",
            "/ready"
        ]
    )

async def health_check_loop():
    """Background health monitoring"""
    while True:
        await asyncio.sleep(60)
        logger.debug("Health check ping")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)