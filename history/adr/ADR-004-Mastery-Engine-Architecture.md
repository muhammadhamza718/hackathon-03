# ADR-004: Mastery Engine State Store and Event Processing Architecture

**Status**: ✅ Accepted
**Date**: 2026-01-14
**Deciders**: Architecture Team, Product Team
**Impact**: Critical - Foundation for learning analytics and personalized education

---

## Context

The Mastery Engine is a stateful microservice that tracks student learning progress across multiple dimensions using a sophisticated mastery formula (40% Completion + 30% Quiz + 20% Quality + 10% Consistency). It needs to:

1. **Process real-time learning events** from multiple agents (Exercise, Review, Concepts)
2. **Store persistent state** for 50,000+ concurrent students
3. **Calculate mastery scores** efficiently using MCP patterns
4. **Provide predictive analytics** for personalized learning paths
5. **Scale horizontally** with the multi-agent fleet
6. **Ensure data consistency** across distributed systems

**Technical Constraints**:
- High throughput: 1000+ calculations/second
- Low latency: <100ms P95 for queries
- Eventual consistency: Acceptable for learning data
- Multi-tenant: School/organizational isolation
- Compliance: GDPR 90-day retention

**Existing Infrastructure**:
- Kubernetes cluster with Dapr sidecars
- Kafka for event streaming
- Redis for caching
- PostgreSQL for persistent storage

## Decision

### Architecture Overview

**Mastery Engine Architecture**:
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

### State Store Strategy

**Primary Pattern**: Dapr State Store with Redis backend

**Key Design**:
```python
# Standardized key patterns for all state operations
student:{student_id}:profile:current_mastery          # Current state
student:{student_id}:mastery:{date}                   # Daily snapshot
student:{student_id}:mastery:{date}:{component}       # Component scores
processed:{event_id}                                 # Idempotency check
student:{student_id}:activity:recent                  # Consistency tracking
student:{student_id}:prediction:{days}                # Cached predictions
student:{student_id}:path:adaptive                    # Learning path
batch:{batch_id}:status                               # Batch operation state
```

**Rationale**:
1. **Fast Lookups**: O(1) access for student queries via deterministic keys
2. **Isolation**: Student-level granularity with natural partitioning
3. **TTL Support**: Automatic cleanup for GDPR compliance
4. **Atomicity**: Dapr provides transactional operations for consistency
5. **Multi-tenancy**: School isolation via prefix patterns
6. **Scalability**: Redis handles 50,000+ concurrent connections

**Risks & Mitigations**:
- **Risk**: Redis single point of failure
  - **Mitigation**: Redis cluster with sentinel failover
- **Risk**: Memory pressure from large datasets
  - **Mitigation**: Aggressive TTL, data compression, read replicas
- **Risk**: Eventual consistency complexity
  - **Mitigation**: Event sourcing with idempotent processing

### Event Processing Strategy

**Primary Pattern**: Kafka with idempotent consumers and DLQ

**Event Flow**:
```python
# 1. Event Ingestion
Learning Agent → Kafka → Mastery Consumer → Validation → Deduplication → Processing

# 2. Processing Pipeline
a) Idempotency Check: processed:{event_id}
b) Data Validation: Schema + business rules
c) State Update: Dapr State Store (transactional)
d) Calculation: MCP skill (algorithmic)
e) Recommendation: Adaptive engine
f) Output Event: mastery.updated + notifications

# 3. Error Handling
Processing Error → Retry (3x) → DLQ → Alert → Manual Review → Reprocess
```

**Event Schemas**:
- Avro format for schema evolution
- BACKWARD_TRANSITIVE compatibility
- Confluent Schema Registry integration

**Rationale**:
1. **Decoupling**: Services don't need to know about each other
2. **Scalability**: Kafka handles high throughput, multiple consumer groups
3. **Reliability**: At-least-once delivery with idempotent processing
4. **Observability**: Complete audit trail of all events
5. **Fault Tolerance**: DLQ prevents data loss, allows manual intervention
6. **Replayability**: Can recalculate mastery by replaying events

**Risks & Mitigations**:
- **Risk**: Kafka consumer lag during high load
  - **Mitigation**: Scale consumers horizontally, increase partitions
- **Risk**: Duplicate events breaking calculations
  - **Mitigation**: Idempotency with event_id checks
- **Risk**: DLQ overflow
  - **Mitigation**: 30-day retention with monitoring alerts

### MCP Skills Design

**Token Efficiency Strategy**: 95% reduction via algorithmic approach

