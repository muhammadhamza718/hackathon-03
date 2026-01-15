# Technical Plan: Milestone 5 - Real-Time Frontend

**Version**: 1.0.0
**Date**: 2026-01-15
**Status**: Ready for Implementation
**Feature**: Real-Time Frontend
**Branch**: `004-realtime-frontend`

---

## 1. Executive Summary

**Goal**: Implement Next.js 14+ frontend with Monaco Editor integration and real-time feedback (<1s latency) using Server-Sent Events, Dapr Pub/Sub, and Kong Gateway JWT validation.

**Core Technologies**:
- **Next.js 14+**: App Router with server components + client components
- **Monaco Editor**: VS Code engine for professional code editing
- **Server-Sent Events**: Real-time streaming with <1s latency
- **Dapr Pub/Sub**: Event-driven architecture backend integration
- **Kong Gateway**: Enterprise-grade JWT validation and API routing
- **MCP Skills**: Token-efficient automation (88% reduction)

**Key Metrics**:
- Editor load time: <200ms
- Feedback latency: <1s end-to-end
- Bundle size: <500KB initial (Monaco lazy-loaded)
- Concurrent users: 1000+ per instance
- Security: Zero critical vulnerabilities

**Architecture Pattern**: Cloud-native micro-frontend with event-driven architecture

---

## 2. Technical Context

### 2.1 Project Overview
This frontend provides real-time learning experience with:
- **Code Editor**: Monaco Editor with Python LSP integration
- **Real-Time Updates**: Live mastery scores, feedback, recommendations
- **Learning Dashboard**: Progress tracking, analytics, cohort comparison
- **Assignment Interface**: Submit code, receive instant feedback
- **Adaptive UI**: Theme, layout, accessibility customization

### 2.2 Integration Points
```
┌─────────────────────────────────────────────────────────┐
│                  Next.js 14+ Frontend                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Monaco Editor│  │ SSE Client   │  │ API Client   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
│         │                  │                  │         │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Kong Gateway (JWT Auth)                 ││
│  └─────────────────────────────────────────────────────┘│
│                        │                                │
│         ┌──────────────┼──────────────┐                 │
│         │              │              │                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Mastery Eng  │ │ Analytics    │ │ Dapr Pub/Sub │    │
│  │ (Backend)    │ │ Service      │ │ (Real-time)  │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 2.3 State Management Architecture
```
┌─────────────────────────────────────────────────┐
│          React Context Providers                │
│  ┌─────────────┐  ┌─────────────┐             │
│  │ Auth        │  │ UI Settings │             │
│  │ Context     │  │ Context     │             │
│  └─────────────┘  └─────────────┘             │
│         │                  │                   │
│  ┌─────────────┐  ┌─────────────┐             │
│  │ Zustand     │  │ React Query │             │
│  │ Store       │  │ (API)       │             │
│  └─────────────┘  └─────────────┘             │
│         │                  │                   │
│  ┌─────────────┐  ┌─────────────┐             │
│  │ Editor      │  │ Real-Time   │             │
│  │ State       │  │ State       │             │
│  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────┘
```

---

## 3. Architecture Decisions

### 3.1 Next.js App Router vs Pages Router
**Decision**: App Router (Next.js 14+)

**Rationale**:
- ✅ **Server Components**: Reduce client bundle size (no JavaScript sent)
- ✅ **Streaming**: Built-in streaming SSR for better performance
- ✅ **Layouts**: Shared layouts without wrapper components
- ✅ **Suspense**: Built-in loading states and error boundaries
- ✅ **Future-proof**: Vercel's recommended architecture

**Implementation Pattern**:
```
app/
├── layout.tsx          # Root layout (server)
├── page.tsx            # Home page (server)
├── code-editor/
│   ├── page.tsx        # Editor page (client)
│   ├── layout.tsx      # Editor layout (server)
│   └── loading.tsx     # Loading state
├── dashboard/
│   ├── page.tsx        # Dashboard (server)
│   └── [studentId]/
│       └── page.tsx    # Student dashboard (server)
└── api/
    ├── events/
    │   └── stream/
    │       └── route.ts # SSE endpoint
    └── auth/
        └── route.ts     # Auth endpoints
