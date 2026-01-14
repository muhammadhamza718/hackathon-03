"""
Detailed Feedback Endpoint
Elite Implementation Standard v2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from main import validate_jwt, SecurityContext

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models with Pydantic v2
class FeedbackRequest(BaseModel):
    """Request model for comprehensive feedback"""
    student_code: str = Field(..., min_length=1, max_length=50000, description="Student code to analyze")
    problem_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Context about the programming problem")
    error_type: Optional[str] = Field(default="general", description="Type of error if applicable")
    language: Optional[str] = Field(default="python", description="Programming language")
    request_level: Optional[str] = Field(default="comprehensive", description="Feedback detail level: quick, standard, comprehensive")

class FeedbackResponse(BaseModel):
    """Response model for comprehensive feedback"""
    status: str
    summary: str = Field(..., description="Overall summary of feedback")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    strengths: List[str] = Field(..., description="Detected strengths in the code")
    improvements: List[str] = Field(..., description="Areas that need improvement")
    detailed_feedback: Dict[str, Any] = Field(..., description="Breakdown by category")
    hint: Optional[str] = Field(None, description="Primary hint for next step")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    estimated_time: Optional[int] = Field(None, description="Estimated minutes to address issues")
    student_id: Optional[str] = Field(None, description="Student identifier from JWT")
    processed_at: str = Field(..., description="ISO timestamp")

class QuickFeedbackResponse(BaseModel):
    """Quick feedback response for immediate response"""
    status: str
    score: float
    key_issues: List[str]
    quick_hint: str

class FeedbackBatchRequest(BaseModel):
    """Batch request for feedback on multiple submissions"""
    submissions: List[FeedbackRequest] = Field(..., min_items=1, max_items=10)

class FeedbackBatchResponse(BaseModel):
    """Batch feedback response"""
    results: List[FeedbackResponse]
    summary: Dict[str, Any] = Field(..., description="Batch summary statistics")

class FeedbackHealthResponse(BaseModel):
    """Health check for feedback service"""
    status: str
    service: str
    mcp_connected: bool
    timestamp: str

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Comprehensive Feedback",
    description="Generate detailed feedback with quality assessment and contextual hints",
    tags=["feedback"]
)
async def generate_feedback(
    request: FeedbackRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Generate comprehensive feedback for student code

    **Security**: JWT token required via Bearer authentication

    **Rate Limit**: 20 requests per minute

    **Feedback Levels**:
    - **quick**: Brief summary with key points
    - **standard**: Balanced detail with actionable items
    - **comprehensive**: Full analysis with multiple categories

    **Integration**: Combines quality assessment + hint generation

    **Example Request**:
    ```json
    {
        "student_code": "function max(a, b) { return a > b ? a : b; }",
        "problem_context": {"topic": "comparison", "expected": "handles edge cases"},
        "error_type": "edge_cases",
        "request_level": "comprehensive"
    }
    ```
    """
    logger.info(f"Feedback request from {security_context.student_id}")

    try:
        # Import both assessment and hint services
        from services.quality_scoring import assess_code_quality_with_mcp
        from services.hint_generator import generate_hint_with_mcp

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

        # Validate feedback level
        valid_levels = ["quick", "standard", "comprehensive"]
        if request.request_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feedback level. Must be one of: {', '.join(valid_levels)}"
            )

        # Get quality assessment
        assessment = await assess_code_quality_with_mcp(
            student_code=request.student_code,
            context=request.problem_context,
            student_id=security_context.student_id,
            language=request.language
        )

        # Generate hint
        hint = await generate_hint_with_mcp(
            student_code=request.student_code,
            problem_context=request.problem_context,
            error_type=request.error_type,
            student_id=security_context.student_id,
            language=request.language,
            hint_level="medium",
            previous_hints=0
        )

        # Construct comprehensive feedback based on level
        strengths = assessment.get("strengths", [])
        improvements = assessment.get("improvements", [])
        recommendations = assessment.get("recommendations", [])

        # Build detailed feedback structure
        detailed_feedback = {
            "quality_breakdown": assessment.get("factors", []),
            "concept_understanding": assessment.get("concept_score", "unknown"),
            "code_structure": assessment.get("structure_score", "unknown"),
            "efficiency": assessment.get("efficiency_score", "unknown"),
            "best_practices": assessment.get("best_practices", []),
            "testing_approach": assessment.get("testing_suggestions", []),
            "optimization_opportunities": assessment.get("optimization_suggestions", [])
        }

        # Generate summary based on request level
        if request.request_level == "quick":
            summary = f"Quality Score: {assessment.get('score', 0.0)}. {len(strengths)} strengths, {len(improvements)} areas for improvement."
        elif request.request_level == "standard":
            summary = f"Overall Quality: {assessment.get('score', 0.0)}/1.0. Your code demonstrates {len(strengths)} key strengths but needs attention in {len(improvements)} areas. {hint.get('text', '')}"
        else:  # comprehensive
            summary = f"Comprehensive Analysis Complete. Score: {assessment.get('score', 0.0)}/1.0. Found {len(strengths)} strengths and {len(improvements)} improvement areas. {len(recommendations)} actionable recommendations provided."

        # Next steps from hint
        next_steps = hint.get("next_steps", [])
        if not next_steps and improvements:
            next_steps = [f"Focus on: {imp}" for imp in improvements[:3]]

        # Estimated time based on complexity
        estimated_time = hint.get("estimated_time")
        if not estimated_time and improvements:
            # Rough estimation: 5 minutes per improvement area
            estimated_time = min(30, len(improvements) * 5)

        logger.info(
            f"Feedback generated for {security_context.student_id} - "
            f"Score: {assessment.get('score', 0.0)}"
        )

        return FeedbackResponse(
            status="success",
            summary=summary,
            quality_score=assessment.get("score", 0.0),
            strengths=strengths,
            improvements=improvements,
            detailed_feedback=detailed_feedback,
            hint=hint.get("text"),
            next_steps=next_steps,
            estimated_time=estimated_time,
            student_id=security_context.student_id,
            processed_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Feedback generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback generation failed: {str(e)}"
        )

