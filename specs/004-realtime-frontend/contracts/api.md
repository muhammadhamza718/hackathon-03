# API Contracts

**Version**: 1.0.0
**Date**: 2026-01-15
**Feature**: Milestone 5 - Real-Time Frontend
**Status**: Complete

## Overview

This document defines the API contracts between the Next.js 14+ frontend and the backend Mastery Engine. All endpoints follow RESTful principles with JSON payloads, JWT authentication, and comprehensive error handling.

## 1. Base URLs

```
Production: https://api.learnflow.com
Staging:    https://api-staging.learnflow.com
Local:      http://localhost:8005
```

All API requests are routed through Kong Gateway at `https://api.learnflow.com/api/v1`.

## 2. Authentication

### 2.1 JWT Token Format
```json
{
  "sub": "user_12345",
  "email": "student@example.com",
  "role": "student",
  "iat": 1640995200,
  "exp": 1640998800,
  "jti": "unique-token-id"
}
```

### 2.2 Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate user and return JWT tokens.

**Request**:
```json
{
  "email": "student@example.com",
  "password": "secure-password"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "user": {
      "id": "user_12345",
      "email": "student@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "role": "student",
      "preferences": {
        "theme": "dark",
        "fontSize": 14,
        "autoSave": true,
        "notifications": true
      }
    }
  },
  "timestamp": "2026-01-15T10:30:00Z"
}
```

**Response (401)**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email or password is incorrect",
    "details": {}
  },
  "timestamp": "2026-01-15T10:30:00Z"
}
```

#### POST /api/v1/auth/refresh
Refresh access token using refresh token.

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  },
  "timestamp": "2026-01-15T10:35:00Z"
}
```

#### POST /api/v1/auth/logout
Invalidate tokens and clear session.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "message": "Successfully logged out"
  },
  "timestamp": "2026-01-15T10:40:00Z"
}
```

## 3. Mastery Engine API

### 3.1 Mastery Calculation

#### POST /api/v1/mastery/calculate
Calculate mastery score for a student on a specific topic.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
X-Request-ID: <uuid>
```

**Request**:
```json
{
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "includeBreakdown": true
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "studentId": "student_001",
    "topicId": "topic_algorithms",
    "overallScore": 78.5,
    "masteryLevel": "proficient",
    "breakdown": {
      "completion": 85.0,
      "quiz": 75.0,
      "quality": 80.0,
      "consistency": 70.0
    },
    "updatedAt": "2026-01-15T10:45:00Z",
    "trend": "improving"
  },
  "metadata": {
    "requestId": "req_12345",
    "processingTime": 45
  }
}
```