**Skill Breakdown**:
```python
# Core Calculation (95% of calculations, 0 LLM calls)
def calculate_mastery(components: Dict[str, float]) -> Dict:
    """Algorithmic 40-30-20-10 formula"""
    weights = {"completion": 0.40, "quiz": 0.30, "quality": 0.20, "consistency": 0.10}
    mastery_score = sum(components[k] * weights[k] for k in weights)
    return {
        "mastery_score": mastery_score,
        "level": determine_level(mastery_score),
        "recommendations": generate_recommendations(components, mastery_score)
    }

# Pattern Recognition (5% of calculations, 100 tokens)
def generate_recommendations(components: Dict[str, float], score: float) -> List[Dict]:
    """Rule-based recommendations from weak areas"""
    weak_areas = [k for k, v in components.items() if v < 0.7]
    return [{"action": "practice", "area": area} for area in weak_areas]

# Predictive Analytics (Rare, 500 tokens)
def predict_trajectory(history: List[float]) -> Dict:
    """Linear regression for trajectory prediction"""
    if len(history) < 3:
        return None

    # Simple trend analysis - no LLM needed
    trend = np.polyfit(range(len(history)), history, 1)[0]
    return {
        "predicted_score": history[-1] + trend * 7,
        "confidence": min(0.9, len(history) * 0.1)
    }
```

**Token Efficiency Calculation**:
- **Baseline**: LLM generates and executes formula (~2000 tokens, $0.01)
- **MCP Approach**: Pre-built scripts (~50 tokens, $0.0001)
- **Savings**: 95% token reduction, 100x cost reduction

**Rationale**:
1. **Cost Efficiency**: Massive reduction in LLM usage
2. **Performance**: Sub-second response times
3. **Determinism**: Algorithmic outputs are consistent and debuggable
4. **Maintainability**: Scripts are testable and version-controlled
5. **Scalability**: No rate limits on algorithmic processing

**Risks & Mitigations**:
- **Risk**: Complex recommendations might need LLM
  - **Mitigation**: Use algorithmic base + optional LLM enhancement
- **Risk**: Formula changes require code deployment
  - **Mitigation**: Feature flags for formula variants
- **Risk**: Pattern recognition limitations
  - **Mitigation**: Gradual expansion of algorithmic capabilities

### Security Model

**Multi-Layer Security**:
```python
class SecurityStack:
    # Layer 1: Authentication
    JWT validation: HS256 with secure secret

    # Layer 2: Authorization
    RBAC: student/teacher/admin roles
    Data access: Student can only see own data
    Teachers: Access to their students only

    # Layer 3: Input Sanitization
    Validation: All inputs via Pydantic
    SQL injection: Dapr handles data access
    XSS: Input length and character limits

    # Layer 4: Audit Logging
    Access logs: All data access recorded
    Compliance: GDPR right-to-audit
    Forensics: Complete event trail
```

**Key Patterns**:
- **Zero Trust**: Verify every request
- **Least Privilege**: Minimal access rights
- **Defense in Depth**: Multiple security layers
- **Auditability**: Complete trace of all actions

**Rationale**:
1. **Compliance**: Meets GDPR and educational data requirements
2. **Safety**: Protects sensitive student data
3. **Accountability**: Complete audit trail for all access
4. **Defense**: Multiple layers prevent common attacks

### Performance Architecture

**Optimization Strategy**:
```python
# Multi-Level Caching
L1: Memory cache (30s TTL) - 100ns access
L2: Redis cache (5min TTL) - 1ms access
L3: State store (persistent) - 10ms access

# Connection Management
Connection pooling for Redis (max 50)
Kafka consumer groups (scale per partition)
HTTP keep-alive for API calls

# Async Processing
Non-blocking I/O for all operations
Background calculation for batch updates
Event streaming for real-time updates
```

**Performance Targets**:
- **Queries**: P95 < 100ms
- **Calculations**: P95 < 500ms
- **Throughput**: 1000+ ops/sec
- **Availability**: 99.9% uptime

**Rationale**:
1. **User Experience**: Fast responses prevent user frustration
2. **Scalability**: Efficient resource usage enables growth
3. **Cost**: Optimized operations reduce infrastructure costs
4. **Reliability**: Robust performance under load

## Consequences

### Positive

1. **Scalability**: Architecture supports 100x growth
2. **Cost Efficiency**: 95% token reduction saves thousands monthly
3. **Reliability**: Event-driven patterns prevent data loss
4. **Flexibility**: Easy to add new learning metrics
5. **Observability**: Complete audit trail and metrics
6. **Maintainability**: Clean separation of concerns
7. **Compliance**: Built-in GDPR and security features

### Negative

1. **Complexity**: Multiple systems to manage (Kafka, Redis, Dapr)
2. **Operational Overhead**: Requires monitoring of all components
3. **Learning Curve**: Team needs Dapr + Kafka expertise
4. **Infrastructure Costs**: Redis + Kafka + Kubernetes resources
5. **Development Time**: More complex than monolithic approach
6. **Debugging**: Distributed tracing required

### Neutral

