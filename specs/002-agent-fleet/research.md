# Research: Milestone 3 - Specialized Agent Fleet

**Date**: 2026-01-13
**Branch**: `002-agent-fleet`
**Focus**: Agent Architecture, MCP Scripts, Event Schemas

## Research Questions for Milestone 3

### 1. Agent Specialization Boundaries

**Question**: What specific logic belongs to each agent to avoid overlap and maintain clear separation?

**Findings**:
- **Progress Agent**: Stateful mastery tracking, score calculation, historical data
- **Debug Agent**: Syntax error detection, code analysis, debugging assistance
- **Concepts Agent**: Knowledge explanations, concept mapping, pedagogical content
- **Exercise Agent**: Problem generation, difficulty calibration, adaptive learning
- **Review Agent**: Code quality assessment, hint generation, feedback systems

**Decision**: Each agent has distinct data ownership and processing responsibilities with clear event subscriptions.

### 2. MCP Script Token Efficiency Targets

**Question**: How to achieve 90%+ token reduction for each agent's specialized logic?

**Strategy**:
- **Progress Agent**: Pre-calculated mastery formulas vs LLM calculation
- **Debug Agent**: Pattern-based error detection vs natural language analysis
- **Concepts Agent**: Templated explanations vs creative writing
- **Exercise Agent**: Algorithmic generation vs ad-hoc problem creation
- **Review Agent**: Rule-based scoring vs qualitative assessment

**Token Efficiency Baseline**: Compare manual implementation (1500-2000 tokens) vs script execution (50-150 tokens)

### 3. Event Schema Design for StudentProgress

**Question**: What Kafka event structure enables efficient processing across 5 agents?

**Requirements**:
- Student identification
- Event type classification
- Timestamp and idempotency
- Contextual data payload
- Event versioning for schema evolution

**Decision**: Use Avro schema with versioning for Kafka compatibility and evolution.

### 4. Dapr Integration Patterns

**Question**: How should each agent interact with Dapr sidecar and pub/sub?

**Pattern**:
- All agents subscribe to `learning.events` topic
- Progress Agent publishes state updates
- All agents use circuit breakers for fault tolerance
- Service invocation for direct agent-to-agent communication when needed

### 5. FastAPI Elite Standard Implementation

**Question**: What specific FastAPI patterns meet Elite Standard requirements?

**Requirements**:
- Pydantic v2 models for validation
- Dependency injection for services
- Async/await for all I/O
- Structured logging with trace correlation
- Health endpoints with detailed status
- Prometheus metrics endpoint

## Best Practices for Specialized Agents

### MCP Script Design Patterns

**Optimization Strategy**:
1. **Stateless Functions**: Pure functions for predictability
2. **Minimal Context**: Input/output only, no hidden dependencies
3. **Pre-computation**: Cache frequent operations
4. **Early Returns**: Exit early on invalid input
5. **Type Hints**: For self-documenting code

**Token Efficiency Measurement**:
```python
# Baseline: LLM-based approach
tokens_before = 1500  # LLM prompt + context
tokens_after = 50     # Script execution
efficiency = (1 - tokens_after/tokens_before) * 100  # 96.7%
```

### Event-Driven Architecture Patterns

**Topic Partitioning**:
- `learning.events`: Partitioned by `student_id` for ordered processing
- `dead-letter.queue`: Single partition for manual review

**Consumer Groups**:
- Each agent runs as separate consumer group
- Progress Agent: Unique group (state writer)
- Others: Shared group (read-only consumers)

### Kong Gateway Configuration

**Per-Agent Routes**:
```
/triage → Triage Service
/progress → Progress Agent
/debug → Debug Agent
/concepts → Concepts Agent
/exercise → Exercise Agent
/review → Review Agent
```

**Rate Limits**: 100 req/min per student across all agents

### Security Patterns

**JWT Claims Required**:
- `sub`: student_id
- `role`: student/admin
- `exp`: expiration
- `iss`: issuer

**Student ID Propagation**: Via `X-Consumer-Username` header from Kong

### Monitoring & Observability

**Per-Agent Metrics**:
- `agent_requests_total{agent="..."}`
- `agent_latency_seconds{agent="..."}`
- `agent_errors_total{agent="..."}`
- `script_execution_time{script="..."}`

**Trace Context**: W3C Trace Context propagated across all agents

### Schema Evolution Strategy

**Avro Schema Versioning**:
- Version 1.0: Initial event structure
- Backward compatibility: New fields optional
- Forward compatibility: Unknown fields ignored
- Breaking changes: Version bump required

## Technology Stack Decisions

### Python Requirements
- **FastAPI**: Latest stable with Pydantic v2
- **Dapr SDK**: 1.12.0+ for Kubernetes mode
- **Kafka**: Confluent Python client
- **OpenAI Agent SDK**: For natural language processing

### Container Images
- **Base**: python:3.11-slim (security scanned)
- **Dapr**: daprio/daprd:1.12.0
- **Kong**: kong:3.4

### Development Tools
- **Testing**: pytest, pytest-asyncio
- **Linting**: ruff, mypy
- **Security**: bandit, safety

## Risk Mitigation

### Agent Overlap Prevention
**Strategy**: Clear API contracts and event schema discipline
**Mitigation**: Code review for agent boundaries

### Event Processing Failures
**Strategy**: DLQ with manual review process
**Mitigation**: Alerting on DLQ depth > 100 messages

### Performance Degradation
**Strategy**: Load testing with 1000+ concurrent users
**Mitigation**: Horizontal scaling and circuit breakers

### Schema Evolution Breaking Changes
**Strategy**: Avro schema registry with versioning
**Mitigation**: Consumer validation and graceful degradation

## Exit Criteria

- [ ] All 5 agent architectures designed
- [ ] Event schemas defined and tested
- [ ] MCP scripts designed for 90%+ efficiency
- [ ] Security model complete
- [ ] Monitoring strategy defined
- [ ] Ready for implementation planning

---
**Status**: Research Complete
**Next**: Create plan.md, data-model.md, and contracts/