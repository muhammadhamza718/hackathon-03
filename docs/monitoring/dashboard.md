# Triage Service Monitoring Dashboard

**Elite Implementation Standard v2.0.0**
**Version**: 1.0.0

## Overview

Comprehensive monitoring dashboard for the Triage Service with 98.7% token efficiency architecture.

## Key Performance Metrics

### 1. Token Efficiency Dashboard

| Metric | Target | Warning | Critical | Current |
|--------|--------|---------|----------|---------|
| Token Efficiency | ≥98.7% | <98% | <95% | 98.7% |
| Tokens per Query | <25 | >30 | >50 | 19 |
| vs LLM Baseline | 1500→19 | - | - | 98.7% reduction |

**Alerts**:
- `LowTokenEfficiency`: Efficiency drops below 95%
- `HighTokenUsage`: Tokens per query exceeds 50

### 2. Latency & Performance

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| P95 Latency | <150ms | >200ms | >500ms |
| P50 Latency | <50ms | >100ms | >200ms |
| Request Rate | 1000 req/s | 500 req/s | 200 req/s |

**Alerts**:
- `TriageServiceHighLatency`: P95 > 500ms for 5+ minutes
- `HighErrorRate`: Error rate > 5%

### 3. System Health

| Component | Status Check | Frequency | Alert Threshold |
|-----------|--------------|-----------|-----------------|
| Triage Service | /health | 30s | 3 consecutive failures |
| Dapr Sidecar | /v1.0/healthz | 30s | 3 consecutive failures |
| Circuit Breakers | State tracking | Real-time | OPEN state |

**Alerts**:
- `TriageServiceDown`: Service unavailable
- `CircuitBreakerOpen`: Agent in OPEN state

### 4. Security Monitoring

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Auth Failures | >10/min | `HighAuthFailureRate` |
| JWT Validation Failures | >5/min | Critical |
| Schema Violations | >20/hour | Warning |
| Rate Limit Violations | >50/hour | `RateLimitExceeded` |

**Audit Events**:
- All security events logged to Kafka
- Compliance reports generated hourly
- High-risk students flagged automatically

### 5. Resource Utilization

| Resource | Target | Warning | Critical |
|----------|--------|---------|----------|
| CPU Usage | <50% | >70% | >85% |
| Memory Usage | <200MB | >250MB | >300MB |
| Pod Restarts | 0 | >3/hour | >10/hour |

**Alerts**:
- `HighMemoryUsage`: Memory > 80% for 5+ minutes

## Dashboard Panels

### Primary Dashboard (Grafana)

**Panel 1: Token Efficiency Trend**
```
Panel: Line Graph
Query: triage_efficiency_percentage
Time Range: 24h
Refresh: 10s
Targets: 98.7% line
```

**Panel 2: Request Latency Distribution**
```
Panel: Heatmap
Query: histogram_quantile(0.95, http_request_duration_seconds)
Refresh: 5s
Buckets: 0-50ms, 50-100ms, 100-200ms, 200ms+
```

**Panel 3: Circuit Breaker State**
```
Panel: Status Grid
Query: triage_circuit_breaker_state
Agents: debug-agent, concepts-agent, exercise-agent, progress-agent, review-agent
States: CLOSED (Green), OPEN (Red), HALF_OPEN (Yellow)
```

**Panel 4: Intent Classification Volume**
```
Panel: Bar Chart
Query: rate(triage_intent_total[5m]) by (intent)
Intents: syntax_help, concept_explanation, practice_exercises, progress_check
```

### Security Dashboard

**Panel 5: Security Events Timeline**
```
Panel: Timeline
Query: security_events_total
Types: AUTH_FAILURE, AUTHZ_VIOLATION, SCHEMA_VIOLATION, CIRCUIT_BREAKER
Severity: High, Medium, Low
```

**Panel 6: High-Risk Students**
```
Panel: Table
Query: security_high_risk_students
Columns: Student ID, Event Count, Risk Level, Last Activity
Threshold: ≥5 events
```

### Performance Dashboard

**Panel 7: Token Usage Breakdown**
```
Panel: Pie Chart
Query: triage_tokens_total by (intent)
```

**Panel 8: End-to-End Processing Time**
```
Panel: Line Graph
Query: triage_processing_duration_seconds
Percentiles: p50, p95, p99
```

