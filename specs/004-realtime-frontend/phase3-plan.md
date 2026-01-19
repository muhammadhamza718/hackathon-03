# Phase 3: Real-Time Integration & Backend Connectivity
**Feature**: Real-Time Frontend | **Version**: 1.0.0 | **Date**: 2026-01-15
**Branch**: `004-realtime-frontend` | **Previous Phase**: Phase 2 (Core Components Complete)

## Executive Summary

Phase 3 bridges the frontend MVP with production backend infrastructure using Dapr for real-time event distribution and Kong for API gateway management. This phase transforms the standalone frontend into a fully integrated component of the Mastery Engine architecture.

**Scope**: 47 tasks (T090-T136) across 5 workstreams
**Timeline**: Week 3-4 (Estimated 5-7 days)
**Quality Gates**: Integration testing, security validation, performance benchmarks

---

## Architecture Overview

### Current State (Phase 2 Complete)
- ✅ Monaco Editor with Python support and real-time features
- ✅ SSE client with reconnection and filtering
- ✅ Dashboard with live updates and visualizations
- ✅ Code Editor page with feedback integration
- ✅ Toast notifications and mastery updates
- ⚠️  Mock data and simulated events (needs real backend connectivity)

### Target State (Phase 3 Complete)
- ✅ All Phase 2 features preserved
- ✅ Dapr pub/sub integration for real-time events
- ✅ Kong JWT authentication and rate limiting
- ✅ Production API endpoint integration
- ✅ MCP skills for intelligent configuration
- ✅ Performance optimization and code splitting
- ✅ Comprehensive integration testing

---

## 5 Workstreams (Parallelizable)

### 3.1 Dapr Pub/Sub Integration (T090-T096)

**Objective**: Connect frontend SSE streams to backend Dapr pub/sub system for real-time event distribution.

**Current Infrastructure Available**:
- Dapr deployment: `infrastructure/k8s/dapr/`
- Pub/sub component: `infrastructure/dapr/components/kafka-pubsub.yaml`
- Service invocation: `infrastructure/dapr/components/service-invocation.yaml`

**Implementation Plan**:

1. **T090**: Create Dapr subscription management API route
   - New API route: `frontend/src/app/api/dapr/subscribe/route.ts`
   - Endpoint: `POST /api/dapr/subscribe`
   - Request: `{ topics: string[], studentId: string }`
   - Response: `{ subscriptionId: string, status: "active" }`

2. **T091**: Implement topic filtering logic for student-specific events
   - Filter events by student ID to ensure privacy
   - Map Dapr topics to frontend event types
   - Update SSE client: `frontend/src/lib/sse.ts:85-110`

3. **T092**: Add Dapr sidecar health checks
   - Health endpoint: `GET /api/dapr/health`
   - Check Dapr sidecar availability
   - Integrate with existing SSE health monitoring

4. **T093**: Create event routing from Dapr to SSE streams
   - Bridge Dapr pub/sub to SSE EventSource
   - Transform Dapr messages to SSEEvent format
   - Handle subscription lifecycle management

5. **T094**: Implement event transformation (Dapr → Frontend format)
   - Create transformer functions for each event type
   - Map backend event structure to frontend SSEEvent
   - Preserve metadata and timestamps

6. **T095**: Add Dapr event acknowledgment logic
   - Implement positive acknowledgment for processed events
   - Handle negative acknowledgment for failed events
   - Retry logic for transient failures

7. **T096**: Write integration tests for Dapr connectivity
   - Test subscription management
   - Test event flow from Dapr to frontend
   - Test error scenarios and reconnection

**Test Criteria**:
- [ ] Frontend can subscribe to Dapr topics successfully
- [ ] Events flow from backend to frontend in real-time (<100ms latency)
- [ ] Topic filtering works correctly (student isolation)
- [ ] Event format matches frontend expectations
- [ ] Health checks detect Dapr sidecar failures
- [ ] Reconnection works after Dapr restart

**Dependencies**: Backend Dapr deployment must be running

---

### 3.2 Kong Gateway Integration (T100-T106)

**Objective**: Secure and optimize API traffic through Kong gateway with JWT authentication and rate limiting.

**Current Infrastructure Available**:
- Kong deployment: (assumed from existing routes)
- JWT plugin config: `infrastructure/kong/jwt-plugin.yaml`
- Service routes: `infrastructure/kong/routes.yaml`

**Implementation Plan**:

1. **T100**: Configure Kong JWT plugin for frontend routes
   - Update `infrastructure/kong/jwt-plugin.yaml` with frontend routes
   - Add JWT validation to `/api/*` endpoints
   - Configure claim validation (studentId, permissions)

