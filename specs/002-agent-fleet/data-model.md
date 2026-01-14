# Data Model: Specialized Agent Fleet

**Branch**: `002-agent-fleet` | **Date**: 2026-01-13
**Context**: Milestone 3 - Five specialized tutoring agents with stateful mastery tracking

## Entity Overview

### Core Entities

1. **StudentProgress** (Kafka Events + State Store)
2. **MasteryScores** (Stateful Calculation)
3. **AgentRequest** (Unified Request Schema)
4. **AgentResponse** (Unified Response Schema)
5. **ErrorEvent** (Dead Letter Queue Schema)

## Entity Relationship Diagram

```
┌─────────────────┐
│   Student       │
│   (External)    │
└────────┬────────┘
         │
         │ produces
         ▼
┌─────────────────┐
│ StudentProgress │◄─────────────────┐
│   Event         │                   │
└────────┬────────┘                   │
         │                            │
         │ consumed by                │
         ▼                            │
┌─────────────────┐   ┌─────────────┐ │
│ Progress Agent  │   │ Debug Agent │ │
│ (State Writer)  │   │ (Consumer)  │ │
└────────┬────────┘   └──────┬──────┘ │
         │                   │        │
         │ publishes         │        │
         │ to events         │        │
         ▼                   ▼        │
┌─────────────────────────────────────┐
│         Kafka Learning Events       │
└─────────────────┬───────────────────┘
                  │
         ┌────────┴────────┬───────────┬──────────┐
         ▼                 ▼           ▼          ▼
   ┌──────────┐   ┌──────────┐  ┌──────────┐ ┌──────────┐
   │ Concepts │   │ Exercise │  │ Review   │ │ Dead     │
   │ Agent    │   │ Agent    │  │ Agent    │ │ Letter   │
   │ (Consumer)│  │ (Consumer)│  │ (Consumer)│ │ Queue    │
   └──────────┘   └──────────┘  └──────────┘ └──────────┘
```

## Detailed Entity Definitions

### 1. StudentProgress (Kafka Event)

**Purpose**: Core event schema for all student learning progress updates

**Storage**: Kafka topic `learning.events` (Avro format)

**Schema Version**: 1.0

**Fields**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `event_id` | string | Yes | UUID for event identification | `"evt-12345-abc"` |
| `event_type` | string | Yes | Event classification | `"student.progress.update"` |
| `timestamp` | long | Yes | Unix timestamp (millis) | `1642095000000` |
| `version` | string | Yes | Schema version | `"1.0"` |
| `student_id` | string | Yes | Student identifier | `"stu-00123"` |
| `component` | string | Yes | Learning component | `"loops"` |
| `scores` | object | Yes | Component scores | See below |
| `mastery` | float | Yes | Calculated mastery (0-1) | `0.835` |
| `idempotency_key` | string | Yes | Prevent duplicates | `"key-123"` |

**scores Object**:

```json
{
  "completion": 0.85,
  "quiz": 0.90,
  "quality": 0.75,
  "consistency": 0.80
}
```

**Validation Rules**:
- All scores must be between 0.0 and 1.0
- `mastery` must equal weighted calculation: `completion*0.4 + quiz*0.3 + quality*0.2 + consistency*0.1`
- `idempotency_key` must be unique per logical event

**Kafka Configuration**:
```yaml
topic: learning.events
partitions: 6  # Partitioned by student_id
replication: 3
retention: 7 days
```

**Python Implementation**:
```python
from pydantic import BaseModel, Field, validator
from typing import Dict
from datetime import datetime

class ComponentScores(BaseModel):
    completion: float = Field(..., ge=0.0, le=1.0)
    quiz: float = Field(..., ge=0.0, le=1.0)
    quality: float = Field(..., ge=0.0, le=1.0)
    consistency: float = Field(..., ge=0.0, le=1.0)

class StudentProgress(BaseModel):
    event_id: str
    event_type: str = "student.progress.update"
    timestamp: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))
    version: str = "1.0"
    student_id: str
    component: str
    scores: ComponentScores
    mastery: float
    idempotency_key: str

    @validator('mastery')
    def validate_mastery(cls, v, values):
        if 'scores' in values:
            expected = (
                values['scores'].completion * 0.4 +
                values['scores'].quiz * 0.3 +
                values['scores'].quality * 0.2 +
                values['scores'].consistency * 0.1
            )
            if abs(v - expected) > 0.001:
                raise ValueError(f"Mastery must equal calculated value: {expected}")
        return v
```

### 2. MasteryScores (Dapr State Store)

**Purpose**: Persistent storage of current mastery state per student

**Storage**: Dapr State Store (Redis)

**Key Pattern**: `student:{student_id}:mastery:latest`

**Structure**:
```json
{
  "student_id": "stu-00123",
  "latest_scores": {
    "loops": {
      "completion": 0.85,
      "quiz": 0.90,
      "quality": 0.75,
      "consistency": 0.80
    },
    "functions": {
      "completion": 0.70,
      "quiz": 0.65,
      "quality": 0.80,
      "consistency": 0.75
    }
  },
  "overall_mastery": 0.778,
  "last_updated": "2026-01-13T10:30:00Z",
  "components_tracked": ["loops", "functions"]
}
```

