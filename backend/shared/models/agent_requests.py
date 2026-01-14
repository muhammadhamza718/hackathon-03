"""
Agent Request Models
Elite Implementation Standard v2.0.0

Unified request schemas for all agent fleet microservices.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


class AgentType(str, Enum):
    """Supported agent types in the fleet"""
    PROGRESS = "progress"
    DEBUG = "debug"
    CONCEPTS = "concepts"
    EXERCISE = "exercise"
    REVIEW = "review"


class SecurityContext(BaseModel):
    """JWT security context for authentication"""
    student_id: str
    token: str
    permissions: List[str] = ["read", "write"]


class AgentRequest(BaseModel):
    """Base request model for all agent interactions"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    request_id: UUID = Field(default_factory=uuid4)
    agent_type: AgentType
    student_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProgressRequest(AgentRequest):
    """Request model for Progress Agent"""
    component: str
    scores: Dict[str, float] = Field(..., description="Scores for completion, quiz, quality, consistency")

    @field_validator('scores')
    @classmethod
    def validate_scores(cls, v):
        for key, value in v.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Score {key} must be between 0.0 and 1.0")
        return v


class DebugRequest(AgentRequest):
    """Request model for Debug Agent"""
    code: str
    language: str = "python"
    error_context: Optional[str] = None


class ConceptsRequest(AgentRequest):
    """Request model for Concepts Agent"""
    concept_name: str
    depth: str = "standard"  # standard, deep, beginner
    prerequisites: bool = False


class ExerciseRequest(AgentRequest):
    """Request model for Exercise Agent"""
    topic: str
    difficulty: str = "medium"  # beginner, medium, hard
    problem_type: str = "practice"


class ReviewRequest(AgentRequest):
    """Request model for Review Agent"""
    code: str
    review_type: str = "quality"  # quality, hints, feedback
    context: Optional[str] = None