# Mastery Engine Troubleshooting Guide

**Version**: 1.0.0 | **Last Updated**: 2026-01-15 | **Service**: mastery-engine

## Quick Reference

| Issue Category | Symptoms | Quick Fix |
|----------------|----------|-----------|
| **Service Down** | `/health` returns 503 | Check dependencies (Redis, Dapr, Kafka) |
| **Slow Responses** | P95 > 500ms | Check Redis cache, scale pods, check Kafka lag |
| **Dapr Errors** | 500 on service calls | Verify Dapr sidecar running: `kubectl get pods` |
| **Kafka Issues** | Events not processed | Check consumer groups, DLQ topic, topic existence |
| **Auth Failures** | 401/403 responses | Validate JWT secret, check role assignments |

---

## 1. Service Health Issues

### Symptoms
- `/health` endpoint returns 503
- `/ready` endpoint fails dependency checks
- Application crashes on startup

### Diagnosis Steps

```bash
# Check pod status
kubectl get pods -n learnflow -l app=mastery-engine

# View logs
kubectl logs -n learnflow -l app=mastery-engine --tail=100

# Check Dapr sidecar status
kubectl logs -n learnflow -l app=mastery-engine -c daprd

# Verify dependencies
kubectl exec -n learnflow deployment/mastery-engine -- \
  curl -s http://localhost:3500/v1.0/healthz
```

### Common Causes & Fixes

**Issue: Redis Connection Failed**
```bash
# Verify Redis is running
kubectl get pods -n learnflow -l app=redis

# Check Redis service
kubectl get svc -n learnflow redis

# Test connection from mastery-engine pod
kubectl exec -n learnflow deployment/mastery-engine -- \
  python -c "import redis; r=redis.Redis(host='redis', port=6379); r.ping()"
```

**Issue: Dapr Sidecar Not Ready**
```bash
# Check Dapr status
kubectl get pods -n learnflow -l app=dapr-sidecar

# View Dapr logs
kubectl logs -n learnflow -l app=dapr-sidecar --tail=50

# Restart Dapr sidecar (deletes pod, Kubernetes recreates)
kubectl delete pod -n learnflow -l app=mastery-engine
```

**Issue: Kafka Topics Missing**
```bash
# List topics
kubectl exec -n learnflow deployment/kafka -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# Create missing topics
kubectl exec -n learnflow deployment/kafka -- \
  kafka-topics.sh --create --topic mastery.events --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092

kubectl exec -n learnflow deployment/kafka -- \
  kafka-topics.sh --create --topic mastery.dlq --partitions 1 --replication-factor 1 --bootstrap-server localhost:9092
```

---

## 2. Performance Issues

### Symptoms
- Slow response times (> 500ms P95)
- High memory usage
- CPU spikes during batch processing
- Slow batch operations

### Diagnosis

```bash
# Check metrics endpoint
curl http://<service>/metrics

# Monitor pod resources
kubectl top pods -n learnflow -l app=mastery-engine

# Check Redis latency
kubectl exec -n learnflow deployment/mastery-engine -- \
  python -c "import time; import redis; r=redis.Redis(host='redis'); start=time.time(); r.ping(); print(f'Redis latency: {(time.time()-start)*1000:.2f}ms')"

# Check Kafka consumer lag
kubectl exec -n learnflow deployment/kafka -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group mastery-engine-group
```

### Solutions

**Slow Redis Performance**
- Enable Redis pipelining in state_manager.py
- Check Redis memory usage: `kubectl exec -n learnflow deployment/redis -- redis-cli info memory`
- Scale Redis cluster if memory usage > 80%

**Kafka Consumer Lag**
- Increase consumer instances: `replicas: 3` in deployment.yaml
- Check batch processing time in analytics_service.py
- Monitor processing speed: should be < 500ms per event

**Slow Batch Operations**
```bash
# Check batch job status
curl -X GET http://<service>/api/v1/batch/status/<batch_id>

# Monitor concurrent processing
# In logs, look for: "Processing batch job" and "Completed batch job"
```

