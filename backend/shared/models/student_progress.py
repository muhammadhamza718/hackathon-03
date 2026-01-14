"""
Student Progress Event Model
Elite Implementation Standard v2.0.0

Kafka event model for student progress updates, Avro-compatible.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID, uuid4


class ComponentScores(BaseModel):
    """Component score breakdown"""
    model_config = ConfigDict(str_strip_whitespace=True)

    completion: float = Field(..., ge=0.0, le=1.0, description="Exercise completion rate")
    quiz: float = Field(..., ge=0.0, le=1.0, description="Quiz performance")
    quality: float = Field(..., ge=0.0, le=1.0, description="Solution quality")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Learning consistency")


class StudentProgress(BaseModel):
    """
    Student Progress Event for Kafka Streaming
    Avro-compatible event schema with evolution support

    Topic: learning.events
    Partition key: student_id
    Retention: 7 days
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: str = Field(default="student.progress.update", description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    version: str = Field(default="1.0", description="Schema version for evolution")

    student_id: str = Field(..., description="Student identifier")
    component: str = Field(..., description="Learning component/topic")
    scores: ComponentScores = Field(..., description="Score breakdown")
    mastery: float = Field(..., ge=0.0, le=1.0, description="Overall mastery score (calculated)")

    idempotency_key: str = Field(..., description="Idempotency key for deduplication")

    # Optional fields for future evolution
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Additional metadata")

    def calculate_mastery(self) -> float:
        """
        Calculate mastery using 40/30/20/10 formula
        40% completion + 30% quiz + 20% quality + 10% consistency
        """
        return (
            self.scores.completion * 0.4 +
            self.scores.quiz * 0.3 +
            self.scores.quality * 0.2 +
            self.scores.consistency * 0.1
        )

    def model_post_init(self, __context):
        """Post-initialization to ensure mastery matches calculated value"""
        if not hasattr(self, '_manual_mastery') or not self._manual_mastery:
            # Auto-calculate mastery if not explicitly set
            object.__setattr__(self, 'mastery', self.calculate_mastery())


class ProgressEventBatch(BaseModel):
    """Batch of progress events for bulk processing"""
    events: list[StudentProgress]
    batch_id: UUID = Field(default_factory=uuid4)
    batch_size: int = Field(default=0)
    processed_at: Optional[datetime] = None