@router.post(
    "/feedback/quick",
    response_model=QuickFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Quick Feedback",
    description="Generate immediate feedback with minimal latency",
    tags=["feedback"]
)
async def generate_quick_feedback(
    request: FeedbackRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Generate quick feedback for immediate response

    **Use Case**: Real-time feedback during coding sessions
    **Optimized**: Uses cached assessment when possible
    """
    logger.info(f"Quick feedback request from {security_context.student_id}")

    try:
        from services.quality_scoring import assess_code_quality_with_mcp
        from services.hint_generator import generate_hint_with_mcp

        # Fast-track validation
        if not request.student_code.strip():
            raise HTTPException(status_code=400, detail="Empty code")

        # Quick assessment with simplified context
        assessment = await assess_code_quality_with_mcp(
            student_code=request.student_code[:1000],  # Limit for speed
            context=request.problem_context,
            student_id=security_context.student_id,
            language=request.language
        )

        # Quick hint
        hint = await generate_hint_with_mcp(
            student_code=request.student_code[:500],
            problem_context=request.problem_context,
            error_type=request.error_type,
            student_id=security_context.student_id,
            language=request.language,
            hint_level="direct",
            previous_hints=0
        )

        return QuickFeedbackResponse(
            status="success",
            score=assessment.get("score", 0.0),
            key_issues=assessment.get("improvements", [])[:3],  # Top 3 issues
            quick_hint=hint.get("text", "Review your code logic.")
        )

    except Exception as e:
        logger.error(f"Quick feedback error: {e}")
        return QuickFeedbackResponse(
            status="error",
            score=0.0,
            key_issues=["Unable to assess"],
            quick_hint="Please try again"
        )

@router.post(
    "/feedback/batch",
    response_model=FeedbackBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Feedback Generation",
    description="Generate comprehensive feedback for multiple submissions",
    tags=["feedback"]
)
async def batch_generate_feedback(
    request: FeedbackBatchRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Generate feedback for multiple student submissions

    **Use Case**: Teacher reviewing class assignments
    **Limit**: Maximum 10 submissions per batch
    **Returns**: Individual feedback for each submission + batch statistics
    """
    logger.info(f"Batch feedback for {security_context.student_id} - {len(request.submissions)} submissions")

    if len(request.submissions) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 submissions per batch request"
        )

    results = []
    total_score = 0
    total_strengths = 0
    total_improvements = 0

    for idx, submission in enumerate(request.submissions):
        try:
            # Reuse the single feedback logic
            from services.quality_scoring import assess_code_quality_with_mcp
            from services.hint_generator import generate_hint_with_mcp

            assessment = await assess_code_quality_with_mcp(
                student_code=submission.student_code,
                context=submission.problem_context,
                student_id=f"{security_context.student_id}_batch_{idx}",
                language=submission.language
            )

            hint = await generate_hint_with_mcp(
                student_code=submission.student_code,
                problem_context=submission.problem_context,
                error_type=submission.error_type,
                student_id=f"{security_context.student_id}_batch_{idx}",
                language=submission.language,
                hint_level="medium",
                previous_hints=0
            )

            strengths = assessment.get("strengths", [])
            improvements = assessment.get("improvements", [])
            recommendations = assessment.get("recommendations", [])

            score = assessment.get("score", 0.0)
            total_score += score
            total_strengths += len(strengths)
            total_improvements += len(improvements)

            results.append(FeedbackResponse(
                status="success",
                summary=f"Quality: {score}/1.0. {len(strengths)} strengths, {len(improvements)} improvements.",
                quality_score=score,
                strengths=strengths,
                improvements=improvements,
                detailed_feedback={
                    "factors": assessment.get("factors", []),
                    "category_breakdown": assessment.get("category_scores", {})
                },
                hint=hint.get("text"),
                next_steps=hint.get("next_steps", []),
                estimated_time=hint.get("estimated_time", 10),
                student_id=f"{security_context.student_id}_batch_{idx}",
                processed_at=datetime.utcnow().isoformat()
            ))

        except Exception as e:
            logger.error(f"Batch feedback item {idx} failed: {e}")
            results.append(FeedbackResponse(
                status="error",
                summary=f"Failed to analyze submission: {str(e)}",
                quality_score=0.0,
                strengths=[],
                improvements=[],
                detailed_feedback={},
                hint=None,
                next_steps=[],
                estimated_time=None,
                student_id=f"{security_context.student_id}_batch_{idx}",
                processed_at=datetime.utcnow().isoformat()
            ))

    batch_summary = {
        "total_submissions": len(request.submissions),
        "successful": sum(1 for r in results if r.status == "success"),
        "average_score": total_score / len(request.submissions) if results else 0,
        "total_strengths": total_strengths,
        "total_improvements": total_improvements,
        "recommendations": min(10, total_improvements)  # Top priority items
    }

    return FeedbackBatchResponse(
        results=results,
        summary=batch_summary
    )

