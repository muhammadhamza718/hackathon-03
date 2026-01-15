"""
Event Models
============

Pydantic models for learning events and Kafka message schemas.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import json

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Types of learning events"""
    EXERCISE_COMPLETED = "exercise.completed"
    QUIZ_COMPLETED = "quiz.completed"
    LESSON_VIEWED = "lesson.viewed"
    CONTENT_RATED = "content.rated"
    MILESTONE_REACHED = "milestone.reached"


class EventSource(str, Enum):
    """Source of the event"""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API = "api"
    BATCH_PROCESS = "batch_process"


class LearningEvent(BaseModel):
    """
    Core learning event model for Kafka event streaming
    """
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    event_type: EventType
    student_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: EventSource = Field(default=EventSource.WEB_APP)

    # Event-specific data
    data: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    version: str = Field("1.0.0", description="Event schema version")
    correlation_id: Optional[str] = Field(None, description="For request tracing")

    @field_validator('event_id')
    @classmethod
    def validate_event_id(cls, v):
        """Validate event_id format"""
        if not v or len(v) < 8:
            raise ValueError("Event ID must be a valid UUID")
        return v

    def get_data_hash(self) -> str:
        """Generate hash of event data for idempotency checks"""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def to_kafka_message(self) -> Dict[str, any]:
        """Convert to Kafka message format"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "student_id": self.student_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "data": self.data,
            "version": self.version,
            "correlation_id": self.correlation_id
        }

    @classmethod
    def from_kafka_message(cls, message: Dict[str, any]) -> 'LearningEvent':
        """Create LearningEvent from Kafka message"""
        return cls(
            event_id=message["event_id"],
            event_type=EventType(message["event_type"]),
            student_id=message["student_id"],
            timestamp=datetime.fromisoformat(message["timestamp"]),
            source=EventSource(message["source"]),
            data=message.get("data", {}),
            version=message.get("version", "1.0.0"),
            correlation_id=message.get("correlation_id")
        )


class ExerciseCompletedEvent(LearningEvent):
    """Event for completed exercises"""
    event_type: EventType = Field(default=EventType.EXERCISE_COMPLETED, const=True)

    # Required data fields
    exercise_id: str
    difficulty: str  # easy/medium/hard/expert
    time_spent_seconds: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    correctness: float = Field(..., ge=0.0, le=1.0)

    # Optional fields
    topic_ids: List[str] = Field(default_factory=list)
    hints_used: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0)

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v):
        valid_difficulties = ["easy", "medium", "hard", "expert"]
        if v not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of {valid_difficulties}")
        return v

    def model_post_init(self, __context):
        """Initialize data field with exercise-specific data"""
        self.data = {
            "exercise_id": self.exercise_id,
            "difficulty": self.difficulty,
            "time_spent_seconds": self.time_spent_seconds,
            "completion_rate": self.completion_rate,
            "correctness": self.correctness,
            "topic_ids": self.topic_ids,
            "hints_used": self.hints_used,
            "retries": self.retries
        }


class QuizCompletedEvent(LearningEvent):
    """Event for completed quizzes"""
    event_type: EventType = Field(default=EventType.QUIZ_COMPLETED, const=True)

    # Required data fields
    quiz_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    questions_total: int = Field(..., ge=1)
    questions_correct: int = Field(..., ge=0)
    time_spent_seconds: int

    # Optional fields
    topic_ids: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None

    @field_validator('questions_correct')
    @classmethod
    def validate_questions_correct(cls, v, values):
        if "questions_total" in values and v > values["questions_total"]:
            raise ValueError("Correct questions cannot exceed total questions")
        return v

    def model_post_init(self, __context):
        self.data = {
            "quiz_id": self.quiz_id,
            "score": self.score,
            "questions_total": self.questions_total,
            "questions_correct": self.questions_correct,
            "time_spent_seconds": self.time_spent_seconds,
            "topic_ids": self.topic_ids,
            "difficulty": self.difficulty
        }


class LessonViewedEvent(LearningEvent):
    """Event for lesson views"""
    event_type: EventType = Field(default=EventType.LESSON_VIEWED, const=True)

    lesson_id: str
    duration_seconds: int = Field(..., ge=0)
    completion_percentage: float = Field(..., ge=0.0, le=1.0)
    topic_ids: List[str] = Field(default_factory=list)

    def model_post_init(self, __context):
        self.data = {
            "lesson_id": self.lesson_id,
            "duration_seconds": self.duration_seconds,
            "completion_percentage": self.completion_percentage,
            "topic_ids": self.topic_ids
        }


class ContentRatedEvent(LearningEvent):
    """Event for content ratings"""
    event_type: EventType = Field(default=EventType.CONTENT_RATED, const=True)

    content_id: str
    content_type: str  # exercise/lesson/quiz
    rating: int = Field(..., ge=1, le=5)
    helpful: Optional[bool] = None
    comment: Optional[str] = Field(None, max_length=1000)

    def model_post_init(self, __context):
        self.data = {
            "content_id": self.content_id,
            "content_type": self.content_type,
            "rating": self.rating,
            "helpful": self.helpful,
            "comment": self.comment
        }


class MilestoneReachedEvent(LearningEvent):
    """Event for milestone achievements"""
    event_type: EventType = Field(default=EventType.MILESTONE_REACHED, const=True)

    milestone_type: str  # streak/consecutive_days/total_exercises/etc
    milestone_value: int
    message: str
    previous_value: Optional[int] = None

    def model_post_init(self, __context):
        self.data = {
            "milestone_type": self.milestone_type,
            "milestone_value": self.milestone_value,
            "message": self.message,
            "previous_value": self.previous_value
        }


class ProcessingRecord(BaseModel):
    """Record of event processing for idempotency and monitoring"""
    event_id: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    success: bool
    error_message: Optional[str] = None
    processing_time_ms: float
    state_updates: int = Field(default=0)
    attempts: int = Field(default=1)


class EventValidationResult(BaseModel):
    """Result of event validation"""
    valid: bool
    event: Optional[LearningEvent] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class KafkaMessageConfig(BaseModel):
    """Configuration for Kafka topic operations"""
    topic_requests: str = Field(default="mastery.requests")
    topic_results: str = Field(default="mastery.results")
    topic_dlq: str = Field(default="mastery.dlq")
    consumer_group: str = Field(default="mastery-engine-v1")
    batch_size: int = Field(default=100, ge=1, le=1000)
    poll_timeout_ms: int = Field(default=1000, ge=100, le=30000)
    retry_attempts: int = Field(default=3, ge=0, le=10)


# Factory functions for creating events
def create_learning_event(
    event_type: str,
    student_id: str,
    data: Dict[str, any],
    event_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> LearningEvent:
    """
    Factory function to create appropriate LearningEvent subclass

    Args:
        event_type: Type of event as string
        student_id: Student identifier
        data: Event-specific data
        event_id: Optional custom event ID
        correlation_id: Optional correlation ID for tracing

    Returns:
        Appropriate LearningEvent subclass instance
    """
    import uuid

    event_id = event_id or str(uuid.uuid4())

    event_map = {
        EventType.EXERCISE_COMPLETED.value: ExerciseCompletedEvent,
        EventType.QUIZ_COMPLETED.value: QuizCompletedEvent,
        EventType.LESSON_VIEWED.value: LessonViewedEvent,
        EventType.CONTENT_RATED.value: ContentRatedEvent,
        EventType.MILESTONE_REACHED.value: MilestoneReachedEvent,
    }

    event_class = event_map.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")

    # Merge data with required fields
    base_params = {
        "event_id": event_id,
        "student_id": student_id,
        "correlation_id": correlation_id
    }

    # For events that have their own fields, extract from data
    if event_type == EventType.EXERCISE_COMPLETED.value:
        return event_class(**base_params, **data)
    elif event_type == EventType.QUIZ_COMPLETED.value:
        return event_class(**base_params, **data)
    elif event_type == EventType.LESSON_VIEWED.value:
        return event_class(**base_params, **data)
    elif event_type == EventType.CONTENT_RATED.value:
        return event_class(**base_params, **data)
    elif event_type == EventType.MILESTONE_REACHED.value:
        return event_class(**base_params, **data)

    # Fallback to base event
    return LearningEvent(event_id=event_id, event_type=EventType(event_type), student_id=student_id, data=data)


def validate_event_data(event_type: str, data: Dict[str, any]) -> EventValidationResult:
    """
    Validate event data against event type requirements

    Returns:
        Validation result with success/failure and any errors
    """
    try:
        event = create_learning_event(event_type, "temp_validation", data)
        return EventValidationResult(valid=True, event=event)
    except Exception as e:
        return EventValidationResult(valid=False, errors=[str(e)])


class EventBatch(BaseModel):
    """Batch of events for bulk processing"""
    events: List[LearningEvent]
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_events: int = Field(default=0)

    def model_post_init(self, __context):
        self.total_events = len(self.events)

    def to_kafka_messages(self) -> List[Dict[str, any]]:
        """Convert batch to Kafka message format"""
        return [event.to_kafka_message() for event in self.events]