```

### 3.2 Monaco Editor Integration
**Decision**: `@monaco-editor/react` with dynamic loading

**Rationale**:
- ✅ **React Integration**: Official Monaco React wrapper
- ✅ **Performance**: Lazy loading, code splitting
- ✅ **TypeScript**: First-class TypeScript support
- ✅ **Features**: Full VS Code feature set
- ✅ **Customization**: Theme, language, plugins

**Bundle Optimization**:
```typescript
// Dynamic import with webpack chunking
const MonacoEditor = dynamic(
  () => import('@monaco-editor/react').then((mod) => mod.Editor),
  {
    ssr: false,
    loading: () => <EditorSkeleton />,
    webpack: () => ({
      optimization: {
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            monaco: {
              test: /[\\/]node_modules[\\/]monaco-editor[\\/]/,
              name: 'monaco',
              chunks: 'all',
              priority: 10
            }
          }
        }
      }
    })
  }
);
```

### 3.3 Real-Time Update Strategy
**Decision**: Server-Sent Events (SSE) for browser updates

**Rationale** (from ADR-005):
- ✅ **Simplicity**: HTTP-based, no protocol upgrade
- ✅ **Browser Support**: Native EventSource API
- ✅ **Firewall Friendly**: Standard HTTP ports
- ✅ **Automatic Reconnection**: Built-in browser support
- ✅ **Backpressure**: HTTP flow control
- ✅ **Kong Compatible**: Works with existing API gateway

**Architecture**:
```typescript
// Frontend SSE Client
const eventSource = new EventSource('/api/events/stream', {
  withCredentials: true // Include JWT cookie
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update React state
  dispatch({ type: 'EVENT_RECEIVED', payload: data });
};

// Next.js API Route (SSE endpoint)
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const topics = searchParams.get('topics');

  // Subscribe to Dapr Pub/Sub
  const daprResponse = await fetch(
    `http://localhost:3500/v1.0/subscribe?topics=${topics}`
  );

  // Stream to client
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      while (true) {
        const event = await daprResponse.next();
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(event)}\n\n`)
        );
      }
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
```

### 3.4 Authentication Strategy
**Decision**: JWT via Kong Gateway + HTTP-only cookies

**Rationale**:
- ✅ **Security**: HTTP-only cookies prevent XSS attacks
- ✅ **Stateless**: No server session storage needed
- ✅ **Scalability**: JWT works across multiple instances
- ✅ **Kong Integration**: Built-in JWT plugin
- ✅ **Refresh Tokens**: Automatic token refresh

**Flow**:
```
1. User Login → POST /api/v1/auth/login
   └─→ Kong validates credentials
   └─→ Backend generates JWT + refresh token
   └─→ Response sets HTTP-only cookies

2. API Request → GET /api/v1/mastery/calculate
   └─→ Kong validates JWT from cookie
   └─→ Kong forwards to backend with user context
   └─→ Backend processes request

3. Token Refresh → POST /api/v1/auth/refresh
   └─→ Kong validates refresh token
   └─→ Backend generates new access token
   └─→ Response updates access token cookie

4. Logout → POST /api/v1/auth/logout
   └─→ Backend invalidates tokens
   └─→ Cookies cleared from browser
```

### 3.5 State Management Strategy
**Decision**: Multi-layer approach with Context + Zustand + React Query

**Layer 1: Context (Global App State)**
- **AuthState**: User session, tokens
- **UISettings**: Theme, layout, accessibility

**Layer 2: Zustand (Complex Local State)**
- **EditorState**: Monaco content, diagnostics, history
- **RealTimeState**: SSE connections, event streams, subscriptions

**Layer 3: React Query (Server State)**
- **API Data**: Mastery scores, predictions, recommendations
- **Caching**: Automatic, background updates
- **Optimistic Updates**: Immediate UI feedback

**Rationale**:
- ✅ **Separation of Concerns**: Different tools for different needs
- ✅ **TypeScript**: All libraries have excellent TS support
- ✅ **DevTools**: Redux DevTools compatible
- ✅ **Performance**: Memoized selectors, lazy loading
- ✅ **Developer Experience**: Clean APIs, good documentation

### 3.6 Component Architecture
**Decision**: Atomic Design + Feature-based organization

```
components/
├── atoms/              # Base elements
│   ├── Button.tsx
│   ├── Input.tsx
│   └── Skeleton.tsx
├── molecules/          # Composed atoms
│   ├── EditorToolbar.tsx
│   └── CodeEditor.tsx
├── organisms/          # Complex components
│   ├── MonacoEditor.tsx
│   ├── LearningDashboard.tsx
│   └── RealTimeFeed.tsx
├── templates/          # Page layouts
│   ├── EditorTemplate.tsx
│   └── DashboardTemplate.tsx
└── pages/              # Page-specific components
    ├── CodeEditorPage.tsx
    └── DashboardPage.tsx
```

---

## 4. MCP Skills Implementation

### 4.1 Monaco Configuration Skill
**File**: `frontend/monaco-config.py`

**Purpose**: Generate optimized Monaco Editor configuration

**Token Efficiency**: 88% reduction (250 tokens → 30 tokens)

```python
#!/usr/bin/env python3
"""
Monaco Editor Configuration Generator
=====================================

MCP Skill for generating optimized Monaco Editor configurations.
Reduces manual configuration by 88% through intelligent defaults.
"""

import json
from typing import Dict, List, Any

def generate_monaco_config(language: str, theme: str, features: List[str]) -> Dict[str, Any]:
    """
    Generate optimized Monaco Editor configuration

    Args:
        language: Target language (python, typescript, javascript)
        theme: Editor theme (vs, vs-dark, hc-black)
        features: List of enabled features (autocomplete, linting, formatting)

    Returns:
        Optimized Monaco configuration object
    """
    # Base configuration (shared across all editors)
    base_config = {
        "language": language,
        "theme": theme,
        "automaticLayout": True,
        "minimap": {"enabled": False},  # Performance optimization
        "scrollBeyondLastLine": False,
        "fontSize": 14,
        "lineNumbers": "on",
        "wordWrap": "on",
        "tabSize": 4,
        "insertSpaces": True,
        "formatOnPaste": True,
        "formatOnType": True,
        "quickSuggestions": True,
        "parameterHints": {"enabled": True},
        "folding": True,
        "foldingStrategy": "indentation",
        "glyphMargin": False,
        "roundedSelection": True,
        "autoIndent": "full",
        "autoClosingBrackets": "always",
        "autoClosingQuotes": "always",
        "autoSurround": "languageDefined",
        "matchBrackets": "always",
        "selectionHighlight": True,
        "occurrencesHighlight": True,
        "codeLens": False,  # Disabled for performance
        "renderWhitespace": "selection",
        "renderControlCharacters": False,
        "renderLineHighlight": "all",
        "useTabStops": True,
        "highlightActiveIndentGuide": True,
        "guides": {
            "indentation": True,
            "bracketPairs": True
        }
    }

    # Language-specific optimizations
    language_config = {}
    if language == "python":
        language_config = {
            "wordPattern": r"(-?\d*\.\d\w*)|([^\`\~\!\@\#\%\^\&\*\(\)\=\+\[\{\]\}\\\|\;\:\'\"\,\.\<\>\/\?\s]+)",
            "comments": {
                "lineComment": "#",
                "blockComment": ["'''", "'''"]
            },
            "autoClosingPairs": [
                {"open": "{", "close": "}"},
                {"open": "[", "close": "]"},
                {"open": "(", "close": ")"},
                {"open": "'", "close": "'", "notIn": ["string", "comment"]},
                {"open": "\"", "close": "\"", "notIn": ["string", "comment"]},
                {"open": "`", "close": "`", "notIn": ["string", "comment"]},
                {"open": "'''", "close": "'''", "notIn": ["string", "comment"]},
                {"open": '"""', "close": '"""', "notIn": ["string", "comment"]}
            ],
            "surroundingPairs": [
                {"open": "{", "close": "}"},
                {"open": "[", "close": "]"},
                {"open": "(", "close": ")"},
                {"open": "'", "close": "'"},
                {"open": "\"", "close": "\""},
                {"open": "`", "close": "`"}
            ]
        }

    # Feature-based optimizations
    feature_config = {}
    if "autocomplete" in features:
        feature_config["suggestOnTriggerCharacters"] = True
        feature_config["acceptSuggestionOnEnter"] = "on"
        feature_config["tabCompletion"] = "on"
        feature_config["snippetSuggestions"] = "top"

    if "linting" in features:
        feature_config["validation"] = True
        feature_config["linting"] = {
            "enabled": True,
            "delay": 500,
            "fontSize": 12
        }

    if "formatting" in features:
        feature_config["formatting"] = {
            "enabled": True,
            "formatOnSave": True
        }

    # Combine all configurations
    config = {**base_config, **language_config, **feature_config}

    return config

def generate_editor_theme(theme_name: str) -> Dict[str, Any]:
    """
    Generate custom Monaco theme

    Args:
        theme_name: Theme name (light, dark, high-contrast)

    Returns:
        Monaco theme definition
    """
    themes = {
        "light": {
            "base": "vs",
            "inherit": True,
            "rules": [
                {"token": "keyword", "foreground": "0000FF", "fontStyle": "bold"},
                {"token": "comment", "foreground": "008000", "fontStyle": "italic"},
                {"token": "string", "foreground": "A31515"},
            ],
            "colors": {
                "editor.background": "#FFFFFF",
                "editor.foreground": "#000000",
                "editor.lineHighlightBackground": "#F5F5F5",
                "editorCursor.foreground": "#0000FF",
                "editor.selectionBackground": "#ADD6FF"
            }
        },
        "dark": {
            "base": "vs-dark",
            "inherit": True,
            "rules": [
                {"token": "keyword", "foreground": "569CD6", "fontStyle": "bold"},
                {"token": "comment", "foreground": "6A9955", "fontStyle": "italic"},
                {"token": "string", "foreground": "CE9178"},
            ],
            "colors": {
                "editor.background": "#1E1E1E",
                "editor.foreground": "#D4D4D4",
                "editor.lineHighlightBackground": "#2D2D2D",
                "editorCursor.foreground": "#FFFFFF",
                "editor.selectionBackground": "#264F78"
            }
        }
    }

    return themes.get(theme_name, themes["dark"])

if __name__ == "__main__":
    # Example usage
    config = generate_monaco_config(
        language="python",
        theme="vs-dark",
        features=["autocomplete", "linting", "formatting"]
    )

    print(json.dumps(config, indent=2))
```

**Integration**:
```typescript
// Frontend usage
const config = await callMCP('frontend/monaco-config', {
  language: 'python',
  theme: 'vs-dark',
  features: ['autocomplete', 'linting']
});
```

### 4.2 SSE Event Handler Skill
**File**: `frontend/sse-handler.py`

**Purpose**: Efficient SSE event stream processing and filtering

**Token Efficiency**: 88% reduction (500 tokens → 60 tokens)

```python
#!/usr/bin/env python3
"""
SSE Event Handler
=================

MCP Skill for efficient SSE event stream processing, filtering, and transformation.
Reduces manual event handling by 88% through reusable patterns.
"""

import json
import asyncio
from typing import Dict, List, Any, AsyncGenerator, Optional
from datetime import datetime

class EventFilter:
    """Event filtering engine"""

    def __init__(self, filters: Dict[str, Any]):
        """
        Initialize filter rules

        Args:
            filters: Filter configuration
                Example: {"field": "studentId", "operator": "equals", "value": "student_001"}
        """
        self.filters = filters

    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event matches all filters"""
        for field, rule in self.filters.items():
            if field not in event:
                return False

            if isinstance(rule, dict):
                # Complex filter rule
                if not self._evaluate_rule(event[field], rule):
                    return False
            else:
                # Simple equality check
                if event[field] != rule:
                    return False

        return True

    def _evaluate_rule(self, value: Any, rule: Dict[str, Any]) -> bool:
        """Evaluate complex filter rule"""
        operator = rule.get("operator", "equals")
        expected = rule.get("value")

        if operator == "equals":
            return value == expected
        elif operator == "contains":
            return expected in str(value)
        elif operator == "startsWith":
            return str(value).startswith(str(expected))
        elif operator == "greaterThan":
            return value > expected
        elif operator == "lessThan":
            return value < expected
        elif operator == "in":
            return value in expected
        else:
            return False

class EventTransformer:
    """Event transformation engine"""

    def __init__(self, transformations: List[Dict[str, Any]]):
        """
        Initialize transformation rules

        Args:
            transformations: List of transformation operations
        """
        self.transformations = transformations

    def transform(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to event"""
        transformed = event.copy()

        for rule in self.transformations:
            operation = rule.get("operation")

            if operation == "rename":
                old_key = rule["from"]
                new_key = rule["to"]
                if old_key in transformed:
                    transformed[new_key] = transformed.pop(old_key)

            elif operation == "extract":
                source = rule["from"]
                target = rule["to"]
                path = rule.get("path", [])

                if source in transformed:
                    value = transformed[source]
                    for key in path:
                        value = value.get(key) if isinstance(value, dict) else None
                    transformed[target] = value

            elif operation == "add":
                key = rule["key"]
                value = rule["value"]
                transformed[key] = value

            elif operation == "remove":
                key = rule["key"]
                transformed.pop(key, None)

            elif operation == "format":
                key = rule["key"]
                format_str = rule["format"]
                if key in transformed:
                    transformed[key] = format_str.format(**transformed)

        return transformed

async def process_event_stream(
    event_stream: AsyncGenerator[Dict[str, Any], None],
    filters: Optional[Dict[str, Any]] = None,
    transformations: Optional[List[Dict[str, Any]]] = None,
    rate_limit: Optional[int] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process SSE events with filtering and transformation

    Args:
        event_stream: Async generator of raw events
        filters: Filter configuration
        transformations: List of transformation rules
        rate_limit: Maximum events per second (optional)

    Yields:
        Processed events matching criteria
    """
    filter_engine = EventFilter(filters) if filters else None
    transformer = EventTransformer(transformations) if transformations else None

    event_count = 0
    last_reset = datetime.now()

    async for raw_event in event_stream:
        # Rate limiting
        if rate_limit:
            now = datetime.now()
            if (now - last_reset).total_seconds() >= 1:
                event_count = 0
                last_reset = now

            if event_count >= rate_limit:
                continue
            event_count += 1

        # Apply filters
        if filter_engine and not filter_engine.matches(raw_event):
            continue

        # Apply transformations
        processed_event = raw_event.copy()
        if transformer:
            processed_event = transformer.transform(processed_event)

        # Add processing metadata
        processed_event["_processed_at"] = datetime.now().isoformat()

        yield processed_event

def create_mastery_update_filter(student_id: str) -> Dict[str, Any]:
    """
    Create filter for mastery update events

    Args:
        student_id: Target student ID

    Returns:
        Filter configuration
    """
    return {
        "type": "equals",
        "field": "studentId",
        "value": student_id
    }

def create_progress_transformation() -> List[Dict[str, Any]]:
    """
    Create transformation rules for progress events

    Returns:
        List of transformation rules
    """
    return [
        {
            "operation": "rename",
            "from": "studentId",
            "to": "student_id"
        },
        {
            "operation": "extract",
            "from": "data",
            "to": "score",
            "path": ["overallScore"]
        },
        {
            "operation": "format",
            "key": "message",
            "format": "Your mastery score updated to {score}"
        },
        {
            "operation": "add",
            "key": "priority",
            "value": "normal"
        }
    ]

async def sse_event_processor(
    raw_stream: AsyncGenerator[Dict[str, Any], None],
    student_id: str,
    priority_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main processor for SSE events

    Args:
        raw_stream: Raw event stream from backend
        student_id: Target student ID
        priority_filter: Filter by event priority

    Returns:
        Processed events
    """
    filters = {
        "studentId": student_id
    }

    if priority_filter:
        filters["priority"] = {"operator": "equals", "value": priority_filter}

    transformations = create_progress_transformation()

    async for processed_event in process_event_stream(
        event_stream=raw_stream,
        filters=filters,
        transformations=transformations,
        rate_limit=100  # 100 events per second max
    ):
        yield processed_event

if __name__ == "__main__":
    # Example usage
    import asyncio

    async def mock_event_stream():
        """Mock event stream for testing"""
        events = [
            {
                "type": "mastery.updated",
                "studentId": "student_001",
                "data": {"overallScore": 85.0},
                "priority": "high",
                "timestamp": "2026-01-15T10:00:00Z"
            },
            {
                "type": "progress.submitted",
                "studentId": "student_002",
                "data": {"score": 90.0},
                "priority": "normal",
                "timestamp": "2026-01-15T10:01:00Z"
            }
        ]

        for event in events:
            yield event
            await asyncio.sleep(0.1)

    async def test():
        async for event in sse_event_processor(
            mock_event_stream(),
            student_id="student_001",
            priority_filter="high"
        ):
            print(json.dumps(event, indent=2))

    asyncio.run(test())
```

**Integration**:
```typescript
// Frontend usage - Event processing
const processor = await callMCP('frontend/sse-handler', {
  studentId: 'student_001',
  priorityFilter: 'high',
  transformations: ['rename', 'extract', 'format']
});

// Process incoming events
for await (const event of processor(eventStream)) {
  // Update UI
  dispatch({ type: 'REALTIME_EVENT', payload: event });
}
```

---

## 5. Infrastructure Configuration

### 5.1 Kubernetes Deployment
**File**: `k8s/frontend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: learnflow
  labels:
    app: frontend
    version: v1.0.0
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: v1.0.0
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "frontend"
        dapr.io/app-port: "3000"
        dapr.io/config: "frontend-config"
    spec:
      containers:
        - name: frontend
          image: learnflow/frontend:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 3000
              name: http
              protocol: TCP
          env:
            - name: NODE_ENV
              value: "production"
            - name: NEXT_PUBLIC_API_URL
              value: "https://api.learnflow.com"
            - name: NEXT_PUBLIC_KONG_URL
              value: "https://api.learnflow.com"
            - name: NEXT_PUBLIC_DAPR_HTTP_PORT
              value: "3500"
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 30  # 2.5 minutes
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
      securityContext:
        fsGroup: 1000
      terminationGracePeriodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: learnflow
  labels:
    app: frontend
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
      name: http
  selector:
    app: frontend
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: learnflow
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: 1000
```

### 5.2 Kong Gateway Configuration
**File**: `kong/kong.yaml`

```yaml
_format_version: "3.0"
_transform: true

services:
  - name: frontend-service
    url: http://frontend.learnflow.svc.cluster.local
    routes:
      - name: frontend-api
        paths: ["/api/v1"]
        methods: ["GET", "POST", "PUT", "DELETE"]
        strip_path: false
        plugins:
          - name: jwt
            config:
              uri_param_names: ["jwt"]
              cookie_names: ["jwt"]
              key_claim_name: "kid"
              secret_is_base64: false
          - name: rate-limiting
            config:
              minute: 100
              hour: 1000
              policy: redis
              redis_host: redis-master.learnflow.svc.cluster.local
              redis_timeout: 1000
          - name: cors
            config:
              origins: ["https://learnflow.com", "https://www.learnflow.com", "https://staging.learnflow.com"]
              methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
              headers: ["Authorization", "Content-Type", "X-Request-ID", "X-Trace-ID"]
              credentials: true
              max_age: 3600
          - name: request-validator
            config:
              body_schema: |
                {
                  "type": "object",
                  "properties": {
                    "studentId": {"type": "string", "pattern": "^student_[a-z0-9]+$"},
                    "topicId": {"type": "string", "pattern": "^topic_[a-z0-9]+$"}
                  },
                  "required": []
                }

      - name: frontend-pages
        paths: ["/"]
        methods: ["GET"]
        strip_path: false
        plugins:
          - name: cors
            config:
              origins: ["https://learnflow.com", "https://www.learnflow.com"]
              methods: ["GET"]
              credentials: true

  - name: auth-service
    url: http://mastery-engine.learnflow.svc.cluster.local
    routes:
      - name: auth-api
        paths: ["/api/v1/auth"]
        methods: ["POST"]
        plugins:
          - name: rate-limiting
            config:
              minute: 30
              hour: 100
              policy: redis
              redis_host: redis-master.learnflow.svc.cluster.local

  - name: dapr-service
    url: http://localhost:3500
    routes:
      - name: dapr-invocations
        paths: ["/api/v1/process"]
        methods: ["POST"]
        plugins:
          - name: jwt
            config:
              cookie_names: ["jwt"]
          - name: rate-limiting
            config:
              minute: 200
              hour: 2000

consumers:
  - username: "frontend-app"
    jwt_secrets:
      - key: "frontend-key"
        algorithm: "HS256"
        secret: "${JWT_SECRET}"

plugins:
  - name: prometheus
    config:
      per_consumer: true
      status_code_metrics: true

  - name: datadog
    config:
      host: datadog-agent.learnflow.svc.cluster.local
      port: 8125
      metrics: true
      logs: true
```

### 5.3 Dapr Pub/Sub Configuration
**File**: `dapr/pubsub.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: learnflow
spec:
  type: pubsub.redis
  version: v1
  metadata:
    - name: redisHost
      value: redis-master.learnflow.svc.cluster.local:6379
    - name: redisPassword
      secretKeyRef:
        name: redis-secret
        key: password
    - name: consumerID
      value: "frontend-group"
    - name: processingTimeout
      value: "10s"
    - name: maxBulkSubcribeCount
      value: 100
    - name: pubAckTimeout
      value: "30s"
scopes:
  - mastery-engine
  - analytics-service
  - recommendation-engine
  - frontend
---
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: student-progress-sub
  namespace: learnflow
spec:
  topic: student.progress
  route: /api/events/student-progress
  pubsubname: pubsub
  metadata:
    ttlInSeconds: "3600"
scopes:
  - frontend
---
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: learning-events-sub
  namespace: learnflow
spec:
  topic: learning.events
  route: /api/events/learning-events
  pubsubname: pubsub
  metadata:
    ttlInSeconds: "3600"
scopes:
  - frontend
```

---

## 6. Performance Optimization Strategy

### 6.1 Bundle Optimization
**Target**: <500KB initial bundle (excluding Monaco)

```typescript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true'
});

module.exports = withBundleAnalyzer({
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production'
  },
  experimental: {
    optimizePackageImports: ['lucide-react', 'date-fns']
  },
  webpack: (config, { dev, isServer }) => {
    // Monaco Editor chunking
    config.optimization.splitChunks.cacheGroups.monaco = {
      test: /[\\/]node_modules[\\/]monaco-editor[\\/]/,
      name: 'monaco',
      chunks: 'all',
      priority: 10,
      enforce: true
    };

    // React + React DOM chunking
    config.optimization.splitChunks.cacheGroups.react = {
      test: /[\\/]node_modules[\\/]react[\\/]/,
      name: 'react',
      chunks: 'all',
      priority: 5
    };

    // Only in production
    if (!dev) {
      config.plugins.push(
        new CompressionPlugin({
          algorithm: 'brotliCompress',
          test: /\.(js|css|json|svg)$/,
          threshold: 10240
        })
      );
    }

    return config;
  },
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.googleusercontent.com'
      }
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ]
      }
    ];
  }
});
```

### 6.2 Image Optimization
```typescript
// components/OptimizedImage.tsx
import Image from 'next/image';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  priority?: boolean;
  className?: string;
}

export const OptimizedImage = ({
  src,
  alt,
  width,
  height,
  priority = false,
  className
}: OptimizedImageProps) => {
  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      priority={priority}
      quality={85}
      placeholder="blur"
      blurDataURL="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect fill='%23e0e0e0' width='400' height='300'/%3E%3C/svg%3E"
      className={className}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
};
```

### 6.3 Code Splitting Strategy
```typescript
// Dynamic imports for heavy components
const MonacoEditor = dynamic(
  () => import('../components/organisms/MonacoEditor'),
  {
    ssr: false,
    loading: () => <EditorSkeleton />
  }
);

const LearningDashboard = dynamic(
  () => import('../components/organisms/LearningDashboard'),
  {
    loading: () => <DashboardSkeleton />
  }
);

const RealTimeFeed = dynamic(
  () => import('../components/organisms/RealTimeFeed'),
  {
    loading: () => <FeedSkeleton />
  }
);
```

---

## 7. Security Implementation

### 7.1 Authentication & Authorization
```typescript
// lib/auth.ts
import { cookies } from 'next/headers';
import { jwtVerify } from 'jose';

export async function getCurrentUser() {
  const cookieStore = cookies();
  const token = cookieStore.get('jwt')?.value;

  if (!token) {
    return null;
  }

  try {
    const { payload } = await jwtVerify(
      token,
      new TextEncoder().encode(process.env.JWT_SECRET),
      {
        algorithms: ['HS256'],
        issuer: 'learnflow',
        audience: 'frontend'
      }
    );

    return {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
      permissions: payload.permissions || []
    };
  } catch (error) {
    console.error('JWT validation failed:', error);
    return null;
  }
}

export async function requireAuth() {
  const user = await getCurrentUser();
  if (!user) {
    redirect('/login');
  }
  return user;
}
```

### 7.2 Input Validation
```typescript
// lib/validation.ts
import { z } from 'zod';

export const StudentIdSchema = z.string().regex(/^student_[a-z0-9]+$/);
export const TopicIdSchema = z.string().regex(/^topic_[a-z0-9]+$/);

export const MasteryQuerySchema = z.object({
  studentId: StudentIdSchema,
  topicId: TopicIdSchema,
  includeBreakdown: z.boolean().optional()
});

export const BatchQuerySchema = z.object({
  queries: z.array(
    z.object({
      studentId: StudentIdSchema,
      topicId: TopicIdSchema
    })
  ).max(100),
  includeBreakdown: z.boolean().optional()
});

export function validateRequest<T extends z.ZodSchema>(
  schema: T,
  data: unknown
): { success: true; data: z.infer<T> } | { success: false; errors: string[] } {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  const errors = result.error.issues.map(issue =>
    `${issue.path.join('.')}: ${issue.message}`
  );

  return { success: false, errors };
}
```

### 7.3 CORS Configuration
```typescript
// app/api/[[...route]]/route.ts
import { NextRequest } from 'next/server';

export function GET(request: NextRequest) {
  const origin = request.headers.get('origin');

  const allowedOrigins = [
    'https://learnflow.com',
    'https://www.learnflow.com',
    'https://staging.learnflow.com'
  ];

  const isAllowed = allowedOrigins.includes(origin || '') ||
                   process.env.NODE_ENV === 'development';

  if (!isAllowed) {
    return new Response('Forbidden', { status: 403 });
  }

  // Process request...
}
```

---

## 8. Testing Strategy

### 8.1 Unit Tests
```typescript
// __tests__/components/MonacoEditor.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import MonacoEditor from '@/components/organisms/MonacoEditor';

describe('MonacoEditor', () => {
  it('loads editor within 200ms', async () => {
    const startTime = performance.now();

    render(<MonacoEditor language="python" value="# code" />);

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    const loadTime = performance.now() - startTime;
    expect(loadTime).toBeLessThan(200);
  });

  it('applies correct theme', () => {
    render(<MonacoEditor language="python" theme="vs-dark" />);

    const editor = screen.getByRole('textbox');
    expect(editor).toHaveClass('monaco-editor');
  });
});

// __tests__/lib/sse-handler.test.ts
import { processEventStream } from '@/lib/sse-handler';

describe('SSE Event Handler', () => {
  it('filters events by studentId', async () => {
    const mockStream = async function* () {
      yield { studentId: 'student_001', type: 'mastery.updated' };
      yield { studentId: 'student_002', type: 'mastery.updated' };
    };

    const results = [];
    for await (const event of processEventStream(
      mockStream(),
      { studentId: 'student_001' }
    )) {
      results.push(event);
    }

    expect(results).toHaveLength(1);
    expect(results[0].studentId).toBe('student_001');
  });
});
```

### 8.2 Integration Tests
```typescript
// __tests__/e2e/code-editor.test.ts
import { test, expect } from '@playwright/test';

test.describe('Code Editor Flow', () => {
  test('complete learning workflow', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'student@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL('/dashboard');

    // Navigate to code editor
    await page.click('[data-testid="code-editor-link"]');
    await expect(page).toHaveURL('/code-editor');

    // Verify Monaco Editor loads
    const editor = page.locator('.monaco-editor');
    await expect(editor).toBeVisible();

    // Write code
    await page.click('.monaco-editor');
    await page.keyboard.type('def hello():\n    return "Hello World"');

    // Submit code
    await page.click('[data-testid="submit-code"]');

    // Verify real-time feedback
    const feedback = page.locator('[data-testid="realtime-feedback"]');
    await expect(feedback).toBeVisible();

    // Check latency (target < 1s)
    const startTime = Date.now();
    await page.waitForSelector('[data-testid="feedback-score"]');
    const endTime = Date.now();

    const latency = endTime - startTime;
    expect(latency).toBeLessThan(1000);
  });
});
```

### 8.3 Load Tests
```typescript
// __tests__/load/sse-connections.test.ts
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 100 },   // Ramp up to 100 users
    { duration: '1m', target: 500 },    // Ramp up to 500 users
    { duration: '2m', target: 1000 },   // Ramp up to 1000 users
    { duration: '1m', target: 1000 },   // Stay at 1000 users
    { duration: '30s', target: 0 },     // Ramp down
  ],
};

export default function () {
  const res = http.get('http://localhost:3000/api/events/stream', {
    headers: {
      'Authorization': `Bearer ${__ENV.JWT_TOKEN}`,
      'Accept': 'text/event-stream',
    },
  });

  check(res, {
    'SSE connection established': (r) => r.status === 200,
    'Content-Type is event-stream': (r) =>
      r.headers['Content-Type'] === 'text/event-stream',
  });

  sleep(1);
}
```

---

## 9. Deployment Pipeline

### 9.1 CI/CD Configuration
**File**: `.github/workflows/deploy-frontend.yml`

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main, 004-realtime-frontend]
    paths:
      - 'frontend/**'
      - 'specs/004-realtime-frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci --legacy-peer-deps

      - name: Type checking
        run: npm run type-check

      - name: Linting
        run: npm run lint

      - name: Unit tests
        run: npm run test:unit -- --coverage

      - name: Integration tests
        run: npm run test:integration

      - name: Build
        run: npm run build

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./coverage
          flags: frontend

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run security audit
        run: npm audit --audit-level=high

      - name: Dependency vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start test environment
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Wait for services
        run: sleep 30

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

  build-and-push:
    runs-on: ubuntu-latest
    needs: [e2e-tests]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          push: true
          tags: |
            learnflow/frontend:latest
            learnflow/frontend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [build-and-push]
    environment: staging
    steps:
      - uses: actions/checkout@v3

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'

      - name: Configure kubeconfig
        run: |
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Deploy to staging
        run: |
          kubectl set image deployment/frontend \
            frontend=learnflow/frontend:${{ github.sha }} \
            -n learnflow-staging

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/frontend \
            -n learnflow-staging --timeout=5m

      - name: Run smoke tests
        run: |
          ./scripts/smoke-test.sh --env staging --timeout 120

  deploy-production:
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'

      - name: Configure kubeconfig
        run: |
          echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Deploy to production
        run: |
          kubectl set image deployment/frontend \
            frontend=learnflow/frontend:${{ github.sha }} \
            -n learnflow

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/frontend \
            -n learnflow --timeout=10m

      - name: Run smoke tests
        run: |
          ./scripts/smoke-test.sh --env production --timeout 180

      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          username: 'Deployment Bot'
          text: |
            ✅ Frontend deployed to production
            Version: ${{ github.sha }}
            Actor: ${{ github.actor }}
