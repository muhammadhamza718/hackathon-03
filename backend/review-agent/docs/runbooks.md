# Review Agent Runbooks
**Elite Implementation Standard v2.0.0**

## Overview

This document provides operational runbooks for the Review Agent microservice. All procedures follow Elite Implementation Standards and include safety checks and rollback procedures.

---

## 🔧 Common Operations

### 1. Local Development Setup

#### Prerequisites
- Python 3.11+
- pip
- Git

#### Setup Steps
```bash
# Clone repository
git clone <repository>
cd learnflow/backend/review-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_basic.py

# Start development server
cd src
python -m uvicorn main:app --reload --port 8004
```

**Health Check**: `curl http://localhost:8004/health`

#### Troubleshooting
- **Port already in use**: Change port with `--port 8005`
- **Missing dependencies**: Run `pip install --upgrade -r requirements.txt`
- **Import errors**: Ensure `PYTHONPATH` includes `src/`

---

### 2. Docker Deployment

#### Build Image
```bash
# From project root
cd backend/review-agent

# Build with tag
docker build -t learnflow/review-agent:latest .

# Verify build
docker images | grep review-agent
```

#### Run Container
```bash
# Basic run
docker run -p 8004:8004 learnflow/review-agent:latest

# With environment variables
docker run -p 8004:8004 \
  -e KAFKA_BROKER=kafka:9092 \
  -e JWT_SECRET=your-secret \
  learnflow/review-agent:latest

# With volume for logs (optional)
docker run -p 8004:8004 \
  -v /var/log/review-agent:/app/logs \
  learnflow/review-agent:latest
```

**Health Check**: `curl http://localhost:8004/health`

#### Debug Container
```bash
# Shell access
docker exec -it <container-id> /bin/bash

# View logs
docker logs <container-id> -f

# Check processes
docker top <container-id>
```

#### Troubleshooting
- **Build fails**: Check Dockerfile syntax and dependencies
- **Container exits immediately**: Check logs with `docker logs`
- **Port conflicts**: Use different port mapping `-p 8005:8004`
- **Missing permissions**: Ensure Docker user has access to build context

---

### 3. Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Dapr installed in cluster
- Kafka cluster available

#### Deploy Review Agent
```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Apply service
kubectl apply -f k8s/service.yaml

# Verify pods
kubectl get pods -n learnflow -l app=review-agent

# Check logs
kubectl logs -n learnflow deployment/review-agent -f
```

#### Verify Deployment
```bash
# Check pod status
kubectl get pods -n learnflow

# Check service
kubectl get svc -n learnflow review-agent

# Port forward for local testing
kubectl port-forward -n learnflow svc/review-agent 8004:8004

# Test health endpoint
curl http://localhost:8004/health
```

#### Update Deployment
```bash
# Build new image
docker build -t learnflow/review-agent:v1.1.0 .

# Push to registry
docker push learnflow/review-agent:v1.1.0

# Update image in deployment
kubectl set image deployment/review-agent \
  review-agent=learnflow/review-agent:v1.1.0 \
  -n learnflow

# Rolling update status
kubectl rollout status deployment/review-agent -n learnflow
```

#### Rollback
```bash
# Check rollout history
kubectl rollout history deployment/review-agent -n learnflow

# Rollback to previous version
kubectl rollout undo deployment/review-agent -n learnflow

# Or rollback to specific revision
kubectl rollout undo deployment/review-agent --to-revision=2 -n learnflow
```

#### Troubleshooting
- **Pod not starting**: `kubectl describe pod <pod-name> -n learnflow`
- **CrashLoopBackOff**: `kubectl logs <pod-name> -n learnflow --previous`
- **Image pull errors**: Verify registry credentials and image name
- **Dapr not enabled**: Check Dapr sidecar injector is running
- **Kafka unreachable**: Verify network policies and service discovery

---

### 4. Dapr Integration Management

#### Verify Dapr Sidecar
```bash
# Check if sidecar is injected
kubectl get pods -n learnflow -l app=review-agent -o jsonpath='{.items[0].spec.containers[*].name}'

# Should show: review-agent Dapr
```

#### Check Dapr Logs
```bash
# Review agent logs
kubectl logs -n learnflow deployment/review-agent -c review-agent

# Dapr sidecar logs
kubectl logs -n learnflow deployment/review-agent -c daprd
```

