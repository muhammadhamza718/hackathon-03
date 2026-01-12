# Runbook: High Latency Incident

**Priority**: High
**Impact**: User Experience Degradation
**MTTR Target**: < 15 minutes

## Symptoms

- P95 latency exceeds 200ms
- User complaints about slow responses
- Dashboard shows red latency indicators
- Alert: `TriageServiceHighLatency` triggered

## Immediate Actions (0-2 minutes)

### 1. Check Service Health
```bash
kubectl get pods -n learnflow -l app=triage-service
kubectl describe pod -n learnflow <pod-name>
kubectl logs -n learnflow <pod-name> -c triage-service --tail=100
```

### 2. Check Dapr Sidecar
```bash
kubectl logs -n learnflow <pod-name> -c daprd --tail=50
kubectl port-forward <pod-name> 3500:3500
curl http://localhost:3500/v1.0/healthz
```

### 3. Check Circuit Breaker Status
```bash
curl http://localhost:8000/api/v1/triage/circuit-breakers
```

## Diagnosis (2-10 minutes)

### 4. Analyze Metrics
Check Grafana dashboard for:
- **Token Efficiency**: Should be ≥98.7%
- **Intent Distribution**: Any unusual patterns?
- **Agent Response Times**: Which agent is slow?
- **Circuit Breaker States**: Any OPEN circuits?

### 5. Identify Bottleneck
```bash
# Check specific intent performance
kubectl logs -n learnflow <pod-name> | grep "processing_time"

# Check Dapr service invocation latency
kubectl logs -n learnflow <pod-name> -c daprd | grep "service_invocation"
```

### 6. Verify Token Efficiency
```python
# Quick verification
python3 -c "
import sys
sys.path.insert(0, 'backend/triage-service/src')
from services.openai_router import OpenAIRouter
router = OpenAIRouter()
result = router.classify_intent('syntax error')
print(f'Tokens: {result[\"token_estimate\"]}, Efficiency: {(1500-result[\"token_estimate\"])/1500*100:.1f}%')
"
```

## Resolution (10-15 minutes)

### Scenario A: Single Agent Slow

**If concepts-agent is slow:**
```bash
# Check agent health
kubectl get pods -n learnflow -l app=concepts-agent

# If unhealthy, scale temporarily
kubectl scale deployment concepts-agent --replicas=5 -n learnflow

# Monitor recovery
watch 'kubectl get pods -n learnflow -l app=concepts-agent'
```

### Scenario B: All Agents Slow

**If all agents affected:**
1. Check Dapr cluster health
2. Verify network connectivity between services
3. Check resource limits (CPU/memory)
4. Review recent deployments

```bash
# Scale all triage-service pods
kubectl scale deployment triage-service --replicas=5 -n learnflow

# Monitor scaling
kubectl get pods -n learnflow -l app=triage-service -w
```

### Scenario C: Token Efficiency Drop

**If efficiency < 95%:**
1. Verify skill library is loading correctly
2. Check OpenAI API status
3. Check for recent code changes

```bash
# Check skill library files
ls -la backend/triage-service/skills-library/triage-logic/

# Verify imports
python3 -c "from services.openai_router import OpenAIRouter; print('OK')"
```

## Escalation

### If Not Resolved in 15 Minutes

1. **Page on-call engineer**
2. **Check recent deployments**
   ```bash
   kubectl rollout history deployment/triage-service -n learnflow
   kubectl rollout undo deployment/triage-service -n learnflow --to-revision=<previous>
   ```
3. **Emergency scaling**
   ```bash
   kubectl scale deployment triage-service --replicas=10 -n learnflow
   ```

### If Not Resolved in 30 Minutes

1. **Escalate to team lead**
2. **Consider service degradation**
   ```bash
   kubectl set env deployment/triage-service LOG_LEVEL=DEBUG -n learnflow
   ```
3. **Enable emergency mode** (if available)

## Verification

### Post-Incident Checks

```bash
# Verify latency recovery
kubectl logs -n learnflow <pod-name> | grep "processing_time" | tail -20

# Check circuit breaker closed
curl http://localhost:8000/api/v1/triage/circuit-breakers | jq '.summary.closed'

# Verify token efficiency
curl http://localhost:8000/metrics | grep efficiency
```

### Expected Metrics
- P95 latency < 150ms
- All circuit breakers CLOSED
- Token efficiency ≥ 98.7%
- No errors in logs

## Prevention

### Proactive Monitoring
- Set up alerts for latency > 100ms (warning before critical)
- Monitor token efficiency trends
- Track circuit breaker state changes

### Capacity Planning
- Review request volume patterns
- Scale proactively during peak hours
- Ensure 30% headroom capacity

## Related Documents

- [Circuit Breaker Runbook](./circuit-breaker.md)
- [Token Efficiency Runbook](./token-efficiency.md)
- [Service Recovery](./service-recovery.md)

---

**Last Updated**: 2024-01-15
**Owner**: Platform Engineering Team
**Review Cycle**: Monthly