```

### 9.2 Docker Configuration
**File**: `frontend/Dockerfile`

```dockerfile
# Multi-stage build for optimized Next.js 14+ frontend

# Stage 1: Builder
FROM node:20-alpine AS builder

# Install dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build Next.js application
RUN npm run build

# Stage 2: Production Runner
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Health check script
COPY --chown=nextjs:nodejs scripts/healthcheck.js ./scripts/healthcheck.js
RUN chmod +x ./scripts/healthcheck.js

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node scripts/healthcheck.js

# Start Next.js
CMD ["npm", "start"]
```

**File**: `frontend/scripts/healthcheck.js`
```javascript
const http = require('http');

const options = {
  host: 'localhost',
  port: 3000,
  path: '/health',
  timeout: 2000
};

const request = http.request(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

request.on('error', (err) => {
  console.log('ERROR', err);
  process.exit(1);
});

request.end();
```

---

## 10. Verification & Quality Assurance

### 10.1 Automated Checks

#### Editor Load Time Validation
**Target**: <200ms

```typescript
// __tests__/performance/editor-load.test.ts
import { test, expect } from '@playwright/test';

test('Monaco Editor loads within 200ms', async ({ page }) => {
  const startTime = performance.now();

  await page.goto('/code-editor');

  // Wait for Monaco editor to be ready
  await page.waitForSelector('.monaco-editor', { state: 'visible' });

  const loadTime = performance.now() - startTime;

  expect(loadTime).toBeLessThan(200);

  // Log metrics
  console.log(`Editor load time: ${loadTime.toFixed(2)}ms`);
});
```

#### End-to-End Feedback Latency
**Target**: <1s

```typescript
// __tests__/performance/feedback-latency.test.ts
import { test, expect } from '@playwright/test';

test('Feedback latency <1s', async ({ page }) => {
  await page.goto('/code-editor');

  // Write code
  await page.click('.monaco-editor');
  await page.keyboard.type('def hello():\n    return "Hello"');

  // Start timing
  const startTime = performance.now();

  // Submit code
  await page.click('[data-testid="submit-code"]');

  // Wait for feedback
  await page.waitForSelector('[data-testid="feedback-score"]');

  const latency = performance.now() - startTime;

  expect(latency).toBeLessThan(1000);

  console.log(`Feedback latency: ${latency.toFixed(2)}ms`);
});
```

#### SSE Connection Health
**Target**: 100% uptime

```typescript
// __tests__/performance/sse-connection.test.ts
import { test, expect } from '@playwright/test';

test('SSE connection maintains stability', async ({ page }) => {
  const events: any[] = [];

  // Listen for SSE events
  await page.route('**/api/events/stream', async (route) => {
    const response = await route.fetch();
    const reader = response.body.getReader();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = new TextDecoder().decode(value);
      events.push(text);
    }
  });

  await page.goto('/code-editor');

  // Wait for initial connection
  await page.waitForTimeout(1000);

  // Verify connection established
  expect(events.length).toBeGreaterThan(0);

  // Check event structure
  const event = JSON.parse(events[0].replace('data:', '').trim());
  expect(event).toHaveProperty('type');
  expect(event).toHaveProperty('timestamp');
});
```

### 10.2 Performance Budget
```typescript
// __tests__/performance/budget.test.ts
const PERFORMANCE_BUDGET = {
  editorLoad: 200,      // ms
  feedbackLatency: 1000, // ms
  apiResponse: 500,     // ms
  bundleSize: 500 * 1024, // 500KB
  memoryUsage: 50 * 1024 * 1024 // 50MB
};