#### Invoke Service via Dapr
```bash
# Using Dapr CLI
dapr invoke --app-id review-agent --method process --payload '{"intent":"quality_assessment"}'

# Using curl via Dapr
curl -X POST http://localhost:3500/v1.0/invoke/review-agent/method/process \
  -H "Content-Type: application/json" \
  -d '{"intent":"quality_assessment","student_code":"x=1"}'
```

#### Troubleshooting
- **Service not discovered**: Check Dapr annotation in deployment
- **Method not found**: Verify endpoint exists in FastAPI app
- **Timeout issues**: Check app health and readiness

---

### 5. Kafka Event Processing

#### Verify Kafka Connection
```bash
# From within cluster pod
kubectl exec -it <review-agent-pod> -n learnflow -- /bin/bash

# Test connectivity
nc -zv kafka-cluster 9092

# List topics
kafka-topics --bootstrap-server kafka-cluster:9092 --list
```

#### Monitor Events
```bash
# Consumer group status
kafka-consumer-groups --bootstrap-server kafka-cluster:9092 --group review-agent --describe

# Tail topic events
kafka-console-consumer --bootstrap-server kafka-cluster:9092 \
  --topic review.requests --from-beginning
```

#### Enable/Disable Kafka
```bash
# Disable (for debugging)
kubectl set env deployment/review-agent KAFKA_ENABLED=false -n learnflow

# Enable
kubectl set env deployment/review-agent KAFKA_ENABLED=true -n learnflow
```

#### Troubleshooting
- **Connection refused**: Check Kafka broker health and network policies
- **Topic not found**: Auto-create may be disabled, create topic manually
- **Authentication failed**: Verify credentials in secrets
- **Consumer lag**: Scale up review-agent replicas

---

### 6. Security Operations

#### Rotate JWT Secret
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# Update secret
kubectl create secret generic review-agent-secrets \
  --from-literal=jwt-secret=$NEW_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/review-agent -n learnflow
```

#### Security Audit
```bash
# Check security context
kubectl get pod <pod-name> -n learnflow -o yaml | grep securityContext

# Verify read-only filesystem
kubectl exec -it <pod-name> -n learnflow -- touch /tmp/test  # Should fail

# Check non-root user
kubectl exec -it <pod-name> -n learnflow -- id
```

#### Input Sanitization Testing
```bash
# Test SQL injection protection
curl -X POST http://localhost:8004/review/assess \
  -H "Authorization: Bearer test-token" \
  -d '{"student_code":"SELECT * FROM users --","problem_context":{}}'

# Should return 400 error
```

#### Rate Limit Testing
```bash
# Rapid requests to test limit
for i in {1..15}; do
  curl -s http://localhost:8004/health > /dev/null
  echo "Request $i"
done

# Should see rate limiting after threshold
```

---

### 7. Monitoring & Observability

#### Health Monitoring
```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8004/health | jq'

# Get detailed metrics
curl http://localhost:8004/ready
curl http://localhost:8004/
```

#### Log Aggregation
```bash
# Follow logs with timestamp
kubectl logs -n learnflow deployment/review-agent -f --timestamps

# Filter for errors
kubectl logs -n learnflow deployment/review-agent | grep -i error

# Last 100 lines with context
kubectl logs -n learnflow deployment/review-agent --tail=100
```

#### Performance Metrics
```bash
# Resource usage
kubectl top pods -n learnflow -l app=review-agent

# Detailed resource metrics
kubectl describe pod <pod-name> -n learnflow | grep -A 10 "Containers:"

# Prometheus metrics (if enabled)
curl http://localhost:8004/metrics
```

---

### 8. Backup & Recovery

#### Backup Configuration
```bash
# Export deployment
kubectl get deployment review-agent -n learnflow -o yaml > backup-deployment.yaml

# Export service
kubectl get svc review-agent -n learnflow -o yaml > backup-service.yaml

# Export config
kubectl get configmap -n learnflow > backup-config.yaml
```

#### Recovery
```bash
# Apply from backup
kubectl apply -f backup-deployment.yaml
kubectl apply -f backup-service.yaml

