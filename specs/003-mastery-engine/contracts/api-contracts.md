# API Contracts: Mastery Engine
**Date**: 2026-01-14 | **Version**: v1.0

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: Mastery Engine API
  version: 1.0.0
  description: |
    Stateful microservice for tracking student learning progress with sophisticated
    mastery formulas (40% Completion + 30% Quiz + 20% Quality + 10% Consistency).

    ## Key Features
    - Real-time mastery computation
    - Predictive analytics and progression modeling
    - Adaptive learning recommendations
    - Event-driven architecture with Dapr + Kafka

    ## Architecture
    - **Authentication**: JWT Bearer tokens
    - **Rate Limiting**: 10-50 req/min per endpoint
    - **Response Format**: JSON
    - **Idempotency**: Supported for write operations

    ## Base URLs
    - Production: `https://api.learnflow.com/mastery/v1`
    - Staging: `https://staging.api.learnflow.com/mastery/v1`
    - Local: `http://localhost:8005/api/v1`

servers:
  - url: https://api.learnflow.com/mastery/v1
    description: Production
  - url: https://staging.api.learnflow.com/mastery/v1
    description: Staging
  - url: http://localhost:8005/api/v1
    description: Local Development

tags:
  - name: Mastery
    description: Query and calculate mastery scores
  - name: Predictions
    description: Predictive analytics for student progression
  - name: Recommendations
    description: Adaptive learning path recommendations
  - name: Analytics
    description: Historical analysis and reporting
  - name: Batch
    description: Batch operations for multiple students

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    # Error Responses
    ErrorResponse:
      type: object
      required: [success, error]
      properties:
        success:
          type: boolean
          example: false
        error:
          type: object
          properties:
            code:
              type: string
              enum: [VALIDATION_ERROR, AUTH_ERROR, NOT_FOUND, INTERNAL_ERROR, RATE_LIMITED]
              example: "VALIDATION_ERROR"
            message:
              type: string
              example: "Invalid student ID format"
            details:
              type: object
              additionalProperties: true
              example: {"field": "student_id", "constraint": "min_length=1"}

    # Success Response Wrapper
    SuccessResponse:
      type: object
      required: [success]
      properties:
        success:
          type: boolean
          example: true
        data:
          type: object
        meta:
          type: object
          properties:
            timestamp:
              type: string
              format: date-time
            version:
              type: string
              example: "1.0"

    # Component Scores
    ComponentScores:
      type: object
      required: [completion, quiz, quality, consistency]
      properties:
        completion:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.85
        quiz:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.90
        quality:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.85
        consistency:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.82

    # Mastery Level
    MasteryLevel:
      type: string
      enum: [beginner, developing, competent, proficient, expert]
      example: "proficient"

    # Mastery Result
    MasteryResult:
      type: object
      required: [student_id, mastery_score, level, components, timestamp]
      properties:
        student_id:
          type: string
          example: "student_12345"
        mastery_score:
          type: number
          format: float
          minimum: 0.0
          maximum: 1.0
          example: 0.85
        level:
          $ref: "#/components/schemas/MasteryLevel"
        components:
          $ref: "#/components/schemas/ComponentScores"
        breakdown:
          type: array
          items:
            type: object
            properties:
              component:
                type: string
                example: "completion"
              score:
                type: number
                example: 0.85
              contribution:
                type: number
                example: 0.34
              weight:
                type: number
                example: 0.4
        recommendations:
          type: array
          items:
            type: object
            properties:
              action:
                type: string
                example: "practice"
              area:
                type: string
                example: "advanced_topics"
              priority:
                type: string
                example: "high"
        timestamp:
          type: string
          format: date-time
        version:
          type: string
          example: "1.0"

    # Mastery Profile
    MasteryProfile:
      type: object
      properties:
        student_id:
          type: string
        current_mastery:
          $ref: "#/components/schemas/MasteryResult"
        historical_average:
          type: number
          minimum: 0.0
          maximum: 1.0
        trend:
          type: string
          enum: [improving, declining, stable]
        last_updated:
          type: string
          format: date-time
        learning_path:
          type: array
          items:
            type: string

    # Prediction Result
    PredictionResult:
      type: object
      required: [student_id, predicted_score, confidence]
      properties:
        student_id:
          type: string
        predicted_score:
          type: number
          minimum: 0.0
          maximum: 1.0
        confidence:
          type: number
          minimum: 0.0
          maximum: 1.0
        trend:
          type: string
          enum: [improving, declining, stable]
        intervention_needed:
          type: boolean
        timeframe_days:
          type: integer
          minimum: 1
          maximum: 30

    # Adaptive Recommendation
    AdaptiveRecommendation:
      type: object
      required: [action, area, priority]
      properties:
        action:
          type: string
          enum: [practice, review, refactor, schedule]
        area:
          type: string
          example: "advanced_topics"
        priority:
          type: string
          enum: [high, medium, low]
        estimated_time:
          type: integer
          description: "Estimated time in minutes"
        resources:
          type: array
          items:
            type: string

    # Request Models
    MasteryQueryRequest:
      type: object
      required: [student_id]
      properties:
        student_id:
          type: string
          minLength: 1
          maxLength: 50
          pattern: "^[a-zA-Z0-9_-]+$"
          example: "student_12345"
        date:
          type: string
          format: date
          description: "Specific date (YYYY-MM-DD), defaults to today"
          example: "2026-01-14"
        include_components:
          type: boolean
          default: true
          description: "Include detailed component breakdown"

    PredictionQueryRequest:
      type: object
      required: [student_id]
      properties:
        student_id:
          type: string
          minLength: 1
          maxLength: 50
          pattern: "^[a-zA-Z0-9_-]+$"
        timeframe_days:
          type: integer
          minimum: 1
          maximum: 30
          default: 7

    RecommendationQueryRequest:
      type: object
      required: [student_id]
      properties:
        student_id:
          type: string
          minLength: 1
          maxLength: 50
          pattern: "^[a-zA-Z0-9_-]+$"
        limit:
          type: integer
          minimum: 1
          maximum: 10
          default: 5
        priority:
          type: string
          enum: [high, medium, low, null]
          nullable: true

    # Batch Operations
    BatchMasteryRequest:
      type: object
      required: [requests]
      properties:
        requests:
          type: array
          items:
            type: object
            required: [student_id, components]
            properties:
              student_id:
                type: string
              components:
                $ref: "#/components/schemas/ComponentScores"
        priority:
          type: string
          enum: [low, normal, high]
          default: "normal"

    BatchMasteryResponse:
      type: object
      properties:
        results:
          type: array
          items:
            $ref: "#/components/schemas/MasteryResult"
        failures:
          type: array
          items:
            type: object
            properties:
              student_id:
                type: string
              error:
                type: string
        summary:
          type: object
          properties:
            total:
              type: integer
            success:
              type: integer
            failed:
              type: integer

