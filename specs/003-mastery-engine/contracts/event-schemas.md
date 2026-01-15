# Event Schemas: Mastery Engine
**Date**: 2026-01-14 | **Version**: v1.0

This document defines the Kafka event schemas for the Mastery Engine, following Avro specification for compatibility and schema evolution.

## 1. Event Schema Registry

### Schema Versioning Strategy
- **Topic**: `mastery.events.v1`
- **Compatibility**: BACKWARD_TRANSITIVE
- **Storage**: Confluent Schema Registry

## 2. Core Event Schemas

### Mastery Calculation Request Event
```json
{
  "type": "record",
  "name": "MasteryCalculationRequest",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event requesting mastery calculation for a student",
  "fields": [
    {
      "name": "event_id",
      "type": "string",
      "doc": "Unique event identifier (UUID v4)"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["mastery.calculation.requested"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis",
      "doc": "Event creation timestamp"
    },
    {
      "name": "student_id",
      "type": "string",
      "doc": "Student identifier"
    },
    {
      "name": "components",
      "type": {
        "type": "map",
        "values": "double"
      },
      "doc": "Component scores (completion, quiz, quality, consistency)"
    },
    {
      "name": "source",
      "type": "string",
      "doc": "Origin service (exercise-agent, review-agent, etc.)"
    },
    {
      "name": "metadata",
      "type": [
        {
          "type": "map",
          "values": "string"
        },
        "null"
      ],
      "default": null,
      "doc": "Additional context data"
    }
  ]
}
```

### Mastery Updated Event
```json
{
  "type": "record",
  "name": "MasteryUpdated",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event signaling mastery calculation completion and update",
  "fields": [
    {
      "name": "event_id",
      "type": "string",
      "doc": "Unique event identifier (UUID v4)"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["mastery.updated", "mastery.threshold.reached"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "mastery_score",
      "type": "double",
      "doc": "Overall mastery score (0.0 to 1.0)"
    },
    {
      "name": "components",
      "type": {
        "type": "record",
        "name": "ComponentScores",
        "fields": [
          {"name": "completion", "type": "double"},
          {"name": "quiz", "type": "double"},
          {"name": "quality", "type": "double"},
          {"name": "consistency", "type": "double"}
        ]
      }
    },
    {
      "name": "level",
      "type": {
        "type": "enum",
        "name": "MasteryLevel",
        "symbols": ["beginner", "developing", "competent", "proficient", "expert"]
      }
    },
    {
      "name": "recommendations",
      "type": {
        "type": "array",
        "items": {
          "type": "record",
          "name": "Recommendation",
          "fields": [
            {"name": "action", "type": "string"},
            {"name": "area", "type": "string"},
            {"name": "priority", "type": "string"},
            {"name": "estimated_time", "type": ["int", "null"], "default": null}
          ]
        }
      }
    },
    {
      "name": "previous_score",
      "type": ["double", "null"],
      "default": null
    }
  ]
}
```

### Exercise Completion Event
```json
{
  "type": "record",
  "name": "ExerciseCompletion",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event for exercise completion submission",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["exercise.completion.submitted"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "exercise_id",
      "type": "string"
    },
    {
      "name": "total_exercises",
      "type": "int"
    },
    {
      "name": "completed_exercises",
      "type": "int"
    },
    {
      "name": "difficulty",
      "type": {
        "type": "enum",
        "name": "DifficultyLevel",
        "symbols": ["beginner", "intermediate", "advanced"]
      }
    },
    {
      "name": "time_taken",
      "type": "int",
      "doc": "Time in seconds"
    },
    {
      "name": "completion_rate",
      "type": "double",
      "doc": "Derived completion score"
    }
  ]
}
```

### Quiz Performance Event
```json
{
  "type": "record",
  "name": "QuizPerformance",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event for quiz performance tracking",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["quiz.performance.submitted"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "quiz_id",
      "type": "string"
    },
    {
      "name": "total_questions",
      "type": "int"
    },
    {
      "name": "correct_answers",
      "type": "int"
    },
    {
      "name": "time_spent",
      "type": "int",
      "doc": "Time in seconds"
    },
    {
      "name": "confidence_score",
      "type": "double",
      "doc": "Student self-reported confidence"
    },
    {
      "name": "quiz_score",
      "type": "double",
      "doc": "Derived quiz score (0.0 to 1.0)"
    }
  ]
}
```

