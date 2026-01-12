# Data Model: LearnFlow Multi-Agent AI Tutoring Platform

**Feature**: `001-learnflow-architecture`
**Date**: 2025-01-11
**Phase**: Phase 1 Design
**Status**: Complete

## Entity Overview

This document defines the core data entities for LearnFlow, their relationships, validation rules, and state transitions. All entities must comply with the JSON Schema governance requirements from the specification.

## Core Entities

### 1. StudentProgress Event Schema

**Purpose**: Central event schema for all inter-service communication via Kafka

**JSON Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["student_id", "exercise_id", "timestamp", "agent_source"],
  "properties": {
    "student_id": {
      "type": "string",
      "pattern": "^student_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
      "description": "UUID format student identifier"
    },
    "exercise_id": {
      "type": "string",
      "pattern": "^ex_[a-zA-Z0-9_-]+$",
      "description": "Unique exercise identifier"
    },
    "completion_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Normalized completion percentage (0.0-1.0)"
    },
    "quiz_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Normalized quiz performance (0.0-1.0)"
    },
    "quality_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Code quality assessment (0.0-1.0)"
    },
    "consistency_score": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "description": "Learning consistency metric (0.0-1.0)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of event"
    },
    "agent_source": {
      "type": "string",
      "enum": ["concepts", "review", "debug", "exercise", "progress"],
      "description": "Origin agent of the event"
    },
    "idempotency_key": {
      "type": "string",
      "pattern": "^[a-f0-9]{32}$",
      "description": "32-character hex idempotency key"
    },
    "metadata": {
      "type": "object",
      "description": "Agent-specific additional data",
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

**Validation Rules**:
- All scores must be normalized to 0.0-1.0 range before publishing
- `idempotency_key` must be generated for all exercise submissions
- `timestamp` must be UTC and within 5 seconds of event creation
- Schema validation failure → dead-letter queue topic

**Kafka Topic**: `learning.events`
**Partition Key**: `student_id`

---

### 2. MasteryScore Entity

**Purpose**: Persistent storage of calculated mastery scores in Dapr State Store

**Storage Key Pattern**: `student:{student_id}:mastery:{date}:{component}`
**TTL**: 90 days for individual records, 1 year for aggregated

**Entity Structure**:
```json
{
  "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
  "date": "2025-01-11",
  "components": {
    "completion": {
      "value": 0.75,
      "count": 3,
      "last_updated": "2025-01-11T14:30:00Z"
    },
    "quiz": {
      "value": 0.80,
      "count": 2,
      "last_updated": "2025-01-11T14:25:00Z"
    },
    "quality": {
      "value": 0.90,
      "count": 5,
      "last_updated": "2025-01-11T14:20:00Z"
    },
    "consistency": {
      "value": 0.85,
      "count": 10,
      "last_updated": "2025-01-11T14:15:00Z"
    }
  },
  "final_score": 0.795,
  "calculated_at": "2025-01-11T14:30:00Z",
  "version": 1
}
```

**Mastery Calculation Formula**:
```python
final_score = (
    0.40 * components.completion.value +
    0.30 * components.quiz.value +
    0.20 * components.quality.value +
    0.10 * components.consistency.value
)
```

**State Transitions**:
1. **New Event**: Create component record with count=1
2. **Updated Event**: Increment count, recalculate average
3. **Daily Aggregation**: Roll up to single record per day
4. **Trend Analysis**: Query historical records for learning path optimization

---

### 3. IdempotencyKey Entity

**Purpose**: Prevent duplicate processing of exercise submissions

**Storage Key Pattern**: `student:{student_id}:idempotency:{request_key}`
**TTL**: 24 hours (matching JWT expiration)

**Entity Structure**:
```json
{
  "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
  "request_key": "abc123def456abc123def456abc123de",
  "processed_at": "2025-01-11T14:30:00Z",
  "result": {
    "exercise_id": "ex_python_fibonacci",
    "outcome": "correct",
    "feedback": "Excellent implementation!"
  }
}
```

**Usage Flow**:
1. Client generates idempotency key (32-char hex)
2. Progress Agent checks Redis for existing key
3. If exists: Return cached result immediately
4. If new: Process and store result with TTL

**Duplicate Detection**:
- Window: 1 minute (configurable)
- Response: 200 OK with cached result body
- No duplicate events published to Kafka

---

### 4. Sandbox Execution Request

**Purpose**: Input schema for Python code execution in sandbox

**API Contract**:
```json
{
  "code": "string",
  "student_id": "string",
  "exercise_id": "string",
  "timeout_ms": 5000,
  "memory_limit_mb": 50,
  "requirements": ["numpy", "pandas"]
}
```

**Sandbox Response**:
```json
{
  "status": "success|timeout|error|memory_exceeded",
  "output": "stdout content",
  "errors": "stderr content",
  "execution_time_ms": 2340,
  "peak_memory_mb": 32.5
}
```

**Security Constraints**:
- No network access
- Filesystem read-only except `/tmp`
- Max execution time: 5000ms
- Max memory: 50MB
- No system call access

---

## API Contracts

### Triage Service API

**Base URL**: `/api/v1/triage`

#### POST /intent/detect
```yaml
openapi: 3.0.0
info:
  title: Triage Service Intent Detection
  version: 1.0.0
paths:
  /api/v1/triage/intent/detect:
    post:
      summary: Detect intent from student query
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id, query]
              properties:
                student_id:
                  type: string
                  format: uuid
                query:
                  type: string
                  maxLength: 1000
                context:
                  type: object
                  description: Previous conversation context
      responses:
        '200':
          description: Intent successfully detected
          content:
            application/json:
              schema:
                type: object
                properties:
                  intent:
                    type: string
                    enum: [syntax_error, concept_explanation, code_review, exercise, progress_query]
                  confidence:
                    type: number
                    minimum: 0.0
                    maximum: 1.0
                  target_agent:
                    type: string
                    enum: [debug, concepts, review, exercise, progress]
                  routing_metadata:
                    type: object
        '400':
          description: Invalid input or unable to detect intent
```

#### POST /route
```yaml
paths:
  /api/v1/triage/route:
    post:
      summary: Route query to appropriate agent
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id, query, idempotency_key]
              properties:
                student_id:
                  type: string
                  format: uuid
                query:
                  type: string
                idempotency_key:
                  type: string
                  pattern: "^[a-f0-9]{32}$"
                context:
                  type: object
      responses:
        '200':
          description: Query routed and processed
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
                  agent:
                    type: string
                  processing_time_ms:
                    type: integer
                  events_published:
                    type: array
                    items:
                      type: string
```

### Agent APIs (Common Pattern)

**Base URL**: `/api/v1/agents/{agent_name}`

#### POST /process
```yaml
paths:
  /api/v1/agents/{agent_name}/process:
    post:
      summary: Process request in specific agent
      parameters:
        - name: agent_name
          in: path
          required: true
          schema:
            type: string
            enum: [concepts, review, debug, exercise, progress]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id, input_data]
              properties:
                student_id:
                  type: string
                  format: uuid
                input_data:
                  type: object
                  description: Agent-specific input
                idempotency_key:
                  type: string
      responses:
        '200':
          description: Agent processing complete
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: object
                  events:
                    type: array
                    items:
                      $ref: '#/components/schemas/StudentProgress'
```

### Sandbox API

#### POST /execute/python
```yaml
paths:
  /api/v1/sandbox/execute/python:
    post:
      summary: Execute Python code in sandbox
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [code, student_id]
              properties:
                code:
                  type: string
                  maxLength: 10000
                student_id:
                  type: string
                  format: uuid
                exercise_id:
                  type: string
                timeout_ms:
                  type: integer
                  minimum: 1000
                  maximum: 10000
                  default: 5000
                memory_limit_mb:
                  type: integer
                  minimum: 10
                  maximum: 100
                  default: 50
      responses:
        '200':
          description: Execution completed
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [success, timeout, error, memory_exceeded]
                  output:
                    type: string
                  errors:
                    type: string
                  execution_time_ms:
                    type: integer
                  peak_memory_mb:
                    type: number
        '422':
          description: Code execution failed
```

### Progress Agent Special APIs

#### GET /mastery/{student_id}
```yaml
paths:
  /api/v1/agents/progress/mastery/{student_id}:
    get:
      summary: Get current mastery scores for student
      parameters:
        - name: student_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Mastery scores retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MasteryScore'
```

#### POST /mastery/calculate
```yaml
paths:
  /api/v1/agents/progress/mastery/calculate:
    post:
      summary: Calculate mastery from progress events
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id, events]
              properties:
                student_id:
                  type: string
                  format: uuid
                events:
                  type: array
                  items:
                    $ref: '#/components/schemas/StudentProgress'
      responses:
        '200':
          description: Calculation complete
          content:
            application/json:
              schema:
                type: object
                properties:
                  calculated_score:
                    type: number
                  breakdown:
                    type: object
```

---

## Key Relationships

### Event Flow
```
Student Submission → Triage Service → Target Agent → StudentProgress Event → Kafka → Progress Agent → MasteryScore (Dapr)
```

### State Store Relationships
```
Student ID → MasteryScore (current)
Student ID → IdempotencyKey (recent submissions)
Student ID → Exercise Attempts (history)
```

### Kafka Event Dependencies
- All agents publish to `learning.events` topic
- Progress Agent consumes all events
- Other agents consume specific agent sources for coordination

---

## Validation Rules Summary

### Cross-Agent Validation
1. **Schema Compliance**: All events must validate against StudentProgress schema
2. **Score Normalization**: All scores 0.0-1.0, never negative or >1.0
3. **Idempotency**: All exercise submissions require idempotency key
4. **Timestamp Consistency**: All events use UTC ISO8601 format
5. **Student ID Format**: UUID format enforced consistently

### Performance Constraints
- **Event Size**: < 1KB per StudentProgress event
- **State Key Length**: < 255 characters
- **Mastery Calculation**: < 5 seconds per student
- **Event Processing**: < 1 second per event in Progress Agent

---

## Database Index Strategy (PostgreSQL for History)

```sql
-- Student progress history table (for long-term analysis)
CREATE TABLE student_history (
    student_id UUID,
    date DATE,
    event_count INTEGER,
    avg_completion DECIMAL(4,3),
    avg_quiz DECIMAL(4,3),
    avg_quality DECIMAL(4,3),
    avg_consistency DECIMAL(4,3),
    PRIMARY KEY (student_id, date)
);

-- Index for trend analysis
CREATE INDEX idx_student_date ON student_history(student_id, date DESC);
CREATE INDEX idx_completion_trend ON student_history(avg_completion);
```

**Note**: PostgreSQL used only for historical aggregation and analytics. Real-time operations use Dapr state store.