2. **T101**: Implement automatic token refresh on 401 responses
   - Update API client: `frontend/src/lib/api-client.ts:45-75`
   - Add interceptor for 401 responses
   - Implement token refresh logic with retry
   - Store refreshed tokens securely

3. **T102**: Add rate limit handling in API client
   - Parse `X-RateLimit-*` headers
   - Implement exponential backoff for rate-limited requests
   - Add request queue for failed requests
   - Update API hooks to handle rate limits gracefully

4. **T103**: Create Kong health check endpoint
   - New endpoint: `GET /api/health/kong`
   - Verify Kong connectivity and latency
   - Integrate with existing health monitoring

5. **T104**: Configure CORS headers in Kong
   - Update Kong routes configuration
   - Add CORS plugin for frontend origin
   - Configure allowed methods and headers
   - Set proper CORS policies for security

6. **T105**: Implement request validation for API endpoints
   - Add input validation middleware
   - Validate request bodies, headers, and parameters
   - Return proper error responses for invalid requests
   - Log validation failures for monitoring

7. **T106**: Write security tests for JWT validation
   - Test invalid token scenarios
   - Test expired token handling
   - Test token tampering detection
   - Test rate limit enforcement

**Test Criteria**:
- [ ] Kong validates JWT tokens on all protected routes
- [ ] Rate limiting returns proper headers (X-RateLimit-*)
- [ ] CORS allows requests from frontend origin only
- [ ] Token refresh happens automatically on expiry
- [ ] Invalid tokens are rejected with 401
- [ ] Rate limits prevent abuse while allowing legitimate traffic

**Dependencies**: Kong must be deployed and configured

---

### 3.3 API Endpoint Integration (T110-T116)

**Objective**: Replace mock data with real backend API calls for mastery calculation, analytics, and recommendations.

**Implementation Plan**:

1. **T110**: Implement mastery calculation endpoint integration
   - Create API hook: `frontend/src/lib/hooks/useMastery.ts`
   - Endpoint: `GET /api/mastery/calculate/{studentId}`
   - Integrate with dashboard mastery score display
   - Cache results for 5 minutes

2. **T111**: Create batch processing endpoint integration
   - Batch API hook: `frontend/src/lib/hooks/useBatch.ts`
   - Endpoint: `POST /api/batch/process`
   - Support multiple assignment submissions
   - Handle batch responses and errors

3. **T112**: Integrate predictive analytics endpoints
   - Analytics hook: `frontend/src/lib/hooks/useAnalytics.ts`
   - Endpoints: `GET /api/analytics/predictions/{studentId}`
   - Update 7-day prediction cards on dashboard
   - Cache predictions for 1 hour

4. **T113**: Implement recommendation endpoint integration
   - Recommendations hook: `frontend/src/lib/hooks/useRecommendations.ts`
   - Endpoint: `GET /api/recommendations/{studentId}`
   - Update recommendation list component
   - Track recommendation acceptance

5. **T114**: Create historical analytics endpoint integration
   - Historical data hook: `frontend/src/lib/hooks/useHistorical.ts`
   - Endpoint: `GET /api/analytics/history/{studentId}`
   - Support date range queries
   - Update progress timeline visualization

6. **T115**: Implement cohort comparison endpoint integration
   - Cohort hook: `frontend/src/lib/hooks/useCohort.ts`
   - Endpoint: `GET /api/analytics/cohort/{studentId}`
   - Compare with anonymized peer data
   - Update cohort comparison widget

7. **T116**: Write comprehensive API integration tests
   - Test each API hook with mock backend
   - Test error scenarios and network failures
   - Test data transformation and validation
   - Test caching behavior

**Test Criteria**:
- [ ] All API endpoints return expected data structure
- [ ] Error handling works for failed API calls
- [ ] Response times meet performance targets (<500ms)
- [ ] API hooks provide proper TypeScript types
- [ ] Caching reduces API calls by 60%
- [ ] Offline mode gracefully degrades functionality

**Dependencies**: Backend API services must be deployed and accessible

---

### 3.4 MCP Skills Integration (T120-T126)

**Objective**: Leverage MCP (Model Context Protocol) skills to automate Monaco and SSE configuration, reducing manual code by 88%.

**Implementation Plan**:

1. **T120**: Create Monaco configuration skill
   - Skill file: `frontend/monaco-config.py`
   - Input: Language, theme, editor requirements
   - Output: Complete Monaco editor configuration
   - Integration: Generate configs dynamically

2. **T121**: Implement SSE handler skill
   - Skill file: `frontend/sse-handler.py`
   - Input: Event type, priority, data
   - Output: Transformed SSEEvent with proper formatting
   - Integration: Process events before display