**Response (400)**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Missing required fields",
    "details": {
      "missing": ["studentId", "topicId"]
    }
  },
  "timestamp": "2026-01-15T10:45:00Z"
}
```

#### POST /api/v1/mastery/query
Batch query mastery scores for multiple students/topics.

**Request**:
```json
{
  "queries": [
    {
      "studentId": "student_001",
      "topicId": "topic_algorithms"
    },
    {
      "studentId": "student_002",
      "topicId": "topic_algorithms"
    }
  ],
  "includeBreakdown": false
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "studentId": "student_001",
        "topicId": "topic_algorithms",
        "overallScore": 78.5,
        "masteryLevel": "proficient"
      },
      {
        "studentId": "student_002",
        "topicId": "topic_algorithms",
        "overallScore": 92.0,
        "masteryLevel": "advanced"
      }
    ],
    "total": 2
  },
  "metadata": {
    "requestId": "req_12346",
    "processingTime": 78
  }
}
```

### 3.2 Predictive Analytics

#### POST /api/v1/predictions/next-week
Get 7-day mastery prediction for a student.

**Request**:
```json
{
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "confidenceThreshold": 0.7
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "prediction": {
      "predictedScore": 85.2,
      "confidence": 0.82,
      "trend": "improving",
      "interventionNeeded": false,
      "factors": [
        "consistent_practice",
        "improving_quiz_scores",
        "high_assignment_completion"
      ]
    },
    "generatedAt": "2026-01-15T11:00:00Z"
  },
  "metadata": {
    "cacheHit": false,
    "processingTime": 120
  }
}
```

#### POST /api/v1/predictions/trajectory
Get mastery trajectory over time.

**Request**:
```json
{
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "days": 14
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "trajectory": [
      {
        "date": "2026-01-01",
        "score": 65.0,
        "confidence": 0.65
      },
      {
        "date": "2026-01-08",
        "score": 72.0,
        "confidence": 0.72
      },
      {
        "date": "2026-01-15",
        "score": 78.5,
        "confidence": 0.82
      }
    ],
    "summary": {
      "avgScore": 71.8,
      "trend": "improving",
      "volatility": 0.15
    }
  },
  "metadata": {
    "cacheHit": true,
    "cacheAge": 300
  }
}
```

### 3.3 Recommendations

#### POST /api/v1/recommendations/adaptive
Get adaptive learning recommendations.

**Request**:
```json
{
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "maxRecommendations": 5
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "id": "rec_001",
        "type": "practice",
        "area": "dynamic_programming",
        "priority": "high",
        "estimatedTime": 45,
        "description": "Practice dynamic programming problems to improve algorithmic thinking",
        "actionItems": [
          "Solve 5 DP problems",
          "Review recursion concepts",
          "Complete DP quiz"
        ],
        "links": [
          "/content/dp-basics",
          "/practice/dp-easy"
        ]
      },
      {
        "id": "rec_002",
        "type": "review",
        "area": "sorting_algorithms",
        "priority": "medium",
        "estimatedTime": 30,
        "description": "Review sorting algorithms to strengthen fundamentals",
        "actionItems": [
          "Review quicksort implementation",
          "Compare sorting algorithm complexities",
          "Complete sorting quiz"
        ],
        "links": [
          "/content/sorting",
          "/quiz/sorting"
        ]
      }
    ],
    "generatedAt": "2026-01-15T11:15:00Z"
  },
  "metadata": {
    "processingTime": 85
  }
}
```

#### POST /api/v1/recommendations/learning-path
Generate comprehensive learning path.

**Request**:
```json
{
  "studentId": "student_001",
  "targetTopic": "topic_algorithms",
  "weeks": 4,
  "intensity": "balanced"  // "light" | "balanced" | "intensive"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "path": {
      "id": "path_001",
      "weeks": 4,
      "estimatedTotalTime": 600, // minutes
      "modules": [
        {
          "week": 1,
          "focus": "fundamentals",
          "topics": ["recursion", "sorting", "searching"],
          "timeEstimate": 120,
          "difficulty": "beginner"
        },
        {
          "week": 2,
          "focus": "data_structures",
          "topics": ["trees", "graphs", "hash_tables"],
          "timeEstimate": 150,
          "difficulty": "intermediate"
        },
        {
          "week": 3,
          "focus": "algorithms",
          "topics": ["dynamic_programming", "greedy", "backtracking"],
          "timeEstimate": 180,
          "difficulty": "intermediate"
        },
        {
          "week": 4,
          "focus": "advanced",
          "topics": ["advanced_dp", "graph_algorithms", "complexity_analysis"],
          "timeEstimate": 150,
          "difficulty": "advanced"
        }
      ],
      "checkpoints": [
        {
          "week": 2,
          "assessment": "midpoint_quiz",
          "passingScore": 70
        },
        {
          "week": 4,
          "assessment": "final_project",
          "passingScore": 80
        }
      ]
    }
  }
}
```

## 4. Analytics API

### 4.1 Batch Processing

#### POST /api/v1/batch/mastery
Submit batch mastery calculation request.

**Request**:
```json
{
  "studentIds": ["student_001", "student_002", "student_003"],
  "topicId": "topic_algorithms",
  "priority": "normal",
  "callbackUrl": "https://frontend.com/api/callback/batch-complete"
}
```

**Response (202)**:
```json
{
  "success": true,
  "data": {
    "batchId": "batch_12345",
    "status": "queued",
    "estimatedTime": 30,
    "submittedAt": "2026-01-15T12:00:00Z"
  },
  "metadata": {
    "requestId": "req_12347"
  }
}
```

#### GET /api/v1/batch/mastery/{batchId}
Check batch processing status.

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "batchId": "batch_12345",
    "status": "completed",
    "progress": 100,
    "results": [
      {
        "studentId": "student_001",
        "overallScore": 78.5,
        "status": "success"
      },
      {
        "studentId": "student_002",
        "overallScore": 92.0,
        "status": "success"
      }
    ],
    "completedAt": "2026-01-15T12:00:25Z"
  }
}
```

### 4.2 Historical Analytics

#### POST /api/v1/analytics/mastery-history
Get historical mastery data.

