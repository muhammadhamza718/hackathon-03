# State Store Key Patterns: Mastery Engine
**Date**: 2026-01-14 | **Version**: v1.0

This document defines the comprehensive Dapr State Store key naming patterns and data structures for the Mastery Engine.

## 1. Key Naming Convention

### Standard Format
```
{entity_type}:{identifier}:{component}:{date}:{subcomponent}
```

### Entity Types
- `student` - Student-related data
- `processed` - Event processing checkpoints
- `batch` - Batch operation state
- `cache` - Temporary cache data
- `system` - System-level configuration

### Identifier Format
- **Student ID**: `student_{uuid}` or `{school_id}_{student_id}`
- **Date**: `YYYY-MM-DD` (ISO 8601)
- **Component**: `mastery`, `profile`, `history`, `activity`
- **Subcomponent**: Specific data category

## 2. Key Patterns by Category

### 2.1 Current Mastery Data
```
student:{student_id}:profile:current_mastery
└─ Structure: MasteryResult (JSON)
└─ TTL: None (persistent)
└─ Purpose: Fast access to current mastery state
```

**Example**:
```
student:student_12345:profile:current_mastery
→ {
  "student_id": "student_12345",
  "mastery_score": 0.85,
  "level": "proficient",
  "components": {...},
  "timestamp": "2026-01-14T10:30:00Z"
}
```

### 2.2 Daily Mastery Snapshots
```
student:{student_id}:mastery:{date}
└─ Structure: MasteryResult (JSON)
└─ TTL: 90 days (GDPR compliance)
└─ Purpose: Historical tracking and trend analysis
```

**Example**:
```
student:student_12345:mastery:2026-01-14
student:student_12345:mastery:2026-01-13
student:student_12345:mastery:2026-01-12
```

### 2.3 Component Scores
```
student:{student_id}:mastery:{date}:{component}
└─ Structure: float (0.0 to 1.0)
└─ TTL: 90 days
└─ Purpose: Component-level granularity
```

**Components**:
```
student:student_12345:mastery:2026-01-14:completion    → 0.85
student:student_12345:mastery:2026-01-14:quiz          → 0.90
student:student_12345:mastery:2026-01-14:quality       → 0.85
student:student_12345:mastery:2026-01-14:consistency   → 0.82
```

### 2.4 Event Processing Checkpoints
```
processed:{event_id}
└─ Structure: ProcessingRecord (JSON)
└─ TTL: 7 days
└─ Purpose: Idempotency guarantee
```

**Example**:
```
processed:550e8400-e29b-41d4-a716-446655440000
→ {
  "event_id": "550e8400-...",
  "processed_at": "2026-01-14T10:30:00Z",
  "result": "success",
  "mastery_score": 0.85
}
```

### 2.5 Activity Tracking
```
student:{student_id}:activity:recent
└─ Structure: ActivityData (JSON)
└─ TTL: 30 days
└─ Purpose: Consistency calculation
```

**Example**:
```
student:student_12345:activity:recent
→ {
  "last_activity": "2026-01-14T10:30:00Z",
  "current_streak": 7,
  "max_streak": 15,
  "activity_log": [
    "2026-01-14",
    "2026-01-13",
    "2026-01-12",
    ...
  ]
}
```

### 2.6 Historical Data
```
student:{student_id}:history:{type}
└─ Structure: HistoryData (JSON)
└─ TTL: None (aggregated historical)
└─ Purpose: Trend analysis and predictions
```

**History Types**:
```
student:student_12345:history:full          → All mastery snapshots
student:student_12345:history:components   → Component trends
student:student_12345:history:recommendations → All recommendations given
```

### 2.7 Predictive Cache
```
student:{student_id}:prediction:{timeframe}
└─ Structure: PredictionResult (JSON)
└─ TTL: 1 hour
└─ Purpose: Cache expensive predictions
```

