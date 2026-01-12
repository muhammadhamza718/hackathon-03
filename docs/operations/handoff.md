# Operations Handoff Document

**Triage Service - LearnFlow Platform**
**Version**: 1.0.0
**Handoff Date**: 2024-01-15

## Executive Summary

The Triage Service is a **skills-first intelligent routing system** achieving **98.7% token efficiency** compared to traditional LLM approaches. It handles request classification, routing, and Dapr service orchestration with enterprise-grade resilience.

**Key Metrics:**
- **Token Efficiency**: 98.7% reduction (1500 → 19 tokens)
- **P95 Latency**: ~15ms (target: <150ms)
- **Uptime Target**: 99.9%
- **Current Deployment**: 3 replicas

## Architecture Overview

### Request Flow
```
Kong Gateway (JWT + Rate Limit)
    ↓
Triage Service (Security Context)
    ↓
Skills Library (Intent Detection)
    ↓
Router (Routing Decision)
    ↓
Dapr Client (Service Invocation)
    ↓
Target Agent (Debug/Concepts/Exercise/Progress)
    ↓
Audit Logger (Kafka + Compliance)
```

### Critical Components

#### 1. Skills Library (`skills-library/triage-logic/`)
- **intent-detection.py**: Classifies user queries into 4 intents
- **route-selection.py**: Maps intents to target agents
- **Efficiency**: <50 tokens, <20ms per classification

#### 2. Triage Service (`backend/triage-service/`)
- **FastAPI application** with 5 endpoints
- **Dual security**: Auth + Authorization middleware
- **Circuit breaker**: Per-agent protection
- **Dapr integration**: Service invocation + resiliency

#### 3. Dapr Layer
- **Circuit Breakers**: 5 failures → 30s open
- **Retry Policy**: 3 attempts, exponential backoff
- **Timeout**: 2s per service call

#### 4. Security Stack
- **Kong**: JWT validation + rate limiting (100 req/min)
- **Auth Middleware**: X-Consumer-Username → student_id
- **Audit**: All events to Kafka
- **Compliance**: SOC2-ready reporting

## On-Call Procedures

### First Responder Checklist (0-5 minutes)

**1. Check Alert Severity**
```bash
# View active alerts
# Connect to monitoring: https://grafana.learnflow.com

# Check service health
curl https://api.learnflow.com/health
# Expected: {"status": "healthy", "phase": "2"}
```

**2. Quick System Status**
```bash
# Check pod status
kubectl get pods -n learnflow -l app=triage-service

# Check circuit breakers
curl https://api.learnflow.com/api/v1/triage/circuit-breakers

# Check recent errors
kubectl logs -n learnflow -l app=triage-service --since=5m | grep ERROR
```

**3. User Impact Assessment**
```bash
# Check error rate
# Grafana: Rate of 5xx errors in last 5 minutes
# Target: <1% error rate

# Check latency
# Grafana: P95 latency for triage-service
# Target: <150ms
```

### Alert Response Matrix

| Alert | Severity | First Action | Escalate To |
|-------|----------|--------------|-------------|
| Service Down | Critical | Check logs, scale pods | Team Lead (5m) |
| Circuit Breaker Open | High | Check agent health | On-call (2m) |
| High Latency | High | Check metrics | Team Lead (10m) |
| Low Token Efficiency | Medium | Check skill library | Architect (15m) |
| Auth Failure Spike | Critical | Check Kong config | Security (immediate) |

## Key Runbooks

### Critical Issues
1. **[Service Down](../runbooks/service-recovery.md)** - Complete outage
2. **[High Latency](../runbooks/high-latency.md)** - Performance degradation
3. **[Circuit Breaker Open](../runbooks/circuit-breaker.md)** - Partial outage

### Performance Issues
4. **[Token Efficiency Drop](../runbooks/token-efficiency.md)** - Efficiency degradation
5. **[Memory/CPU Issues](../runbooks/resource-management.md)** - Resource exhaustion

### Security Issues
6. **[Auth Failures](../runbooks/auth-issues.md)** - Authentication problems
7. **[Security Incidents](../runbooks/security-incident.md)** - Breach response

## Monitoring & Alerting

### Dashboards

**Primary**: https://grafana.learnflow.com/d/triage-service
- Token efficiency trend
- Latency distribution
- Circuit breaker states
- Intent volume

**Security**: https://grafana.learnflow.com/d/triage-security
- Auth failures
- Schema violations
- Rate limit violations
- High-risk students

**Infrastructure**: https://grafana.learnflow.com/d/triage-infra
- Pod health
- Resource usage
- Network metrics
- Dapr metrics

### Critical Metrics to Watch

**Token Efficiency**
```promql
triage_efficiency_percentage
# Alert if < 95%
```

**Circuit Breakers**
```promql
triage_circuit_breaker_state{state="open"}
# Alert if > 0 for 2+ minutes
```

**Latency**
```promql
histogram_quantile(0.95, http_request_duration_seconds_bucket)
# Alert if > 500ms for 5+ minutes
```

**Auth Failures**
```promql
rate(auth_failure_total[5m])
# Alert if > 0.1 per second
```

## Operational Tasks

### Daily (On-Call)
- [ ] Check overnight alerts
- [ ] Review error rates
- [ ] Verify backup systems
- [ ] Check capacity headroom

### Weekly (Platform Team)
- [ ] Performance review
- [ ] Security compliance check
- [ ] Cost analysis
- [ ] Incident review

### Monthly (Engineering)
- [ ] Dependency updates
- [ ] Capacity planning
- [ ] Chaos testing
- [ ] Disaster recovery drill

## Troubleshooting Guide

### User Reports "Slow Response"

