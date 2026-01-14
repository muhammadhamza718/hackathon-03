"""
Code Quality Assessment Endpoint
Elite Implementation Standard v2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import types locally to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import SecurityContext

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models with Pydantic v2
class AssessmentRequest(BaseModel):
    """Request model for code quality assessment"""
    student_code: str = Field(..., min_length=1, max_length=50000, description="Student code to assess")
    problem_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Context about the programming problem")
    language: Optional[str] = Field(default="python", description="Programming language")
    rubric: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom assessment rubric")

class AssessmentResponse(BaseModel):
    """Response model for code quality assessment"""
    status: str
    score: float = Field(..., ge=0.0, le=1.0, description="Quality score between 0.0 and 1.0")
    factors: List[Dict[str, Any]] = Field(..., description="Breakdown of assessment factors")
    strengths: List[str] = Field(default_factory=list, description="Detected strengths")
    improvements: List[str] = Field(default_factory=list, description="Areas for improvement")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    student_id: Optional[str] = Field(None, description="Student identifier from JWT")
    processed_at: str = Field(..., description="ISO timestamp of assessment")

class AssessmentHealthResponse(BaseModel):
    """Health check for assessment service"""
    status: str
    service: str
    mcp_connected: bool
    timestamp: str

@router.post(
    "/assess",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess Code Quality",
    description="Evaluate student code quality with detailed scoring and recommendations",
    tags=["assessment"]
)
async def assess_code_quality(
    request: AssessmentRequest,
    security_context: "SecurityContext" = Depends(lambda: __import__('main').validate_jwt())
):
    """
    Assess code quality with comprehensive analysis

    **Security**: JWT token required via Bearer authentication

    **Rate Limit**: 30 requests per minute

    **Input Validation**:
    - Code length: 1-50,000 characters
    - Language: Currently supports Python, JavaScript, Java, C++
    - Sanitization: Automatic injection prevention

    **Returns**:
    - Quality score (0.0-1.0 scale)
    - Factor breakdown
    - Strengths and improvements
    - Actionable recommendations

    **Example Request**:
    ```json
    {
        "student_code": "def calculate_sum(a, b):\n    return a + b",
        "problem_context": {"topic": "basic_functions", "difficulty": "easy"},
        "language": "python"
    }
    ```
    """
    logger.info(f"Assessment request from {security_context.student_id}")

    try:
        # Import the MCP-assisted quality scoring service
        from services.quality_scoring import assess_code_quality_with_mcp

        # Validate input
        if not request.student_code or len(request.student_code.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student code cannot be empty"
            )

        if len(request.student_code) > 50000:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Code exceeds maximum length of 50,000 characters"
            )

        # Perform assessment using MCP-integrated service
        assessment = await assess_code_quality_with_mcp(
            student_code=request.student_code,
            context=request.problem_context,
            student_id=security_context.student_id,
            language=request.language,
            custom_rubric=request.rubric
        )

        # Log successful assessment
        logger.info(
            f"Assessment completed for {security_context.student_id} - "
            f"Score: {assessment.get('score', 0.0)}"
        )

        return AssessmentResponse(
            status="success",
            score=assessment.get("score", 0.0),
            factors=assessment.get("factors", []),
            strengths=assessment.get("strengths", []),
            improvements=assessment.get("improvements", []),
            recommendations=assessment.get("recommendations", []),
            student_id=security_context.student_id,
            processed_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Assessment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment failed: {str(e)}"
        )

@router.get(
    "/assess/health",
    response_model=AssessmentHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Assessment Service Health",
    description="Health check for the assessment service and MCP connection",
    tags=["assessment"]
)
async def assess_health(security_context: SecurityContext = Depends(validate_jwt)):
    """
    Health check endpoint for assessment service

    Verifies:
    - Service is running
    - MCP connection is healthy
    - Dependencies are available

    Returns connectivity status and timestamp
    """
    try:
        from services.quality_scoring import check_mcp_connection

        mcp_healthy = await check_mcp_connection()

        return AssessmentHealthResponse(
            status="healthy" if mcp_healthy else "degraded",
            service="assessment",
            mcp_connected=mcp_healthy,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return AssessmentHealthResponse(
            status="unhealthy",
            service="assessment",
            mcp_connected=False,
            timestamp=datetime.utcnow().isoformat()
        )

@router.post(
    "/assess/batch",
    response_model=List[AssessmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Batch Code Assessment",
    description="Assess multiple code submissions in a single request",
    tags=["assessment"]
)
async def batch_assess_code_quality(
    requests: List[AssessmentRequest],
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Batch assessment for multiple code submissions

    **Use Case**: Teachers reviewing multiple student submissions

    **Limit**: Maximum 20 assessments per batch request

    **Returns**: Array of assessment results in same order as requests
    """
    logger.info(f"Batch assessment request from {security_context.student_id} - {len(requests)} items")

    if len(requests) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 assessments per batch request"
        )

    results = []
    for req in requests:
        try:
            # Reuse the single assessment logic
            from services.quality_scoring import assess_code_quality_with_mcp

            assessment = await assess_code_quality_with_mcp(
                student_code=req.student_code,
                context=req.problem_context,
                student_id=security_context.student_id,
                language=req.language,
                custom_rubric=req.rubric
            )

            results.append(AssessmentResponse(
                status="success",
                score=assessment.get("score", 0.0),
                factors=assessment.get("factors", []),
                strengths=assessment.get("strengths", []),
                improvements=assessment.get("improvements", []),
                recommendations=assessment.get("recommendations", []),
                student_id=security_context.student_id,
                processed_at=datetime.utcnow().isoformat()
            ))

        except Exception as e:
            logger.error(f"Batch assessment item failed: {e}")
            # Include failed item with error status
            results.append(AssessmentResponse(
                status="error",
                score=0.0,
                factors=[],
                strengths=[],
                improvements=[],
                recommendations=[f"Failed: {str(e)}"],
                student_id=security_context.student_id,
                processed_at=datetime.utcnow().isoformat()
            ))

    return results

@router.post(
    "/assess/validate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Validate Assessment Request",
    description="Validate assessment request without performing assessment",
    tags=["assessment"]
)
async def validate_assessment_request(
    request: AssessmentRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Pre-validation endpoint for assessment requests

    Returns validation results without processing the assessment.
    Useful for client-side validation and debugging.
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "code_length": len(request.student_code),
        "has_context": bool(request.problem_context),
        "language": request.language
    }

    # Length validation
    if len(request.student_code) == 0:
        validation_result["valid"] = False
        validation_result["errors"].append("Code cannot be empty")

    if len(request.student_code) > 50000:
        validation_result["valid"] = False
        validation_result["errors"].append("Code exceeds 50,000 character limit")

    if len(request.student_code) > 45000:
        validation_result["warnings"].append("Code is near length limit")

    # Language support check
    supported_languages = ["python", "javascript", "java", "c++", "typescript"]
    if request.language and request.language.lower() not in supported_languages:
        validation_result["warnings"].append(f"Language '{request.language}' may have limited support")

    return validation_result