# Verify restoration
kubectl get all -n learnflow -l app=review-agent
```

---

## 🚨 Incident Response

### Service Down

**Detection**: Health check fails
**Impact**: Student assessments unavailable

**Response**:
1. **Immediate** (0-5 min)
   ```bash
   kubectl get pods -n learnflow -l app=review-agent
   kubectl logs -n learnflow deployment/review-agent --tail=50
   ```

2. **Investigation** (5-15 min)
   ```bash
   kubectl describe pod <pod-name> -n learnflow
   kubectl get events -n learnflow --sort-by='.lastTimestamp'
   ```

3. **Mitigation** (15-30 min)
   ```bash
   # If pod crash: Check resource limits
   kubectl get pod <pod-name> -n learnflow -o jsonpath='{.spec.containers[0].resources}'

   # If image issues: Pull locally and retag
   docker pull learnflow/review-agent:latest
   docker tag learnflow/review-agent:latest learnflow/review-agent:backup
   ```

4. **Recovery** (30-60 min)
   ```bash
   # Rollback to known good state
   kubectl rollout undo deployment/review-agent -n learnflow

   # Scale down/up to force redeployment
   kubectl scale deployment/review-agent --replicas=0 -n learnflow
   kubectl scale deployment/review-agent --replicas=2 -n learnflow
   ```

### High Memory Usage

**Detection**: `kubectl top pods` shows >80% memory limit

**Response**:
1. Check memory configuration:
   ```bash
   kubectl get deployment review-agent -n learnflow -o yaml | grep -A 5 memory
   ```

2. Analyze memory usage:
   ```bash
   kubectl exec -it <pod-name> -n learnflow -- /bin/bash
   top
   ```

3. Increase limits:
   ```bash
   kubectl patch deployment review-agent -n learnflow --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "1Gi"}]'
   ```

### Kafka Processing Lag

**Detection**: Consumer lag growing

**Response**:
1. Check consumer group:
   ```bash
   kafka-consumer-groups --bootstrap-server kafka-cluster:9092 --group review-agent --describe
   ```

2. Scale up pods:
   ```bash
   kubectl scale deployment review-agent --replicas=4 -n learnflow
   ```

3. Check event processing:
   ```bash
   kubectl logs -n learnflow deployment/review-agent -f | grep "Processing"
   ```

---

## 📋 Maintenance Windows

### Regular Maintenance Tasks

**Daily**:
- Health check verification
- Log review for errors
- Resource usage monitoring

**Weekly**:
- Security patch updates
- Dependency version checks
- Backup verification
- Performance metric review

**Monthly**:
- Full security audit
- Disaster recovery drill
- Capacity planning review
- Documentation updates

### Update Procedure

**Security Updates**:
```bash
# Update dependencies
pip list --outdated
pip-review --auto

# Test changes
python -m pytest tests/unit/ -v

# Deploy to staging
# Run integration tests
# Deploy to production
```

**Application Updates**:
```bash
# 1. Version control
git tag v1.1.0
git push origin v1.1.0

# 2. Build and test
docker build -t learnflow/review-agent:v1.1.0 .
python -m pytest tests/

# 3. Deploy to staging
kubectl set image deployment/review-agent review-agent=learnflow/review-agent:v1.1.0 --namespace=staging

# 4. Verify staging
# ... testing ...

# 5. Deploy to production
kubectl set image deployment/review-agent review-agent=learnflow/review-agent:v1.1.0 --namespace=learnflow

# 6. Monitor
kubectl rollout status deployment/review-agent -n learnflow --watch
```

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | 8004 | HTTP port |
| `KAFKA_ENABLED` | No | true | Enable Kafka consumer |
| `KAFKA_BROKER` | If enabled | localhost:9092 | Kafka broker address |
| `KAFKA_TOPIC` | No | review.requests | Kafka topic name |
| `JWT_SECRET` | Yes | - | JWT signing secret |
| `LOG_LEVEL` | No | INFO | Logging level |

### Resource Limits

**Development**:
```yaml
requests:
  memory: "128Mi"
  cpu: "100m"
limits:
  memory: "256Mi"
  cpu: "250m"
```

**Production**:
```yaml
requests:
  memory: "256Mi"
  cpu: "250m"
limits:
  memory: "512Mi"
  cpu: "500m"
```

---

## 🆘 Support Escalation

### Level 1: Application Team
- Response: 15 minutes
- Contact: #review-agent-team
- Scope: Application logs, configuration, basic troubleshooting

### Level 2: Platform Team
- Response: 1 hour
- Contact: #platform-team
- Scope: Kubernetes, Dapr, networking, infrastructure

### Level 3: SRE/DevOps
- Response: 4 hours
- Contact: #sre-oncall
- Scope: Cluster health, security incidents, disaster recovery

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-14
**Owner**: LearnFlow Platform Team
**Next Review**: 2026-02-14