### Quality Assessment Event
```json
{
  "type": "record",
  "name": "QualityAssessment",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event for code quality assessment",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["quality.assessment.completed"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "submission_id",
      "type": "string"
    },
    {
      "name": "code_quality_score",
      "type": "double",
      "doc": "Code review score (0.0 to 1.0)"
    },
    {
      "name": "correctness_score",
      "type": "double",
      "doc": "Correctness evaluation (0.0 to 1.0)"
    },
    {
      "name": "efficiency_score",
      "type": "double",
      "doc": "Algorithmic efficiency score (0.0 to 1.0)"
    },
    {
      "name": "peer_review_score",
      "type": ["double", "null"],
      "default": null
    },
    {
      "name": "average_quality",
      "type": "double",
      "doc": "Derived quality score"
    }
  ]
}
```

### Consistency Tracking Event
```json
{
  "type": "record",
  "name": "ConsistencyTracking",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event for tracking study consistency",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["consistency.activity.recorded"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "current_streak",
      "type": "int",
      "doc": "Consecutive days of activity"
    },
    {
      "name": "max_streak",
      "type": "int",
      "doc": "Historical maximum streak"
    },
    {
      "name": "days_since_last_activity",
      "type": "int"
    },
    {
      "name": "activity_dates",
      "type": {
        "type": "array",
        "items": "long"
      },
      "logicalType": "timestamp-millis-array"
    },
    {
      "name": "consistency_score",
      "type": "double",
      "doc": "Derived consistency score (0.0 to 1.0)"
    }
  ]
}
```

### Mastery Threshold Event
```json
{
  "type": "record",
  "name": "MasteryThreshold",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event when mastery crosses important thresholds",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "event_type",
      "type": {
        "type": "enum",
        "name": "EventType",
        "symbols": ["mastery.threshold.reached"]
      }
    },
    {
      "name": "timestamp",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "student_id",
      "type": "string"
    },
    {
      "name": "threshold_type",
      "type": {
        "type": "enum",
        "name": "ThresholdType",
        "symbols": ["beginner_to_developing", "developing_to_competent", "competent_to_proficient", "proficient_to_expert"]
      }
    },
    {
      "name": "previous_score",
      "type": "double"
    },
    {
      "name": "new_score",
      "type": "double"
    },
    {
      "name": "previous_level",
      "type": "MasteryLevel"
    },
    {
      "name": "new_level",
      "type": "MasteryLevel"
    },
    {
      "name": "celebration_message",
      "type": ["string", "null"],
      "default": null
    }
  ]
}
```

## 3. Dead Letter Queue Schema

### Failed Event
```json
{
  "type": "record",
  "name": "FailedEvent",
  "namespace": "com.learnflow.mastery.v1",
  "doc": "Event that failed processing and was moved to DLQ",
  "fields": [
    {
      "name": "event_id",
      "type": "string"
    },
    {
      "name": "original_event_type",
      "type": "string"
    },
    {
      "name": "original_payload",
      "type": "string",
      "doc": "JSON string of original event"
    },
    {
      "name": "error_message",
      "type": "string"
    },
    {
      "name": "error_type",
      "type": {
        "type": "enum",
        "name": "ErrorType",
        "symbols": ["validation_error", "processing_error", "timeout_error", "dependency_error"]
      }
    },
    {
      "name": "failed_at",
      "type": "long",
      "logicalType": "timestamp-millis"
    },
    {
      "name": "retry_count",
      "type": "int",
      "default": 0
    },
    {
      "name": "stack_trace",
      "type": ["string", "null"],
      "default": null
    }
  ]
}
```

## 4. Event Processing Flow

### 1. Ingestion Flow
```
Exercise Agent → Kafka → Mastery Consumer → Validation → Processing → State Store
     ↓
Quiz Agent   → Kafka → Mastery Consumer → Validation → Processing → State Store
     ↓
Review Agent → Kafka → Mastery Consumer → Validation → Processing → State Store
```

### 2. Calculation Flow
```
Raw Events → Kafka Consumer → MCP Skill Calculator → Dapr State Store → Mastery Updated Event
    ↓
Recommendation Engine → Adaptive Path → Kafka → Notification Service
```

### 3. Error Handling Flow
```
Processing Error → Retry (3x) → DLQ → Alert → Manual Review → Reprocess
```

## 5. Kafka Topic Configuration

### Topic: `mastery.events`
```yaml
partitions: 6
replication_factor: 3
config:
  retention.ms: 604800000  # 7 days
  cleanup.policy: compact
  min.insync.replicas: 2
  compression.type: snappy
```

### Topic: `mastery.requests`
```yaml
partitions: 6
replication_factor: 3
config:
  retention.ms: 86400000  # 1 day
  cleanup.policy: delete
  min.insync.replicas: 2
```