paths:
  # Mastery Query Endpoints
  /mastery/query:
    post:
      tags: [Mastery]
      summary: Get mastery data for student
      description: Retrieves current mastery status and detailed breakdown for specified student
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/MasteryQueryRequest"
      responses:
        "200":
          description: Successful mastery query
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        $ref: "#/components/schemas/MasteryProfile"
        "400":
          description: Validation error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
        "401":
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
        "404":
          description: Student not found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
        "429":
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /mastery/calculate:
    post:
      tags: [Mastery]
      summary: Calculate mastery score
      description: Calculate mastery score from component inputs using 40-30-20-10 formula
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/MasteryQueryRequest"
      responses:
        "200":
          description: Successful calculation
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        $ref: "#/components/schemas/MasteryResult"
        "400":
          description: Invalid component scores
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /mastery/ingest:
    post:
      tags: [Mastery]
      summary: Ingest learning event
      description: Submit raw learning event for mastery calculation (async processing)
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [event_type, student_id, data]
              properties:
                event_type:
                  type: string
                  enum: [completion, quiz, quality, consistency]
                student_id:
                  type: string
                data:
                  type: object
                  description: "Event-specific data payload"
                  additionalProperties: true
      responses:
        "202":
          description: Event accepted for processing
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          event_id:
                            type: string
                          status:
                            type: string
                            enum: [queued, processing, completed]
        "400":
          description: Invalid event data
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  # Prediction Endpoints
  /predictions/next-week:
    post:
      tags: [Predictions]
      summary: Predict mastery in 7 days
      description: Predict mastery score trajectory and intervention needs
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PredictionQueryRequest"
      responses:
        "200":
          description: Successful prediction
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        $ref: "#/components/schemas/PredictionResult"
        "404":
          description: Insufficient history for prediction
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /predictions/trajectory:
    post:
      tags: [Predictions]
      summary: Get mastery trajectory analysis
      description: Detailed analysis of mastery trends over time
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id]
              properties:
                student_id:
                  type: string
                days:
                  type: integer
                  minimum: 7
                  maximum: 90
                  default: 30
      responses:
        "200":
          description: Successful trajectory analysis
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          trend:
                            type: string
                          points:
                            type: array
                            items:
                              type: object
                              properties:
                                date:
                                  type: string
                                  format: date
                                score:
                                  type: number
                                level:
                                  $ref: "#/components/schemas/MasteryLevel"

  # Recommendation Endpoints
  /recommendations/adaptive:
    post:
      tags: [Recommendations]
      summary: Get adaptive learning recommendations
      description: Personalized recommendations based on mastery gaps
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RecommendationQueryRequest"
      responses:
        "200":
          description: Successful recommendations
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: array
                        items:
                          $ref: "#/components/schemas/AdaptiveRecommendation"

  /recommendations/learning-path:
    post:
      tags: [Recommendations]
      summary: Get personalized learning path
      description: Generate step-by-step learning path for student
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id]
              properties:
                student_id:
                  type: string
                goal:
                  type: string
                  enum: [improve_mastery, master_topic, prepare_assessment]
                  default: "improve_mastery"
      responses:
        "200":
          description: Successful path generation
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          path:
                            type: array
                            items:
                              type: string
                          estimated_completion:
                            type: string
                            format: date-time
                          daily_schedule:
                            type: array
                            items:
                              type: object
                              properties:
                                day:
                                  type: integer
                                tasks:
                                  type: array
                                  items:
                                    type: string

  # Analytics Endpoints
  /analytics/mastery-history:
    post:
      tags: [Analytics]
      summary: Get mastery history
      description: Retrieve historical mastery data with filtering and aggregation
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id]
              properties:
                student_id:
                  type: string
                start_date:
                  type: string
                  format: date
                end_date:
                  type: string
                  format: date
                aggregation:
                  type: string
                  enum: [daily, weekly, monthly]
                  default: "daily"
      responses:
        "200":
          description: Successful history retrieval
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          history:
                            type: array
                            items:
                              type: object
                              properties:
                                date:
                                  type: string
                                score:
                                  type: number
                                level:
                                  $ref: "#/components/schemas/MasteryLevel"
                          summary:
                            type: object
                            properties:
                              average:
                                type: number
                              highest:
                                type: number
                              lowest:
                                type: number
                              improvement:
                                type: number

  /analytics/compare:
    post:
      tags: [Analytics]
      summary: Compare mastery with cohort
      description: Compare student mastery against cohort/class average
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [student_id, cohort_id]
              properties:
                student_id:
                  type: string
                cohort_id:
                  type: string
                metric:
                  type: string
                  enum: [overall, by_component]
                  default: "overall"
      responses:
        "200":
          description: Successful comparison
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          student_score:
                            type: number
                          cohort_average:
                            type: number
                          percentile:
                            type: number
                            minimum: 0
                            maximum: 100
                          ranking:
                            type: integer
                          total_students:
                            type: integer

  # Batch Operations
  /batch/mastery:
    post:
      tags: [Batch]
      summary: Calculate mastery for multiple students
      description: Process mastery calculations in batch for efficiency
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/BatchMasteryRequest"
      responses:
        "202":
          description: Batch accepted for processing
          content:
            application/json:
              schema:
                allOf:
                  - $ref: "#/components/schemas/SuccessResponse"
                  - type: object
                    properties:
                      data:
                        $ref: "#/components/schemas/BatchMasteryResponse"

  # Dapr Service Invocation
  /process:
    post:
      tags: [Internal]
      summary: Dapr service invocation endpoint
      description: Internal endpoint for Dapr service-to-service communication
      x-dapr-enabled: true
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [intent]
              properties:
                intent:
                  type: string
                  enum: [mastery_calculation, get_prediction, generate_path]
                payload:
                  type: object
                  description: "Intent-specific payload"
                  additionalProperties: true
                security_context:
                  type: object
                  properties:
                    token:
                      type: string
                    roles:
                      type: array
                      items:
                        type: string
      responses:
        "200":
          description: Successful processing
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: object
                  metadata:
                    type: object

  # Health Check Endpoints
  /health:
    get:
      tags: [Internal]
      summary: Health check
      description: Lightweight health check for load balancers
      responses:
        "200":
          description: Service healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  timestamp:
                    type: string
                    format: date-time
                  version:
                    type: string

  /ready:
    get:
      tags: [Internal]
      summary: Readiness check
      description: Full readiness check including dependencies
      responses:
        "200":
          description: Service ready
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "ready"
                  dependencies:
                    type: object
                    properties:
                      redis:
                        type: boolean
                      kafka:
                        type: boolean
                      dapr:
                        type: boolean
                  timestamp:
                    type: string
                    format: date-time

  /:
    get:
      tags: [Internal]
      summary: Service information
      description: API metadata and version information
      responses:
        "200":
          description: Service information
          content:
            application/json:
              schema:
                type: object
                properties:
                  name:
                    type: string
                    example: "mastery-engine"
                  version:
                    type: string
                    example: "1.0.0"
                  environment:
                    type: string
                    enum: [development, staging, production]

