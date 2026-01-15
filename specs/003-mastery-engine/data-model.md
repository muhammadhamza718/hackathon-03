# Phase 1 Data Model Design: Mastery Engine
**Date**: 2026-01-14 | **Branch**: `003-mastery-engine`

This document defines the comprehensive data models for the Mastery Engine microservice.

## 1. Core Pydantic Models

### Mastery Components
```python
# File: src/models/mastery.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class MasteryLevel(str, Enum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    PROFICIENT = "proficient"
    EXPERT = "expert"

class ComponentScores(BaseModel):
    """Individual mastery component scores (0.0 to 1.0)"""
    completion: float = Field(..., ge=0.0, le=1.0, description="Completion rate component")
    quiz: float = Field(..., ge=0.0, le=1.0, description="Quiz performance component")
    quality: float = Field(..., ge=0.0, le=1.0, description="Code quality component")
    consistency: float = Field(..., ge=0.0, le=1.0, description="Consistency component")

    @validator('completion', 'quiz', 'quality', 'consistency')
    def validate_component_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Component scores must be between 0.0 and 1.0')
        return round(v, 3)

class MasteryCalculationRequest(BaseModel):
    """Request payload for mastery calculation"""
    student_id: str = Field(..., min_length=1, description="Student identifier")
    components: ComponentScores
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

class BreakdownItem(BaseModel):
    """Individual breakdown component with weighted contribution"""
    component: str
    score: float
    contribution: float
    weight: float

class MasteryResult(BaseModel):
    """Complete mastery calculation result"""
    student_id: str
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    level: MasteryLevel
    components: ComponentScores
    breakdown: List[BreakdownItem]
    recommendations: List[Dict[str, str]]
    timestamp: datetime
    version: str = Field(default="1.0")

class MasteryProfile(BaseModel):
    """Student's current mastery state"""
    student_id: str
    current_mastery: MasteryResult
    historical_average: float
    trend: str  # "improving", "declining", "stable"
    last_updated: datetime
    learning_path: List[str]

### Historical Data
class MasteryHistoryPoint(BaseModel):
    """Single point in mastery history"""
    timestamp: datetime
    score: float
    components: ComponentScores
    level: MasteryLevel

class MasteryHistory(BaseModel):
    """Complete mastery history for a student"""
    student_id: str
    history: List[MasteryHistoryPoint]
    summary: Dict[str, float]  # averages, max, min, etc.

### Predictive Models
class PredictionResult(BaseModel):
    """Mastery prediction for future timeframe"""
    student_id: str
    predicted_score: float
    confidence: float
    trend: str
    intervention_needed: bool
    timeframe_days: int = 7

class AdaptiveRecommendation(BaseModel):
    """Personalized learning recommendation"""
    action: str  # "practice", "review", "refactor", "schedule"
    area: str    # specific area to work on
    priority: str  # "high", "medium", "low"
    estimated_time: Optional[int] = None  # minutes
    resources: List[str] = Field(default_factory=list)

## 2. Event Schemas

### Mastery Events
```python
# File: src/models/events.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

class EventType(str, Enum):
    MASTERY_CALCULATION_REQUESTED = "mastery.calculation.requested"
    MASTERY_UPDATED = "mastery.updated"
    MASTERY_THRESHOLD_REACHED = "mastery.threshold.reached"
    LEARNING_PATH_RECOMMENDED = "learning.path.recommended"

