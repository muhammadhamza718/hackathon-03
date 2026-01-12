# Infrastructure Connections & Endpoints
**Milestone 1: Infrastructure & Common Schema**
**Generated**: 2026-01-12
**Status**: Operational Readiness Complete

## Service Endpoints

### Kafka Cluster
- **Service**: `kafka:9092`
- **Namespace**: `learnflow`
- **Protocol**: PLAINTEXT
- **Topics**:
  - `learning.events` (12 partitions, 3 replicas)
  - `dead-letter.queue` (6 partitions, 3 replicas)
- **Configuration**:
  - Retention: 7 days (learning.events), 30 days (dead-letter.queue)
  - Compression: snappy (learning.events), gzip (dead-letter.queue)
  - Min ISR: 2

### Dapr Sidecar
- **Control Plane**: `dapr-api:3500` (HTTP), `dapr-api:50001` (gRPC)
- **Namespace**: `dapr-system`
- **Components**: 3 registered
  - `statestore-redis` (Progress Agent only)
  - `kafka-pubsub` (all services)
  - `service-invocation-config` (all services)

### PostgreSQL
- **Service**: `postgresql:5432`
- **Namespace**: `learnflow`
- **Database**: `learnflow`
- **User**: `learnflow_user`
- **Storage**: 5Gi

## Dapr Components Configuration

### Redis State Store (Progress Agent)
```yaml
Component: statestore-redis
Type: state.redis
Metadata:
  redisHost: redis:6379
  poolSize: 10
  maxRetries: 3
  readTimeout: 100ms
  writeTimeout: 100ms
```

### Kafka Pub/Sub
```yaml
Component: kafka-pubsub
Type: pubsub.kafka
Metadata:
  brokers: kafka:9092
  consumerGroup: learnflow-consumers
  maxMessageBytes: 10485760
  consumeRetryInterval: 200ms
```

### Service Invocation
```yaml
Component: service-invocation-config
Routes:
  triage-service: triage-service:8000
  progress-agent: progress-agent:8000
  concepts-agent: concepts-agent:8000
  review-agent: review-agent:8000
  debug-agent: debug-agent:8000
  exercise-agent: exercise-agent:8000
  sandbox-service: sandbox-service:8000
```

## Connection Strings

### For Development
```bash
# Kafka
kafka-console-consumer --bootstrap-server localhost:9092 --topic learning.events --from-beginning
kafka-topics --bootstrap-server localhost:9092 --list

# Dapr
dapr --help
dapr dashboard --kubernetes

# PostgreSQL (via port-forward)
kubectl port-forward svc/postgresql 5432:5432
psql -h localhost -U learnflow_user -d learnflow
```

### For Production (Kubernetes Services)
```yaml
# Kafka Bootstrap
kafka:9092

# Dapr API
dapr-api.dapr-system:3500

# PostgreSQL
postgresql.learnflow:5432
```

## Health Endpoints

### Kafka Health
```bash
kafka-broker-api-versions --bootstrap-server kafka:9092
kafka-topics --bootstrap-server kafka:9092 --describe --topic learning.events
```

### Dapr Health
```bash
# Check Dapr operator
kubectl get pods -n dapr-system

# Check component registration
kubectl get components -n learnflow
```

### PostgreSQL Health
```bash
# Connection test
psql -h postgresql.learnflow -U learnflow_user -d learnflow -c "SELECT 1"
```

## Monitoring & Observability

### Metrics Collection
- **Kafka**: JMX on port 9999 (Prometheus exporters)
- **Dapr**: Built-in metrics on port 9090
- **PostgreSQL**: pg_stat_statements extension enabled

### Log Aggregation
```bash
# All services send logs to stdout
# Collect with:
kubectl logs -n learnflow -l app=<service-name> -f
```

### Tracing
- **Dapr**: Zipkin endpoint `http://zipkin:9411/api/v2/spans`
- **Sampling Rate**: 100% (development)

## Security Configuration

### Network Policies
```yaml
# Allow ingress only from within cluster
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: learnflow
```

### Resource Limits
```yaml
# Kafka (per broker)
Resources:
  Requests: 500m CPU, 1Gi RAM
  Limits: 1000m CPU, 2Gi RAM

# PostgreSQL
Resources:
  Requests: 250m CPU, 256Mi RAM
  Limits: 500m CPU, 512Mi RAM

# Dapr
Resources:
  Requests: 100m CPU, 100Mi RAM
  Limits: 500m CPU, 200Mi RAM
```

## Backup & Recovery

### PostgreSQL
- **Strategy**: Daily snapshots to persistent volume
- **Command**: `pg_dump -h postgresql -U learnflow_user learnflow > backup.sql`
- **Location**: /var/lib/postgresql/data/backups

### Kafka
- **Strategy**: Log retention + replication
- **Recovery**: Automatic from replicas

### Redis
- **Strategy**: RDB persistence with AOF
- **Backup**: Redis data volume snapshots

## Performance Baselines

### Connection Pools
- **Kafka**: 10 concurrent handlers per service
- **Dapr**: Sidecar connection pooling
- **PostgreSQL**: 10 connections per service pod

### Resource Usage (Expected)
- **Kafka**: ~2GB memory per broker (3 brokers = 6GB)
- **Dapr**: ~100MB per sidecar (11 sidecars = 1.1GB)
- **PostgreSQL**: ~256MB (baseline), ~1GB under load
- **Total**: ~8-10GB cluster resources

## Next Steps for Production

1. **Security**: Add TLS for Kafka, Redis auth, PostgreSQL SSL
2. **Monitoring**: Deploy Prometheus + Grafana stack
3. **Alerting**: Configure P95 latency alerts
4. **Scaling**: Set up HPA for agent services
5. **Disaster Recovery**: Cross-region replication strategy

## Validation Status

- ✅ **Infrastructure Health**: All services operational
- ✅ **Schema Compatibility**: 100% validation pass
- ✅ **Resource Allocation**: Within budget
- ✅ **Network Configuration**: Policies applied
- ✅ **Observability**: Logs, metrics, traces configured

---

*This document is automatically generated from Milestone 1 implementation. All endpoints and configurations have been validated.*