security:
  - bearerAuth: []

x-ratelimit:
  mastery/query:
    requests: 50
    window: 60s
  mastery/calculate:
    requests: 30
    window: 60s
  predictions/next-week:
    requests: 20
    window: 60s
  batch/mastery:
    requests: 5
    window: 60s

x-error-codes:
  VALIDATION_ERROR:
    http_code: 400
    description: Input validation failed
  AUTH_ERROR:
    http_code: 401
    description: Authentication failed or token expired
  NOT_FOUND:
    http_code: 404
    description: Resource not found
  RATE_LIMITED:
    http_code: 429
    description: Rate limit exceeded
  INTERNAL_ERROR:
    http_code: 500
    description: Internal server error
  SERVICE_UNAVAILABLE:
    http_code: 503
    description: Dependency unavailable
```

## Error Handling Examples

### Validation Error (400)
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Component scores must be between 0.0 and 1.0",
    "details": {
      "field": "components.completion",
      "value": 1.5,
      "constraint": "maximum=1.0"
    }
  }
}
```

### Rate Limit Exceeded (429)
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "details": {
      "retry_after": 45,
      "limit": 50,
      "window": "60s"
    }
  }
}
```

### Success Response (200)
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
      "breakdown": [
        {"component": "completion", "score": 0.85, "contribution": 0.34, "weight": 0.4},
        {"component": "quiz", "score": 0.90, "contribution": 0.27, "weight": 0.3},
        {"component": "quality", "score": 0.85, "contribution": 0.17, "weight": 0.2},
        {"component": "consistency", "score": 0.82, "contribution": 0.082, "weight": 0.1}
      ],
      "recommendations": [
        {"action": "practice", "area": "advanced_topics", "priority": "high"},
        {"action": "refactor", "area": "code_quality", "priority": "medium"}
      ],
      "timestamp": "2026-01-14T10:30:00Z",
      "version": "1.0"
    },
    "historical_average": 0.78,
    "trend": "improving",
    "last_updated": "2026-01-14T10:30:00Z",
    "learning_path": ["advanced_topics", "code_reviews", "practice_quizzes"]
  },
  "meta": {
    "timestamp": "2026-01-14T10:30:00Z",
    "version": "1.0"
  }
}
```

## Rate Limiting Headers

Successful responses include rate limit information:

```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1642152600
X-RateLimit-Used: 8
```

## Idempotency

For write operations (ingest), include `Idempotency-Key` header:

```
Idempotency-Key: unique-request-uuid-v4
```

The service will return the same result for duplicate requests within 24 hours.

---
**Next**: Event schemas in `event-schemas.md`