**Example**:
```
student:student_12345:prediction:7days
→ {
  "predicted_score": 0.88,
  "confidence": 0.85,
  "trend": "improving",
  "intervention_needed": false,
  "calculated_at": "2026-01-14T10:30:00Z"
}
```

### 2.8 Adaptive Learning Paths
```
student:{student_id}:path:adaptive
└─ Structure: List[String] (JSON)
└─ TTL: 24 hours
└─ Purpose: Personalized learning path
```

**Example**:
```
student:student_12345:path:adaptive
→ [
  "practice_advanced_topics",
  "code_review_exercises",
  "mock_assessment"
]
```

### 2.9 Batch Operation State
```
batch:{batch_id}:status
└─ Structure: BatchStatus (JSON)
└─ TTL: 7 days
└─ Purpose: Track batch processing progress
```

**Example**:
```
batch:batch_20260114_001:status
→ {
  "batch_id": "batch_20260114_001",
  "total_requests": 100,
  "completed": 85,
  "failed": 2,
  "in_progress": 13,
  "started_at": "2026-01-14T10:00:00Z",
  "status": "processing"
}
```

## 3. Multi-Tenant Patterns

### School/Institution Isolation
```
school:{school_id}:student:{student_id}:profile:current_mastery
```

**Example**:
```
school:university_abc:student:12345:profile:current_mastery
school:school_xyz:student:67890:profile:current_mastery
```

### Cross-School Aggregation
```
school:{school_id}:aggregation:mastery:{date}
└─ Structure: AggregateStats (JSON)
└─ Purpose: School-level analytics
```

## 4. TTL Strategy

### Automatic Expiration
```python
TTL_CONFIG = {
    # Processing checkpoints (7 days for idempotency)
    "processed:*": 7 * 24 * 60 * 60,  # 604,800 seconds

    # Activity data (30 days)
    "student:*:activity:*": 30 * 24 * 60 * 60,  # 2,592,000 seconds

    # Predictive cache (1 hour)
    "student:*:prediction:*": 60 * 60,  # 3,600 seconds

    # Adaptive paths (24 hours)
    "student:*:path:*": 24 * 60 * 60,  # 86,400 seconds

    # Mastery snapshots (90 days for GDPR)
    "student:*:mastery:*": 90 * 24 * 60 * 60,  # 7,776,000 seconds

    # Batch state (7 days)
    "batch:*": 7 * 24 * 60 * 60,  # 604,800 seconds
}
```

### GDPR Compliance
```python
# Student data deletion
async def delete_student_data(student_id: str):
    """Delete all student data for GDPR compliance"""
    patterns_to_delete = [
        f"student:{student_id}:*",
        f"school:*:student:{student_id}:*"
    ]

    for pattern in patterns_to_delete:
        keys = await state_store.keys(pattern)
        await state_store.delete(keys)

    # Log deletion for audit
    await audit_log("gdpr_deletion", student_id)
```

## 5. Key Derivation Functions

### Python Implementation
```python
from datetime import datetime
from typing import Optional

class StateKeyBuilder:
    """Utility class for building state store keys"""

    @staticmethod
    def current_mastery(student_id: str) -> str:
        return f"student:{student_id}:profile:current_mastery"

    @staticmethod
    def daily_mastery(student_id: str, date: Optional[datetime] = None) -> str:
        if date is None:
            date = datetime.utcnow()
        date_str = date.strftime("%Y-%m-%d")
        return f"student:{student_id}:mastery:{date_str}"

    @staticmethod
    def component_score(student_id: str, component: str, date: Optional[datetime] = None) -> str:
        if date is None:
            date = datetime.utcnow()
        date_str = date.strftime("%Y-%m-%d")
        return f"student:{student_id}:mastery:{date_str}:{component}"

    @staticmethod
    def processed_event(event_id: str) -> str:
        return f"processed:{event_id}"

    @staticmethod
    def activity_recent(student_id: str) -> str:
        return f"student:{student_id}:activity:recent"

    @staticmethod
    def prediction(student_id: str, days: int) -> str:
        return f"student:{student_id}:prediction:{days}days"

    @staticmethod
    def adaptive_path(student_id: str) -> str:
        return f"student:{student_id}:path:adaptive"

    @staticmethod
    def batch_status(batch_id: str) -> str:
        return f"batch:{batch_id}:status"

    @staticmethod
    def school_mastery(school_id: str, student_id: str) -> str:
        return f"school:{school_id}:student:{student_id}:profile:current_mastery"
```