@router.get(
    "/feedback/health",
    response_model=FeedbackHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Feedback Service Health",
    description="Health check for the feedback generation service",
    tags=["feedback"]
)
async def feedback_health(security_context: SecurityContext = Depends(validate_jwt)):
    """
    Health check endpoint for feedback service

    Verifies MCP connections for both assessment and hint services
    """
    try:
        from services.quality_scoring import check_mcp_connection as check_assessment_mcp
        from services.hint_generator import check_mcp_connection as check_hint_mcp

        assessment_healthy = await check_assessment_mcp()
        hint_healthy = await check_hint_mcp()

        mcp_healthy = assessment_healthy and hint_healthy

        return FeedbackHealthResponse(
            status="healthy" if mcp_healthy else "degraded",
            service="feedback",
            mcp_connected=mcp_healthy,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return FeedbackHealthResponse(
            status="unhealthy",
            service="feedback",
            mcp_connected=False,
            timestamp=datetime.utcnow().isoformat()
        )

@router.post(
    "/feedback/validate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Validate Feedback Request",
    description="Validate feedback request without processing",
    tags=["feedback"]
)
async def validate_feedback_request(
    request: FeedbackRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Pre-validation endpoint for feedback requests

    Returns validation results without generating feedback.
    Useful for client validation before sending requests.
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "code_length": len(request.student_code),
        "has_context": bool(request.problem_context),
        "language": request.language,
        "level": request.request_level
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

    # Level validation
    valid_levels = ["quick", "standard", "comprehensive"]
    if request.request_level not in valid_levels:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Invalid level. Must be: {', '.join(valid_levels)}")

    # Warning for minimal context
    if not request.problem_context:
        validation_result["warnings"].append("Limited context may reduce feedback relevance")

    return validation_result