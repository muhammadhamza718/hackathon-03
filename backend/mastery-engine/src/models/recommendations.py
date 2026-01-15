"""
Recommendation Models
=====================

Models for adaptive learning recommendations and learning paths.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of learning actions"""
    PRACTICE = "practice"
    REVIEW = "review"
    REFACTOR = "refactor"
    SCHEDULE = "schedule"
    LEARN_NEW = "learn_new"
    ASSESS = "assess"


class PriorityLevel(str, Enum):
    """Priority levels for recommendations"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComponentArea(str, Enum):
    """Mastery component areas"""
    COMPLETION = "completion"
    QUIZ = "quiz"
    QUALITY = "quality"
    CONSISTENCY = "consistency"


class AdaptiveRecommendation(BaseModel):
    """Single personalized learning recommendation"""

    action: ActionType
    area: ComponentArea
    priority: PriorityLevel
    description: str = Field(..., min_length=5, description="Human-readable recommendation")
    estimated_time: Optional[int] = Field(None, ge=1, description="Estimated time in minutes")
    resources: List[str] = Field(default_factory=list, description="Learning resources/links")
    difficulty: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")

    # Internal metadata
    score_gap: Optional[float] = Field(None, ge=0.0, le=1.0, description="Gap from target threshold")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence in this recommendation")


class LearningPath(BaseModel):
    """Sequential learning path with dependencies"""

    student_id: str
    path_id: str
    recommendations: List[AdaptiveRecommendation]
    estimated_completion: datetime
    total_time_estimate: int = Field(..., ge=0, description="Total minutes for complete path")
    priority_areas: List[ComponentArea]

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("1.0.0")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecommendationQuery(BaseModel):
    """Request for adaptive recommendations"""

    student_id: str
    limit: int = Field(5, ge=1, le=20)
    priority: Optional[PriorityLevel] = None
    component_filter: Optional[List[ComponentArea]] = None


class LearningPathQuery(BaseModel):
    """Request for comprehensive learning path"""

    student_id: str
    target_level: Optional[str] = Field(None, pattern="^(novice|developing|proficient|master)$")
    max_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)


class RecommendationContext(BaseModel):
    """Contextual data for generating recommendations"""

    current_mastery: float
    component_scores: Dict[str, float]
    trend: str
    activity_level: str
    recent_performance: Optional[float] = None
    days_active: int = Field(0, ge=0)


class RecommendationMetric(BaseModel):
    """Metrics for tracking recommendation effectiveness"""

    student_id: str
    recommendation_id: str
    generated_at: datetime
    completed_at: Optional[datetime] = None
    time_to_completion: Optional[int] = None
    improvement_score: Optional[float] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)


class ComponentThresholdAnalysis(BaseModel):
    """Analysis of which components need attention"""

    component: ComponentArea
    current_score: float
    threshold: float = 0.7
    gap: float
    needs_attention: bool
    recommended_action: ActionType
    priority: PriorityLevel
    estimated_time_to_threshold: int  # minutes


class RecommendationConfig(BaseModel):
    """Configuration for recommendation engine"""

    # Thresholds
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0)
    consistency_threshold: float = Field(0.7, ge=0.0, le=1.0)
    completion_threshold: float = Field(0.8, ge=0.0, le=1.0)
    quiz_threshold: float = Field(0.75, ge=0.0, le=1.0)

    # Time estimates (minutes)
    practice_time_per_gap: int = Field(15, ge=5, le=60)
    review_time_per_gap: int = Field(10, ge=5, le=60)
    refactor_time_per_gap: int = Field(20, ge=5, le=60)
    learn_new_time: int = Field(30, ge=10, le=120)

    # Priority mapping
    high_gap_threshold: float = Field(0.2, ge=0.0, le=0.5)
    medium_gap_threshold: float = Field(0.1, ge=0.0, le=0.3)


class StateKeyPatterns:
    """State store key patterns for recommendations"""

    @staticmethod
    def recommendation(student_id: str, timestamp: datetime) -> str:
        return f"student:{student_id}:recommendation:{timestamp.strftime('%Y-%m-%d-%H-%M')}"

    @staticmethod
    def learning_path(student_id: str) -> str:
        return f"student:{student_id}:learning_path:current"

    @staticmethod
    def recommendation_metrics(student_id: str) -> str:
        return f"student:{student_id}:recommendation_metrics"

    @staticmethod
    def component_analysis(student_id: str) -> str:
        return f"student:{student_id}:component_analysis"