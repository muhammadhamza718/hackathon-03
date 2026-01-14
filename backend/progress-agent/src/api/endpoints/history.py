"""
Historical Trends Endpoint
Progress Agent
"""

from fastapi import APIRouter, Query
from typing import List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/history", tags=["history"])

class TrendDataPoint(BaseModel):
    timestamp: str
    mastery_level: float
    sessions: int
    time_spent_minutes: int

class HistoricalTrend(BaseModel):
    student_id: str
    topic_id: str
    start_date: str
    end_date: str
    trend: List[TrendDataPoint]
    trend_direction: str  # "improving", "declining", "stable"
    average_improvement: float

@router.get("/trend/{student_id}/{topic_id}")
async def get_historical_trend(
    student_id: str,
    topic_id: str,
    days: int = Query(30, description="Number of days to look back")
):
    """
    Get historical trend data for a specific topic
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate sample trend data
    trend = []
    current_mastery = 0.3
    for i in range(days):
        if i % 7 == 0:  # Weekly improvement
            current_mastery = min(0.95, current_mastery + 0.05)

        point = TrendDataPoint(
            timestamp=(start_date + timedelta(days=i)).isoformat(),
            mastery_level=current_mastery + (0.02 * i / days),  # Slight variation
            sessions=1 if i % 3 == 0 else 0,
            time_spent_minutes=30 if i % 3 == 0 else 0
        )
        trend.append(point)

    return HistoricalTrend(
        student_id=student_id,
        topic_id=topic_id,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        trend=trend,
        trend_direction="improving",
        average_improvement=0.02
    )

@router.get("/milestones/{student_id}")
async def get_learning_milestones(student_id: str):
    """
    Get significant learning milestones and achievements
    """
    return {
        "student_id": student_id,
        "milestones": [
            {
                "type": "topic_mastered",
                "topic_id": "python_basic",
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "value": "Python Basics"
            },
            {
                "type": "time_invested",
                "hours": 20,
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat()
            }
        ]
    }