**Python Implementation**:
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class MasteryData(BaseModel):
    completion: float
    quiz: float
    quality: float
    consistency: float

class MasteryScores(BaseModel):
    student_id: str
    latest_scores: Dict[str, MasteryData]
    overall_mastery: float
    last_updated: str
    components_tracked: List[str]

    @property
    def total_components(self) -> int:
        return len(self.components_tracked)
```

### 3. AgentRequest (Base Request Schema)

**Purpose**: Unified request structure for all agents

**Usage**: Input for all agent endpoints

**Structure**:
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AgentRequest(BaseModel):
    student_id: str = Field(..., min_length=1, description="Student identifier")
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request time")

class DebugRequest(AgentRequest):
    code: str = Field(..., min_length=1, description="Code to analyze")
    language: str = Field(default="python", description="Programming language")

class ExerciseRequest(AgentRequest):
    topic: str = Field(..., description="Learning topic")
    difficulty: Optional[str] = Field(default="medium", description="easy|medium|hard")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Problem constraints")

class ReviewRequest(AgentRequest):
    code: str = Field(..., min_length=1, description="Code to review")
    criteria: List[str] = Field(default=["readability", "efficiency", "style"], description="Review criteria")
```

### 4. AgentResponse (Unified Response Schema)

**Purpose**: Standardized response across all agents

**Structure**:
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from datetime import datetime