### Topic: `mastery.results`
```yaml
partitions: 6
replication_factor: 3
config:
  retention.ms: 172800000  # 2 days
  cleanup.policy: delete
  min.insync.replicas: 2
```

### Topic: `mastery.dlq`
```yaml
partitions: 3
replication_factor: 3
config:
  retention.ms: 2592000000  # 30 days
  cleanup.policy: delete
  min.insync.replicas: 2
```

## 6. Event Serialization

### Recommended Serializers
- **Key**: StringSerializer
- **Value**: KafkaAvroSerializer (with Schema Registry)

### Configuration
```properties
# Producer
key.serializer=org.apache.kafka.common.serialization.StringSerializer
value.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
schema.registry.url=http://schema-registry:8081
auto.register.schemas=false
```

## 7. Consumer Group Management

### Mastery Calculation Consumer
```python
group_id = "mastery-calculation-v1"
auto_offset_reset = "latest"
enable_auto_commit = False  # Manual commit after successful processing
max_poll_records = 50
```

### Recommendation Consumer
```python
group_id = "mastery-recommendations-v1"
auto_offset_reset = "earliest"
enable_auto_commit = True
```

## 8. Event Flow Examples

### Example 1: Completion Event Processing
```json
// Input Event (from Exercise Agent)
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "exercise.completion.submitted",
  "timestamp": 1642152600000,
  "student_id": "student_12345",
  "exercise_id": "ex_001",
  "total_exercises": 10,
  "completed_exercises": 8,
  "difficulty": "intermediate",
  "time_taken": 1800,
  "completion_rate": 0.8
}

// Internal Processing
1. Consumer receives event
2. Validates schema
3. Checks idempotency (processed:550e8400-...)
4. Updates state store:
   - student:12345:mastery:2026-01-14:completion = 0.8
   - student:12345:activity:recent = update timestamp
5. Triggers mastery calculation
6. Publishes MasteryUpdated event
```

### Example 2: Mastery Calculation Result
```json
// Output Event
{
  "event_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "event_type": "mastery.updated",
  "timestamp": 1642152650000,
  "student_id": "student_12345",
  "mastery_score": 0.85,
  "components": {
    "completion": 0.80,
    "quiz": 0.90,
    "quality": 0.85,
    "consistency": 0.82
  },
  "level": "proficient",
  "recommendations": [
    {
      "action": "practice",
      "area": "advanced_topics",
      "priority": "high",
      "estimated_time": 60
    }
  ],
  "previous_score": 0.78
}
```

## 9. Schema Evolution

### Backward Compatible Changes
```python
# Adding optional field
# NEW FIELD MUST be nullable or have default

# ✅ GOOD
{
  "name": "new_field",
  "type": ["string", "null"],
  "default": null
}

# ❌ BAD - Breaking change
{
  "name": "new_field",
  "type": "string"  # No default, existing records will fail
}
```

### Version History
- **v1.0**: Initial schema
- **v1.1**: Added `recommendations.estimated_time` (optional)
- **v1.2**: Added `metadata` to all events (optional)

## 10. Monitoring Events

### Metrics Events
```json
{
  "event_type": "mastery.metrics.collected",
  "timestamp": 1642152650000,
  "metrics": {
    "mastery.calculations.per.second": 450,
    "kafka.processing.lag.ms": 120,
    "state.store.latency.ms": 8,
    "dlq.events.count": 0
  }
}
```

### Alert Events
```json
{
  "event_type": "mastery.alert.triggered",
  "timestamp": 1642152650000,
  "severity": "high",
  "alert_type": "processing_failure_rate",
  "message": "DLQ rate exceeds threshold",
  "current_value": 0.05,
  "threshold": 0.01
}
```

## 11. Event Bus Patterns

### Command Pattern
```python
# Request mastery calculation
{
  "event_type": "mastery.calculation.requested",
  "command": "calculate_now",
  "student_id": "student_12345",
  "urgency": "high"
}
```

### Domain Event Pattern
```python
# State has changed
{
  "event_type": "mastery.updated",
  "student_id": "student_12345",
  "state_change": {
    "previous": 0.78,
    "new": 0.85,
    "reason": "component_completion"
  }
}
```

### Integration Event Pattern
```python
# External system notification
{
  "event_type": "mastery.threshold.reached",
  "student_id": "student_12345",
  "trigger": {
    "service": "mastery-engine",
    "action": "level_up",
    "requires_action": ["notification_service", "gamification_service"]
  }
}
```

---
**Next**: State store key patterns in `state-store-keys.md`