**Request**:
```json
{
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "dateRange": {
    "start": "2025-12-01",
    "end": "2026-01-15"
  },
  "aggregation": "daily"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "date": "2025-12-01",
        "score": 65.0,
        "count": 1
      },
      {
        "date": "2025-12-08",
        "score": 68.5,
        "count": 2
      },
      // ... daily entries
    ],
    "statistics": {
      "mean": 71.8,
      "median": 70.5,
      "stdDev": 8.2,
      "trend": "improving",
      "volatility": 0.15
    }
  }
}
```

### 4.3 Cohort Comparison

#### POST /api/v1/analytics/compare
Compare performance across cohorts.

**Request**:
```json
{
  "cohorts": [
    {
      "name": "Cohort A",
      "studentIds": ["student_001", "student_002", "student_003"]
    },
    {
      "name": "Cohort B",
      "studentIds": ["student_004", "student_005", "student_006"]
    }
  ],
  "topicId": "topic_algorithms",
  "components": ["completion", "quiz", "quality"]
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "comparisons": [
      {
        "cohort": "Cohort A",
        "overall": {
          "mean": 78.5,
          "median": 80.0,
          "stdDev": 6.2,
          "percentile": {
            "25": 75.0,
            "50": 80.0,
            "75": 82.0
          }
        },
        "components": {
          "completion": 85.0,
          "quiz": 75.0,
          "quality": 80.0
        }
      },
      {
        "cohort": "Cohort B",
        "overall": {
          "mean": 82.3,
          "median": 83.0,
          "stdDev": 5.8,
          "percentile": {
            "25": 80.0,
            "50": 83.0,
            "75": 85.0
          }
        },
        "components": {
          "completion": 88.0,
          "quiz": 80.0,
          "quality": 82.0
        }
      }
    ],
    "significance": {
      "pValue": 0.045,
      "significant": true,
      "effectSize": 0.42
    }
  }
}
```

## 5. Dapr Service Invocation

### 5.1 Process Endpoint
Direct service-to-service communication via Dapr.

#### POST /api/v1/process
Generic service invocation endpoint.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
Dapr-App-Id: mastery-engine
```

**Request**:
```json
{
  "intent": "mastery_calculation",
  "payload": {
    "studentId": "student_001",
    "topicId": "topic_algorithms"
  },
  "security_context": {
    "token": "<jwt_token>",
    "userId": "user_12345",
    "role": "student"
  }
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "overallScore": 78.5,
    "masteryLevel": "proficient",
    "breakdown": {
      "completion": 85.0,
      "quiz": 75.0,
      "quality": 80.0,
      "consistency": 70.0
    }
  },
  "metadata": {
    "service": "mastery-engine",
    "processingTime": 45
  }
}
```

## 6. Real-Time Events API

### 6.1 Server-Sent Events Stream

#### GET /api/v1/events/stream
Establish SSE connection for real-time updates.

**Headers**:
```
Authorization: Bearer <access_token>
Accept: text/event-stream
X-Request-ID: <uuid>
```

**Query Parameters**:
```
?topics=student.progress,learning.events
&studentId=student_001
&filter=high_priority
```

**Event Types**:

**mastery.updated**:
```json
event: mastery.updated
data: {
  "studentId": "student_001",
  "topicId": "topic_algorithms",
  "newScore": 78.5,
  "oldScore": 75.0,
  "delta": 3.5,
  "timestamp": "2026-01-15T13:00:00Z"
}
```

**feedback.received**:
```json
event: feedback.received
data: {
  "studentId": "student_001",
  "assignmentId": "assign_001",
  "feedback": "Great work on the recursion section! Consider optimizing your base cases.",
  "score": 85,
  "instructorId": "instructor_001",
  "timestamp": "2026-01-15T13:05:00Z"
}
```

**learning.recommendation**:
```json
event: learning.recommendation
data: {
  "studentId": "student_001",
  "recommendation": {
    "id": "rec_001",
    "type": "practice",
    "area": "dynamic_programming",
    "priority": "high"
  },
  "timestamp": "2026-01-15T13:10:00Z"
}
```

### 6.2 Event Subscription Management

#### POST /api/v1/events/subscribe
Subscribe to specific event topics.

**Request**:
```json
{
  "topics": ["student.progress", "learning.events"],
  "filters": [
    {
      "field": "studentId",
      "operator": "equals",
      "value": "student_001"
    }
  ],
  "callbackUrl": "https://frontend.com/api/webhook/events"
}
```

**Response (200)**:
```json
{
  "success": true,
  "data": {
    "subscriptionId": "sub_12345",
    "topics": ["student.progress", "learning.events"],
    "status": "active",
    "createdAt": "2026-01-15T14:00:00Z"
  }
}
```

## 7. Error Responses

### 7.1 Standard Error Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "email",
      "constraint": "required"
    },
    "retryable": false,
    "timestamp": "2026-01-15T10:30:00Z"
  },
  "metadata": {
    "requestId": "req_12345"
  }
}
```

