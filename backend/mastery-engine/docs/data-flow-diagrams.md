# Data Flow Diagrams - Mastery Engine
**Elite Implementation Standard v2.0.0**

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Learning Agent │    │  Mastery Engine  │    │  Notification   │
│    (Exercise)   │────│   Core Service   │────│     Service     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │    ┌──────────────────┴──────────────────┐      │
         │    │                                     │      │
         │    │   Dapr State Store (Redis)          │      │
         │    │   ┌─────────────────────────────┐   │      │
         │    │   │ Current Mastery (Key/Value) │   │      │
         │    │   │ Daily Snapshots             │   │      │
         │    │   │ Component Scores            │   │      │
         │    │   │ Event History               │   │      │
         │    │   └─────────────────────────────┘   │      │
         │    │                                     │      │
         │    │   Kafka Event Bus                   │      │
         │    │   ┌─────────────────────────────┐   │      │
         │    │   │ mastery.requests (Input)    │   │      │
         │    │   │ mastery.results (Output)    │   │      │
         │    │   │ mastery.dlq (Error)         │   │      │
         │    │   └─────────────────────────────┘   │      │
         │    │                                     │      │
         │    │   MCP Skills Layer                  │      │
         │    │   ┌─────────────────────────────┐   │      │
         │    │   │ Algorithmic Calculations    │   │      │
         │    │   │ Pattern Matching            │   │      │
         │    │   │ Predictive Analytics        │   │      │
         │    │   └─────────────────────────────┘   │      │
         │    └─────────────────────────────────────┘      │
         │                        │                        │
         │                        ▼                        │
         └─────────────► mastery.calculation.requested     │
                                                │          │
                                                ▼          │
                                 mastery.threshold.reached  │
                                                │          │
                                                ▼          │
                                 learning.path.recommended  │
                                                           │
                                                           ▼
                                            Push notifications to students
```

## Event Processing Flow

### 1. Event Ingestion & Processing
```
Learning Agent → Kafka Producer → mastery.requests topic
                                           ↓
                                   Kafka Consumer
                                           ↓
                                ┌──────────────────┐
                                │ Event Validation │ (Schema + Business Rules)
                                └──────────────────┘
                                           ↓
                                ┌──────────────────┐
                                │ Idempotency Check│ (processed:{event_id})
                                └──────────────────┘
                                           ↓
                                ┌──────────────────┐
                                │ State Update     │ (Dapr State Store)
                                └──────────────────┘
                                           ↓
                                ┌──────────────────┐
                                │ Mastery Calc     │ (MCP Skill)
                                └──────────────────┘
                                           ↓
                                ┌──────────────────┐
                                │ Recommendations  │ (Adaptive Engine)
                                └──────────────────┘
                                           ↓
                                mastery.results topic
                                           ↓
                                Notification Service
```

### 2. Query Flow
```
API Request → /mastery/query
                 ↓
           JWT Validation
                 ↓
           Rate Limit Check
                 ↓
           State Key Build
                 ↓
           Dapr State Store (Redis)
                 ↓
           Response Format
                 ↓
           Return to Client
```

### 3. Error Handling
```
Processing Error
     ↓
Retry Logic (3x)
     ↓
If Still Failing
     ↓
Move to DLQ (mastery.dlq)
     ↓
Alert Monitoring
     ↓
Manual Review & Repair
```

## State Store Data Model

### Key Patterns
```
student:12345:profile:current_mastery          → MasteryResult (JSON)
student:12345:mastery:2026-01-14               → MasteryResult (JSON)
student:12345:mastery:2026-01-14:completion    → 0.85 (float)
student:12345:mastery:2026-01-14:quiz          → 0.90 (float)
student:12345:mastery:2026-01-14:quality       → 0.85 (float)
student:12345:mastery:2026-01-14:consistency   → 0.82 (float)

processed:550e8400-e29b-41d4-a716-446655440000 → ProcessingRecord (JSON)

student:12345:activity:recent                   → ActivityData (JSON)
student:12345:prediction:7days                  → PredictionResult (JSON)
student:12345:path:adaptive                     → List[str] (JSON)
```

### TTL Configuration
```
processed:*               → 7 days   (Idempotency)
student:*:prediction:*    → 1 hour   (Cache)
student:*:activity:*      → 30 days  (Recent activity)
student:*:mastery:*       → 90 days  (GDPR compliance)
```

## API Endpoint Flow

### POST /mastery/query
```
Request → Validation → Authentication → Rate Limit → State Query → Response
            ↓              ↓              ↓           ↓            ↓
          Pydantic      JWT Check     Token       Dapr       JSON
          Model         RBAC          Count       Store      Serialization