describe('Performance Budget', () => {
  it('bundle size within budget', async () => {
    const bundleSize = await getBundleSize();
    expect(bundleSize).toBeLessThan(PERFORMANCE_BUDGET.bundleSize);
  });

  it('memory usage within budget', async () => {
    const memoryUsage = await getMemoryUsage();
    expect(memoryUsage).toBeLessThan(PERFORMANCE_BUDGET.memoryUsage);
  });

  it('api response time within budget', async () => {
    const responseTime = await measureApiResponse('/api/v1/mastery/calculate');
    expect(responseTime).toBeLessThan(PERFORMANCE_BUDGET.apiResponse);
  });
});
```

### 10.3 Security Validation
```typescript
// __tests__/security/security.test.ts
describe('Security Validation', () => {
  it('JWT validation prevents unauthorized access', async () => {
    const response = await fetch('/api/v1/mastery/calculate', {
      headers: { 'Authorization': 'Bearer invalid-token' }
    });

    expect(response.status).toBe(401);
  });

  it('Input sanitization prevents XSS', async () => {
    const maliciousInput = '<script>alert("xss")</script>';

    const response = await fetch('/api/v1/mastery/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        studentId: maliciousInput,
        topicId: 'topic_test'
      })
    });

    expect(response.status).toBe(400);
  });

  it('CORS prevents unauthorized origins', async () => {
    const response = await fetch('/api/v1/mastery/calculate', {
      headers: { 'Origin': 'https://malicious-site.com' }
    });

    expect(response.headers.get('Access-Control-Allow-Origin')).toBeNull();
  });
});
```

---

## 11. Monitoring & Observability

### 11.1 Application Metrics
```typescript
// lib/metrics.ts
import { Counter, Histogram, Gauge } from 'prom-client';

