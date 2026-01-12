# Runbook: Circuit Breaker Open Incident

**Priority**: High
**Impact**: Service Degradation
**MTTR Target**: < 10 minutes (auto-heal), < 20 minutes (manual)

## Symptoms

- Alert: `CircuitBreakerOpen` triggered
- `/api/v1/triage/circuit-breakers` shows OPEN state
- Service invocations failing fast
- Error responses for specific agents
- Dashboard shows red circuit breaker indicator

## Immediate Actions (0-2 minutes)

### 1. Identify Open Circuit
```bash
# Check circuit breaker status
curl http://localhost:8000/api/v1/triage/circuit-breakers | jq

# Expected output:
# {
#   "circuit_breakers": {
#     "debug-agent": {"state": "OPEN", "can_attempt": false, "failure_count": 5},
#     "concepts-agent": {"state": "CLOSED", "can_attempt": true, "failure_count": 0}
#   },
#   "summary": {
#     "open": 1,
#     "closed": 4,
#     "half_open": 0
#   }
# }
```

### 2. Check Affected Agent
```bash
# Get agent health
curl http://localhost:8000/api/v1/triage/health/debug-agent

# Check agent pods
kubectl get pods -n learnflow -l app=debug-agent

# Check agent logs
kubectl logs -n learnflow -l app=debug-agent --tail=50
```

## Diagnosis (2-5 minutes)

### 3. Review Failure Pattern
```bash
# Check recent failure logs
kubectl logs -n learnflow <triage-pod> | grep "invoke_agent.*debug-agent" | tail -20

# Look for specific error
kubectl logs -n learnflow <triage-pod> | grep "CIRCUIT_BREAKER" | tail -10
```

### 4. Identify Root Cause

**Check for:**
- Network connectivity issues
- Agent service down
- Resource exhaustion (CPU/memory)
- Database/backend service issues
- Recent deployments

```bash
# Agent resource usage
kubectl top pods -n learnflow -l app=debug-agent

# Check for crashes
kubectl get events -n learnflow --sort-by='.lastTimestamp' | grep debug-agent

# Dapr sidecar status
kubectl logs -n learnflow -l app=debug-agent -c daprd --tail=20
```

## Resolution (5-15 minutes)

### Scenario A: Agent Service Down

**If agent pod is not running:**
```bash
# Force recreation
kubectl delete pod -n learnflow -l app=debug-agent

# Wait for recovery
kubectl get pods -n learnflow -l app=debug-agent -w

# Check if auto-healing triggers
watch 'kubectl logs -n learnflow -l app=debug-agent --tail=5'
```

### Scenario B: Resource Exhaustion

**If agent is OOMKilled or CPU throttled:**
```bash
# Scale agent horizontally
kubectl scale deployment debug-agent --replicas=5 -n learnflow

# Increase resource limits if needed
kubectl patch deployment debug-agent -n learnflow --patch '{"spec":{"template":{"spec":{"containers":[{"name":"debug-agent","resources":{"limits":{"cpu":"1000m","memory":"512Mi"}}}]}}}}'
```

### Scenario C: Network Issues

**If network connectivity is problematic:**
```bash
# Test Dapr service invocation
kubectl exec -n learnflow <triage-pod> -- curl http://localhost:3500/v1.0/invoke/debug-agent/method/health

# Check Dapr logs
kubectl logs -n learnflow -l app=debug-agent -c daprd | grep -i error
```

### Scenario D: Backend Service Issue

**If agent depends on external service:**
```bash
# Check external dependencies
kubectl exec -n learnflow -l app=debug-agent -- env | grep DATABASE
kubectl exec -n learnflow -l app=debug-agent -- nc -zv $DATABASE_HOST $DATABASE_PORT

# Check for connection pool exhaustion
kubectl logs -n learnflow -l app=debug-agent | grep "connection"
```

### Scenario E: Automatic Recovery Waiting