Optimization suggestions:
- Increase `max_concurrent_batches` in analytics_service.py
- Use Redis pipeline operations for bulk operations
- Consider read replicas for historical queries

---

## 3. Dapr Integration Issues

### Symptoms
- 500 errors on `/process` endpoints
- "Service invocation failed" errors
- Security context validation failures

### Common Issues

**Issue: Dapr Service Discovery**
```bash
# List registered services
kubectl exec -n learnflow deployment/mastery-engine -- \
  curl -s http://localhost:3500/v1.0/metadata | jq '.registeredComponents'

# Check Dapr logs for service registration
kubectl logs -n learnflow -l app=dapr-sidecar --tail=100 | grep "registered"
```

**Issue: Security Context Propagation**
```bash
# Verify JWT validation works
curl -X POST http://<service>/api/v1/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token" \
  -d '{"intent": "mastery_calculation", "payload": {"student_id": "test"}}'

# Should return 401 Unauthorized
```

**Solution**: Check security.py:
```python
# Verify JWT secret matches between services
# Check environment variable: JWT_SECRET
# Must be consistent across all microservices
```

---

## 4. Kafka Event Processing Issues

### Symptoms
- Events not being processed
- Events going to DLQ (dead-letter queue)
- Duplicate processing of events
- Memory usage growing continuously

### Diagnosis

```bash
# Check consumer group status
kubectl exec -n learnflow deployment/kafka -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group mastery-engine-group --describe

# Check DLQ topic
kubectl exec -n learnflow deployment/kafka -- \
  kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic mastery.dlq --from-beginning --max-messages 10

# View application logs for event processing
kubectl logs -n learnflow -l app=mastery-engine --tail=200 | grep "KAFKA"
```

### Common Problems

**Events in DLQ Topic**
- **Cause**: Invalid event schema or processing errors
- **Solution**: Check event validation in event_validator.py
- **Debug**: `kubectl logs -n learnflow -l app=mastery-engine | grep "DLQ"`

**Duplicate Processing**
- **Cause**: Idempotency check failing
- **Solution**: Verify Redis is storing event_ids correctly
- **Debug**: Check state_manager.py for `event:` key patterns

**Consumer Not Starting**
- **Cause**: Kafka connectivity or topic permissions
- **Solution**:
  ```bash
  # Check topic ACLs
  kafka-acls.sh --bootstrap-server localhost:9092 --list --topic mastery.events

  # Test connection
  kafka-topics.sh --bootstrap-server localhost:9092 --list
  ```

**Memory Leak**
- **Cause**: Not consuming events or event buffer overflow
- **Solution**: Check consumer configuration in kafka_consumer.py:
  ```python
  # Ensure proper batch size and polling
  consumer.poll(timeout_ms=1000)
  consumer.commit()  # After successful processing
  ```

---

## 5. Database/State Store Issues

### Symptoms
- Data not persisting across restarts
- State store errors on write
- Slow read operations
- Key collisions

### Diagnosis

```bash
# Check Redis keys
kubectl exec -n learnflow deployment/redis -- redis-cli KEYS "student:*" | head -20

# Monitor Redis operations
kubectl exec -n learnflow deployment/redis -- redis-cli --latency

# Check memory usage
kubectl exec -n learnflow deployment/redis -- redis-cli INFO memory
```

### Common Issues

**State Not Persisting**
```python
# Verify TTL is not too aggressive
# In state_manager.py, check default TTL settings:
# Student data: 90 days (GDPR compliance)
# Cache data: 1 hour
# Event checkpoints: 7 days

# Check if keys have expired
kubectl exec -n learnflow deployment/redis -- redis-cli TTL "student:123:mastery:2025-01-15"
```

**Key Pattern Issues**
```python
# Expected patterns from StateKeyPatterns class:
# student:{student_id}:mastery:{date}:{component}
# student:{student_id}:event:{event_id}
# prediction:{student_id}:cache
# batch:{batch_id}:status
```