1. **Language Choice**: Python 3.11+ provides good performance
2. **Testing**: Requires comprehensive integration testing
3. **Deployment**: Kubernetes-native but needs proper setup
4. **Documentation**: Extensive docs required for all components

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Dapr State Store (Redis)
- [ ] Configure Kafka cluster
- [ ] Create FastAPI application skeleton
- [ ] Implement security layer (JWT, RBAC)
- [ ] Set up CI/CD pipeline

### Phase 2: Core Services (Week 3-4)
- [ ] Implement state manager with key patterns
- [ ] Build mastery calculator MCP skills
- [ ] Create API endpoints (mastery, predictions, recommendations)
- [ ] Implement Kafka consumer with idempotency
- [ ] Add input validation and sanitization

### Phase 3: Integration (Week 5-6)
- [ ] Integrate with Exercise Agent
- [ ] Integrate with Review Agent
- [ ] Implement Dapr service invocation
- [ ] Set up event publishing
- [ ] Create notification triggers

### Phase 4: Testing & Optimization (Week 7-8)
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests (API + Dapr + Kafka)
- [ ] Load testing (1000+ ops/sec)
- [ ] Security testing (penetration tests)
- [ ] Performance optimization

### Phase 5: Production Deployment (Week 9-10)
- [ ] Kubernetes manifests
- [ ] Monitoring and alerting
- [ ] Runbook documentation
- [ ] Disaster recovery procedures
- [ ] Production deployment

## Alternative Approaches Considered

### Alternative 1: Traditional Database (PostgreSQL)

**Pros**:
- Simple, well-understood technology
- Strong consistency guarantees
- Rich query capabilities
- Mature tooling

**Cons**:
- Horizontal scaling complexity
- No built-in event streaming
- Higher latency for some operations
- Less suitable for event sourcing

**Rejection**: Doesn't meet real-time requirements or event-driven architecture

### Alternative 2: In-Memory Only (Redis)

**Pros**:
- Extremely fast (sub-millisecond)
- Simple data model
- Horizontal scaling via clustering

**Cons**:
- Data loss risk on restart
- Limited query capabilities
- No built-in event streaming
- Memory cost for large datasets

**Rejection**: Insufficient persistence and audit capabilities

### Alternative 3: Direct Microservices Communication

**Pros**:
- Simple service-to-service calls
- Lower infrastructure complexity
- Direct synchronous processing

**Cons**:
- Tight coupling between services
- Cascading failures
- No audit trail
- Difficult to scale independently

**Rejection**: Violates microservices best practices and introduces tight coupling

### Alternative 4: Monolithic Approach

**Pros**:
- Simple deployment
- Direct function calls
- No network overhead
- Easier debugging

**Cons**:
- Scalability limitations
- Technology lock-in
- Difficult to maintain
- Single point of failure

**Rejection**: Doesn't align with multi-agent fleet architecture

## Metrics & Success Criteria

### Technical Metrics
- **Token Efficiency**: >95% reduction vs baseline
- **API Response Time**: P95 < 100ms for queries
- **Calculation Throughput**: >1000 ops/sec
- **System Availability**: >99.9% uptime
- **Event Processing Lag**: <500ms
- **State Store Latency**: <10ms

### Business Metrics
- **Student Engagement**: 20% increase in daily active users
- **Learning Velocity**: 15% faster skill acquisition
- **Personalization**: 90% of students receive relevant recommendations
- **Teacher Efficiency**: 30% reduction in manual assessment time

### Compliance Metrics
- **GDPR Compliance**: 100% data deletion requests processed in 24 hours
- **Audit Completeness**: 100% of data access logged
- **Security Score**: Zero critical vulnerabilities

## Monitoring & Observability

### Metrics to Track
```promql
# Performance
rate(mastery_calculation_duration_seconds_bucket[5m])
rate(http_requests_total{status=~"5.."}[5m])

# Throughput
rate(kafka_consumption_messages_total[5m])
rate(state_store_operations_total[5m])

# Errors
increase(mastery_calculation_failures_total[5m])
increase(kafka_dlq_messages_total[5m])

# Resource Usage
redis_memory_used_bytes / redis_memory_max_bytes
kafka_consumer_lag
```

### Alerting Rules
- **Critical**: DLQ message rate > 0.1% of throughput
- **High**: Calculation failure rate > 1%
- **Medium**: State store latency P95 > 50ms
- **Low**: Consumer lag > 1000 messages

## References

- **Spec**: [specs/003-mastery-engine/spec.md]
- **Plan**: [specs/003-mastery-engine/plan.md]
- **Research**: [specs/003-mastery-engine/research.md]
- **Data Model**: [specs/003-mastery-engine/data-model.md]
- **API Contracts**: [specs/003-mastery-engine/contracts/api-contracts.md]
- **Event Schemas**: [specs/003-mastery-engine/contracts/event-schemas.md]

---

**Document Version**: 1.0
**Last Updated**: 2026-01-14
**Next Review**: When requirements change or major architectural decisions are needed