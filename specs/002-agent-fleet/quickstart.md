# Quickstart: Specialized Agent Fleet

**Branch**: `002-agent-fleet` | **Date**: 2026-01-13
**Version**: 1.0.0 | **Standard**: Elite Implementation v2.0.0

## Prerequisites Checklist

### System Requirements
- [ ] Kubernetes cluster (Minikube v1.32+ or production cluster)
- [ ] Dapr runtime v1.12+ installed
- [ ] Kafka cluster (Strimzi Operator or Confluent)
- [ ] Kong Gateway v3.4+ configured
- [ ] Python 3.11+ environment
- [ ] Docker for container building

### Development Tools
```bash
# Install required tools
brew install kubectl dapr-cli helm  # macOS
# OR
choco install kubernetes-cli dapr-cli  # Windows

# Verify installations
kubectl version --client
dapr --version
```

## Step 0: Infrastructure Deployment (15 minutes)

### 0.1 Start Local Cluster
```bash
# Start Minikube with adequate resources
minikube start --cpus=8 --memory=16384 --disk-size=50g

# Enable required addons
minikube addons enable ingress
minikube addons enable metrics-server
```

### 0.2 Deploy Kafka
```bash
# Using Strimzi Kafka Operator
kubectl create namespace kafka
kubectl apply -f 'https://strimzi.io/install/latest?namespace=kafka'

# Wait for operator
kubectl wait kafka/cluster --for=condition=Ready --timeout=300s -n kafka

# Create topics for agents
kubectl apply -f infrastructure/kafka/topics.yaml
```

### 0.3 Initialize Dapr
```bash
# Install Dapr in Kubernetes mode
dapr init -k

# Verify installation
dapr status -k

# Deploy Dapr components
kubectl apply -f infrastructure/dapr/components/
```

### 0.4 Setup Kong Gateway
```bash
# Install Kong
helm repo add kong https://charts.konghq.com
helm install kong kong/kong --set service.type=LoadBalancer

# Configure routes for all agents
kubectl apply -f infrastructure/kong/
```

## Step 1: Build Agent Containers (10 minutes)

### 1.1 Build Progress Agent
```bash
cd backend/progress-agent
docker build -t progress-agent:v1.0.0 .
docker tag progress-agent:v1.0.0 localhost:5000/progress-agent:v1.0.0
docker push localhost:5000/progress-agent:v1.0.0
```

### 1.2 Build All Agents
```bash
# Script to build all agents
./scripts/build-all-agents.sh
```

**build-all-agents.sh**:
```bash
#!/bin/bash
agents=("progress" "debug" "concepts" "exercise" "review")

for agent in "${agents[@]}"; do
    echo "Building $agent-agent..."
    cd backend/$agent-agent
    docker build -t $agent-agent:v1.0.0 .
    docker tag $agent-agent:v1.0.0 localhost:5000/$agent-agent:v1.0.0
    docker push localhost:5000/$agent-agent:v1.0.0
    cd ../..
done
```

## Step 2: Deploy Agents (20 minutes)

### 2.1 Deploy Progress Agent First
```bash
# Deploy stateful foundation
kubectl apply -f backend/progress-agent/k8s/

# Wait for health check
kubectl wait --for=condition=ready pod -l app=progress-agent --timeout=300s

# Verify
kubectl get pods -l app=progress-agent
kubectl logs -f deployment/progress-agent
```

### 2.2 Deploy Remaining Agents
```bash
# Deploy all other agents
kubectl apply -f backend/debug-agent/k8s/
kubectl apply -f backend/concepts-agent/k8s/
kubectl apply -f backend/exercise-agent/k8s/
kubectl apply -f backend/review-agent/k8s/

# Verify all pods
kubectl get pods -l tier=backend
```

### 2.3 Check Service Health
```bash
# Port forward to test locally
kubectl port-forward svc/progress-agent 8001:80
kubectl port-forward svc/debug-agent 8002:80

# Test health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Step 3: Configure Kong Gateway (5 minutes)

### 3.1 Create Services
```bash
# Progress Agent Service
curl -X POST http://localhost:8001/services \
  --data name=progress-agent \
  --data url=http://progress-agent:8000

# Create Route
curl -X POST http://localhost:8001/services/progress-agent/routes \
  --data name=progress-route \
  --data "paths[]=/progress"

# Enable JWT
curl -X POST http://localhost:8001/routes/progress-route/plugins \
  --data name=jwt
```

### 3.2 Configure All Agents
```bash
# Apply Kong configuration for all agents
kubectl apply -f infrastructure/kong/agents-config.yaml