class EventMetadata(BaseModel):
    """Event metadata for tracking and debugging"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str  # Origin service (e.g., "exercise-agent", "review-agent")
    version: str = "1.0"

class ExerciseCompletionData(BaseModel):
    """Data for exercise completion events"""
    total_exercises: int
    completed_exercises: int
    difficulty: str
    timestamp: datetime

class QuizPerformanceData(BaseModel):
    """Data for quiz performance events"""
    total_questions: int
    correct_answers: int
    time_spent: int  # seconds
    confidence_score: float

class QualityAssessmentData(BaseModel):
    """Data for quality assessment events"""
    code_quality_score: float
    correctness_score: float
    efficiency_score: float
    peer_review_score: Optional[float]

class ConsistencyData(BaseModel):
    """Data for consistency tracking"""
    current_streak: int
    max_streak: int
    days_since_last_activity: int
    activity_dates: List[datetime]

class MasteryCalculationRequestEvent(BaseModel):
    """Event requesting mastery calculation"""
    metadata: EventMetadata
    student_id: str
    components: Dict[str, Any]
    context: Dict[str, str] = Field(default_factory=dict)

class MasteryUpdatedEvent(BaseModel):
    """Event signaling mastery score update"""
    metadata: EventMetadata
    student_id: str
    mastery_score: float
    components: ComponentScores
    level: MasteryLevel
    recommendations: List[AdaptiveRecommendation]

class ThresholdReachedEvent(BaseModel):
    """Event when mastery crosses important thresholds"""
    metadata: EventMetadata
    student_id: str
    threshold: str  # "beginner", "competent", "proficient", "expert"
    previous_score: float
    new_score: float
    timestamp: datetime

class LearningPathRecommendedEvent(BaseModel):
    """Event with personalized learning path"""
    metadata: EventMetadata
    student_id: str
    path: List[str]
    estimated_completion: datetime
    priority_areas: List[str]

### Dead Letter Queue
class FailedEvent(BaseModel):
    """Event that failed processing and went to DLQ"""
    original_event: Dict[str, Any]
    error_message: str
    error_type: str
    failed_at: datetime
    retry_count: int = 0

## 3. State Store Key Patterns

```python
# File: src/models/state_keys.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class StateKeyPattern:
    """Standardized patterns for Dapr State Store keys"""

    # Current mastery state
    @staticmethod
    def current_mastery(student_id: str) -> str:
        return f"student:{student_id}:profile:current_mastery"

    # Daily mastery snapshot
    @staticmethod
    def daily_mastery(student_id: str, date: str) -> str:
        return f"student:{student_id}:mastery:{date}"

    # Individual components
    @staticmethod
    def component_score(student_id: str, component: str, date: str) -> str:
        return f"student:{student_id}:mastery:{date}:{component}"

    # Event processing checkpoint
    @staticmethod
    def processed_event(event_id: str) -> str:
        return f"processed:{event_id}"

    # Student history
    @staticmethod
    def mastery_history(student_id: str) -> str:
        return f"student:{student_id}:history:full"

    # Recent activity
    @staticmethod
    def recent_activity(student_id: str) -> str:
        return f"student:{student_id}:activity:recent"

    # Predictive cache
    @staticmethod
    def prediction_cache(student_id: str) -> str:
        return f"student:{student_id}:prediction:cache"

    # Adaptive path
    @staticmethod
    def adaptive_path(student_id: str) -> str:
        return f"student:{student_id}:path:adaptive"

class StateManager:
    """Manages state store operations with standardized key patterns"""

    def __init__(self, dapr_client):
        self.dapr = dapr_client
        self.store_name = "statestore"

    async def get_current_mastery(self, student_id: str) -> Optional[MasteryResult]:
        key = StateKeyPattern.current_mastery(student_id)
        result = await self.dapr.state.get(self.store_name, key)
        return MasteryResult.parse_raw(result) if result else None

    async def save_mastery_snapshot(self, student_id: str, mastery: MasteryResult, date: str):
        # Save daily snapshot
        daily_key = StateKeyPattern.daily_mastery(student_id, date)
        await self.dapr.state.save(
            self.store_name,
            [ {"key": daily_key, "value": mastery.json()} ]
        )

        # Update current mastery
        current_key = StateKeyPattern.current_mastery(student_id)
        await self.dapr.state.save(
            self.store_name,
            [ {"key": current_key, "value": mastery.json()} ]
        )

## 4. API Request/Response Models

### Query Endpoints
```python
# File: src/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class MasteryQueryRequest(BaseModel):
    """Request mastery data for student"""
    student_id: str
    date: Optional[date] = Field(None, description="Specific date (defaults to today)")
    include_components: bool = Field(True, description="Include detailed component breakdown")

class MasteryQueryResponse(BaseModel):
    """Response for mastery query"""
    success: bool
    data: Optional[MasteryProfile] = None
    error: Optional[str] = None

class PredictionQueryRequest(BaseModel):
    """Request prediction for student"""
    student_id: str
    timeframe_days: int = Field(7, ge=1, le=30)

class PredictionQueryResponse(BaseModel):
    """Response for prediction query"""
    success: bool
    data: Optional[PredictionResult] = None
    error: Optional[str] = None

class RecommendationQueryRequest(BaseModel):
    """Request recommendations for student"""
    student_id: str
    limit: int = Field(5, ge=1, le=10)
    priority: Optional[str] = None

class RecommendationQueryResponse(BaseModel):
    """Response for recommendation query"""
    success: bool
    data: List[AdaptiveRecommendation] = Field(default_factory=list)
    error: Optional[str] = None

class BatchMasteryRequest(BaseModel):
    """Batch mastery calculation request"""
    requests: List[MasteryCalculationRequest]
    priority: str = Field("normal", pattern="^(low|normal|high)$")

class BatchMasteryResponse(BaseModel):
    """Batch mastery calculation response"""
    results: List[MasteryResult]
    failures: List[Dict[str, str]] = Field(default_factory=list)
    summary: Dict[str, int]  # counts, averages

## 5. Database/State Store Schema (Conceptual)

### Redis Key Structure
```
# Mastery Data
student:12345:profile:current_mastery          # MasteryResult (JSON)
student:12345:mastery:2026-01-14               # MasteryResult (JSON)
student:12345:mastery:2026-01-14:completion    # float (0.85)
student:12345:mastery:2026-01-14:quiz          # float (0.90)
student:12345:mastery:2026-01-14:quality       # float (0.85)
student:12345:mastery:2026-01-14:consistency   # float (0.82)

# History
student:12345:history:full                     # MasteryHistory (JSON)
student:12345:activity:recent                  # ActivityData (JSON)

# Processing
processed:{event_id}                           # ProcessingRecord (JSON, TTL 7d)
student:12345:prediction:cache                 # PredictionResult (JSON, TTL 1h)
student:12345:path:adaptive                    # List[str] (JSON)

# Multi-tenant isolation
school:ABC123:student:12345:profile:current    # For school-level access
```

### TTL Configurations
```
processed:*               # 7 days (event deduplication)
student:*:prediction:cache # 1 hour (prediction cache)
student:*:activity:recent  # 30 days (recent activity)
mastery.dlq.*             # 30 days (dead letter queue)
```

## 6. Validation Rules

### Component Score Validation
```python
VALIDATION_RULES = {
    "completion": {
        "min": 0.0,
        "max": 1.0,
        "required_precision": 3,
        "description": "Must be 0.0 to 1.0, rounded to 3 decimals"
    },
    "quiz": {
        "min": 0.0,
        "max": 1.0,
        "required_precision": 3,
        "description": "Must be 0.0 to 1.0, rounded to 3 decimals"
    },
    "quality": {
        "min": 0.0,
        "max": 1.0,
        "required_precision": 3,
        "description": "Must be 0.0 to 1.0, rounded to 3 decimals"
    },
    "consistency": {
        "min": 0.0,
        "max": 1.0,
        "required_precision": 3,
        "description": "Must be 0.0 to 1.0, rounded to 3 decimals"
    }
}
```

### ID Format Requirements
```python
STUDENT_ID_PATTERN = r"^[a-zA-Z0-9_-]{1,50}$"
EVENT_ID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
```

## 7. Versioning Strategy

### Model Versioning
- **Current**: v1.0
- **Backward Compatibility**: 2 versions supported
- **Migration Strategy**: Automatic migration on read/write

### API Versioning
```
/api/v1/mastery/query          # Current
/api/v2/mastery/query          # Future enhancements

Headers:
X-Mastery-Model-Version: 1.0
X-Request-Id: uuid-v4
```

## 8. Security Considerations

### Data Classification
```python
class DataClassification(str, Enum):
    PUBLIC = "public"           # Mastery scores themselves
    INTERNAL = "internal"       # Detailed component breakdowns
    SENSITIVE = "sensitive"     # Raw event data, predictive models
    CONFIDENTIAL = "confidential"  # Audit logs

# Apply classification
MASTERY_DATA_CLASSIFICATION = {
    "mastery_score": DataClassification.PUBLIC,
    "component_breakdown": DataClassification.INTERNAL,
    "raw_events": DataClassification.SENSITIVE,
    "audit_logs": DataClassification.CONFIDENTIAL
}
```

### Encryption Requirements
- **At Rest**: Redis encryption enabled
- **In Transit**: TLS 1.3 for all communications
- **Key Management**: Dapr secret store integration

## 9. Scalability Considerations

### Data Volume Estimates (per 50k students)
- **Daily snapshots**: 50k × 30 days = 1.5M records
- **Event storage**: 1M events/day × 30 days = 30M events
- **Cache size**: ~500MB for active students (5k)
- **Total storage**: ~50GB (Redis) + ~300GB (Kafka retention)

### Partitioning Strategy
```python
# Student ID based sharding
def get_shard_key(student_id: str) -> str:
    """Consistent hashing for student distribution"""
    hash_value = hash(student_id)
    return f"shard_{hash_value % 16}"

# Kafka partition assignment
def get_kafka_partition(student_id: str) -> int:
    """Deterministic partition assignment"""
    return hash(student_id) % 6  # 6 partitions
```

---
**Next**: Create API contracts and event schemas in `/specs/003-mastery-engine/contracts/`