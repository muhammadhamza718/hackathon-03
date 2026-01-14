# Kong Gateway Configuration for Triage Service

**Elite Implementation Standard v2.0.0**

This document describes the Kong configuration for the LearnFlow Triage Service.

## Service Configuration

### Service Definition

```yaml
name: triage-service
url: http://triage-service:8000
retries: 5
connect_timeout: 60000
write_timeout: 60000
read_timeout: 60000
```

### Route Configuration

```yaml
name: triage-route
service: triage-service
paths:
  - /api/v1/triage
  - /api/v1/triage/*
methods:
  - POST
  - GET
  - PUT
  - DELETE
strip_path: false
preserve_host: true
```

## Plugins Configuration

### JWT Plugin

**File**: `infrastructure/kong/plugins/jwt-config.yaml`

```yaml
name: jwt
config:
  key_claim_name: kid
  secret_is_base64: false
  run_on_preflight: false
  maximum_expiration: 86400
```

**Behavior**:
- Validates JWT tokens on all routes
- Extracts `student_id` from `sub` claim
- Enforces token expiration
- Returns 401 for invalid tokens

### Rate Limiting Plugin

```yaml
name: rate-limiting
config:
  minute: 100
  hour: 5000
  policy: redis
  redis_host: redis-cluster
  redis_port: 6379
  fault_tolerant: true
  hide_client_headers: false
```

**Behavior**:
- 100 requests per minute per student
- 5000 requests per hour per student
- Redis-based policy for distributed consistency
- Returns 429 when limit exceeded

### Request Transformer Plugin

```yaml
name: request-transformer
config:
  add:
    headers:
      - "X-Consumer-Username:$consumer_username"
      - "X-Request-ID:$uuid"
  remove:
    headers:
      - "X-Real-IP"
```

**Behavior**:
- Injects consumer identity headers
- Adds request correlation ID
- Removes sensitive internal headers

## Complete Service Example

```bash
# Create service
curl -X POST http://kong-admin:8001/services \
  --data name=triage-service \
  --data url=http://triage-service:8000

# Create route
curl -X POST http://kong-admin:8001/services/triage-service/routes \
  --data "name=triage-route" \
  --data "paths[]=/api/v1/triage" \
  --data "methods[]=POST" \
  --data "preserve_host=true"

# Enable JWT plugin on route
curl -X POST http://kong-admin:8001/routes/triage-route/plugins \
  --data "name=jwt"

# Enable rate limiting on route
curl -X POST http://kong-admin:8001/routes/triage-route/plugins \
  --data "name=rate-limiting" \
  --data "config.minute=100" \
  --data "config.policy=redis" \
  --data "config.redis_host=redis-cluster"
```

## Security Considerations

### JWT Validation Flow

1. Client presents JWT token in `Authorization: Bearer <token>` header
2. Kong validates JWT signature and expiration
3. Kong extracts `sub` claim (student_id)
4. Kong adds `X-Consumer-Username: <student_id>` header
5. Request forwarded to triage-service
6. Tri-service extracts student_id from header

### Token Requirements

- **Algorithm**: HS256 or RS256
- **Required Claims**:
  - `sub` (student_id)
  - `exp` (expiration time)
  - `iss` (issuer)
  - `iat` (issued at)
- **Expiration**: Max 24 hours (86400 seconds)

## Monitoring & Observability

### Available Metrics

Kong provides the following metrics for the triage-service route:

- `kong_http_status{code="200"}` - Successful requests
- `kong_http_status{code="401"}` - Unauthorized (JWT validation failed)
- `kong_http_status{code="429"}` - Rate limited requests
- `kong_latency_bucket{le="..."}` - Request latency distribution

### Health Checks

```bash
# Service health
curl http://kong-admin:8001/status

# Route health
curl http://kong-admin:8001/services/triage-service
```

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check JWT token is valid and not expired
- Verify `kid` claim matches registered key
- Ensure token signature is correct

**429 Too Many Requests**
- Rate limit exceeded
- Wait for next minute/hour window
- Consider requesting rate limit increase

**502 Bad Gateway**
- triage-service may be down
- Check service health
- Verify network connectivity

## Performance Tuning

### Optimal Configuration

```yaml
# Service timeouts
connect_timeout: 5000
write_timeout: 5000
read_timeout: 30000

# Rate limiting
minute: 150  # Adjust based on load
hour: 7500

# Retry policy
retries: 3
```

**Generated**: 2026-01-13
**Version**: 1.0.0
**Compliance**: Elite Standard v2.0.0