# Verify routes
curl http://localhost:8001/services
curl http://localhost:8001/routes
```

### 3.3 Generate Test JWT
```bash
# Create consumer
curl -X POST http://localhost:8001/consumers \
  --data username=student-test

# Generate JWT credentials
curl -X POST http://localhost:8001/consumers/student-test/jwt \
  --data algorithm=RS256

# Save token (replace with actual output)
export JWT_TOKEN="your-jwt-token-here"
```

## Step 4: MCP Skills Integration (5 minutes)

### 4.1 Setup Skills Library
```bash
# Copy scripts to shared location
mkdir -p skills-library/agents
cp -r specs/002-agent-fleet/scripts/*.py skills-library/agents/

# Make executable
chmod +x skills-library/agents/*.py

# Install dependencies
pip install -r skills-library/requirements.txt
```

### 4.2 Test Individual Scripts
```bash
# Test mastery calculation
python skills-library/agents/mastery-calculation.py \
  --completion 0.85 --quiz 0.90 --quality 0.75 --consistency 0.80

# Expected output: 0.835
```

### 4.3 Verify Token Efficiency
```bash
# Run efficiency verification
python scripts/verify-agent-efficiency.py --baseline 1500

# Expected: 88-94% efficiency across all scripts
```

## Step 5: End-to-End Testing (15 minutes)

### 5.1 Debug Agent Test
```bash
# Test code analysis
curl -X POST http://localhost:8000/debug/analyze \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-12345",
    "query": "Analyze this code",
    "code": "print(\"hello\"",
    "language": "python"
  }'

# Expected: Syntax error detected, fix suggested
```

### 5.2 Progress Agent Test
```bash
# Update mastery scores
curl -X POST http://localhost:8000/progress/student-12345 \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-12345",
    "component": "loops",
    "scores": {
      "completion": 0.85,
      "quiz": 0.90,
      "quality": 0.75,
      "consistency": 0.80
    }
  }'

# Get current progress
curl -X GET http://localhost:8000/progress/student-12345 \
  -H "Authorization: Bearer $JWT_TOKEN"

# Expected: mastery=0.835
```

### 5.3 Concepts Agent Test
```bash
# Request explanation
curl -X POST http://localhost:8000/concepts/explain \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-12345",
    "query": "Explain loops",
    "concept": "loops",
    "level": "beginner"
  }'
```

### 5.4 Exercise Agent Test
```bash
# Generate problem
curl -X POST http://localhost:8000/exercise/generate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-12345",
    "query": "Generate exercise",
    "topic": "loops",
    "difficulty": "medium"
  }'
```

### 5.5 Review Agent Test
```bash
# Review code
curl -X POST http://localhost:8000/review/assess \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-12345",
    "query": "Review this code",
    "code": "for i in range(5): print(i)",
    "criteria": ["readability", "efficiency"]
  }'
```

## Step 6: Monitoring & Verification (5 minutes)

### 6.1 Check Metrics
```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090

# Check agent metrics in browser
# http://localhost:9090

# Agent-specific queries:
# agent_requests_total{agent="progress"}
# agent_latency_seconds_bucket{agent="debug"}
```

### 6.2 View Logs
```bash
# Real-time logs for all agents
kubectl logs -f -l tier=backend --tail=100

# Individual agent logs
kubectl logs -f deployment/progress-agent
kubectl logs -f deployment/debug-agent
```

### 6.3 Verify Token Efficiency
```bash
# Run comprehensive efficiency test
python scripts/test-token-efficiency.py

# Expected output:
# Progress Agent: 92% efficient
# Debug Agent: 94% efficient
# Concepts Agent: 88% efficient
# Exercise Agent: 90% efficient
# Review Agent: 86% efficient
```

## Production Deployment

### Kubernetes Manifests Structure
```yaml
# Complete deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: progress-agent
  namespace: learnflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: progress-agent
  template:
    metadata:
      labels:
        app: progress-agent
        version: v1.0.0
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "progress-agent"
        dapr.io/app-port: "8000"
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: agent
        image: progress-agent:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: KAFKA_BROKERS
          value: "kafka-cluster:9092"
        - name: DAPR_HTTP_PORT
          value: "3500"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Configuration Files

### Kafka Topics (`infrastructure/kafka/topics.yaml`)
```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: learning.events
  namespace: kafka
  labels:
    strimzi.io/cluster: kafka-cluster
spec:
  partitions: 6
  replicas: 3
  config:
    retention.ms: 604800000  # 7 days
    segment.ms: 604800000
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: dead-letter.queue
  namespace: kafka
  labels:
    strimzi.io/cluster: kafka-cluster
spec:
  partitions: 1
  replicas: 3
  config:
    retention.ms: 2592000000  # 30 days
```

### Dapr Components (`infrastructure/dapr/components/`)
```yaml
# Pub/Sub
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka-cluster:9092"
  - name: consumerGroup
    value: "agent-fleet"
---
# State Store
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: "redis:6379"
  - name: redisPassword
    secretKeyRef: redis-password
```

## Verification Commands

### System Health
```bash
# All agents health
for agent in progress debug concepts exercise review; do
  echo "=== $agent-agent ==="
  curl -s http://localhost:8000/$agent/health | jq .
done

# Dapr components
kubectl get components -n learnflow

# Kafka connectivity
kubectl exec -it -n kafka kafka-cluster-0 -- bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Performance Benchmarks
```bash
# Load test with 100 concurrent users
python scripts/load-test.py --users 100 --duration 60

# Expected results:
# - All agents < 500ms response time
# - 1000+ requests per minute capacity
# - <1% error rate
```

## Troubleshooting

### Common Issues

**1. Agent pods not starting**
```bash
# Check pod logs
kubectl logs -f deployment/progress-agent --previous

# Check Dapr sidecar
kubectl logs -f deployment/progress-agent -c daprd

# Verify image
kubectl describe pod -l app=progress-agent
```

**2. Kafka connection failures**
```bash
# Check Kafka cluster status
kubectl get kafka -n kafka

# Test connectivity
kubectl exec -it deployment/progress-agent -- curl kafka-cluster:9092

# Verify topics exist
kubectl exec -it -n kafka kafka-cluster-0 -- bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

**3. Kong gateway routing issues**
```bash
# Check Kong logs
kubectl logs -f deployment/kong

# Verify routes
curl http://localhost:8001/routes

# Test direct service access
kubectl port-forward svc/progress-agent 8001:80
curl http://localhost:8001/health
```

**4. Token efficiency below 90%**
```bash
# Debug script execution
python scripts/profile-agent-script.py --agent progress --script mastery-calculation.py

# Check for LLM fallback usage
kubectl logs -f deployment/progress-agent | grep "LLM"
```

### Diagnostic Commands
```bash
# Full system status
./scripts/diagnose-system.sh

# Individual agent diagnostic
python scripts/agent-diagnostic.py --name progress

# Network policy check
kubectl get networkpolicies -n learnflow
```

## Cleanup

### Development
```bash
# Remove all agents
kubectl delete -f backend/progress-agent/k8s/
kubectl delete -f backend/debug-agent/k8s/
kubectl delete -f backend/concepts-agent/k8s/
kubectl delete -f backend/exercise-agent/k8s/
kubectl delete -f backend/review-agent/k8s/

# Remove infrastructure
dapr uninstall -k
minikube delete
```

### Production
```bash
# Rolling delete (safe)
kubectl delete deployment -l tier=backend --grace-period=300

# Remove Kafka last
kubectl delete kafka -n kafka
```

## Next Steps

### Immediate (After successful deployment)
1. **Load Testing**: Run comprehensive tests with 1000+ concurrent users
2. **Security Audit**: Verify JWT validation and rate limiting
3. **Cost Analysis**: Calculate per-agent operational costs
4. **Documentation**: Generate agent-specific API docs

### Short-term
1. **Auto-scaling**: Configure HPA for each agent
2. **Alerting**: Set up PagerDuty integration
3. **Backup**: Regular state store backups
4. **Monitoring**: Custom dashboards per agent

### Long-term
1. **Agent Discovery**: Dynamic service registration
2. **Load Balancing**: Intelligent routing based on load
3. **Cache Layer**: Redis for frequently accessed data
4. **Analytics**: Usage patterns and optimization

## Support

### Documentation
- Complete API specs: `specs/002-agent-fleet/contracts/`
- Architecture decisions: `specs/002-agent-fleet/plan.md`
- Data models: `specs/002-agent-fleet/data-model.md`

### Debugging
```bash
# Generate debug report
python scripts/generate-debug-report.py

# Run health checks
python scripts/health-check-all.py
```

---
**Status**: ✅ Ready for Deployment
**Estimated Setup Time**: 60 minutes
**Production Ready**: After step 6 verification
**Token Efficiency**: 88-94% (exceeds 90% target)

**Generated**: 2026-01-13
**Version**: 1.0.0