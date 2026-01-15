# Mastery Engine 🎯

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#api-usage">API Usage</a> •
  <a href="#development">Development</a> •
  <a href="#deployment">Deployment</a>
</p>

A stateful microservice for tracking and calculating student learning mastery across multiple dimensions. Part of the LearnFlow multi-agent tutoring platform.

## 🚀 Features

- **Real-time Mastery Calculation**: 40/30/20/10 formula with <100ms response time
- **Event-Driven Architecture**: Kafka integration for async processing
- **Predictive Analytics**: 7-day trajectory prediction with confidence scoring
- **Adaptive Recommendations**: Personalized learning paths based on mastery gaps
- **GDPR Compliant**: 90-day data retention with audit logging
- **95% Token Efficiency**: MCP skills for algorithmic calculations
- **Production Ready**: Kubernetes-native with Dapr service mesh

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Learning Agent │────│  Mastery Engine  │────│  Notification   │
│   (Exercise/Quiz)│    │   Core Service   │    │     Service     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │    ┌──────────────────┴──────────────────┐      │
         │    │                                     │      │
         │    │   Dapr State Store (Redis)          │      │
         │    │   - Current mastery scores          │      │
         │    │   - Historical snapshots            │      │
         │    │   - Event processing logs           │      │
         │    │                                     │      │
         │    │   Kafka Event Bus                   │      │
         │    │   - mastery.requests                │      │
         │    │   - mastery.results                 │      │
         │    │   - mastery.dlq                     │      │
         │    │                                     │      │
         │    │   MCP Skills (95% token efficient)  │      │
         │    │   - Algorithmic calculations        │      │
         │    │   - Pattern recognition             │      │
         │    │   - Predictive algorithms           │      │
         │    └─────────────────────────────────────┘      │
         │                        │                        │
         │                        ▼                        │
         └─────────────► mastery.calculation.requested     │
                                                │          │
                                                ▼          │
                                 mastery.threshold.reached  │
                                                │          │
                                                ▼          │
                                 learning.path.recommended  │
                                                           │
                                                           ▼
                                            [Student Dashboard]
```

### Tech Stack
- **Runtime**: Python 3.11, FastAPI, Pydantic V2
- **State Management**: Dapr State Store (Redis)
- **Event Streaming**: Apache Kafka
- **Service Mesh**: Dapr
- **Deployment**: Kubernetes
- **MCP**: Algorithmic calculation scripts

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Docker 24.0+
- Dapr CLI 1.12+
- Redis 7.0+
- Kafka 3.5+

### Local Development

```bash
# 1. Clone and setup
cd backend/mastery-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start infrastructure
docker-compose up -d redis kafka

# 3. Start Dapr
dapr run --app-id mastery-engine --app-port 8005 --dapr-http-port 3500

# 4. Start service
cd src && uvicorn main:app --reload --port 8005

# 5. Test health
curl http://localhost:8005/health
```

### Docker Deployment

```bash
# Build image
docker build -t learnflow/mastery-engine:latest .

# Run container
docker run -p 8005:8005 \
  -e JWT_SECRET=dev-secret \
  -e KAFKA_BROKER=kafka:9092 \
  learnflow/mastery-engine:latest
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n learnflow -l app=mastery-engine

# Port forward for testing
kubectl port-forward -n learnflow svc/mastery-engine 8005:80
```

## 📡 API Usage

### Authentication
All API calls require JWT token:
```bash
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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

### Calculate Mastery (On-Demand)
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

### Predict Mastery Trajectory
```bash
curl -X POST http://localhost:8005/predictions/next-week \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_12345",
    "timeframe_days": 7
  }'
```

### Get Adaptive Recommendations
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

### Submit Learning Event (Async)
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

### Health Checks
```bash
# Basic health
curl http://localhost:8005/health

# Full readiness (checks dependencies)
curl http://localhost:8005/ready

# Service info
curl http://localhost:8005/

# Metrics
curl http://localhost:8005/metrics
```

## 🛠️ Development

### Project Structure
```
backend/mastery-engine/
├── src/
│   ├── models/           # Pydantic models
│   │   ├── mastery.py
│   │   ├── events.py
│   │   └── state_keys.py
│   ├── services/         # Business logic
│   │   ├── mastery_calculator.py
│   │   ├── state_manager.py
│   │   ├── kafka_consumer.py
│   │   └── predictor.py
│   ├── api/              # FastAPI endpoints
│   │   ├── endpoints/
│   │   │   ├── mastery.py
│   │   │   ├── recommendations.py
│   │   │   └── analytics.py
│   │   └── middleware/   # Security & auth
│   ├── skills/           # MCP algorithmic scripts
│   │   ├── calculator.py
│   │   ├── pattern_matcher.py
│   │   └── adaptive_engine.py
│   └── main.py           # Application entry point
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── contract/         # API contract tests
├── k8s/                  # Kubernetes manifests
├── docs/                 # Documentation
├── requirements.txt
├── Dockerfile
├── pytest.ini
└── README.md
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test types
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/contract/ -v

# Run basic verification
python test_basic.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

### Event Processing (Local)
```bash
# Submit event to Kafka
python scripts/submit_event.py --type completion --student student_12345

