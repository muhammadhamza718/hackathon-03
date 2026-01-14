"""
Progress Retrieval Endpoint
Progress Agent
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/progress", tags=["progress"])

class ProgressSummary(BaseModel):
    student_id: str
    total_topics: int
    mastered_topics: int
    in_progress_topics: int
    completion_rate: float
    last_active: str

class TopicProgress(BaseModel):
    topic_id: str
    topic_name: str
    mastery_level: float
    time_spent_minutes: int
    sessions: int
    last_session: str

@router.get("/summary/{student_id}", response_model=ProgressSummary)
async def get_progress_summary(student_id: str):
    """
    Get overall progress summary for a student
    """
    return ProgressSummary(
        student_id=student_id,
        total_topics=12,
        mastered_topics=3,
        in_progress_topics=6,
        completion_rate=25.0,
        last_active=datetime.now().isoformat()
    )

@router.get("/topics/{student_id}")
async def get_topic_progress(
    student_id: str,
    status: Optional[str] = Query(None, description="Filter by status: mastered, in_progress, not_started")
):
    """
    Get detailed progress for all topics
    """
    topics = [
        TopicProgress(
            topic_id="python_basic",
            topic_name="Python Basics",
            mastery_level=0.85,
            time_spent_minutes=120,
            sessions=5,
            last_session=(datetime.now() - timedelta(days=2)).isoformat()
        ),
        TopicProgress(
            topic_id="data_structures",
            topic_name="Data Structures",
            mastery_level=0.62,
            time_spent_minutes=90,
            sessions=3,
            last_session=(datetime.now() - timedelta(days=1)).isoformat()
        )
    ]

    if status == "mastered":
        return [t for t in topics if t.mastery_level >= 0.8]
    elif status == "in_progress":
        return [t for t in topics if 0.3 <= t.mastery_level < 0.8]
    elif status == "not_started":
        return [t for t in topics if t.mastery_level < 0.3]

    return topics