## 6. Data Access Patterns

### 6.1 Read Patterns
```python
# Fast access to current state
async def get_current_mastery(student_id: str) -> MasteryResult:
    key = StateKeyBuilder.current_mastery(student_id)
    return await state_store.get(key)

# Historical query
async def get_mastery_history(student_id: str, start: date, end: date) -> List[MasteryResult]:
    keys = []
    current = start
    while current <= end:
        keys.append(StateKeyBuilder.daily_mastery(student_id, current))
        current += timedelta(days=1)

    results = await state_store.get_many(keys)
    return [r for r in results if r is not None]

# Component analysis
async def get_component_trend(student_id: str, component: str, days: int = 30) -> List[float]:
    keys = [
        StateKeyBuilder.component_score(student_id, component, datetime.utcnow() - timedelta(days=i))
        for i in range(days)
    ]
    return await state_store.get_many(keys)
```

### 6.2 Write Patterns
```python
# Transactional save (all or nothing)
async def save_mastery_update(student_id: str, mastery: MasteryResult):
    """Save mastery update with transactional consistency"""
    date = datetime.utcnow()

    operations = [
        {
            "operation": "upsert",
            "key": StateKeyBuilder.current_mastery(student_id),
            "value": mastery.json()
        },
        {
            "operation": "upsert",
            "key": StateKeyBuilder.daily_mastery(student_id, date),
            "value": mastery.json()
        },
        {
            "operation": "upsert",
            "key": StateKeyBuilder.component_score(student_id, "completion", date),
            "value": str(mastery.components.completion)
        },
        {
            "operation": "upsert",
            "key": StateKeyBuilder.component_score(student_id, "quiz", date),
            "value": str(mastery.components.quiz)
        },
        {
            "operation": "upsert",
            "key": StateKeyBuilder.component_score(student_id, "quality", date),
            "value": str(mastery.components.quality)
        },
        {
            "operation": "upsert",
            "key": StateKeyBuilder.component_score(student_id, "consistency", date),
            "value": str(mastery.components.consistency)
        }
    ]

    await state_store.transaction(operations)
```

### 6.3 Batch Patterns
```python
# Efficient batch retrieval
async def get_batch_mastery(student_ids: List[str]) -> Dict[str, MasteryResult]:
    keys = [StateKeyBuilder.current_mastery(sid) for sid in student_ids]
    results = await state_store.get_many(keys)
    return dict(zip(student_ids, results))

# Batch update
async def save_batch_mastery(updates: Dict[str, MasteryResult]):
    operations = []
    for student_id, mastery in updates.items():
        operations.extend([
            {"operation": "upsert", "key": StateKeyBuilder.current_mastery(student_id), "value": mastery.json()},
            {"operation": "upsert", "key": StateKeyBuilder.daily_mastery(student_id), "value": mastery.json()}
        ])

    await state_store.transaction(operations)
```

## 7. Consistency Patterns

### 7.1 Event Sourcing
```python
# Append-only event log
async def append_mastery_event(student_id: str, event: MasteryUpdatedEvent):
    """Store immutable event for audit trail"""
    event_key = f"student:{student_id}:events:{event.timestamp}:{event.event_id}"
    await state_store.save(event_key, event.json(), ttl=90*24*60*60)

# Rebuild current state from events
async def rebuild_mastery_from_events(student_id: str) -> MasteryResult:
    event_keys = await state_store.keys(f"student:{student_id}:events:*")
    events = await state_store.get_many(sorted(event_keys))
    # Process events to reconstruct state
    return aggregate_events(events)
```

