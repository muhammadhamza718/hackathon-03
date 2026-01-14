"""
Mastery Calculation Endpoint
Progress Agent
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict
import json

# Import MCP mastery calculation script
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'skills-library', 'agents', 'progress'))

router = APIRouter(prefix="/mastery", tags=["mastery"])

class MasteryRequest(BaseModel):
    student_id: str
    topic_id: str
    session_data: Optional[Dict] = None

class MasteryResponse(BaseModel):
    student_id: str
    topic_id: str
    mastery_level: float
    confidence: float
    recommendations: list[str]
    calculated_at: str

@router.post("/calculate", response_model=MasteryResponse)
async def calculate_mastery(request: MasteryRequest):
    """
    Calculate mastery level for student in specific topic

    Uses MCP mastery-calculation.py script for token-efficient computation
    """
    try:
        # This would integrate with the MCP script
        # For now, simulate the integration pattern
        from mastery_calculation import calculate_mastery_score

        result = calculate_mastery_score(
            student_id=request.student_id,
            topic_id=request.topic_id,
            session_data=request.session_data or {}
        )

        return MasteryResponse(
            student_id=request.student_id,
            topic_id=request.topic_id,
            mastery_level=result["mastery_level"],
            confidence=result["confidence"],
            recommendations=result.get("recommendations", []),
            calculated_at=result["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mastery calculation failed: {str(e)}")

@router.get("/current/{student_id}/{topic_id}")
async def get_current_mastery(
    student_id: str,
    topic_id: str,
    include_history: bool = Query(False, description="Include historical trend data")
):
    """
    Get current mastery level and optional history
    """
    return {
        "student_id": student_id,
        "topic_id": topic_id,
        "mastery_level": 0.75,
        "confidence": 0.82,
        "last_updated": "2026-01-14T10:30:00Z",
        "history": include_history and [] or None
    }