**Performance Tuning**
- Use Redis pipelining for bulk operations (already implemented)
- Consider Redis clustering for > 1M keys
- Monitor key count: `kubectl exec -n learnflow deployment/redis -- redis-cli DBSIZE`

---

## 6. Security & Authentication Issues

### Symptoms
- 401 Unauthorized errors
- 403 Forbidden errors
- JWT validation failures
- Role-based access denial

### Diagnosis

```bash
# Test JWT validation
python -c "
import jwt
from src.security import SecurityManager
sm = SecurityManager(jwt_secret='your-secret')
try:
    decoded = sm.validate_jwt('your-token')
    print('Valid:', decoded)
except Exception as e:
    print('Invalid:', e)
"

# Check audit logs
kubectl logs -n learnflow -l app=mastery-engine | grep "AUDIT"
```

### Common Issues

**JWT Secret Mismatch**
```bash
# Ensure JWT_SECRET is consistent across services
echo $JWT_SECRET

# Should match between:
# - mastery-engine deployment
# - any service generating JWTs
# - any service validating JWTs
```

**Role Assignment Issues**
```python
# Verify roles in JWT payload:
# {"user_id": "123", "roles": ["student"], "exp": 1234567890}

# Role hierarchy:
# - admin: full access
# - teacher: cohort access, student-specific access
# - student: own data only
```

**Input Sanitization Blocking Valid Requests**
- **Solution**: Check sanitization rules in security.py
- **Test**: Use `/ready` endpoint to verify sanitization isn't too aggressive

---

## 7. Logging & Monitoring Issues

### Symptoms
- Missing logs
- Unstructured log output
- No correlation IDs in logs
- Performance metrics not showing

### Diagnosis

```bash
# Check log format (should be JSON in production)
kubectl logs -n learnflow -l app=mastery-engine --tail=20

# Verify correlation ID tracking
kubectl logs -n learnflow -l app=mastery-engine | grep "correlation_id"

# Check metrics endpoint
curl http://<service>/metrics | grep "mastery_engine"
```

### Configuration

**JSON Logging in Production**
```python
# In src/main.py, verify:
# LOG_LEVEL=INFO (or DEBUG for development)
# ENVIRONMENT=production triggers JSON format

# Check environment variables:
kubectl exec -n learnflow deployment/mastery-engine -- env | grep LOG_
```

**Missing Correlation IDs**
- Verify middleware order in main.py (security_headers_middleware must be first)
- Check all requests include X-Request-ID header

**Metrics Not Appearing**
- Ensure /metrics endpoint is being called (Prometheus scraping)
- Verify performance_metrics dict is being updated in middleware

---

## 8. Docker Issues

### Symptoms
- Build fails
- Container crashes on start
- "No such file or directory" errors
- Dependency issues in container

### Diagnosis

```bash
# Build with verbose output
docker build -t mastery-engine:latest . --no-cache --progress=plain 2>&1 | tee build.log

# Run container interactively
docker run -it --rm mastery-engine:latest /bin/sh

# Check running container logs
docker logs <container_id> --tail=50
```

### Common Issues

**Build Fails**
```dockerfile
# Check Dockerfile multi-stage build
# Stage 1: Builder should install all dev dependencies
# Stage 2: Runner should copy only necessary files

# Common fix: Ensure requirements.txt is in build context
# Check .dockerignore isn't excluding critical files
```

**Missing Dependencies**
```bash
# Test pip install locally
pip install -r requirements.txt --dry-run

# Check for platform-specific dependencies
# Some packages need system libraries (e.g., numpy, pandas)
```

**Container Crash on Start**
```bash
# Run with command override
docker run -it --rm mastery-engine:latest python -c "import src.main; print('Import OK')"

# Check environment variables are set
docker run -it --rm --env-file .env mastery-engine:latest env | grep JWT
```

---

## 9. Kubernetes Issues

### Symptoms
- Pods stuck in Pending/ContainerCreating
- CrashLoopBackOff errors
- ImagePullBackOff errors
- Readiness probe failures

### Diagnosis

