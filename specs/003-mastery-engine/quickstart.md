# Quickstart Guide: Mastery Engine
**Date**: 2026-01-14 | **Version**: v1.0

This guide provides a complete walkthrough for setting up and using the Mastery Engine microservice.

## Prerequisites

### System Requirements
- **Python**: 3.11+
- **Docker**: 24.0+ (for containerized deployment)
- **Kubernetes**: 1.28+ (for cluster deployment)
- **Dapr**: 1.12+ (for service mesh)
- **Kafka**: 3.5+ (for event streaming)
- **Redis**: 7.0+ (for state store)

### Development Tools
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Dapr CLI (macOS)
brew install dapr/tap/dapr-cli

# Install Dapr CLI (Windows)
winget install Dapr.CLI

# Install Kafka (using Docker)
docker-compose -f kafka-compose.yaml up -d

# Install Redis (using Docker)
docker run -d --name redis-master -p 6379:6379 redis:7-alpine
```

## 1. Local Development Setup

### Step 1: Clone and Setup
```bash
# Navigate to project directory
cd F:\Courses\Hamza\Hackathon-3

# Checkout the mastery engine branch
git checkout 003-mastery-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd backend/mastery-engine
pip install -r requirements.txt
```

### Step 2: Dapr Configuration
```bash
# Initialize Dapr locally
dapr init

# Verify Dapr installation
dapr --version

# Start Dapr placement service (for state store)
dapr run --app-id mastery-engine --app-port 8005 --dapr-http-port 3500 --dapr-grpc-port 50001
```

### Step 3: Configuration Files

Create `.env` file in `backend/mastery-engine/`:
```env
# Server Configuration
PORT=8005
ENVIRONMENT=development
LOG_LEVEL=INFO

# Dapr Configuration
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
DAPR_STATE_STORE=statestore
DAPR_PUBSUB=pubsub

# Kafka Configuration
KAFKA_ENABLED=true
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=mastery.requests
KAFKA_CONSUMER_GROUP=mastery-engine-v1

# JWT Security
JWT_SECRET=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Redis (via Dapr State Store)
REDIS_HOST=localhost:6379
REDIS_PASSWORD=

# Performance Tuning
RATE_LIMIT_ENABLED=true
MAX_CONCURRENT_REQUESTS=100
CACHE_TTL=300
```

### Step 4: Start Development Server
```bash
# Terminal 1: Start Dapr sidecar
dapr run --app-id mastery-engine --app-port 8005 --dapr-http-port 3500 --dapr-grpc-port 50001

# Terminal 2: Start FastAPI server
cd src
uvicorn main:app --reload --port 8005

# Terminal 3: Start Kafka consumer (if event processing needed)
python -m services.kafka_consumer
```

### Step 5: Verify Installation
```bash
# Health check
curl http://localhost:8005/health

# Ready check
curl http://localhost:8005/ready

# Service info
curl http://localhost:8005/
```

Expected response:
```json
{
  "name": "mastery-engine",
  "version": "1.0.0",
  "environment": "development"
}
```

## 2. Docker Deployment

### Build Docker Image
```bash
cd backend/mastery-engine

# Build image
docker build -t learnflow/mastery-engine:latest .

# Verify build
docker images | grep mastery-engine
```

### Run Container Locally
```bash
# Basic run
docker run -p 8005:8005 \
  -e JWT_SECRET=dev-secret \
  -e KAFKA_BROKER=kafka:9092 \
  learnflow/mastery-engine:latest

# With Dapr sidecar (production-like)
docker run -p 8005:8005 \
  --network learnflow-network \
  -e JWT_SECRET=dev-secret \
  -e KAFKA_BROKER=kafka:9092 \
  -e DAPR_HTTP_PORT=3500 \
  learnflow/mastery-engine:latest
```

### Docker Compose Setup
Create `docker-compose.yaml` in `backend/mastery-engine/`:
```yaml
version: '3.8'

services:
  mastery-engine:
    build: .
    ports:
      - "8005:8005"
    environment:
      - JWT_SECRET=dev-secret
      - KAFKA_BROKER=kafka:9092
      - REDIS_HOST=redis:6379
    depends_on:
      - redis
      - kafka
    networks:
      - learnflow-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - learnflow-network

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
    networks:
      - learnflow-network

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    networks:
      - learnflow-network

networks:
  learnflow-network:
    driver: bridge
