"""
Fix Suggestion Endpoint
Debug Agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

class SuggestionRequest(BaseModel):
    code: str
    error_message: str
    context: Optional[dict] = None

class FixSuggestion(BaseModel):
    line_number: int
    current_code: str
    suggested_fix: str
    explanation: str
    confidence: float
    severity: str

@router.post("/", response_model=List[FixSuggestion])
async def get_fix_suggestions(request: SuggestionRequest):
    """
    Generate specific fix suggestions for code errors
    """
    try:
        suggestions = []

        # Basic suggestion logic based on error patterns
        if "missing" in request.error_message.lower() and "parenthesis" in request.error_message.lower():
            suggestions.append(FixSuggestion(
                line_number=1,
                current_code=request.code,
                suggested_fix=request.code.rstrip() + ")",
                explanation="Add closing parenthesis to complete the function call",
                confidence=0.95,
                severity="high"
            ))

        elif "undefined" in request.error_message.lower():
            suggestions.append(FixSuggestion(
                line_number=1,
                current_code=request.code,
                suggested_fix=f"# TODO: Define missing variable/function\n{request.code}",
                explanation="The referenced variable or function is not defined",
                confidence=0.90,
                severity="medium"
            ))

        else:
            suggestions.append(FixSuggestion(
                line_number=1,
                current_code=request.code,
                suggested_fix=request.code,
                explanation="Review the error message and stack trace for specific issues",
                confidence=0.70,
                severity="low"
            ))

        return suggestions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")

@router.post("/hints")
async def get_learning_hints(error_pattern: str, student_level: str = "beginner"):
    """
    Get educational hints based on error pattern and student level
    """
    hints = {
        "beginner": [
            "Read the error message carefully - it tells you exactly what's wrong",
            "Check line numbers mentioned in the error",
            "Compare your code with working examples",
            "Use print statements to debug variable values"
        ],
        "intermediate": [
            "Use a debugger to step through your code",
            "Review the logic flow and data types",
            "Check edge cases and boundary conditions",
            "Refactor complex expressions into smaller parts"
        ],
        "advanced": [
            "Analyze the call stack for context",
            "Consider algorithm complexity",
            "Review memory usage patterns",
            "Evaluate exception handling strategy"
        ]
    }

    level_hints = hints.get(student_level, hints["beginner"])
    return {"hints": level_hints, "pattern": error_pattern}