**If agent recently recovered but circuit still OPEN:**
```bash
# Wait for timeout (default 30s)
# Monitor half-open transition
watch 'curl http://localhost:8000/api/v1/triage/health/debug-agent'

# Check circuit breaker timestamp
curl http://localhost:8000/api/v1/triage/circuit-breakers | jq '.circuit_breakers.debug-agent'
```

## Emergency Manual Reset (Only if needed)

### Force Circuit Close
**⚠️ Only use if agent is confirmed healthy and auto-recovery is stuck**

```bash
# This requires direct access to triage-service internals
# Modify via debug endpoint if available
curl -X POST http://localhost:8000/api/v1/triage/debug/reset-circuit/debug-agent

# Or restart triage-service to reset all circuits
kubectl rollout restart deployment/triage-service -n learnflow
```

## Verification (15-18 minutes)

### After Resolution

```bash
# 1. Verify circuit closed
curl http://localhost:8000/api/v1/triage/circuit-breakers | jq '.circuit_breakers.debug-agent.state'
# Should output: "CLOSED"

# 2. Test service invocation
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "student-12345"}'

# 3. Monitor for 5 minutes
watch 'curl http://localhost:8000/api/v1/triage/circuit-breakers | jq .summary'

# 4. Check error rate
kubectl logs -n learnflow -l app=triage-service --since=5m | grep -c "error\|ERROR"
```

### Expected State
- All circuit breakers: `CLOSED`
- Failure counts: `0`
- Service invocations: successful
- No new alerts

## Prevention

### Proactive Measures

**1. Configure Appropriate Thresholds**
```yaml
# infrastructure/dapr/components/resiliency.yaml
circuitBreakers:
  triage-circuit:
    threshold: 5        # Failures before opening
    timeout: 30s        # Time in OPEN state
    interval: 10s       # Health check interval
    halfOpenMaxRequests: 3
```

**2. Set Resource Limits**
```yaml
# Ensure adequate resources
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
```

**3. Implement Health Checks**
```python
# All agents must implement /health endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "dependencies": check_db()}
```

**4. Monitoring Setup**
```yaml
# Prometheus alerting rules
- alert: CircuitBreakerWarning
  expr: triage_circuit_breaker_state{state="HALF_OPEN"} == 1
  for: 2m
  labels: {severity: warning}
```

## Escalation

### If Not Resolved in 10 Minutes

1. **Page on-call engineer**
2. **Check for widespread issues**
   ```bash
   # Are other agents affected?
   curl http://localhost:8000/api/v1/triage/circuit-breakers | jq '.summary'

   # Check overall system health
   kubectl get pods -n learnflow --all-namespaces
   ```

### If Not Resolved in 20 Minutes

1. **Escalate to team lead**
2. **Consider traffic routing**
   ```bash
   # If debug-agent consistently fails, route to fallback
   # This requires code changes or feature flag
   ```

3. **Emergency measures**
   ```bash
   # Scale all services
   kubectl scale deployment --all --replicas=10 -n learnflow

   # Check cluster resources
   kubectl top nodes
   ```

## Impact Assessment

### User Impact During Incident

**User Experience:**
- Queries routed to debug-agent will fail
- Other intents continue working
- Automatic fallback to review-agent possible

**Business Impact:**
- Partial service degradation
- No complete outage
- Feature degradation (syntax help unavailable)

### Communication

**Internal:**
- Alert in #learnflow-alerts Slack channel
- Update incident channel with status every 5 min
- Notify stakeholders after 15 min

**External:**
- Only if >50% of users affected
- Use status page: status.learnflow.com

## Related Documents

- [High Latency Runbook](./high-latency.md)
- [Service Recovery](./service-recovery.md)
- [Monitoring Dashboard](../monitoring/dashboard.md)

---

**Last Updated**: 2024-01-15
**Owner**: Platform Engineering Team
**Review Cycle**: Monthly
**Auto-Heal Expected**: Yes (within 30-60 seconds)