### 7.2 Optimistic Concurrency
```python
# Version-based concurrency control
async def update_with_version(student_id: str, new_mastery: MasteryResult, expected_version: int):
    key = StateKeyBuilder.current_mastery(student_id)

    # Get current with metadata
    current = await state_store.get_with_metadata(key)

    if current.metadata.version != expected_version:
        raise ConcurrentModificationError()

    new_mastery.version = expected_version + 1
    await state_store.save(key, new_mastery.json(), metadata={"version": new_mastery.version})
```

## 8. Caching Strategy

### Multi-Level Cache
```python
class MasterCache:
    """L1 (memory) + L2 (Redis) + L3 (persistent storage)"""

    def __init__(self):
        self.memory_cache = {}  # TTL: 30s
        self.redis = RedisClient()
        self.state_store = DaprStateStore()

    async def get_mastery(self, student_id: str) -> Optional[MasteryResult]:
        # L1: Memory
        key = f"mastery:{student_id}"
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if time.time() - item["timestamp"] < 30:
                return item["data"]

        # L2: Redis
        cached = await self.redis.get(key)
        if cached:
            data = MasteryResult.parse_raw(cached)
            self.memory_cache[key] = {"data": data, "timestamp": time.time()}
            return data

        # L3: State Store
        data = await self.state_store.get(StateKeyBuilder.current_mastery(student_id))
        if data:
            # Populate L2 and L1
            await self.redis.setex(key, 300, data.json())  # 5 min TTL
            self.memory_cache[key] = {"data": data, "timestamp": time.time()}

        return data
```

## 9. Monitoring and Debugging

### Key Inspection
```python
async def debug_student_state(student_id: str):
    """Debug all keys for a student"""
    patterns = [
        f"student:{student_id}:*",
        f"processed:*"
    ]

    all_keys = []
    for pattern in patterns:
        keys = await state_store.keys(pattern)
        all_keys.extend(keys)

    print(f"Found {len(all_keys)} keys for student {student_id}")
    for key in sorted(all_keys):
        value = await state_store.get(key)
        ttl = await state_store.ttl(key)
        print(f"{key}: {value} (TTL: {ttl}s)")
```

### Key Metrics
```python
async def get_key_metrics():
    """Monitor state store usage"""
    patterns = {
        "current_mastery": "student:*:profile:current_mastery",
        "daily_snapshots": "student:*:mastery:*",
        "processed_events": "processed:*",
        "activity_data": "student:*:activity:*",
        "predictions": "student:*:prediction:*",
        "paths": "student:*:path:*"
    }

    metrics = {}
    for name, pattern in patterns.items():
        count = len(await state_store.keys(pattern))
        metrics[name] = count

    return metrics
```

## 10. Performance Optimization

### Key Length Optimization
```python
# Shortened patterns for better performance
OPTIMIZED_PATTERNS = {
    "current": "st:{sid}:cur",           # student:12345:profile:current_mastery
    "daily": "st:{sid}:m:{date}",        # student:12345:mastery:2026-01-14
    "component": "st:{sid}:m:{date}:{c}", # student:12345:mastery:2026-01-14:completion
    "processed": "proc:{eid}",           # processed:550e8400-...
}
```

### Partitioning Strategy
```python
def get_partition_key(student_id: str) -> str:
    """Consistent hashing for key distribution"""
    import hashlib
    hash_obj = hashlib.md5(student_id.encode())
    partition = int(hash_obj.hexdigest(), 16) % 16
    return f"p{partition}:{student_id}"

# Usage
async def get_optimized_key(student_id: str, pattern: str) -> str:
    partition_key = get_partition_key(student_id)
    return pattern.format(sid=partition_key)
```

---
**Summary**: All state store patterns have been defined. Ready to proceed with quickstart guide.