**Quick Check:**
1. `curl /metrics` → Check processing time
2. `curl /circuit-breakers` → Check for OPEN circuits
3. `kubectl logs` → Look for errors
4. Grafana → Check latency trends

**Possible Causes:**
- Circuit breaker OPEN (check agent health)
- High load (scale pods)
- Skills library issue (check imports)
- Network latency (check Dapr logs)

### User Reports "Unexpected Response"

**Quick Check:**
1. Check intent classification: `classify_intent(query)`
2. Check routing: `route_selection(intent)`
3. Check agent response in logs
4. Verify student_id propagation

**Common Issues:**
- Wrong intent classification
- Incorrect routing decision
- Agent returning errors
- Missing security context

### User Reports "Authentication Failed"

**Quick Check:**
1. Check Kong logs
2. Verify JWT claims
3. Check auth middleware logs
4. Verify X-Consumer-Username header

**Common Issues:**
- Expired JWT
- Missing Kong headers
- Student ID format issue
- Role mismatch

## Emergency Contacts

### On-Call Rotation
- **Primary**: [Name] - [Phone] - [Slack]
- **Secondary**: [Name] - [Phone] - [Slack]
- **Tertiary**: [Name] - [Phone] - [Slack]

### Escalation Path
1. **On-call engineer** (0-15 min)
2. **Team lead** (15-30 min)
3. **Engineering manager** (30-60 min)
4. **VP Engineering** (60+ min)

### Subject Matter Experts
- **Security**: [Name] - [Slack]
- **Dapr**: [Name] - [Slack]
- **Kafka**: [Name] - [Slack]
- **OpenAI**: [Name] - [Slack]

## Configuration & Secrets

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...
KAFKA_BROKERS=kafka-cluster:9092
DAPR_HTTP_PORT=3500

# Optional
LOG_LEVEL=INFO
MAX_CONCURRENCY=100
TIMEOUT_SECONDS=2
```

### Kubernetes ConfigMaps
```yaml
# dapr-components-config
# Contains Dapr component definitions
```

### Secrets (Vault)
```yaml
# openai-secret
# kafka-credentials
# jwt-signing-key
```

## Common Commands

### Service Management
```bash
# View logs
kubectl logs -n learnflow -l app=triage-service -f

# Restart service
kubectl rollout restart deployment/triage-service -n learnflow

# Scale service
kubectl scale deployment triage-service --replicas=5 -n learnflow

# Check resource usage
kubectl top pods -n learnflow -l app=triage-service
```

### Debugging
```bash
# Port forward for local testing
kubectl port-forward svc/triage-service 8000:80 -n learnflow

# Check Dapr components
kubectl port-forward <pod> 3500:3500
curl http://localhost:3500/v1.0/components

# Test service invocation
curl http://localhost:3500/v1.0/invoke/debug-agent/method/health
```

### Maintenance
```bash
# Rolling update
kubectl set image deployment/triage-service triage-service=learnflow/triage-service:v1.0.1 -n learnflow

# View rollout status
kubectl rollout status deployment/triage-service -n learnflow

# Rollback if needed
kubectl rollout undo deployment/triage-service -n learnflow
```

## Integration Points

### Upstream (Inputs)
- **Kong Gateway**: JWT auth, rate limiting
- **Student Portal**: API requests
- **Mobile App**: User queries

### Downstream (Outputs)
- **Debug Agent**: Syntax help
- **Concepts Agent**: Explanations
- **Exercise Agent**: Practice problems
- **Progress Agent**: Progress tracking
- **Review Agent**: Fallback routing

### Cross-Cutting
- **Kafka**: Event streaming
- **Redis**: State store (optional)
- **Prometheus**: Metrics
- **Grafana**: Visualization
- **PagerDuty**: Alerting

## Success Criteria

### User Experience
- ✅ Response < 200ms P95
- ✅ 98.7% token efficiency
- ✅ <1% error rate
- ✅ Accurate routing (95%+)

### System Health
- ✅ 99.9% uptime
- ✅ All circuit breakers closed
- ✅ Resource usage < 70%
- ✅ Zero critical security events

### Operational
- ✅ Mean time to detect < 1m
- ✅ Mean time to resolve < 15m
- ✅ Successful rollbacks < 5m
- ✅ No manual intervention for auto-healing

## Known Issues & Workarounds

### Current Issues
1. **Skills library import path**: Requires specific directory structure
   - **Workaround**: Use absolute paths in production

2. **Dapr SDK version**: Must use 1.12.0
   - **Workaround**: Pin version in requirements.txt

3. **Kafka connectivity**: Timeout issues under high load
   - **Workaround**: Increase connection pool size

### Historical Incidents
1. **2024-01-10**: Circuit breaker stuck in HALF_OPEN
   - **Root cause**: Health check timing
   - **Resolution**: Updated timeout configuration

2. **2024-01-05**: Token efficiency drop to 92%
   - **Root cause**: Skills library not loading
   - **Resolution**: Fixed import path

## Documentation Links

- **Architecture**: [docs/architecture/triage-service.md](../architecture/triage-service.md)
- **Monitoring**: [docs/monitoring/dashboard.md](../monitoring/dashboard.md)
- **Runbooks**: [docs/runbooks/](../runbooks/)
- **API Reference**: [docs/api/](../api/)
- **Changelog**: [CHANGELOG.md](../../../CHANGELOG.md)

---

**Handoff Checklist**
- [ ] All documents reviewed
- [ ] Monitoring dashboards access confirmed
- [ ] Runbooks understood
- [ ] Emergency contacts verified
- [ ] On-call rotation confirmed
- [ ] Training completed

**Next Review**: 2024-02-15
**Owner**: Platform Engineering Team
**Contact**: #platform-team on Slack