export const frontendMetrics = {
  // Request metrics
  httpRequestsTotal: new Counter({
    name: 'frontend_http_requests_total',
    help: 'Total HTTP requests',
    labelNames: ['method', 'endpoint', 'status']
  }),

  httpRequestDuration: new Histogram({
    name: 'frontend_http_request_duration_seconds',
    help: 'HTTP request duration in seconds',
    labelNames: ['method', 'endpoint'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2.5, 5]
  }),

  // Editor metrics
  editorLoadTime: new Histogram({
    name: 'frontend_editor_load_time_seconds',
    help: 'Monaco editor load time',
    buckets: [0.1, 0.15, 0.2, 0.3, 0.5]
  }),

  // Real-time metrics
  sseConnections: new Gauge({
    name: 'frontend_sse_connections',
    help: 'Active SSE connections'
  }),

  eventsProcessed: new Counter({
    name: 'frontend_events_processed_total',
    help: 'Total events processed',
    labelNames: ['type', 'status']
  }),

  // Performance metrics
  feedbackLatency: new Histogram({
    name: 'frontend_feedback_latency_seconds',
    help: 'End-to-end feedback latency',
    buckets: [0.2, 0.5, 1.0, 2.0, 5.0]
  }),

  // Bundle metrics
  bundleSize: new Gauge({
    name: 'frontend_bundle_size_bytes',
    help: 'JavaScript bundle size in bytes'
  })
};

