"""
Difficulty Calibration Endpoint
Exercise Agent
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict, List
import json

router = APIRouter(tags=["calibration"])

class CalibrationRequest(BaseModel):
    student_id: str
    concept: str
    recent_performance: List[float]  # List of recent scores (0.0 to 1.0)
    student_history: Dict = {}

class CalibrationResponse(BaseModel):
    student_id: str
    concept: str
    recommended_difficulty: str
    confidence: float
    estimated_mastery: float
    next_suggestion: str
    calibration_data: Dict

@router.post("/", response_model=CalibrationResponse)
async def calibrate_difficulty(request: CalibrationRequest):
    """
    Calibrate exercise difficulty based on student performance data
    """
    try:
        from services.difficulty_calibration import calibrate_difficulty_with_mcp

        # Calculate average performance
        avg_performance = sum(request.recent_performance) / len(request.recent_performance) if request.recent_performance else 0.5

        # Use MCP calibration service
        difficulty = await calibrate_difficulty_with_mcp(
            mastery=avg_performance,
            success_rate=avg_performance
        )

        # Determine next suggestion
        if avg_performance > 0.8:
            next_action = "Increase challenge with advanced problems"
        elif avg_performance > 0.6:
            next_action = "Continue with intermediate problems"
        else:
            next_action = "Review fundamentals with beginner problems"

        return CalibrationResponse(
            student_id=request.student_id,
            concept=request.concept,
            recommended_difficulty=difficulty,
            confidence=0.85,
            estimated_mastery=avg_performance,
            next_suggestion=next_action,
            calibration_data={
                "average_performance": avg_performance,
                "recent_scores": request.recent_performance,
                "samples": len(request.recent_performance)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")

@router.get("/progress/{student_id}")
async def get_progress_metrics(student_id: str, concept: str = Query(None)):
    """
    Get detailed progress metrics for a student
    """
    # Simulated progress data
    metrics = {
        "student_id": student_id,
        "concept": concept,
        "mastery_score": 0.75,
        "completion_rate": 0.8,
        "avg_time_per_problem": 12.5,
        "difficulty_breakdown": {
            "beginner": {"completed": 8, "success_rate": 0.9},
            "intermediate": {"completed": 5, "success_rate": 0.7},
            "advanced": {"completed": 1, "success_rate": 0.5}
        },
        "recommendation": "Ready for intermediate challenges"
    }
    return metrics

@router.post("/adaptive-learning-path")
async def generate_adaptive_path(requests: List[CalibrationRequest]):
    """
    Generate adaptive learning path for multiple concepts
    """
    path = []
    for req in requests:
        try:
            from services.difficulty_calibration import calibrate_difficulty_with_mcp

            avg_performance = sum(req.recent_performance) / len(req.recent_performance) if req.recent_performance else 0.5
            difficulty = await calibrate_difficulty_with_mcp(avg_performance, avg_performance)

            path.append({
                "concept": req.concept,
                "recommended_difficulty": difficulty,
                "mastery": avg_performance,
                "estimated_exercises": max(3, int((1 - avg_performance) * 10)),
                "status": "ready"
            })
        except Exception as e:
            path.append({
                "concept": req.concept,
                "status": "error",
                "error": str(e)
            })

    return {"learning_path": path}

@router.get("/difficulty-rules")
async def get_difficulty_rules():
    """
    Get the difficulty calibration rules for transparency
    """
    return {
        "rules": [
            {
                "condition": "mastery > 0.8 AND success_rate > 0.7",
                "action": "recommend_hard_difficulty",
                "rationale": "Student demonstrates strong understanding"
            },
            {
                "condition": "mastery > 0.5",
                "action": "recommend_medium_difficulty",
                "rationale": "Student has foundational knowledge"
            },
            {
                "condition": "mastery <= 0.5",
                "action": "recommend_easy_difficulty",
                "rationale": "Focus on building fundamentals"
            }
        ],
        "parameters": {
            "mastery_threshold_hard": 0.8,
            "success_threshold_hard": 0.7,
            "mastery_threshold_medium": 0.5
        }
    }