3. **T122**: Create MCP client wrapper for skill invocation
   - Client: `frontend/src/lib/mcp/client.ts`
   - Methods: `invokeSkill(skillName, input)`
   - Error handling and fallback logic
   - Connection management

4. **T123**: Integrate MCP skills with frontend components
   - Update MonacoEditor to use skill-based config
   - Update SSE client to use skill-based event processing
   - Add skill registry and discovery

5. **T124**: Add caching for skill responses
   - Implement LRU cache for skill outputs
   - Cache invalidation on skill updates
   - Performance optimization for repeated calls

6. **T125**: Write unit tests for MCP skill integration
   - Test skill invocation and response handling
   - Test error scenarios and fallbacks
   - Test cache behavior
   - Test integration with components

7. **T126**: Document MCP skill usage patterns
   - Create usage guide for developers
   - Document skill interfaces and contracts
   - Provide examples and best practices

**Test Criteria**:
- [ ] Monaco config skill generates valid configurations
- [ ] SSE handler skill processes events correctly
- [ ] MCP integration reduces manual code by 88%
- [ ] Skill responses are cached appropriately
- [ ] Fallback logic works when MCP service is unavailable
- [ ] Skills can be updated without frontend deployment

**Dependencies**: MCP service must be available (can start with mock implementation)

---

### 3.5 Performance Optimization (T130-T136)

**Objective**: Achieve sub-200ms load times and optimize bundle size for production deployment.

**Implementation Plan**:

1. **T130**: Implement code splitting for Monaco Editor
   - Dynamic import: `import('@monaco-editor/react')`
   - Loading skeleton with progress indicator
   - Error boundary for failed loads
   - Update MonacoEditor component: `frontend/src/components/organisms/MonacoEditor.tsx:35-60`

2. **T131**: Add lazy loading for dashboard components
   - React.lazy for dashboard widgets
   - Suspense boundaries around sections
   - Loading states for each component
   - Update dashboard page: `frontend/src/app/dashboard/page.tsx`

3. **T132**: Optimize bundle size with webpack chunking
   - Configure webpack chunks in `next.config.js`
   - Separate vendor chunks for large libraries
   - Analyze bundle with `@next/bundle-analyzer`
   - Target: <500KB initial bundle (excluding Monaco)

4. **T133**: Implement image optimization with Next.js Image
   - Replace <img> with <Image> component
   - Configure image domains in `next.config.js`
   - Add lazy loading and blur placeholders
   - Optimize dashboard visualizations

5. **T134**: Add compression (Brotli) for static assets
   - Configure compression in Next.js
   - Enable Brotli compression for supported browsers
   - Add compression headers to API responses
   - Monitor compression ratios

6. **T135**: Create performance monitoring middleware
   - Middleware: `frontend/src/middleware/performance.ts`
   - Track Core Web Vitals (LCP, FID, CLS)
   - Send metrics to analytics backend
   - Alert on performance degradation

7. **T136**: Write performance budget tests
   - Bundle size tests: enforce <500KB limit
   - Load time tests: enforce <200ms Monaco load
   - Memory usage tests: prevent memory leaks
   - Performance CI/CD integration

**Test Criteria**:
- [ ] Initial bundle size <500KB (excluding Monaco)
- [ ] Monaco Editor loads in <200ms
- [ ] Images are optimized and lazy-loaded
- [ ] Performance budget passes all metrics
- [ ] Core Web Vitals meet "Good" thresholds
- [ ] No memory leaks in long-running sessions

**Dependencies**: Build pipeline must support bundle analysis

---

## Cross-Workstream Dependencies

```
Dapr Integration (T090-T096)   →  API Integration (T110-T116)
       ↓                               ↓
Kong Integration (T100-T106)   →  MCP Skills (T120-T126)
       ↓                               ↓
Performance (T130-T136) ←─────────────────────────┘
```

**Critical Path**: Dapr → API Integration → Performance Optimization
**Parallelizable**: Kong Integration and MCP Skills can run alongside Dapr/API work

---

## Risk Analysis & Mitigation

### High Risk Items

1. **Dapr Event Flow Complexity**
   - **Risk**: Events not reaching frontend due to topic misconfiguration
   - **Mitigation**: Implement comprehensive logging and dead-letter queue
   - **Kill Switch**: Fallback to simulated events if Dapr unavailable

2. **Kong JWT Token Refresh**
   - **Risk**: Token refresh failures causing user logouts
   - **Mitigation**: Implement refresh token rotation with exponential backoff
   - **Kill Switch**: Graceful degradation to read-only mode