```

Run with:
```bash
docker-compose up -d
```

## 3. Kubernetes Deployment

### Prerequisites
```bash
# Install kubectl
# Install Dapr in cluster
dapr init -k

# Verify Dapr installation
kubectl get pods -n dapr-system
```

### Apply Kubernetes Manifests
```bash
cd backend/mastery-engine/k8s

# Apply configmap
kubectl apply -f configmap.yaml

# Apply deployment
kubectl apply -f deployment.yaml

# Apply service
kubectl apply -f service.yaml
```

### Verify Deployment
```bash
# Check pods
kubectl get pods -n learnflow -l app=mastery-engine

# Check logs
kubectl logs -n learnflow deployment/mastery-engine -f

# Check service
kubectl get svc -n learnflow mastery-engine

# Port forward for local testing
kubectl port-forward -n learnflow svc/mastery-engine 8005:8005
```

## 4. API Usage Examples

### Authentication
All API calls require JWT token:
```bash
# Get token (example - integrate with your auth service)
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Include in all requests
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8005/mastery/query
```

### Query Current Mastery
```bash
curl -X POST http://localhost:8005/mastery/query \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "include_components": true
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "student_id": "student_12345",
    "current_mastery": {
      "student_id": "student_12345",
      "mastery_score": 0.85,
      "level": "proficient",
      "components": {
        "completion": 0.85,
        "quiz": 0.90,
        "quality": 0.85,
        "consistency": 0.82
      },
      "breakdown": [...],
      "recommendations": [...]
    },
    "historical_average": 0.78,
    "trend": "improving"
  }
}
```

### Calculate Mastery
```bash
curl -X POST http://localhost:8005/mastery/calculate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "components": {
      "completion": 0.85,
      "quiz": 0.90,
      "quality": 0.85,
      "consistency": 0.82
    }
  }'
```

### Get Predictions
```bash
curl -X POST http://localhost:8005/predictions/next-week \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "timeframe_days": 7
  }'
```

### Get Recommendations
```bash
curl -X POST http://localhost:8005/recommendations/adaptive \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "limit": 5,
    "priority": "high"
  }'
```

### Ingest Learning Event (Async)
```bash
curl -X POST http://localhost:8005/mastery/ingest \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "completion",
    "student_id": "student_12345",
    "data": {
      "total_exercises": 10,
      "completed_exercises": 8,
      "difficulty": "intermediate"
    }
  }'
```

## 5. Dapr Service Invocation

### From Other Services
```bash
# Service-to-service invocation via Dapr
curl -X POST http://localhost:3500/v1.0/invoke/mastery-engine/method/process \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "mastery_calculation",
    "payload": {
      "student_id": "student_12345",
      "components": {
        "completion": 0.85,
        "quiz": 0.90,
        "quality": 0.85,
        "consistency": 0.82
      }
    },
    "security_context": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "roles": ["student"]
    }
  }'
```

## 6. Testing

### Unit Tests
```bash
cd backend/mastery-engine

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/test_mastery_calculator.py -v
python -m pytest tests/unit/test_state_manager.py -v
python -m pytest tests/unit/test_kafka_consumer.py -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### Integration Tests
```bash
# Test API endpoints
python -m pytest tests/integration/test_api_endpoints.py -v

# Test Dapr integration
python -m pytest tests/integration/test_dapr_integration.py -v

# Test Kafka integration
python -m pytest tests/integration/test_kafka_integration.py -v
```

### Basic Verification
```bash
# Run comprehensive verification script
python test_basic.py

# Expected output:
# ✓ Health check
# ✓ Dapr connectivity
# ✓ Redis connectivity
# ✓ Kafka connectivity
# ✓ API endpoints
# ✓ Basic calculations
```

### Load Testing
```bash
# Install locust
pip install locust

# Create load test
locust -f tests/load/test_load.py --host=http://localhost:8005
```

## 7. Event Processing

### Submit Events via Kafka
```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Submit completion event
event = {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "exercise.completion.submitted",
    "timestamp": 1642152600000,
    "student_id": "student_12345",
    "exercise_id": "ex_001",
    "total_exercises": 10,
    "completed_exercises": 8,
    "difficulty": "intermediate",
    "time_taken": 1800,
    "completion_rate": 0.8
}

producer.send('mastery.requests', event)
producer.flush()
```

### Monitor Processing
```bash
# Monitor Kafka topic
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic mastery.requests --from-beginning

# Monitor results
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic mastery.results --from-beginning

# Monitor DLQ
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic mastery.dlq --from-beginning
```