```

### POST /mastery/ingest (Async)
```
Request → Validation → Kafka Publish → Consumer → Processing → State Update
            ↓              ↓             ↓          ↓           ↓
          Pydantic      Schema        Topic      Idempotency  Transaction
          Model         Registry      mastery.requests
```

### POST /predictions/next-week
```
Request → Validation → Cache Check → Prediction → Cache Store → Response
            ↓              ↓            ↓           ↓            ↓
          Pydantic      Redis       Algorithm    Redis        JSON
          Model         TTL=1hr     (Linear)     Setex
```

## Security Flow

### Authentication & Authorization
```
API Request
   ↓
Extract JWT
   ↓
Validate Signature (HS256)
   ↓
Extract Claims (sub, role, exp)
   ↓
Role-Based Access Control
   ↓
Student ID Matching (if student role)
   ↓
Audit Log Entry
   ↓
Continue Processing
```

### Input Sanitization
```
Raw Input
   ↓
Pydantic Validation (types, constraints)
   ↓
Length Limits (prevent DoS)
   ↓
Character Whitelist (prevent injection)
   ↓
Business Logic Validation
   ↓
Safe Processing
```

## Data Consistency Flow

### Event Sourcing Pattern
```
Learning Event (e.g., exercise completed)
   ↓
Append to Event Log (immutable)
   ↓
Update Current State (idempotent)
   ↓
Calculate New Mastery
   ↓
Publish Update Event
   ↓
Trigger Notifications
```

### Transactional State Update
```
Begin Transaction
   ↓
Update: student:{id}:profile:current_mastery
   ↓
Update: student:{id}:mastery:{date}
   ↓
Update: student:{id}:mastery:{date}:{component} (×4)
   ↓
Commit or Rollback
   ↓
Event Notification on Success
```

## Cache Strategy

### Multi-Level Cache
```
Application Layer (Python dict)
   ↓ TTL: 30 seconds
   ↓ Size: 1000 items

Redis Cache
   ↓ TTL: 5 minutes
   ↓ Clustered

State Store (Persistent)
   ↓ No TTL (except historical)
   ↓ Dapr + Redis
```

### Cache Invalidation
```
New Event Received
   ↓
Invalidate: student:{id}:prediction:*
   ↓
Invalidate: student:{id}:path:adaptive
   ↓
Wait for next query to repopulate
   ↓
Update: student:{id}:profile:current_mastery (atomic)
```

## Monitoring & Metrics Flow

### Request Metrics
```
API Request Received
   ↓
Start Timer
   ↓
Process Request
   ↓
Record Metrics:
- Duration
- Status Code
- Endpoint
- Student ID (anonymized)
   ↓
Return Response
   ↓
Export to Prometheus
```

### Event Processing Metrics
```
Event Consumed from Kafka
   ↓
Increment: events_consumed_total
   ↓
Start Processing Timer
   ↓
Process Event
   ↓
Record:
- Processing duration
- Success/Failure
- State store operations
- DLQ moves
   ↓
Export to Prometheus
```

## Error Flow Diagrams

### Validation Error
```
Invalid Request
   ↓
Pydantic ValidationError
   ↓
Return 400 with details
   ↓
Log to structured logger
   ↓
Return to client
```

### Dependency Failure
```
Redis/Kafka Down
   ↓
Health Check Fails
   ↓
Service marked unhealthy
   ↓
Return 503 (service unavailable)
   ↓
Alert monitoring system
   ↓
Automatic retry on next request
```

### Processing Error (Retryable)
```
Transient Error
   ↓
Retry 3x with exponential backoff
   ↓
Success → Continue
Failure → DLQ
   ↓
Alert for manual review
```

## Integration Points

### Dapr Service Invocation
```
Triage Service
   ↓
Dapr Invoke: mastery-engine/process
   ↓
Mastery Engine Process Endpoint
   ↓
Route by Intent:
- mastery_calculation
- get_prediction
- generate_path
   ↓
Return Standard Response
```

### Kafka Event Publishing
```
Mastery Updated Event
   ↓
Kafka Producer
   ↓
Publish to: mastery.results
   ↓
Multiple Consumer Groups:
- Notification Service
- Analytics Service
- Audit Service
```

## Performance Optimization Flow

### Query Optimization
```
Request Received
   ↓
Check L1 Cache (memory)
   ↓ HIT → Return (μs)
   ↓ MISS
Check L2 Cache (Redis)
   ↓ HIT → Return (ms)
   ↓ MISS
Query State Store
   ↓
Return + Update Cache Layers
```

### Batch Processing
```
Batch Request (1000 students)
   ↓
Validate All
   ↓
Split into Chunks (100 each)
   ↓
Process in Parallel (asyncio.gather)
   ↓
Collect Results
   ↓
Return Summary + Individual Results
```

---
**Document Version**: 1.0.0
**Last Updated**: 2026-01-14
**Status**: Design Complete
**Next**: Implementation Phase