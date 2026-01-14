"""
Hint Generation Endpoint
Elite Implementation Standard v2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import security utilities
from security import validate_jwt, SecurityContext

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models with Pydantic v2
class HintRequest(BaseModel):
    """Request model for hint generation"""
    student_code: str = Field(..., min_length=1, max_length=20000, description="Student code to generate hints for")
    problem_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Context about the programming problem")
    error_type: Optional[str] = Field(default="general", description="Type of error or concept")
    language: Optional[str] = Field(default="python", description="Programming language")
    hint_level: Optional[str] = Field(default="medium", description="Hint granularity: subtle, medium, direct")
    previous_hints: Optional[int] = Field(default=0, description="Number of hints already provided")

class HintResponse(BaseModel):
    """Response model for hint generation"""
    status: str
    text: str = Field(..., description="The generated hint text")
    level: str = Field(..., description="Hint difficulty level")
    estimated_time: Optional[int] = Field(None, description="Estimated minutes to solve")
    category: Optional[str] = Field(None, description="Concept category")
    next_steps: Optional[List[str]] = Field(default_factory=list, description="Recommended next steps")
    student_id: Optional[str] = Field(None, description="Student identifier from JWT")
    processed_at: str = Field(..., description="ISO timestamp of generation")

class HintSuggestionResponse(BaseModel):
    """Response for hint suggestions without generating full hint"""
    available_categories: List[str]
    estimated_hint_count: int
    recommended_approach: str

class HintHealthResponse(BaseModel):
    """Health check for hint service"""
    status: str
    service: str
    mcp_connected: bool
    timestamp: str

@router.post(
    "/hints",
    response_model=HintResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Contextual Hint",
    description="Generate a contextual hint based on student code and error type",
    tags=["hints"]
)
async def generate_hint(
    request: HintRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Generate contextual hint for student code

    **Security**: JWT token required via Bearer authentication

    **Rate Limit**: 50 requests per minute

    **Hint Levels**:
    - **subtle**: Gentle nudges, minimal guidance
    - **medium**: Moderate direction, hints at solution approach
    - **direct**: Clear guidance with examples

    **Adaptive Behavior**:
    - Increases hint directness based on `previous_hints`
    - Adapts to error type patterns
    - Considers problem difficulty

    **Example Request**:
    ```json
    {
        "student_code": "def find_max(nums):\n    max_num = 0\n    for num in nums:\n        if num > max_num:\n            max_num = num\n    return max_num",
        "error_type": "off_by_one",
        "hint_level": "medium",
        "previous_hints": 1
    }
    ```
    """
    logger.info(f"Hint generation request from {security_context.student_id}")

    try:
        # Import the MCP-assisted hint generation service
        from services.hint_generator import generate_hint_with_mcp

        # Validate input
        if not request.student_code or len(request.student_code.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student code cannot be empty"
            )

        if len(request.student_code) > 20000:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Code exceeds maximum length of 20,000 characters"
            )

        # Validate hint level
        valid_levels = ["subtle", "medium", "direct"]
        if request.hint_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid hint level. Must be one of: {', '.join(valid_levels)}"
            )

        # Generate hint using MCP-integrated service
        hint = await generate_hint_with_mcp(
            student_code=request.student_code,
            problem_context=request.problem_context,
            error_type=request.error_type,
            student_id=security_context.student_id,
            language=request.language,
            hint_level=request.hint_level,
            previous_hints=request.previous_hints
        )

        # Log successful hint generation
        logger.info(
            f"Hint generated for {security_context.student_id} - "
            f"Level: {hint.get('level', 'unknown')}"
        )

        return HintResponse(
            status="success",
            text=hint.get("text", ""),
            level=hint.get("level", request.hint_level),
            estimated_time=hint.get("estimated_time"),
            category=hint.get("category"),
            next_steps=hint.get("next_steps", []),
            student_id=security_context.student_id,
            processed_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Hint generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hint generation failed: {str(e)}"
        )