## 8. Advanced Usage

### Batch Processing
```bash
curl -X POST http://localhost:8005/batch/mastery \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {
        "student_id": "student_12345",
        "components": {"completion": 0.85, "quiz": 0.90, "quality": 0.85, "consistency": 0.82}
      },
      {
        "student_id": "student_67890",
        "components": {"completion": 0.70, "quiz": 0.75, "quality": 0.80, "consistency": 0.65}
      }
    ],
    "priority": "high"
  }'
```

### Historical Analysis
```bash
curl -X POST http://localhost:8005/analytics/mastery-history \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "start_date": "2026-01-01",
    "end_date": "2026-01-14",
    "aggregation": "weekly"
  }'
```

### Cohort Comparison
```bash
curl -X POST http://localhost:8005/analytics/compare \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "cohort_id": "class_cs101_2026",
    "metric": "overall"
  }'
```

## 9. Troubleshooting

### Common Issues

**Issue**: Dapr not connecting to state store
```bash
# Check Dapr components
kubectl get components -n dapr-system

# Check Redis connection
redis-cli ping

# Check Dapr logs
kubectl logs -n dapr-system -l app=dapr-sidecar
```

**Issue**: Kafka connection refused
```bash
# Check Kafka brokers
kafka-topics --bootstrap-server localhost:9092 --list

# Check Kafka logs
docker logs kafka-container

# Verify network connectivity
telnet localhost 9092
```

**Issue**: Rate limiting errors
```bash
# Check current limits
curl http://localhost:8005/ready

# Review logs
kubectl logs -n learnflow deployment/mastery-engine --tail=50
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View detailed logs
tail -f /var/log/mastery-engine/app.log

# Trace requests
export TRACE_ENABLED=true
```

## 10. Production Checklist

### Security
- [ ] Change JWT secret to secure random value
- [ ] Enable HTTPS/TLS
- [ ] Set up proper certificate management
- [ ] Configure network policies
- [ ] Enable audit logging

### Performance
- [ ] Tune Redis connection pool
- [ ] Configure Kafka consumer group size
- [ ] Set appropriate resource limits
- [ ] Enable caching layer
- [ ] Monitor P95 latency

### Monitoring
- [ ] Set up Prometheus metrics
- [ ] Configure Grafana dashboards
- [ ] Set up alerting rules
- [ ] Enable distributed tracing
- [ ] Configure log aggregation

### Scaling
- [ ] Horizontal pod autoscaling
- [ ] Redis cluster configuration
- [ ] Kafka partition count
- [ ] Database connection pooling
- [ ] CDN for static assets

### Backup & Recovery
- [ ] Redis backup strategy
- [ ] Kafka data retention
- [ ] State store snapshots
- [ ] Disaster recovery plan
- [ ] Rollback procedures

## 11. Integration with Other Services

### Exercise Agent → Mastery Engine
```python
# In Exercise Agent
async def on_exercise_complete(student_id: str, exercise_data: dict):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "exercise.completion.submitted",
        "timestamp": int(time.time() * 1000),
        "student_id": student_id,
        **exercise_data
    }

    await kafka_producer.send('mastery.requests', event)
```

### Mastery Engine → Notification Service
```python
# In Mastery Engine
async def handle_threshold_reached(student_id: str, new_level: str):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "mastery.threshold.reached",
        "timestamp": int(time.time() * 1000),
        "student_id": student_id,
        "threshold_type": new_level
    }

    await kafka_producer.send('mastery.events', event)
```

### Triage Service → Mastery Engine (Dapr)
```python
# In Triage Service
async def get_mastery_analysis(student_id: str):
    response = await dapr_client.invoke(
        app_id="mastery-engine",
        method="process",
        data={
            "intent": "mastery_calculation",
            "payload": {"student_id": student_id}
        }
    )
    return response
```

## 12. Next Steps

1. **Integration Testing**: Test with other LearnFlow services
2. **Load Testing**: Validate performance at scale
3. **Security Audit**: Complete security review
4. **Documentation**: Complete API documentation
5. **Monitoring**: Set up observability stack
6. **Deployment**: Deploy to staging and production

## Support

For issues and questions:
- **Documentation**: Check `docs/runbooks.md` for operational procedures
- **Architecture**: See `docs/architecture-decisions.md` for design rationale
- **API Reference**: See `contracts/api-contracts.md` for complete API specs

---
**Status**: Quickstart complete. Ready for development and testing.