```bash
# Check pod events
kubectl describe pod -n learnflow -l app=mastery-engine

# Check deployment status
kubectl rollout status deployment/mastery-engine -n learnflow --watch

# View full pod logs including startup
kubectl logs -n learnflow -l app=mastery-engine --previous  # logs from crashed container
```

### Common Issues

**ImagePullBackOff**
```bash
# Check image exists
kubectl get image

# Verify image name in deployment.yaml
# Should match: learnflow/mastery-engine:latest

# If using private registry, check secrets
kubectl get secrets -n learnflow | grep registry
```

**CrashLoopBackOff**
```bash
# Get previous logs
kubectl logs -n learnflow deployment/mastery-engine --previous

# Check resource limits
kubectl top pods -n learnflow -l app=mastery-engine

# Common cause: Memory limit too low
# Increase in deployment.yaml: memory: 512Mi
```

**Readiness Probe Failures**
```bash
# Check probe configuration
kubectl get deployment mastery-engine -n learnflow -o yaml | grep -A 10 readinessProbe

# Test readiness endpoint manually
kubectl exec -n learnflow deployment/mastery-engine -- curl -s http://localhost:8000/ready

# Common fixes:
# - Increase initialDelaySeconds
# - Check dependency health
# - Increase timeout threshold
```

---

## 10. Performance Optimization Checklist

### When to Scale Up
- ✅ CPU usage > 80% consistently
- ✅ Memory usage > 90%
- ✅ Response time P95 > 1s
- ✅ Kafka consumer lag > 1000 messages

### When to Scale Down
- ✅ CPU usage < 20% consistently
- ✅ Memory usage < 50%
- ✅ Zero traffic during off-hours (use HPA)

### Scale Commands
```bash
# Manual scale
kubectl scale deployment mastery-engine --replicas=3 -n learnflow

# Check HPA status (if configured)
kubectl get hpa -n learnflow

# View resource usage
kubectl top pods -n learnflow -l app=mastery-engine
```

---

## Emergency Procedures

### 1. Service Restart (Non-Destructive)
```bash
# Rolling restart (zero downtime)
kubectl rollout restart deployment/mastery-engine -n learnflow

# Watch progress
kubectl rollout status deployment/mastery-engine -n learnflow --watch
```

### 2. Emergency Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/mastery-engine -n learnflow

# Check previous revision
kubectl rollout history deployment/mastery-engine -n learnflow
```

### 3. Debug Mode (Development)
```bash
# Run with debug logging
kubectl set env deployment/mastery-engine LOG_LEVEL=DEBUG -n learnflow

# Port-forward for local testing
kubectl port-forward deployment/mastery-engine 8000:8000 -n learnflow
```

### 4. Data Recovery (State Store)
```bash
# Backup current state
kubectl exec -n learnflow deployment/redis -- redis-cli BGSAVE

# Export specific keys
kubectl exec -n learnflow deployment/redis -- redis-cli --scan --pattern "student:*" > student_keys.txt

# Restore (if needed)
kubectl exec -i -n learnflow deployment/redis -- redis-cli --pipe < backup_commands.txt
```

---

## Monitoring Dashboard Queries (Prometheus)

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Response time (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Kafka consumer lag
kafka_consumer_group_lag{group="mastery-engine-group"}

# Redis operation rate
rate(redis_commands_processed_total[5m])

# Memory usage per pod
container_memory_usage_bytes{pod=~"mastery-engine-.*"} / container_spec_memory_limit_bytes
```

---

## Contact & Escalation

**For emergencies**: Contact on-call engineer immediately
**Performance issues**: Check metrics dashboard first
**Data issues**: Verify Redis state before contacting team

**Slack channels**:
- #ops-mastery-engine (alerts and incidents)
- #dev-mastery-engine (technical questions)
- #data-platform (Kafka/Redis issues)

**Documentation**:
- API docs: `/docs` endpoint on each service
- Metrics: `/metrics` endpoint
- Health: `/ready` and `/health` endpoints

---

*This document is automatically generated and updated. Last built: 2026-01-15*