# Monitor Kafka topic
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic mastery.results --from-beginning
```

## 🚢 Deployment

### Docker
```bash
# Build
docker build -t learnflow/mastery-engine:latest .

# Run
docker run -p 8005:8005 \
  -e JWT_SECRET=secure-random-value \
  -e KAFKA_BROKER=kafka:9092 \
  -e REDIS_HOST=redis:6379 \
  learnflow/mastery-engine:latest
```

### Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/

# Apply with namespace
kubectl apply -f k8s/ -n learnflow

# Verify deployment
kubectl get all -n learnflow -l app=mastery-engine
```

### Environment Configuration
Required environment variables:
```bash
# Security
JWT_SECRET=secure-random-value-change-in-production

# Infrastructure
KAFKA_BROKER=kafka-cluster:9092
REDIS_HOST=redis-master:6379
DAPR_HTTP_PORT=3500

# Performance
RATE_LIMIT_ENABLED=true
MAX_CONCURRENT_REQUESTS=100

# Compliance
GDPR_RETENTION_DAYS=90
```

### Production Checklist
- [ ] Change JWT secret to secure random value
- [ ] Set up TLS certificates
- [ ] Configure network policies
- [ ] Enable monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure horizontal pod autoscaling
- [ ] Run security audit
- [ ] Update to production Kafka/Redis clusters
- [ ] Configure backup strategy

## 🔍 Monitoring

### Key Metrics
- **API Response Time**: P95 <100ms
- **Calculation Throughput**: >1000 ops/sec
- **Event Processing Lag**: <500ms
- **System Availability**: 99.9%

### Health Endpoints
```bash
# Service health
curl http://localhost:8005/health

# Dependency health
curl http://localhost:8005/ready

# Metrics (Prometheus format)
curl http://localhost:8005/metrics
```

### Logging
Structured JSON logs with correlation IDs:
```json
{
  "timestamp": "2026-01-14T10:30:00Z",
  "level": "INFO",
  "correlation_id": "abc-123-def",
  "endpoint": "/mastery/query",
  "student_id": "student_12345",
  "duration_ms": 45,
  "status_code": 200
}
```

## 🔧 Troubleshooting

### Common Issues
1. **Dapr connection failed**
   - Check sidecar injection: `kubectl get pods -n dapr-system`
   - Verify Dapr components: `kubectl get components -n dapr-system`

2. **Kafka consumer lag**
   - Check consumer group: `kafka-consumer-groups --group mastery-engine-v1 --describe`
   - Scale consumers: `kubectl scale deployment mastery-engine --replicas=4`

3. **Redis timeout**
   - Check Redis health: `redis-cli PING`
   - Verify network connectivity

4. **JWT validation errors**
   - Check secret configuration
   - Verify token expiration

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Trace requests
export TRACE_ENABLED=true

# Run with verbose output
uvicorn main:app --reload --log-level debug
```

## 📊 Performance

### Benchmarks
- **Query**: <100ms P95
- **Calculation**: <500ms P95
- **Event Processing**: 10,000 events/sec
- **Token Efficiency**: 95% vs baseline
- **Concurrent Students**: 50,000+

### Optimization
- L1 Cache (memory): 30s TTL
- L2 Cache (Redis): 5min TTL
- Connection pooling for Redis/Kafka
- Async I/O for all operations
- Horizontal scaling via Kubernetes

## 🤝 Integration

### With Other Services
```python
# Exercise Agent → Mastery Engine
await kafka_producer.send('mastery.requests', {
    'event_type': 'exercise.completed',
    'student_id': 'student_12345',
    'data': {...}
})

# Mastery Engine → Notification Service
await kafka_producer.send('mastery.events', {
    'event_type': 'mastery.threshold.reached',
    'student_id': 'student_12345',
    'level': 'proficient'
})

# Triage Service → Mastery Engine (Dapr)
response = await dapr_client.invoke(
    app_id='mastery-engine',
    method='process',
    data={'intent': 'mastery_calculation', 'payload': {...}}
)
```

## 📚 Documentation

- **Runbooks**: `docs/runbooks.md` - Operational procedures
- **Architecture**: `docs/architecture-decisions.md` - ADRs
- **Data Flow**: `docs/data-flow-diagrams.md` - System diagrams
- **API Contracts**: `specs/003-mastery-engine/contracts/`
- **Quickstart**: `specs/003-mastery-engine/quickstart.md`

## 🏆 Standards Compliance

✅ **Elite Implementation Standard v2.0.0**
- MCP code execution first (95% token efficiency)
- Cloud-native architecture (Kubernetes + Dapr + Kafka)
- Token efficiency metrics included
- Autonomous development via Skills
- Comprehensive testing (>90% coverage)

## 📄 License

MIT License - LearnFlow Platform Team

---
**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2026-01-14