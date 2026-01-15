# Mastery Engine Deployment Verification Checklist

**Version**: 1.0.0 | **Last Updated**: 2026-01-15 | **Phase**: Deployment & Production Readiness

## Pre-Deployment Checks

### Code Quality & Security
- [ ] **Unit Tests Pass**: All pytest unit tests pass with >90% coverage
- [ ] **Integration Tests Pass**: All integration tests pass
- [ ] **Security Scan**: Dependency vulnerabilities checked with `safety check`
- [ ] **Code Quality**: Linting passed (flake8, black, isort)
- [ ] **Type Checking**: MyPy passes without critical errors
- [ ] **Git Status**: Clean working tree with no uncommitted changes

### Configuration Validation
- [ ] **Environment Variables**: All required env vars defined in k8s/configmap.yaml
- [ ] **Secrets**: JWT_SECRET and other secrets exist in Kubernetes secrets
- [ ] **Resource Limits**: CPU/Memory limits set appropriately (see deployment.yaml)
- [ ] **Dapr Configuration**: Dapr sidecar enabled and configured
- [ ] **Redis Configuration**: State store name matches Dapr configuration

### Docker Image
- [ ] **Image Builds Successfully**: `docker build .` completes without errors
- [ ] **Image Size**: < 250MB (verify with `docker images`)
- [ ] **Multi-stage Build**: Confirmed using multi-stage Dockerfile
- [ ] **Non-root User**: Container runs as non-root user (check Dockerfile)
- [ ] **Health Check**: Docker HEALTHCHECK configured correctly

## Deployment Verification

### Kubernetes Resources
```bash
# Apply and verify all manifests
kubectl apply -f k8s/ -n learnflow
```

- [ ] **Namespace**: `learnflow` exists or created
- [ ] **ConfigMap**: `mastery-engine-config` created with correct values
- [ ] **Secrets**: `mastery-engine-secrets` created (check with `kubectl get secrets`)
- [ ] **Deployment**: Pods created and running
- [ ] **Service**: ClusterIP service created
- [ ] **Dapr Sidecar**: Dapr container present in pod

### Pod Status
```bash
kubectl get pods -n learnflow -l app=mastery-engine
```

- [ ] **Pod Count**: Expected number of replicas running
- [ ] **Status**: All pods in `Running` state
- [ ] **Ready**: All pods show `1/1` ready
- [ ] **Restarts**: Zero or minimal restarts (< 3)

### Container Logs
```bash
kubectl logs -n learnflow deployment/mastery-engine --tail=50
```

- [ ] **Startup**: No errors during startup
- [ ] **Dependencies**: All dependency checks successful
- [ ] **Ready**: Service marked as ready
- [ ] **No Critical Errors**: No ERROR or CRITICAL level logs

### Service Discovery
```bash
kubectl get services -n learnflow
```

- [ ] **Service Created**: `mastery-engine` service exists
- [ ] **ClusterIP**: Service has ClusterIP assigned
- [ ] **Ports**: Correct ports exposed (8005)

## Dapr Integration

### Dapr Sidecar Status
```bash
kubectl get pods -n learnflow -l app=mastery-engine
kubectl logs -n learnflow -l app=mastery-engine -c daprd
```

- [ ] **Sidecar Running**: daprd container is running
- [ ] **Component Registration**: State store component registered
- [ ] **No Dapr Errors**: No errors in daprd logs

### State Store Connectivity
```bash
kubectl exec -n learnflow deployment/mastery-engine -- \
  python -c "from src.services.state_manager import StateManager; sm = StateManager.create(); await sm.health_check()"
```

- [ ] **Redis Accessible**: Connection successful
- [ ] **Health Check**: `health_check()` returns True
- [ ] **CRUD Operations**: Basic save/get/delete work

## Health Checks

### Liveness Probe
```bash
kubectl exec -n learnflow deployment/mastery-engine -- \
  ./scripts/health-check.sh liveness
```

- [ ] **Response**: HTTP 200 from `/health`
- [ ] **Timeout**: Responds within 3s
- [ ] **Consistency**: Multiple checks succeed

### Readiness Probe
```bash
kubectl exec -n learnflow deployment/mastery-engine -- \
  ./scripts/health-check.sh readiness
```

- [ ] **Response**: HTTP 200 from `/ready`
- [ ] **Dependencies**: All dependencies show as healthy
- [ ] **State Store**: Redis connection verified
- [ ] **Readiness**: Service accepts traffic

### Startup Probe
```bash
kubectl exec -n learnflow deployment/mastery-engine -- \
  ./scripts/k8s-startup-probe.sh
```

- [ ] **Successful Start**: Probe completes successfully
- [ ] **Within Timeout**: Starts within 120s
- [ ] **Dependency Ready**: All dependencies available

## API Endpoint Testing

