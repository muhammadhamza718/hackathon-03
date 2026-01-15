"""
Mastery Models
==============

Pydantic models for mastery calculation and state management.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MasteryLevel(str, Enum):
    """Mastery levels based on score thresholds"""
    NOVICE = "novice"           # 0.0 - 0.4
    DEVELOPING = "developing"   # 0.4 - 0.6
    PROFICIENT = "proficient"   # 0.6 - 0.8
    MASTER = "master"           # 0.8 - 1.0


class ComponentScores(BaseModel):
    """Individual component scores for mastery calculation"""
    completion: float = Field(..., ge=0.0, le=1.0, description="Exercise completion rate (0-1)")
    quiz: float = Field(..., ge=0.0, le=1.0, description="Quiz performance score (0-1)")
    quality: float = Field(..., ge=0.0, le=1.0, description="Quality of work assessment (0-1)")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Consistency of effort (0-1)")

    @field_validator('completion', 'quiz', 'quality', 'consistency')
    @classmethod
    def validate_component_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Component score must be between 0.0 and 1.0, got {v}")
        return v


class MasteryWeights(BaseModel):
    """Formula weights configuration (must sum to 1.0)"""
    completion: float = Field(0.4, ge=0.0, le=1.0)
    quiz: float = Field(0.3, ge=0.0, le=1.0)
    quality: float = Field(0.2, ge=0.0, le=1.0)
    consistency: float = Field(0.1, ge=0.0, le=1.0)

    @field_validator('completion', 'quiz', 'quality', 'consistency')
    @classmethod
    def validate_component_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('completion', 'quiz', 'quality', 'consistency')
    def validate_weights_sum(cls, v, values):
        """Ensure weights sum to 1.0 (within tolerance)"""
        # This will be called for each field, but we need all values
        # We'll validate in a custom root validator instead
        return v

    def calculate_total(self) -> float:
        """Calculate sum of all weights"""
        return self.completion + self.quiz + self.quality + self.consistency

    def validate_sum(self):
        """Validate that weights sum to 1.0 within tolerance"""
        total = self.calculate_total()
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")


class MasteryBreakdown(BaseModel):
    """Detailed breakdown of mastery calculation"""
    completion: float
    quiz: float
    quality: float
    consistency: float
    weighted_sum: float
    weights: MasteryWeights


class MasteryResult(BaseModel):
    """Complete mastery calculation result"""
    student_id: str
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    level: MasteryLevel
    components: ComponentScores
    breakdown: MasteryBreakdown
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("1.0.0", description="Model version for tracking")

    @field_validator('mastery_score')
    @classmethod
    def validate_mastery_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Mastery score must be between 0.0 and 1.0, got {v}")
        return v

    @classmethod
    def calculate_from_components(
        cls,
        student_id: str,
        components: ComponentScores,
        weights: Optional[MasteryWeights] = None
    ) -> 'MasteryResult':
        """
        Calculate mastery score from component scores using the 40/30/20/10 formula

        Formula: M = 0.4*C + 0.3*Q + 0.2*Q + 0.1*C
                 (Completion + Quiz + Quality + Consistency)
        """
        if weights is None:
            weights = MasteryWeights()

        # Validate weights sum to 1.0
        weights.validate_sum()

        # Calculate weighted sum
        weighted_sum = (
            components.completion * weights.completion +
            components.quiz * weights.quiz +
            components.quality * weights.quality +
            components.consistency * weights.consistency
        )

        # Determine mastery level
        if weighted_sum < 0.4:
            level = MasteryLevel.NOVICE
        elif weighted_sum < 0.6:
            level = MasteryLevel.DEVELOPING
        elif weighted_sum < 0.8:
            level = MasteryLevel.PROFICIENT
        else:
            level = MasteryLevel.MASTER

        breakdown = MasteryBreakdown(
            completion=components.completion * weights.completion,
            quiz=components.quiz * weights.quiz,
            quality=components.quality * weights.quality,
            consistency=components.consistency * weights.consistency,
            weighted_sum=weighted_sum,
            weights=weights
        )

        return MasteryResult(
            student_id=student_id,
            mastery_score=weighted_sum,
            level=level,
            components=components,
            breakdown=breakdown
        )


class MasteryQueryRequest(BaseModel):
    """Request to query current mastery state"""
    student_id: str
    include_components: bool = Field(True, description="Include component breakdown")
    include_history: bool = Field(False, description="Include historical snapshots")
    days_history: int = Field(7, ge=1, le=90, description="Days of history to include")


class MasteryCalculateRequest(BaseModel):
    """Request to calculate new mastery from current components"""
    student_id: str
    components: ComponentScores
    weights: Optional[MasteryWeights] = None


class MasteryQueryResponse(BaseModel):
    """Response for mastery query"""
    success: bool = True
    data: Optional[MasteryResult] = None
    historical_average: Optional[float] = None
    trend: Optional[str] = Field(None, description="improving/declining/stable")
    metadata: Dict[str, any] = Field(default_factory=dict)


class HistoricalSnapshot(BaseModel):
    """Historical mastery snapshot"""
    date: datetime
    mastery_score: float
    level: MasteryLevel
    components: ComponentScores


class StudentActivity(BaseModel):
    """Recent activity summary for a student"""
    student_id: str
    last_updated: datetime
    recent_exercises: int = Field(0, ge=0)
    recent_quizzes: int = Field(0, ge=0)
    avg_session_duration: float = Field(0.0, ge=0.0)
    days_active: int = Field(0, ge=0, le=90)


class PredictionResult(BaseModel):
    """Mastery prediction result for future timeframe"""
    student_id: str
    predicted_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence based on historical data volume")
    trend: str = Field(..., pattern="^(improving|declining|stable)$")
    intervention_needed: bool = Field(..., description="Flag if prediction < 0.5")
    timeframe_days: int = Field(7, ge=1, le=30)
    predicted_level: MasteryLevel
    components_projection: ComponentScores
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, any] = Field(default_factory=dict)


class TrajectoryPoint(BaseModel):
    """Single point in mastery trajectory projection"""
    days_from_now: int
    predicted_score: float
    confidence: float
    level: MasteryLevel


class TrajectoryResult(BaseModel):
    """Complete mastery trajectory projection"""
    student_id: str
    trajectory: List[TrajectoryPoint]
    confidence_over_time: List[float]
    intervention_points: List[int]  # Days where intervention is flagged
    overall_trend: str
    metadata: Dict[str, any] = Field(default_factory=dict)


class PredictionModelConfig(BaseModel):
    """Configuration for prediction models"""
    min_history_days: int = Field(3, ge=1, description="Minimum days of history for predictions")
    max_history_days: int = Field(30, ge=7, le=90, description="Maximum days of history to consider")
    cache_ttl_minutes: int = Field(60, ge=1, le=1440, description="Cache duration for predictions")
    intervention_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Score threshold for intervention flag")
    confidence_decay_rate: float = Field(0.95, ge=0.8, le=1.0, description="Confidence decay per day of projection")


class PredictionAccuracyMetric(BaseModel):
    """Tracking metric for prediction accuracy"""
    student_id: str
    prediction_timestamp: datetime
    predicted_score: float
    actual_score: Optional[float] = None
    days_until_verification: int
    error: Optional[float] = None  # |predicted - actual|
    within_variance: Optional[bool] = None
    model_version: str = "1.0.0"


class StateKeyPatterns:
    """Static helper for generating state store key patterns"""

    @staticmethod
    def current_mastery(student_id: str) -> str:
        return f"student:{student_id}:profile:current_mastery"

    @staticmethod
    def daily_snapshot(student_id: str, date: datetime) -> str:
        return f"student:{student_id}:mastery:{date.strftime('%Y-%m-%d')}"

    @staticmethod
    def component_score(student_id: str, date: datetime, component: str) -> str:
        return f"student:{student_id}:mastery:{date.strftime('%Y-%m-%d')}:{component}"

    @staticmethod
    def activity_data(student_id: str) -> str:
        return f"student:{student_id}:activity:recent"

    @staticmethod
    def prediction(student_id: str, days: int) -> str:
        return f"student:{student_id}:prediction:{days}days"

    @staticmethod
    def trajectory(student_id: str) -> str:
        return f"student:{student_id}:trajectory"

    @staticmethod
    def prediction_accuracy(student_id: str, timestamp: datetime) -> str:
        return f"prediction_accuracy:{student_id}:{timestamp.strftime('%Y-%m-%d-%H-%M')}"

    @staticmethod
    def idempotency_check(event_id: str) -> str:
        return f"processed:{event_id}"