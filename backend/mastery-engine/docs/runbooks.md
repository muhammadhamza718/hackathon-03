# Mastery Engine Runbooks
**Elite Implementation Standard v2.0.0**

## Overview

This document provides operational procedures for the Mastery Engine microservice.

## Common Operations

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start Dapr
dapr run --app-id mastery-engine --app-port 8005 --dapr-http-port 3500

# Start service
cd src && uvicorn main:app --reload --port 8005

# Health check
curl http://localhost:8005/health
```

### Docker Deployment
```bash
# Build
docker build -t learnflow/mastery-engine:latest .

# Run
docker run -p 8005:8005 learnflow/mastery-engine:latest
```

### Kubernetes Deployment
```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n learnflow -l app=mastery-engine

# View logs
kubectl logs -n learnflow deployment/mastery-engine -f
```

## Health Checks

### Service Health
```bash
# Basic health
curl http://localhost:8005/health

# Full readiness (checks dependencies)
curl http://localhost:8005/ready

# Metrics endpoint
curl http://localhost:8005/metrics

# Service info
curl http://localhost:8005/
```

### Dapr Integration
```bash
# Check Dapr sidecar
kubectl logs -n learnflow deployment/mastery-engine -c daprd

# Invoke service via Dapr
curl -X POST http://localhost:3500/v1.0/invoke/mastery-engine/method/process \
  -H "Content-Type: application/json" \
  -d '{"intent": "mastery_calculation", "payload": {"student_id": "test"}}'
```

### Kafka Monitoring
```bash
# List topics
kafka-topics --bootstrap-server kafka-cluster:9092 --list

# Consumer group status
kafka-consumer-groups --bootstrap-server kafka-cluster:9092 --group mastery-engine-v1 --describe

# Monitor topic
kafka-console-consumer --bootstrap-server kafka-cluster:9092 \
  --topic mastery.requests --from-beginning
```

### Redis Monitoring
```bash
# Check keys
redis-cli KEYS "student:*" | head -20

# Memory usage
redis-cli INFO memory

# Connection test
redis-cli PING
```

## Incident Response

### Service Down
1. **Check pod status**
   ```bash
   kubectl get pods -n learnflow -l app=mastery-engine
   kubectl describe pod -n learnflow <pod-name>
   ```

2. **Check logs**
   ```bash
   kubectl logs -n learnflow deployment/mastery-engine --tail=50
   kubectl logs -n learnflow deployment/mastery-engine -c daprd
   ```

3. **Check dependencies**
   ```bash
   # Redis
   kubectl exec -it <redis-pod> -- redis-cli PING

   # Kafka
   kafka-topics --bootstrap-server kafka-cluster:9092 --list

   # Dapr
   kubectl get pods -n dapr-system
   ```

4. **Emergency rollback**
   ```bash
   kubectl rollout undo deployment/mastery-engine -n learnflow
   ```

### High Memory Usage
1. **Check current usage**
   ```bash
   kubectl top pods -n learnflow -l app=mastery-engine
   ```

2. **Analyze memory**
   ```bash
   kubectl exec -it <pod-name> -- /bin/bash
   top
   ps aux --sort=-%mem
   ```

3. **Immediate mitigation**
   ```bash
   # Increase limits
   kubectl patch deployment mastery-engine -n learnflow --type='json' \
     -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "512Mi"}]'
   ```

### Kafka Processing Lag
1. **Check consumer lag**
   ```bash
   kafka-consumer-groups --bootstrap-server kafka-cluster:9092 \
     --group mastery-engine-v1 --describe
   ```

2. **Scale consumers**
   ```bash
   kubectl scale deployment mastery-engine --replicas=4 -n learnflow
   ```

3. **Check DLQ**
   ```bash
   kafka-console-consumer --bootstrap-server kafka-cluster:9092 \
     --topic mastery.dlq --from-beginning
   ```

## Security Operations

### JWT Secret Rotation
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# Update secret
kubectl create secret generic mastery-engine-secrets \
  --from-literal=JWT_SECRET=$NEW_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods
kubectl rollout restart deployment/mastery-engine -n learnflow
```