### Core Endpoints
```bash
# Health endpoints
curl http://<service>/health
curl http://<service>/ready
curl http://<service>/metrics
curl http://<service>/
```

- [ ] **Health**: Returns `{ "status": "healthy" }`
- [ ] **Ready**: Returns ready status with dependencies
- [ ] **Metrics**: Prometheus metrics format returned
- [ ] **Info**: Service info with version

### Mastery Endpoints
```bash
# Test with a valid JWT token
curl -X POST http://<service>/api/v1/mastery/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "test_student"}'
```

- [ ] **Query**: Returns mastery data for student
- [ ] **Calculate**: Calculates mastery from scores
- [ ] **Authentication**: Rejects invalid tokens
- [ ] **Validation**: Returns 400 for invalid input

### Analytics Endpoints
```bash
# Batch processing
curl -X POST http://<service>/api/v1/batch/mastery \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"student_ids": ["student1", "student2"], "priority": "normal"}'
```

- [ ] **Batch**: Accepts batch request and returns batch_id
- [ ] **Status**: Batch status endpoint returns progress
- [ ] **History**: Historical analytics work
- [ ] **Cohorts**: Cohort comparison functional

### Dapr Endpoints
```bash
curl -X POST http://<service>/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{"intent": "mastery_calculation", "payload": {"student_id": "test"}}'
```

- [ ] **Service Invocation**: Dapr process endpoint responds
- [ ] **Intent Routing**: Correct routing for all intents
- [ ] **Response Format**: Standardized Dapr response format

## Performance & Monitoring

### Response Time
```bash
# Time critical endpoints
time curl -s http://<service>/health > /dev/null
```

- [ ] **Health**: < 50ms
- [ ] **Ready**: < 200ms
- [ ] **Mastery Query**: < 100ms (with cache)
- [ ] **Batch Submission**: < 500ms

### Metrics Verification
```bash
curl http://<service>/metrics/detailed
```

- [ ] **Active Requests**: Metric tracks active requests
- [ ] **Cache Hit Ratio**: > 70% for Redis cache
- [ ] **Error Rate**: < 1% of total requests
- [ ] **Latency**: Prometheus histograms working

### Prometheus Integration (Optional)
```bash
# If Prometheus is configured
curl http://<service>/metrics
```

- [ ] **Format**: Prometheus text format
- [ ] **Counters**: Request counters increasing
- [ ] **Histograms**: Latency histograms populated
- [ ] **Gauges**: Active requests gauge working

## Security Verification

### Authentication & Authorization
```bash
# Test without token
curl -X POST http://<service>/api/v1/mastery/query \
  -H "Content-Type: application/json" \
  -d '{"student_id": "test"}'
# Should return 401/403
```

- [ ] **No Token**: Returns 401 Unauthorized
- [ ] **Invalid Token**: Returns 401/403
- [ ] **Student Access**: Students can only access own data
- [ ] **Teacher Access**: Teachers can access assigned students
- [ ] **Admin Access**: Admins have full access

### Input Validation
```bash
# Test with malicious input
curl -X POST http://<service>/api/v1/mastery/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "test; DROP TABLE users;--"}'
```

- [ ] **SQL Injection**: Rejected/sanitized
- [ ] **XSS**: Script tags stripped
- [ ] **Command Injection**: Special characters handled
- [ ] **Invalid JSON**: Returns 400 Bad Request

### GDPR Compliance
```bash
# Test data export
curl -X GET http://<service>/api/v1/compliance/export/<student_id> \
  -H "Authorization: Bearer <token>"

# Test data deletion
curl -X DELETE http://<service>/api/v1/compliance/student/<student_id> \
  -H "Authorization: Bearer <token>"
```

- [ ] **Data Export**: Returns complete student data
- [ ] **Data Deletion**: Removes all student data
- [ ] **Audit Logs**: Deletion logged with user ID
- [ ] **TTL**: Old data auto-deleted after 90 days

### Rate Limiting
```bash
# Rapid requests to test rate limit
for i in {1..60}; do
  curl -s http://<service>/health > /dev/null
done
```

- [ ] **50 req/min**: Rate limit enforced
- [ ] **429 Response**: Returns 429 Too Many Requests
- [ ] **Headers**: Includes Retry-After header

## Connection Pool & Circuit Breaker

### Connection Pool Health
```bash
kubectl exec -n learnflow deployment/mastery-engine -- \
  python -c "from src.services.connection_pool import get_redis_pool; await get_redis_pool().health_check()"
```

- [ ] **Redis Pool**: Health check passes
- [ ] **Pool Size**: Connection pool created successfully
- [ ] **Operations**: Redis operations via pool work

### Circuit Breaker Status
```bash
curl http://<service>/metrics/detailed | jq '.circuit_breakers'
```

- [ ] **Initial State**: All circuits closed
- [ ] **Metrics**: Circuit state metrics visible
- [ ] **Fencing**: Service degradation handled correctly

## Kubernetes Features