3. **API Response Time Degradation**
   - **Risk**: Backend API slowness affecting frontend performance
   - **Mitigation**: Implement aggressive caching and request timeouts
   - **Kill Switch**: Show cached data with "stale" indicators

### Medium Risk Items

4. **MCP Service Availability**
   - **Risk**: MCP service downtime affecting configuration generation
   - **Mitigation**: Fallback to hardcoded configurations with feature flag
   - **Monitoring**: Health check alerts for MCP service

5. **Bundle Size Overflow**
   - **Risk**: Performance optimization fails to meet targets
   - **Mitigation**: Progressive optimization with feature flags
   - **Contingency**: Disable non-critical features if needed

---

## Testing Strategy

### Integration Testing (Week 3, Days 1-2)
- [ ] Dapr → Frontend event flow integration tests
- [ ] Kong JWT validation security tests
- [ ] API endpoint integration tests with mock backend
- [ ] MCP skill invocation tests
- [ ] Performance baseline measurements

### End-to-End Testing (Week 3, Days 3-4)
- [ ] Complete user journey: Login → Dashboard → Code Editor → Submission
- [ ] Real-time event flow: Backend → Dapr → Kong → Frontend
- [ ] Error scenarios: Network failures, token expiry, rate limiting
- [ ] Mobile responsiveness testing

### Performance Testing (Week 4, Days 1-2)
- [ ] Load testing: 100 concurrent users
- [ ] Bundle size validation
- [ ] Memory leak detection (24-hour run)
- [ ] Core Web Vitals measurement

### Security Testing (Week 4, Days 3-4)
- [ ] JWT token validation tests
- [ ] Rate limiting abuse scenarios
- [ ] CORS policy validation
- [ ] Input validation and XSS prevention

---

## Deployment Readiness Checklist

### Infrastructure
- [ ] Dapr sidecar deployed to frontend namespace
- [ ] Kong routes configured for frontend API
- [ ] Redis cache available for performance optimization
- [ ] Monitoring stack configured (Prometheus + Grafana)

### Frontend
- [ ] Environment variables configured:
  - `NEXT_PUBLIC_DAPR_ENDPOINT`
  - `NEXT_PUBLIC_KONG_ENDPOINT`
  - `NEXT_PUBLIC_MCP_ENDPOINT`
- [ ] Feature flags for gradual rollout
- [ ] Error boundaries and logging configured
- [ ] Health check endpoints implemented

### Documentation
- [ ] API integration guide
- [ ] Dapr event flow documentation
- [ ] Kong security configuration guide
- [ ] Performance optimization guide

---

## Success Metrics

### Functional Metrics
- ✅ 100% of Phase 2 features working with real backend data
- ✅ Real-time events flowing with <100ms latency
- ✅ JWT authentication working on all protected routes
- ✅ API integration test coverage >90%

### Performance Metrics
- ✅ Initial bundle size <500KB (excluding Monaco)
- ✅ Monaco Editor load time <200ms
- ✅ API response time <500ms (p95)
- ✅ Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1

### Security Metrics
- ✅ 0 critical security vulnerabilities
- ✅ Rate limiting prevents brute force attacks
- ✅ JWT tokens properly validated and refreshed
- ✅ CORS configured for frontend origin only

### Quality Metrics
- ✅ 0 TypeScript errors
- ✅ Integration test pass rate 100%
- ✅ No console errors in production build
- ✅ E2E test coverage of critical paths

---

## Rollback Plan

### Phase 3 Rollback (If Issues Detected)
1. **Immediate**: Disable Dapr integration via feature flag
2. **Short-term**: Revert to mock data (Phase 2 state)
3. **Medium-term**: Fix issues in staging environment
4. **Long-term**: Redeploy with fixes

### Feature-Specific Rollback
- **Dapr Issues**: `FEATURE_DAPR_INTEGRATION=false`
- **Kong Issues**: `FEATURE_KONG_AUTH=false`
- **API Issues**: `FEATURE_API_INTEGRATION=false`
- **MCP Issues**: `FEATURE_MCP_SKILLS=false`

---

## Next Steps

1. **Immediate**: Review and approve Phase 3 plan
2. **Day 1**: Start Dapr integration (T090-T092)
3. **Day 2**: Begin Kong integration (T100-T102)
4. **Day 3**: Start API integration (T110-T113)
5. **Day 4**: Implement MCP skills (T120-T123)
6. **Day 5**: Performance optimization (T130-T136)
7. **Day 6-7**: Testing and bug fixes
8. **Day 8**: Deployment preparation

**Ready to proceed?** Let me know when you'd like to start Phase 3 implementation, and I'll begin with the Dapr integration tasks.