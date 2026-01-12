# LearnFlow Quickstart Guide

**Feature**: `001-learnflow-architecture`
**Date**: 2025-01-11
**Purpose**: Phase 1 deployment and local development setup

## Prerequisites

### Required Tools
- **Docker Desktop** (with Kubernetes enabled)
- **Minikube** (for local K8s development)
- **kubectl** (Kubernetes CLI)
- **dapr CLI** (Dapr command-line tools)
- **Python 3.11+** and **Node.js 18+**
- **Git** (for repository management)

### Verify Installation
```bash
# Check versions
docker --version
minikube version
kubectl version --client
dapr --version
python --version
node --version
```

## Phase 1: Infrastructure Deployment

### Step 1: Start Minikube Cluster
```bash
# Start Minikube with adequate resources
minikube start --cpus=6 --memory=8192 --driver=docker

# Verify cluster status
kubectl cluster-info
kubectl get nodes
```

### Step 2: Deploy Dapr Runtime
```bash
# Initialize Dapr in Kubernetes mode
dapr init -k

# Verify Dapr installation
kubectl get pods -n dapr-system
dapr status -k
```

### Step 3: Deploy Kafka Cluster
Using the `kafka-k8s-setup` Skill from the Skills Library:
```bash
# Navigate to skills directory
cd skills-library/kafka-k8s-setup

# Execute the skill (agent-generated)
./deploy-kafka.py --cluster-name learnflow --partitions 12 --replication 3

# Monitor deployment
kubectl get pods -l app=kafka
kubectl logs -f kafka-0
```

### Step 4: Deploy PostgreSQL
Using the `postgres-k8s-setup` Skill:
```bash
cd skills-library/postgres-k8s-setup

./deploy-postgres.py --db-name learnflow --storage 10Gi

# Verify
kubectl get pods -l app=postgres
```

### Step 5: Configure Dapr Components
```bash
# Apply Dapr component configurations
kubectl apply -f infrastructure/dapr/components.yaml

# Verify components
kubectl get components -n default
```

## Phase 2: Schema and Topic Setup

### Step 1: Create Kafka Topics
```bash
cd skills-library/kafka-k8s-setup

./create-topics.py --topics learning.events,dead-letter.queue --partitions 12,6
```

### Step 2: Validate Schema
```bash
cd skills-library/schema-validation

./validate-schemas.py --schema-file contracts/kafka-schemas.yaml

# Test StudentProgress event schema
./test-event-validation.py --type StudentProgressEvent
```

## Phase 3: Local Development Setup

### 1. Frontend (Next.js)

```bash
# Navigate to frontend
cd learnflow-app/frontend

# Install dependencies
npm install

# Set environment variables
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXTAUTH_SECRET=dev-secret-key-change-in-production
EOF

# Start development server
npm run dev

# Verify at http://localhost:3000
```

### 2. Backend Services

#### Triage Service
```bash
cd learnflow-app/backend/triage-service

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment
export DAPR_HTTP_PORT=3500
export DAPR_GRPC_PORT=50001

# Run with Dapr sidecar
dapr run --app-id triage-service --app-port 8001 -- python main.py
```

#### Specialized Agents (Example: Debug Agent)
```bash
cd learnflow-app/backend/debug-agent

# Install and run
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

dapr run --app-id debug-agent --app-port 8002 -- python main.py
```

#### Sandbox Service
```bash
cd learnflow-app/backend/sandbox-service

# Note: Sandbox runs in isolated containers
dapr run --app-id sandbox-service --app-port 8006 -- python main.py
```

### 3. Dapr Dashboard (Optional)
```bash
dapr dashboard -k
# Access at http://localhost:8080
```

## Phase 4: Testing the Complete Flow

### Test 1: Schema Validation
```bash
cd skills-library/schema-validation

python test-validation.py --student-id student_123e4567-e89b-12d3-a456-426614174000 \
  --exercise-id ex_python_fibonacci --agent debug
```

### Test 2: Triage Routing
```bash
curl -X POST http://localhost:3500/v1.0/invoke/triage-service/method/route \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
    "query": "My code causes stack overflow",
    "idempotency_key": "abc123def456abc123def456abc123de"
  }'
```

### Test 3: Sandbox Execution
```bash
curl -X POST http://localhost:3500/v1.0/invoke/sandbox-service/method/execute/python \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)\nprint(fib(10))",
    "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
    "timeout_ms": 5000
  }'
```

### Test 4: Mastery Calculation
```bash
curl -X POST http://localhost:3500/v1.0/invoke/progress-agent/method/mastery/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
    "events": [
      {
        "student_id": "student_123e4567-e89b-12d3-a456-426614174000",
        "exercise_id": "ex_python_fibonacci",
        "completion_score": 0.75,
        "quiz_score": 0.80,
        "quality_score": 0.90,
        "consistency_score": 0.85,
        "timestamp": "2025-01-11T14:30:00Z",
        "agent_source": "debug"
      }
    ]
  }'
```

## Phase 5: Token Efficiency Benchmarking

### Benchmark Script
```bash
cd skills-library/benchmark

# Run token efficiency tests
python benchmark-token-efficiency.py --all

# Expected results:
# - Triage routing: 85% reduction
# - Mastery calculation: 92% reduction
# - Code execution: 88% reduction
```

### Manual Verification
```bash
# Compare context window usage
python benchmark-vs-manual.py --script triage/intent-detection.py
```

## Troubleshooting

### Common Issues

**Kafka pods not starting**
```bash
kubectl describe pod kafka-0
kubectl logs kafka-0
# May need more resources: minikube stop && minikube start --cpus=8 --memory=12288
```

**Dapr component not found**
```bash
kubectl get components
# If missing: kubectl apply -f infrastructure/dapr/components.yaml
```

**Port conflicts**
```bash
# Kill processes on required ports
lsof -ti:3000,8001,8002,8006 | xargs kill -9
```

**Sandbox execution fails**
```bash
# Check sandbox logs
kubectl logs -f deployment/sandbox-service

# Verify container isolation
kubectl exec -it deployment/sandbox-service -- ps aux
```

### Debug Commands
```bash
# View Kafka messages
kubectl exec -it kafka-0 -- kafka-console-consumer --topic learning.events --from-beginning

# Dapr service invocation logs
dapr run --app-id test-client -- python -c "
import requests
print(requests.get('http://localhost:3500/v1.0/invoke/triage-service/method/health').text)
"

# Kubernetes port forwarding (for external access)
kubectl port-forward service/nextjs-frontend 3000:3000
```

## Production Readiness Checklist

- [ ] Replace development secrets with production values
- [ ] Enable TLS for all service communication
- [ ] Configure Redis cluster for production scale
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation (ELK stack)
- [ ] Enable Dapr observability
- [ ] Set up CI/CD pipeline
- [ ] Configure resource limits for all pods
- [ ] Enable horizontal pod autoscaling
- [ ] Configure backup strategy for PostgreSQL

## Next Steps

Once local setup is verified:
1. **Run Integration Tests**: `/sp.tasks` for Phase 2 breakdown
2. **Deploy to Staging**: Use production-ready Skills
3. **Load Testing**: Validate 1000+ concurrent user scenarios
4. **Security Audit**: Review Kong JWT and sandbox isolation

## File Structure Reference
```
specs/001-learnflow-architecture/
├── plan.md              # This roadmap
├── research.md          # Phase 0 research answers
├── data-model.md        # Entity definitions
├── quickstart.md        # This file
└── contracts/
    ├── openapi.yaml     # API specifications
    └── kafka-schemas.yaml # Event schemas
```