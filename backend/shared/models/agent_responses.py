"""
Agent Response Models
Elite Implementation Standard v2.0.0

Unified response schemas for all agent fleet microservices.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class AgentResponse(BaseModel):
    """Base response model for all agent interactions"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    request_id: UUID
    response_id: UUID = Field(default_factory=lambda: UUID.__new__(UUID))
    agent_type: str
    student_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ResponseStatus
    token_efficiency: float = Field(..., description="Token efficiency 0.0 to 1.0")
    metadata: Optional[Dict[str, Any]] = None


class ProgressResponse(AgentResponse):
    """Response model for Progress Agent"""
    mastery: float = Field(..., ge=0.0, le=1.0)
    breakdown: Dict[str, float]
    trend: Optional[str] = None


class DebugResponse(AgentResponse):
    """Response model for Debug Agent"""
    valid: bool
    errors: List[Dict[str, Any]]
    suggestions: List[str]
    complexity: Optional[Dict[str, float]] = None


class ConceptsResponse(AgentResponse):
    """Response model for Concepts Agent"""
    explanation: str
    prerequisites: List[str]
    related_concepts: List[str]
    difficulty_level: str


class ExerciseResponse(AgentResponse):
    """Response model for Exercise Agent"""
    problem: str
    solution: str
    hints: List[str]
    estimated_time: int


class ReviewResponse(AgentResponse):
    """Response model for Review Agent"""
    quality_score: float = Field(..., ge=0.0, le=1.0)
    feedback: str
    hints: List[str]
    suggestions: List[str]


class ErrorResponse(BaseModel):
    """Standardized error response"""
    request_id: UUID
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)