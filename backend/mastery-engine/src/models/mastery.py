"""
Mastery Models
==============

Pydantic models for mastery calculation and state management.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import UUID

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

    @staticmethod
    def batch_job(batch_id: str) -> str:
        return f"batch:{batch_id}"

    @staticmethod
    def batch_result(batch_id: str, student_id: str) -> str:
        return f"batch:{batch_id}:result:{student_id}"

    @staticmethod
    def analytics_request(request_id: str) -> str:
        return f"analytics:request:{request_id}"


# ==================== PHASE 9: BATCH PROCESSING MODELS ====================

class BatchPriority(str, Enum):
    """Priority levels for batch processing jobs"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class BatchStatus(str, Enum):
    """Status of batch processing job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchMasteryRequest(BaseModel):
    """Request for batch mastery calculation"""
    student_ids: List[str] = Field(..., min_items=1, max_items=1000, description="Up to 1000 student IDs")
    priority: BatchPriority = Field(BatchPriority.NORMAL)
    callback_url: Optional[str] = Field(None, description="Optional webhook for completion notification")


class BatchMasteryItem(BaseModel):
    """Individual result item for batch processing"""
    student_id: str
    success: bool
    mastery_result: Optional[MasteryResult] = None
    error_message: Optional[str] = None


class BatchMasteryResponse(BaseModel):
    """Response for batch mastery calculation request"""
    batch_id: str
    status: BatchStatus
    student_count: int
    processed_count: int = Field(0, description="Number of students processed so far")
    priority: BatchPriority
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[BatchMasteryItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchJobStatus(BaseModel):
    """Status query response for batch job"""
    batch_id: str
    status: BatchStatus
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)
    total_students: int
    processed_students: int
    failed_count: int = Field(0, description="Number of failures")
    estimated_time_remaining: Optional[int] = Field(None, description="Seconds remaining")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== PHASE 9: ANALYTICS MODELS ====================

class AggregationType(str, Enum):
    """Type of data aggregation for historical analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DateRangeRequest(BaseModel):
    """Request for date-range based analytics"""
    student_id: str
    start_date: date
    end_date: date
    aggregation: AggregationType = Field(AggregationType.DAILY)

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        if 'start_date' in values.data and v < values.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


class MasteryHistoryData(BaseModel):
    """Historical mastery data point"""
    date: date
    mastery_score: float
    level: MasteryLevel
    components: ComponentScores
    sample_size: int = Field(1, description="Number of events contributing to this snapshot")


class MasteryHistoryResponse(BaseModel):
    """Response for mastery history query"""
    student_id: str
    start_date: date
    end_date: date
    aggregation: AggregationType
    data: List[MasteryHistoryData]
    statistics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SummaryStatistics(BaseModel):
    """Statistical summary for a period"""
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentiles: Dict[str, float] = Field(default_factory=dict)  # e.g., "25": 0.4, "75": 0.8


class MasteryAnalyticsResponse(BaseModel):
    """Comprehensive analytics response with statistics"""
    student_id: str
    period: DateRangeRequest
    summary: SummaryStatistics
    trend: str = Field(..., pattern="^(improving|declining|stable|inconsistent)$")
    volatility: float = Field(..., ge=0.0, le=1.0, description="Standard deviation normalized to 0-1")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="How consistent the student is")
    component_trends: Dict[str, str] = Field(default_factory=dict)  # Component -> trend
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CohortComparisonRequest(BaseModel):
    """Request for cohort comparison analytics"""
    cohort_a_student_ids: List[str] = Field(..., min_items=2, description="First cohort of students")
    cohort_b_student_ids: List[str] = Field(..., min_items=2, description="Second cohort of students")
    comparison_date: Optional[date] = Field(None, description="Specific date for comparison, or latest")
    include_component_analysis: bool = Field(True, description="Include component-level comparison")
    include_percentiles: bool = Field(True, description="Include percentile rankings")


class CohortComparisonResult(BaseModel):
    """Comparison results between two cohorts"""
    cohort_a_stats: SummaryStatistics
    cohort_b_stats: SummaryStatistics
    statistical_significance: Optional[float] = Field(None, ge=0.0, le=1.0, description="p-value if calculable")
    winner: Optional[str] = Field(None, description="Which cohort performed better")
    component_comparison: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    percentile_rankings: Dict[str, float] = Field(default_factory=dict)  # student_id -> percentile
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StudentComparisonRequest(BaseModel):
    """Request to compare specific students or groups"""
    student_ids: List[str] = Field(..., min_items=2, max_items=50, description="Students to compare")
    metric: str = Field("mastery_score", description="Which metric to compare")
    timeframe_days: int = Field(30, ge=1, le=365, description="Lookback period")


class StudentComparisonResult(BaseModel):
    """Result of student comparison"""
    rankings: List[Dict[str, Any]]  # List of student rankings
    comparisons: Dict[str, Dict[str, Any]]  # Detailed comparisons
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==================== PHASE 10: DAPR INTEGRATION MODELS ====================

class DaprIntent(str, Enum):
    """Intents for Dapr service invocation"""
    MASTERY_CALCULATION = "mastery_calculation"
    GET_PREDICTION = "get_prediction"
    GENERATE_PATH = "generate_path"
    BATCH_PROCESS = "batch_process"
    ANALYTICS_QUERY = "analytics_query"


class DaprSecurityContext(BaseModel):
    """Security context propagated from Dapr"""
    token: Optional[str] = Field(None, description="JWT token for authentication")
    user_id: Optional[str] = Field(None, description="User making the request")
    roles: List[str] = Field(default_factory=list, description="User roles")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class DaprProcessRequest(BaseModel):
    """Request for Dapr service invocation"""
    intent: DaprIntent
    payload: Dict[str, Any] = Field(default_factory=dict, description="Intent-specific payload")
    security_context: Optional[DaprSecurityContext] = None


class DaprProcessResponse(BaseModel):
    """Standardized response for Dapr service invocation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class DaprErrorDetail(BaseModel):
    """Detailed error information for Dapr calls"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retryable: bool = False


# ==================== UTILITY REQUEST/RESPONSE MODELS ====================

class BatchStatusQuery(BaseModel):
    """Query for batch job status"""
    batch_id: str


class AnalyticsConfigResponse(BaseModel):
    """Configuration for analytics services"""
    model_version: str
    config: Dict[str, Any]
    notes: str