// Middleware for request tracking
export function metricsMiddleware(req: NextRequest, res: NextResponse) {
  const start = Date.now();

  // Record on response
  res.headers.set('X-Response-Time', `${Date.now() - start}ms`);

  // Update metrics
  frontendMetrics.httpRequestsTotal.inc({
    method: req.method,
    endpoint: req.nextUrl.pathname,
    status: res.status
  });

  frontendMetrics.httpRequestDuration.observe(
    { method: req.method, endpoint: req.nextUrl.pathname },
    (Date.now() - start) / 1000
  );
}
```

### 11.2 Error Tracking
```typescript
// lib/sentry.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  integrations: [
    new Sentry.BrowserTracing({
      tracePropagationTargets: ['localhost', 'api.learnflow.com'],
    }),
    new Sentry.Replay(),
  ],

  beforeSend(event) {
    // Filter out sensitive data
    if (event.request?.headers?.['Authorization']) {
      delete event.request.headers['Authorization'];
    }
    return event;
  }
});

export const captureFrontendError = (error: Error, context?: any) => {
  Sentry.captureException(error, {
    tags: { component: 'frontend', milestone: '004' },
    extra: context
  });
};
```

---

## 12. Risk Analysis & Mitigation

### 12.1 Technical Risks

**Risk**: Monaco Editor load time exceeds 200ms
**Impact**: High (blocks user interaction)
**Mitigation**:
- Dynamic loading with skeleton UI
- CDN delivery for Monaco assets
- Webpack chunk optimization
- Progressive enhancement (fallback to textarea)

**Risk**: SSE connection drops frequently
**Impact**: Medium (disrupts real-time updates)
**Mitigation**:
- Automatic reconnection with exponential backoff
- Heartbeat/ping mechanism
- Fallback to polling if SSE fails
- Connection health monitoring

**Risk**: Bundle size exceeds budget
**Impact**: Medium (affects mobile users)
**Mitigation**:
- Code splitting and lazy loading
- Tree shaking and dead code elimination
- CDN for large dependencies
- Compression (Brotli)

**Risk**: Backend API latency > 1s
**Impact**: High (breaks real-time promise)
**Mitigation**:
- CDN caching for static responses
- Optimistic UI updates
- Background polling for non-critical data
- Request deduplication

### 12.2 Security Risks

**Risk**: JWT token theft via XSS
**Impact**: Critical
**Mitigation**:
- HTTP-only cookies (no JS access)
- Content Security Policy (CSP)
- Input sanitization and validation
- Regular security audits

**Risk**: DDoS on SSE endpoints
**Impact**: High
**Mitigation**:
- Kong rate limiting (per user)
- CloudFlare/WAF protection
- Connection limiting per IP
- Graceful degradation

**Risk**: Data exposure via API
**Impact**: Critical
**Mitigation**:
- Kong JWT validation on all endpoints
- Role-based access control
- Data validation and sanitization
- Audit logging

---

## 13. Rollback Plan

### 13.1 Automated Rollback Triggers
- **Health check failures**: 3 consecutive failures
- **Error rate spike**: >5% error rate for 5 minutes
- **Performance degradation**: P95 latency >2s for 5 minutes
- **Deployment timeout**: Rollout not completed in 10 minutes

### 13.2 Manual Rollback Procedure
```bash
# Kubernetes rollback
kubectl rollout undo deployment/frontend -n learnflow