class AgentResponse(BaseModel):
    response_id: str = Field(..., description="Response identifier")
    agent_type: str = Field(..., description="Agent type: progress|debug|concepts|exercise|review")
    student_id: str = Field(..., description="Student identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str = Field(..., description="Main response content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    token_efficiency: float = Field(..., description="Token efficiency percentage")
    processing_time_ms: float = Field(..., description="Processing time")
```

**Example Response**:
```json
{
  "response_id": "resp-12345",
  "agent_type": "debug",
  "student_id": "stu-00123",
  "timestamp": "2026-01-13T10:30:00.123Z",
  "content": "Your code has a syntax error at line 3. Missing closing parenthesis.",
  "metadata": {
    "error_line": 3,
    "error_type": "SyntaxError",
    "suggestion": "Add closing parenthesis"
  },
  "token_efficiency": 0.94,
  "processing_time_ms": 45.2
}
```

### 5. ErrorEvent (Dead Letter Queue)

**Purpose**: Schema for failed events that need manual review

**Storage**: Kafka topic `dead-letter.queue`

**Structure**:
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class ErrorEvent(BaseModel):
    event_id: str
    original_event_type: str
    error_type: str
    error_message: str
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    original_payload: Dict[str, Any]
    retry_count: int = Field(default=0, ge=0, le=5)
    consumer_agent: Optional[str] = None

    @property
    def is_permanent_failure(self) -> bool:
        return self.retry_count >= 5
```

## Agent-Specific Data Models

### Progress Agent

**Internal State**:
```python
class StudentProgressState(BaseModel):
    """Internal state for progress agent"""
    student_id: str
    component_history: Dict[str, List[Dict[str, float]]]  # Historical scores
    mastery_trend: List[float]  # Overall mastery over time
    last_event_id: str  # Last processed event
```

### Debug Agent

**Analysis Results**:
```python
class DebugAnalysis(BaseModel):
    """Code analysis results"""
    valid: bool
    errors: List[Dict[str, Any]]
    complexity_score: float
    lines_of_code: int
    suggested_fixes: List[str]
```

### Concepts Agent

**Explanation Package**:
```python
class ConceptExplanation(BaseModel):
    """Packaged explanation"""
    concept: str
    level: str
    explanation: str
    examples: List[str]
    prerequisites: List[str]
    related_concepts: List[str]
```

### Exercise Agent

**Generated Problem**:
```python
class GeneratedExercise(BaseModel):
    """Adaptive exercise"""
    problem: str
    topic: str
    difficulty: str
    hints: List[str]
    test_cases: List[Dict[str, Any]]
    estimated_time_minutes: int
```

### Review Agent

**Quality Assessment**:
```python
class CodeReview(BaseModel):
    """Code review results"""
    overall_score: float
    criteria_scores: Dict[str, float]
    issues_found: List[Dict[str, str]]
    hints: List[str]
    best_practices: List[str]
```

## Database Schema (PostgreSQL - if needed)

### Tables Overview

**students_progress** (for persistent backup):
```sql
CREATE TABLE students_progress (
    student_id VARCHAR(50) PRIMARY KEY,
    latest_scores JSONB NOT NULL,
    overall_mastery DECIMAL(3,2) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_student_mastery ON students_progress(overall_mastery);
CREATE INDEX idx_student_updated ON students_progress(last_updated);
```

**events_log** (audit trail):
```sql
CREATE TABLE events_log (
    event_id VARCHAR(100) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    student_id VARCHAR(50) NOT NULL,
    component VARCHAR(50),
    scores JSONB,
    mastery DECIMAL(3,2),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_student ON events_log(student_id);
CREATE INDEX idx_events_type ON events_log(event_type);
CREATE INDEX idx_events_component ON events_log(component);
```

## Validation Rules

### Score Normalization
- All scores stored in 0.0-1.0 range
- Input scores validated before processing
- Out-of-range values clamped to valid range

### Mastery Calculation
- Formula: `(completion × 0.4) + (quiz × 0.3) + (quality × 0.2) + (consistency × 0.1)`
- Result must be between 0.0 and 1.0
- Components must be present for calculation

### Idempotency
- All events require unique `idempotency_key`
- State stores check for duplicate keys
- Kafka consumers implement deduplication

### Schema Evolution
- Version field required in all schemas
- New fields must be optional
- Breaking changes require major version bump

## Data Flow Patterns

### Event Processing Flow
```
1. Student action → Triage Service
2. Triage publishes event → Kafka `learning.events`
3. Progress Agent consumes → Calculates mastery → Updates State Store
4. Other agents consume → Use event data for their logic
5. All agents publish responses → Kong Gateway → Student
```

### State Management Flow
```
1. Progress Agent writes to Dapr State Store
2. State stored with key: student:{id}:mastery:latest
3. Other agents read from State Store (read-only)
4. Event replay can rebuild state from Kafka
```

### Error Recovery Flow
```
1. Event fails processing → DLQ
2. DLQ contains original payload + error details
3. Retry mechanism up to 5 times
4. After 5 failures → Manual review required
5. Alert sent to monitoring system
```

## Performance Considerations

### State Store Size
- Estimated per student: ~1KB (50 components)
- 1000 students: ~1MB
- Growth rate: ~100KB per day (1000 active students)

### Event Size
- Average StudentProgress: ~500 bytes
- Estimated throughput: 1000 events/minute
- Bandwidth: ~8MB/minute

### Query Patterns
- **Hot**: Current mastery scores (Progress Agent)
- **Warm**: Historical trends (Progress Agent)
- **Cold**: Event audit logs (PostgreSQL)

## Indexing Strategy

### Dapr State Store Keys
- Primary: `student:{student_id}:mastery:latest`
- Historical: `student:{student_id}:mastery:{date}`
- Lock: `student:{student_id}:lock`

### Database Indexes
- Covering index on `student_id + last_updated`
- Composite index on `event_type + component`
- Range index on `processed_at` for time-based queries

## Security & Privacy

### Data Protection
- Student IDs: Pseudonymized in events
- PII: Not stored in event system
- Scores: Only aggregated metrics, no raw assessment data

### Access Control
- Progress Agent: Read/Write to State Store
- Other Agents: Read-only from State Store
- All Agents: Read from Kafka, Write to response topics

### Retention Policy
- Kafka Events: 7 days
- State Store: Retain all historical versions
- DLQ: 30 days for manual review

## Testing Data

### Sample Test Data
```json
{
  "student_id": "test-stu-001",
  "component": "loops",
  "scores": {
    "completion": 0.85,
    "quiz": 0.90,
    "quality": 0.75,
    "consistency": 0.80
  }
}
```

### Expected Calculations
- Individual component: `completion = 0.85`
- Weighted calculation: `0.85*0.4 + 0.90*0.3 + 0.75*0.2 + 0.80*0.1 = 0.835`

## Migration Considerations

### From Milestone 2 (Triage Only)
- New events: No breaking changes to existing events
- Additional processing: New consumers for 5 agents
- State store: New structure, backward compatible

### Schema Versioning
- v1.0: Initial student progress event
- v1.1: Add optional metadata field
- v2.0: Breaking change to scores structure (if needed)

## Monitoring Metrics

### Data Volume
- Events per second per topic
- State store size growth
- Kafka storage usage
- DLQ depth and age

### Processing Quality
- Event processing success rate
- Duplicate event rate
- State consistency checks
- Schema validation failures

### Performance
- State store read/write latency
- Event processing latency per agent
- DLQ processing time
- Recovery time from failures

## Rollback Procedures

### State Store Corruption
```python
# Rebuild from Kafka events
def rebuild_state_store(student_id):
    events = kafka_consumer.get_events(student_id)
    state = {}
    for event in events:
        state = apply_event(state, event)
    return state
```

### Schema Migration Issues
- Maintain schema registry with versions
- Use Avro compatibility checks
- Support rolling upgrades

## Next Steps

1. **Implement schemas**: Convert models to Avro/Pydantic
2. **Create validation tests**: All rules must be tested
3. **Setup Kafka**: Configure topics with proper partitioning
4. **Initialize state store**: Define key patterns
5. **Generate contracts**: OpenAPI specs for all agents

---
**Generated**: 2026-01-13
**Version**: 1.0.0
**Status**: ✅ READY FOR IMPLEMENTATION