## Alert Routing

### Severity Levels

**Critical (PagerDuty)**
- Service down
- Circuit breaker open > 5 minutes
- Auth failure spike (>50/min)
- Memory/CPU critical thresholds

**Warning (Slack)**
- Latency degradation
- Token efficiency drop
- Rate limit violations
- Pod restarts

**Info (Logs)**
- Daily compliance reports
- Performance trends
- Usage statistics

### Escalation Policy

1. **0-5 min**: Auto-healing (circuit breaker, retry)
2. **5-15 min**: On-call engineer notified
3. **15-30 min**: Team lead alerted
4. **30+ min**: Engineering manager + architect

## Log Aggregation

### Structured Logging Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "triage-service",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "user_id": "student-12345",
  "event": "TRIAGE_COMPLETE",
  "data": {
    "intent": "syntax_help",
    "agent": "debug-agent",
    "tokens_used": 18,
    "efficiency": 98.8,
    "processing_ms": 12.5,
    "circuit_breaker": "CLOSED"
  }
}
```

### Key Log Queries

**Find slow requests:**
```
{service="triage-service"}
| json
| processing_ms > 100
| sort_by(processing_ms desc)
```

**Security issues:**
```
{service="triage-service", event=~"AUTH_.*|SCHEMA_.*"}
| level="ERROR" or level="WARN"
```

**Circuit breaker events:**
```
{service="triage-service"}
| event="CIRCUIT_BREAKER"
| state="OPEN"
```

## Tracing

### Distributed Trace Flow

```
Kong Gateway → Triage Service → Dapr → Target Agent
     ↓              ↓            ↓         ↓
  JWT Auth     Security Ctx   Retry    Circuit Br
  Rate Limit   Schema Val     Timeout  Health Check
              Intent Class
              Route Select
              Audit Log
```

### Trace Annotations

- **Token Efficiency**: `%` in span attributes
- **Routing Decision**: Agent name in span
- **Circuit State**: State in span
- **Retry Count**: Attempt number
- **Student ID**: For correlation

## Compliance Metrics

### SOC2 Compliance Dashboard

**Access Control**
- ✅ All requests authenticated
- ✅ JWT validation enforced
- ✅ Role-based access
- ✅ Audit trail complete

**Data Integrity**
- ✅ Schema validation 100%
- ✅ Input sanitization active
- ✅ Error handling comprehensive

**Availability**
- ✅ Uptime >99.9%
- ✅ Circuit breakers active
- ✅ Auto-retry configured

### Hourly Compliance Report

```yaml
report_id: security-report-12345
period: 1h
summary:
  total_events: 45
  risk_score: LOW
  alerts: 0
  compliance: 100%

findings:
  - type: AUTH_FAILURE
    count: 2
    severity: low
    action: monitor

  - type: SCHEMA_VIOLATION
    count: 43
    severity: low
    action: review API docs
```

## Operational Runbooks

### Incident: High Latency

**Symptoms**: P95 latency > 200ms

**Steps**:
1. Check dashboard for specific intent/agent bottleneck
2. Verify circuit breaker states (should be CLOSED)
3. Check Dapr health and network latency
4. Review token efficiency (should be >98%)
5. Scale pods if load > capacity

**Resolution**: Revert to previous version if changes deployed

### Incident: Circuit Breaker Open

**Symptoms**: Agents showing OPEN state

**Steps**:
1. Identify failing agent
2. Check agent health endpoints
3. Review recent deployments
4. Check network connectivity
5. Monitor for automatic recovery

**Resolution**: Manual intervention only if pattern persists > 15 min

### Incident: Token Efficiency Drop

**Symptoms**: Efficiency < 95%

**Steps**:
1. Verify skill library loading
2. Check OpenAI API availability
3. Review recent code changes
4. Compare against baseline metrics

**Resolution**: Rollback to last known good configuration

## Maintenance Windows

### Scheduled Maintenance

**Weekly**:
- Performance optimization review
- Security compliance audit
- Cost analysis

**Monthly**:
- Capacity planning review
- Dependency updates
- Chaos testing exercises

**Quarterly**:
- Full security audit
- Disaster recovery drill
- Architecture review

---

**Dashboard Owner**: Platform Engineering Team
**On-Call**: #learnflow-oncall
**Documentation**: https://docs.learnflow.com/monitoring/triage-service