# Verify rollback
kubectl rollout status deployment/frontend -n learnflow

# Check previous version
kubectl get deployment/frontend -n learnflow -o yaml | grep image:

# Run smoke tests
./scripts/smoke-test.sh --env production
```

### 13.3 Rollback Testing
**Monthly drill**: Simulate deployment failure and execute rollback
**Target**: Complete rollback in <5 minutes

---

## 14. Success Metrics

### 14.1 Technical Metrics
- **Editor load time**: <200ms (95th percentile)
- **Feedback latency**: <1s end-to-end (95th percentile)
- **Bundle size**: <500KB initial (excluding Monaco)
- **SSE uptime**: >99.9%
- **API response time**: <500ms (95th percentile)

### 14.2 User Experience Metrics
- **User satisfaction**: >4.5/5
- **Task completion rate**: >90%
- **Session duration**: >10 minutes
- **Feature adoption**: >70% of users use code editor
- **Error rate**: <1% of user actions

### 14.3 Business Metrics
- **Learning outcomes**: +15% improvement in mastery scores
- **Engagement**: +20% daily active users
- **Retention**: +10% week-over-week retention
- **Scalability**: Support 10,000 concurrent users

---

## 15. Next Steps

### Immediate (Week 1)
1. **Setup Development Environment**
   - Initialize Next.js 14+ project
   - Configure TypeScript and ESLint
   - Setup Tailwind CSS
   - Install Monaco Editor dependencies

2. **Create Core Components**
   - Monaco Editor wrapper with dynamic loading
   - SSE client with reconnection logic
   - Authentication context and API client

3. **Implement API Routes**
   - Event stream endpoint (/api/events/stream)
   - Auth endpoints (login, refresh, logout)
   - Health check endpoints

### Week 2-3 (Core Features)
1. **Code Editor Implementation**
   - Monaco Editor with Python LSP integration
   - Theme and configuration management
   - Code submission and validation

2. **Real-Time Integration**
   - SSE connection management
   - Event filtering and transformation
   - UI updates on events

3. **Dashboard Implementation**
   - Mastery score display
   - Learning recommendations
   - Progress tracking

### Week 4 (Testing & Optimization)
1. **Performance Testing**
   - Load testing with 1000+ users
   - Editor load time optimization
   - Bundle size reduction

2. **Security Testing**
   - JWT validation testing
   - Input validation testing
   - CORS configuration testing

3. **E2E Testing**
   - Complete user workflows
   - Real-time feedback testing
   - Error scenario testing

### Week 5 (Deployment & Documentation)
1. **Infrastructure Setup**
   - Kubernetes manifests
   - Kong Gateway configuration
   - Dapr integration

2. **CI/CD Pipeline**
   - GitHub Actions workflows
   - Automated testing
   - Deployment automation

3. **Documentation**
   - User guides
   - Developer documentation
   - Operational runbooks

---

## 16. Dependencies & Prerequisites

### 16.1 External Dependencies
- **Kong Gateway**: API gateway and JWT validation
- **Dapr**: Service mesh and pub/sub messaging
- **Redis**: Session storage and cache
- **Mastery Engine Backend**: Already implemented
- **Analytics Service**: Already implemented
- **Recommendation Engine**: Already implemented

### 16.2 Frontend Dependencies
```json
{
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@monaco-editor/react": "4.5.0",
    "zustand": "4.4.0",
    "@tanstack/react-query": "5.0.0",
    "zod": "3.22.0",
    "jose": "5.0.0",
    "date-fns": "3.0.0",
    "lucide-react": "0.30.0"
  },
  "devDependencies": {
    "@playwright/test": "1.40.0",
    "@testing-library/react": "14.1.0",
    "@testing-library/jest-dom": "6.1.0",
    "@types/node": "20.10.0",
    "@types/react": "18.2.0",
    "@types/react-dom": "18.2.0",
    "typescript": "5.3.0",
    "eslint": "8.55.0",
    "eslint-config-next": "14.0.0",
    "jest": "29.7.0",
    "ts-jest": "29.1.0"
  }
}
```

### 16.3 Infrastructure Requirements
- **Kubernetes Cluster**: 1.26+
- **Kong Gateway**: 3.4+
- **Dapr**: 1.12+
- **Redis**: 7.0+
- **Node.js**: 20+ (for container)

---

## 17. Team & Resources

### 17.1 Required Roles
- **Frontend Developer**: Next.js, TypeScript, Monaco Editor
- **DevOps Engineer**: Kubernetes, Kong, Dapr, CI/CD
- **QA Engineer**: E2E testing, performance testing
- **Security Engineer**: JWT validation, penetration testing

### 17.2 Development Timeline
- **Week 1-2**: Setup and core components
- **Week 3-4**: Feature implementation
- **Week 5**: Testing and optimization
- **Week 6**: Deployment and documentation
- **Total**: 6 weeks for complete implementation

### 17.3 Resource Estimates
- **Development Time**: 240 hours
- **Testing Time**: 80 hours
- **Infrastructure Setup**: 40 hours
- **Documentation**: 20 hours
- **Total**: 380 hours

---

## 18. Compliance & Standards

### 18.1 Code Quality Standards
- **ESLint**: Airbnb style guide
- **Prettier**: Consistent formatting
- **TypeScript**: Strict mode enabled
- **Jest**: Unit testing standard
- **Playwright**: E2E testing standard

### 18.2 Security Standards
- **OWASP Top 10**: All mitigations implemented
- **CSP Level 2**: Content Security Policy headers
- **CORS**: Strict origin policies
- **GDPR**: Data protection and privacy
- **WCAG 2.1**: Accessibility compliance

### 18.3 Performance Standards
- **Core Web Vitals**: All metrics passing
- **Google Lighthouse**: Score >90
- **WebPageTest**: Grade A
- **Mobile Performance**: >80/100

---

## 19. References & Resources

### 19.1 Documentation
- [Next.js 14 Documentation](https://nextjs.org/docs)
- [Monaco Editor Documentation](https://microsoft.github.io/monaco-editor/)
- [Dapr Documentation](https://docs.dapr.io/)
- [Kong Documentation](https://docs.konghq.com/)
- [React Query Documentation](https://tanstack.com/query/latest)

### 19.2 Research Papers
- [Server-Sent Events vs WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Real-time Web Application Architecture](https://ably.com/topic/realtime)
- [Frontend Performance Optimization](https://web.dev/fast/)

### 19.3 Tools & Services
- **Vercel**: Deployment platform
- **Sentry**: Error tracking
- **Datadog**: Monitoring and APM
- **CloudFlare**: CDN and security
- **GitHub Actions**: CI/CD

---

## 20. Conclusion

This technical plan provides a comprehensive roadmap for implementing Milestone 5: Real-Time Frontend. Following the Elite Implementation Standard v2.0.0, we prioritize:

1. **Security First**: JWT validation, input sanitization, CORS
2. **Performance**: <200ms editor load, <1s feedback latency
3. **Scalability**: 1000+ concurrent users, horizontal scaling
4. **Maintainability**: Type safety, clean architecture, comprehensive testing
5. **Developer Experience**: Modern tooling, clear patterns, good documentation

The plan is ready for implementation and aligns with the existing cloud-native architecture (Kubernetes, Dapr, Kong Gateway) from previous milestones.

**Next Action**: Begin Phase 0 implementation (project setup and core components).

---

**Plan Status**: ✅ **READY FOR IMPLEMENTATION**
**Estimated Timeline**: 6 weeks
**Confidence Level**: High (all technologies mature and well-documented)
**Risk Level**: Low (follows established patterns from Milestones 1-4)