@router.post(
    "/hints/suggest",
    response_model=HintSuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest Hint Strategy",
    description="Analyze code and suggest hint approach without generating full hint",
    tags=["hints"]
)
async def suggest_hint_strategy(
    request: HintRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Analyze code and suggest hint strategy

    Returns what hint categories are available and estimated count needed.
    Useful for teachers planning guidance progression.
    """
    logger.info(f"Hint strategy suggestion for {security_context.student_id}")

    # Basic analysis without MCP (lightweight)
    code_length = len(request.student_code)
    has_context = bool(request.problem_context)
    error_type = request.error_type

    # Estimate based on code characteristics
    if error_type in ["syntax", "import"]:
        estimated_count = 1
        approach = "Direct correction with explanation"
    elif error_type in ["logic", "algorithm"]:
        estimated_count = 2
        approach = "Progressive guidance: concept → approach → implementation"
    elif error_type in ["optimization", "style"]:
        estimated_count = 1
        approach = "Targeted improvement suggestions"
    else:
        estimated_count = 3
        approach = "General debugging workflow"

    # Suggest categories based on error type
    categories_map = {
        "syntax": ["Syntax Error", "Language Basics"],
        "logic": ["Algorithm Logic", "Problem Solving"],
        "runtime": ["Debugging", "Testing"],
        "optimization": ["Performance", "Best Practices"],
        "style": ["Code Quality", "Convention"]
    }

    categories = categories_map.get(request.error_type, ["General Guidance"])

    return HintSuggestionResponse(
        available_categories=categories,
        estimated_hint_count=estimated_count,
        recommended_approach=approach
    )

@router.get(
    "/hints/health",
    response_model=HintHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Hint Service Health",
    description="Health check for the hint generation service",
    tags=["hints"]
)
async def hints_health(security_context: SecurityContext = Depends(validate_jwt)):
    """
    Health check endpoint for hint generation service

    Verifies MCP connection and service availability
    """
    try:
        from services.hint_generator import check_mcp_connection

        mcp_healthy = await check_mcp_connection()

        return HintHealthResponse(
            status="healthy" if mcp_healthy else "degraded",
            service="hints",
            mcp_connected=mcp_healthy,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HintHealthResponse(
            status="unhealthy",
            service="hints",
            mcp_connected=False,
            timestamp=datetime.utcnow().isoformat()
        )

@router.post(
    "/hints/batch",
    response_model=List[HintResponse],
    status_code=status.HTTP_200_OK,
    summary="Batch Hint Generation",
    description="Generate multiple hints for progressive guidance",
    tags=["hints"]
)
async def batch_generate_hints(
    requests: List[HintRequest],
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Generate multiple hints for progressive disclosure

    **Use Case**: Provide a sequence of hints with increasing directness

    **Order**: Should be provided in order of intended disclosure

    **Returns**: Array of hints in same order as requests
    """
    logger.info(f"Batch hint generation for {security_context.student_id} - {len(requests)} items")

    if len(requests) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 hint requests per batch"
        )

    results = []
    for req in requests:
        try:
            from services.hint_generator import generate_hint_with_mcp

            hint = await generate_hint_with_mcp(
                student_code=req.student_code,
                problem_context=req.problem_context,
                error_type=req.error_type,
                student_id=security_context.student_id,
                language=req.language,
                hint_level=req.hint_level,
                previous_hints=req.previous_hints
            )

            results.append(HintResponse(
                status="success",
                text=hint.get("text", ""),
                level=hint.get("level", req.hint_level),
                estimated_time=hint.get("estimated_time"),
                category=hint.get("category"),
                next_steps=hint.get("next_steps", []),
                student_id=security_context.student_id,
                processed_at=datetime.utcnow().isoformat()
            ))

        except Exception as e:
            logger.error(f"Batch hint generation failed: {e}")
            results.append(HintResponse(
                status="error",
                text=f"Failed to generate hint: {str(e)}",
                level="error",
                estimated_time=None,
                category=None,
                next_steps=[],
                student_id=security_context.student_id,
                processed_at=datetime.utcnow().isoformat()
            ))

    return results

@router.post(
    "/hints/validate",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Validate Hint Request",
    description="Validate hint request without generating hint",
    tags=["hints"]
)
async def validate_hint_request(
    request: HintRequest,
    security_context: SecurityContext = Depends(validate_jwt)
):
    """
    Pre-validation endpoint for hint requests

    Returns validation results without processing hint generation.
    Useful for client-side validation and debugging.
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "code_length": len(request.student_code),
        "has_context": bool(request.problem_context),
        "language": request.language,
        "hint_level": request.hint_level
    }

    # Length validation
    if len(request.student_code) == 0:
        validation_result["valid"] = False
        validation_result["errors"].append("Code cannot be empty")

    if len(request.student_code) > 20000:
        validation_result["valid"] = False
        validation_result["errors"].append("Code exceeds 20,000 character limit")

    # Level validation
    valid_levels = ["subtle", "medium", "direct"]
    if request.hint_level not in valid_levels:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Invalid level. Must be: {', '.join(valid_levels)}")

    # Warning for lack of context
    if not request.problem_context:
        validation_result["warnings"].append("No problem context provided - hints may be less targeted")

    return validation_result