### Security Audit
```bash
# Check security context
kubectl get pod <pod-name> -n learnflow -o yaml | grep securityContext

# Verify read-only filesystem
kubectl exec -it <pod-name> -n learnflow -- touch /tmp/test  # Should fail

# Check non-root user
kubectl exec -it <pod-name> -n learnflow -- id
```

### Input Sanitization Test
```bash
# SQL injection test
curl -X POST http://localhost:8005/mastery/query \
  -H "Authorization: Bearer test-token" \
  -d '{"student_id":"test","components":{"completion":0.8,"quiz":0.9,"quality":0.85,"consistency":0.82}}'

# Should validate properly
```

## Performance Operations

### Load Testing
```bash
# Install locust
pip install locust

# Run test
locust -f tests/load/test_load.py --host=http://localhost:8005
```

### Metrics Monitoring
```bash
# Watch metrics
watch -n 5 'curl -s http://localhost:8005/metrics | grep -E "(mastery_calculation|http_request)"'

# Prometheus queries
# rate(http_requests_total[5m])
# rate(mastery_calculation_duration_seconds_sum[5m])
# mastery_engine_memory_usage_bytes
```

### Connection Pooling
```bash
# Check Redis connections
redis-cli CLIENT LIST | wc -l

# Check Kafka consumers
kafka-consumer-groups --bootstrap-server kafka-cluster:9092 \
  --group mastery-engine-v1 --describe
```

## Maintenance Windows

### Regular Maintenance
**Daily:**
- Health check verification
- Log review for errors
- Resource usage monitoring

**Weekly:**
- Security patch updates
- Dependency version checks
- Backup verification

**Monthly:**
- Full security audit
- Disaster recovery drill
- Capacity planning review

### Update Procedure
```bash
# 1. Version control
git tag v1.1.0
git push origin v1.1.0

# 2. Build and test
docker build -t learnflow/mastery-engine:v1.1.0 .
python -m pytest tests/

# 3. Deploy to staging
kubectl set image deployment/mastery-engine \
  mastery-engine=learnflow/mastery-engine:v1.1.0 \
  --namespace=staging

# 4. Verify staging
# ... testing ...

# 5. Deploy to production
kubectl set image deployment/mastery-engine \
  mastery-engine=learnflow/mastery-engine:v1.1.0 \
  --namespace=learnflow

# 6. Monitor rollout
kubectl rollout status deployment/mastery-engine -n learnflow --watch
```

## Troubleshooting

### Common Issues
1. **Dapr connection failures**
   - Check sidecar injection
   - Verify Dapr components
   - Review network policies

2. **Kafka connection issues**
   - Check broker health
   - Verify topic existence
   - Confirm network connectivity

3. **Redis timeout**
   - Check Redis cluster health
   - Verify connection pool settings
   - Review network latency

4. **JWT validation errors**
   - Verify secret configuration
   - Check token expiration
   - Validate algorithm matches

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Trace requests
export TRACE_ENABLED=true

# Run with verbose output
uvicorn main:app --reload --log-level debug
```

## Support Escalation

### Level 1: Application Team
- Response: 15 minutes
- Scope: Application logs, configuration, basic troubleshooting
- Contact: #mastery-engine-team

### Level 2: Platform Team
- Response: 1 hour
- Scope: Kubernetes, Dapr, networking, infrastructure
- Contact: #platform-team

### Level 3: SRE/DevOps
- Response: 4 hours
- Scope: Cluster health, security incidents, disaster recovery
- Contact: #sre-oncall

---
**Document Version**: 1.0.0
**Last Updated**: 2026-01-14
**Owner**: LearnFlow Platform Team
**Next Review**: 2026-02-14