### Resource Management
```bash
kubectl top pods -n learnflow -l app=mastery-engine
```

- [ ] **CPU Usage**: < 500m per pod (baseline)
- [ ] **Memory Usage**: < 512Mi per pod
- [ ] **Scaling**: HPA configured if needed

### Horizontal Pod Autoscaler (if configured)
```bash
kubectl get hpa -n learnflow
```

- [ ] **HPA Exists**: HPA resource created
- [ ] **Metrics**: CPU/Memory targets set
- [ ] **Scaling**: Can scale up/down based on load

### Pod Disruption Budget
```bash
kubectl get pdb -n learnflow
```

- [ ] **PDB Configured**: Prevents all pods going down
- [ ] **Min Available**: Set to 1 or higher

## Load Testing

### Baseline Performance
```bash
# If locust is available
locust -f tests/load/test_load.py --host=http://<service> --users=50 --spawn-rate=5 --run-time=5m
```

- [ ] **50 Users**: System handles 50 concurrent users
- [ ] **Throughput**: > 100 requests/sec sustained
- [ ] **Error Rate**: < 0.1% under load
- [ ] **Latency**: P95 < 200ms under load

### Stress Testing
```bash
# Higher load test
locust -f tests/load/test_load.py --host=http://<service> --users=200 --spawn-rate=20 --run-time=10m
```

- [ ] **200 Users**: Graceful degradation
- [ ] **Circuit Breakers**: Trip at appropriate thresholds
- [ ] **Recovery**: Returns to normal after load reduces

## Logging & Observability

### Structured Logging
```bash
kubectl logs -n learnflow deployment/mastery-engine --tail=20
```

- [ ] **JSON Format**: Logs in JSON structure
- [ ] **Correlation IDs**: All logs include correlation_id
- [ ] **Trace IDs**: Distributed tracing headers present
- [ ] **Error Context**: Errors include stack traces and context

### Log Aggregation (if configured)
```bash
# Check if logs flow to your logging system
# Example: kubectl logs ... | grep "correlation_id" | jq .
```

- [ ] **Log Forwarding**: Logs sent to aggregator
- [ ] **Searchable**: Can query by correlation_id
- [ ] **Retention**: 30-day retention configured

### Tracing
```bash
curl -v http://<service>/health
# Check for X-Request-ID, X-Trace-ID headers
```

- [ ] **Headers**: Response includes tracing headers
- [ ] **Spans**: Trace spans increment correctly
- [ ] **Distributed**: Trace IDs propagate to dependencies

## Rollback Plan

### Verification Checkpoints
- [ ] **Can Rollback**: Previous version image exists
- [ ] **Rollback Command**: `kubectl rollout undo deployment/mastery-engine -n learnflow`
- [ ] **Data Safety**: State store is backward compatible
- [ ] **Notification**: Team aware of rollback procedure

### Monitoring During Deployment
- [ ] **Dashboard**: Metrics dashboard monitoring
- [ ] **Alerts**: Alert rules configured for error rates
- [ ] **SLI/SLO**: Service Level Indicators monitored

## Documentation & Handoff

### Deployment Records
- [ ] **Version**: Docker image tag recorded
- [ ] **Commit**: Git commit hash documented
- [ ] **Time**: Deployment timestamp recorded
- [ ] **Operator**: Deployment operator noted

### Runbooks Updated
- [ ] **troubleshooting.md**: Updated with deployment-specific info
- [ ] **runbooks.md**: Deployment steps documented
- [ ] **escalation**: On-call procedures included

## Sign-off Checklist

| Category | Status | Notes |
|----------|--------|-------|
| **Code Quality** | ☐ | |
| **Security** | ☐ | |
| **Configuration** | ☐ | |
| **Docker Image** | ☐ | |
| **Kubernetes** | ☐ | |
| **Dapr Integration** | ☐ | |
| **Health Checks** | ☐ | |
| **API Endpoints** | ☐ | |
| **Performance** | ☐ | |
| **Monitoring** | ☐ | |
| **Load Testing** | ☐ | |
| **Security Tests** | ☐ | |

## Deployment Approval

**Deployed By**: ___________________
**Date**: ___________________
**Version**: ___________________
**Environment**: ☐ Staging ☐ Production

**Sign-off Required**:
- [ ] **Dev Lead**: ___________________
- [ ] **Ops Lead**: ___________________
- [ ] **Security**: ___________________

---

**Next Actions**:
1. [ ] Run post-deployment smoke tests
2. [ ] Monitor for 30 minutes
3. [ ] Create incident if any checks fail
4. [ ] Update this document with any issues found

**Post-Deployment**:
- Service Dashboard: `kubectl port-forward svc/mastery-engine 8005:8005 -n learnflow`
- Metrics: `curl http://localhost:8005/metrics/detailed`
- Logs: `kubectl logs -f deployment/mastery-engine -n learnflow`
