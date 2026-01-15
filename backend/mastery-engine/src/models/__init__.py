"""
Models Module
=============

Contains all Pydantic models for data validation and serialization.
"""

from .mastery import (
    ComponentScores,
    MasteryCalculationRequest,
    MasteryResult,
    MasteryLevel,
    MasteryProfile,
    MasteryHistoryPoint,
    MasteryHistory,
    PredictionResult,
    AdaptiveRecommendation,
    BreakdownItem
)
from .events import (
    EventMetadata,
    EventType,
    MasteryCalculationRequestEvent,
    MasteryUpdatedEvent,
    ThresholdReachedEvent,
    ExerciseCompletionData,
    QuizPerformanceData,
    QualityAssessmentData,
    ConsistencyData,
    FailedEvent
)
from .state_keys import StateKeyPattern, StateManager

__all__ = [
    # Mastery models
    "ComponentScores",
    "MasteryCalculationRequest",
    "MasteryResult",
    "MasteryLevel",
    "MasteryProfile",
    "MasteryHistoryPoint",
    "MasteryHistory",
    "PredictionResult",
    "AdaptiveRecommendation",
    "BreakdownItem",

    # Event models
    "EventMetadata",
    "EventType",
    "MasteryCalculationRequestEvent",
    "MasteryUpdatedEvent",
    "ThresholdReachedEvent",
    "ExerciseCompletionData",
    "QuizPerformanceData",
    "QualityAssessmentData",
    "ConsistencyData",
    "FailedEvent",

    # State management
    "StateKeyPattern",
    "StateManager"
]