### 7.2 Common Error Codes

| Code | HTTP Status | Retryable | Description |
|------|-------------|-----------|-------------|
| `INVALID_AUTH_TOKEN` | 401 | false | JWT token invalid or expired |
| `INSUFFICIENT_PERMISSIONS` | 403 | false | User lacks required permissions |
| `INVALID_INPUT` | 400 | false | Request validation failed |
| `RESOURCE_NOT_FOUND` | 404 | false | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | true | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | true | Backend service down |
| `TIMEOUT` | 408 | true | Request timeout |
| `INTERNAL_ERROR` | 500 | false | Unexpected server error |

## 8. Rate Limiting

### 8.1 Rate Limit Headers
All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640998800
```

### 8.2 Rate Limit Tiers
- **Anonymous**: 10 req/min
- **Student**: 100 req/min
- **Teacher**: 500 req/min
- **Admin**: 1000 req/min

## 9. Caching Strategy

### 9.1 Cache-Control Headers
```
Cache-Control: public, max-age=300, stale-while-revalidate=60
```

### 9.2 ETag Support
```
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

## 10. Pagination

### 10.1 Request Format
```
?page=1&limit=20&sort=createdAt&order=desc
```

### 10.2 Response Format
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "totalPages": 8,
      "hasNext": true,
      "hasPrevious": false
    }
  }
}
```

## 11. CORS Configuration

### 11.1 Allowed Origins
```
https://learnflow.com
https://www.learnflow.com
https://staging.learnflow.com
http://localhost:3000
```

### 11.2 Allowed Methods
```
GET, POST, PUT, DELETE, OPTIONS
```

### 11.3 Allowed Headers
```
Authorization, Content-Type, X-Request-ID, X-Trace-ID, X-Span-ID
```

## 12. Request/Response Tracing

### 12.1 Request Headers
```
X-Request-ID: <uuid>           # Unique request identifier
X-Trace-ID: <uuid>             # Distributed trace identifier
X-Span-ID: <uuid>              # Current span identifier
```

### 12.2 Response Headers
```
X-Request-ID: <uuid>           # Echoed from request
X-Trace-ID: <uuid>             # Echoed from request
X-Span-ID: <uuid>              # New span ID for this response
X-Response-Time: 45            # Processing time in ms
```

## 13. Health Check Endpoints

### 13.1 Service Health
#### GET /health
Lightweight health check for load balancers.

**Response (200)**:
```json
{
  "status": "healthy",
  "service": "frontend",
  "version": "1.0.0",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

#### GET /ready
Full readiness check including dependencies.

**Response (200)**:
```json
{
  "status": "ready",
  "dependencies": {
    "backend": true,
    "kong": true,
    "dapr": true
  },
  "version": "1.0.0",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

#### GET /metrics
Prometheus metrics endpoint.

**Response**: Prometheus text format

## 14. WebSocket Alternative (Future)

### 14.1 WebSocket Endpoint
#### GET /api/v1/events/ws
WebSocket connection for lower latency updates (future enhancement).

**Protocol**: WebSocket
**Subprotocols**: `graphql-transport-ws` or `graphql-ws`

## 15. GraphQL Alternative

### 15.1 GraphQL Endpoint
#### POST /api/v1/graphql
GraphQL API for complex queries (future enhancement).

**Request**:
```graphql
query GetStudentProgress($studentId: ID!, $topicId: ID!) {
  mastery(studentId: $studentId, topicId: $topicId) {
    overallScore
    masteryLevel
    breakdown {
      completion
      quiz
      quality
      consistency
    }
  }
  predictions(studentId: $studentId, topicId: $topicId) {
    nextWeek {
      predictedScore
      confidence
    }
  }
}
```

---

## Integration Points

This API contract integrates with:
- **Kong Gateway**: JWT validation, rate limiting, routing
- **Dapr Pub/Sub**: Real-time event streaming
- **Mastery Engine**: Backend calculations and analytics
- **Frontend**: Next.js API routes and client-side requests

All endpoints follow RESTful principles with consistent error handling and comprehensive tracing.