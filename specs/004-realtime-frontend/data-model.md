# Frontend Data Models

**Version**: 1.0.0
**Date**: 2026-01-15
**Feature**: Milestone 5 - Real-Time Frontend
**Status**: Complete

## Overview

This document defines the frontend state management data models for the Next.js 14+ real-time application. All models follow TypeScript strict typing and use React Context + Reducer pattern for state management.

## 1. Application State Models

### 1.1 AuthState
Manages user authentication, session, and JWT token lifecycle.

```typescript
interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  tokenExpiry: Date | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: AuthError | null;
}

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'student' | 'teacher' | 'admin';
  avatarUrl?: string;
  preferences: UserPreferences;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  fontSize: number;
  autoSave: boolean;
  notifications: boolean;
}

interface AuthError {
  code: string;
  message: string;
  timestamp: Date;
}
```

**State Transitions**:
- `LOGIN_START` → `isAuthenticated: false`, `isLoading: true`
- `LOGIN_SUCCESS` → `isAuthenticated: true`, `isLoading: false`, `user: {...}`
- `LOGIN_FAILURE` → `isAuthenticated: false`, `isLoading: false`, `error: {...}`
- `LOGOUT` → Reset all to initial state
- `TOKEN_REFRESH` → Update `token` and `tokenExpiry`

**Validation Rules**:
- Token expiry checked every 5 minutes
- Auto-redirect to login if token expired
- Session persistence via HTTP-only cookies

### 1.2 EditorState
Manages Monaco Editor configuration, content, and editing session.

```typescript
interface EditorState {
  content: string;
  language: EditorLanguage;
  theme: EditorTheme;
  configuration: MonacoConfig;
  status: EditorStatus;
  diagnostics: Diagnostic[];
  cursors: CursorPosition[];
  selection: EditorSelection | null;
  history: EditorHistory[];
  isDirty: boolean;
  lastSaved: Date | null;
}

type EditorLanguage = 'python' | 'typescript' | 'javascript' | 'markdown' | 'json';

type EditorTheme = 'vs' | 'vs-dark' | 'hc-black';

interface MonacoConfig {
  fontSize: number;
  minimap: boolean;
  lineNumbers: 'on' | 'off' | 'relative';
  wordWrap: 'on' | 'off' | 'bounded';
  automaticLayout: boolean;
  tabSize: number;
  formatOnPaste: boolean;
  formatOnType: boolean;
  scrollBeyondLastLine: boolean;
  suggestOnTriggerCharacters: boolean;
  quickSuggestions: boolean;
  parameterHints: boolean;
  folding: boolean;
}

interface EditorStatus {
  isReady: boolean;
  loadTime: number; // ms
  languageServerConnected: boolean;
  lastError: string | null;
}

interface Diagnostic {
  severity: 'error' | 'warning' | 'info';
  message: string;
  line: number;
  column: number;
  source?: string;
}

interface CursorPosition {
  line: number;
  column: number;
  selectionStart?: number;
  selectionEnd?: number;
}

interface EditorSelection {
  start: CursorPosition;
  end: CursorPosition;
  text: string;
}

interface EditorHistory {
  timestamp: Date;
  content: string;
  action: 'edit' | 'format' | 'undo' | 'redo';
}
```

**State Transitions**:
- `EDITOR_READY` → `isReady: true`, `loadTime: measured`
- `CONTENT_CHANGE` → Update `content`, `isDirty: true`, push to `history`
- `LANGUAGE_CHANGE` → Update `language`, re-initialize LSP connection
- `THEME_CHANGE` → Update `theme`, apply Monaco theme
- `DIAGNOSTICS_UPDATE` → Replace `diagnostics` array
- `SAVE_START` → `isSaving: true`
- `SAVE_SUCCESS` → `isDirty: false`, `lastSaved: now`, `isSaving: false`

**Validation Rules**:
- Content max length: 100,000 characters
- File size limit: 500KB
- Auto-save every 30 seconds if `isDirty: true`
- History depth: 50 entries maximum

### 1.3 RealTimeState
Manages SSE connections, event streams, and real-time updates.

```typescript
interface RealTimeState {
  connection: ConnectionStatus;
  subscriptions: TopicSubscription[];
  events: RealTimeEvent[];
  lastEvent: RealTimeEvent | null;
  metrics: StreamingMetrics;
  error: StreamingError | null;
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

interface TopicSubscription {
  topic: string;
  filters: EventFilter[];
  active: boolean;
  subscribedAt: Date;
  lastMessage?: Date;
}

interface EventFilter {
  field: string;
  operator: 'equals' | 'contains' | 'startsWith';
  value: string;
}

interface RealTimeEvent {
  id: string;
  type: EventType;
  data: EventData;
  timestamp: Date;
  priority: EventPriority;
  source: EventSource;
}

type EventType =
  | 'mastery.updated'
  | 'progress.submitted'
  | 'feedback.received'
  | 'learning.recommendation'
  | 'error.backend'
  | 'notification.system';

interface EventData {
  [key: string]: any;
}

type EventPriority = 'low' | 'normal' | 'high' | 'critical';

type EventSource = 'mastery-engine' | 'analytics-service' | 'recommendation-engine' | 'system';

interface StreamingMetrics {
  messagesReceived: number;
  messagesFiltered: number;
  bytesReceived: number;
  reconnectCount: number;
  averageLatency: number; // ms
  lastHeartbeat: Date | null;
}

interface StreamingError {
  code: string;
  message: string;
  timestamp: Date;
  retryable: boolean;
  retryCount: number;
}
```

**State Transitions**:
- `CONNECTION_START` → `connection: 'connecting'`
- `CONNECTION_ESTABLISHED` → `connection: 'connected'`
- `EVENT_RECEIVED` → Add to `events`, update `lastEvent`, increment `messagesReceived`
- `CONNECTION_LOST` → `connection: 'reconnecting'`, increment `reconnectCount`
- `CONNECTION_ERROR` → `connection: 'error'`, set `error`

**Validation Rules**:
- Event retention: Last 100 events (FIFO)
- Auto-reconnect with exponential backoff (max 5 attempts)
- Filter evaluation: Real-time on incoming events
- Metrics calculated every 60 seconds

### 1.4 LearningSessionState
Manages active learning session, assignments, and progress tracking.

```typescript
interface LearningSessionState {
  session: LearningSession | null;
  activeAssignment: Assignment | null;
  submissions: Submission[];
  mastery: MasteryResult | null;
  predictions: PredictionResult | null;
  recommendations: Recommendation[];
  isAnalyzing: boolean;
  sessionMetrics: SessionMetrics;
}

interface LearningSession {
  id: string;
  startTime: Date;
  endTime?: Date;
  studentId: string;
  courseId: string;
  activityType: 'coding' | 'quiz' | 'review' | 'project';
  status: 'active' | 'paused' | 'completed';
  tags: string[];
}

interface Assignment {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // minutes
  components: AssignmentComponent[];
  requirements: string[];
  starterCode?: string;
  testCases: TestCase[];
}

interface AssignmentComponent {
  name: string;
  weight: number; // 0-1
  targetScore: number; // 0-100
}

interface TestCase {
  id: string;
  input: any;
  expectedOutput: any;
  description: string;
}

interface Submission {
  id: string;
  assignmentId: string;
  timestamp: Date;
  code: string;
  language: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  testResults: TestResult[];
  overallScore: number;
  feedback: string;
}

interface TestResult {
  testCaseId: string;
  passed: boolean;
  output: any;
  executionTime: number; // ms
  error?: string;
}

interface MasteryResult {
  overall: number;
  breakdown: {
    completion: number;
    quiz: number;
    quality: number;
    consistency: number;
  };
  level: MasteryLevel;
  updatedAt: Date;
}

type MasteryLevel = 'beginner' | 'proficient' | 'advanced' | 'expert';

interface PredictionResult {
  nextWeek: {
    predictedScore: number;
    confidence: number;
    trend: 'improving' | 'stable' | 'declining';
    interventionNeeded: boolean;
  };
  trajectory: TrajectoryPoint[];
  generatedAt: Date;
}

interface TrajectoryPoint {
  date: Date;
  score: number;
  confidence: number;
}

interface Recommendation {
  id: string;
  type: 'practice' | 'review' | 'refactor' | 'schedule';
  area: string;
  priority: 'low' | 'medium' | 'high';
  estimatedTime: number; // minutes
  description: string;
  actionItems: string[];
}

interface SessionMetrics {
  activeTime: number; // minutes
  codeChanges: number;
  submissions: number;
  avgResponseTime: number; // ms
  focusSessions: number;
}
```

**State Transitions**:
- `SESSION_START` → Initialize `session`, `startTime: now`
- `ASSIGNMENT_LOAD` → Set `activeAssignment`
- `CODE_EDIT` → Update `sessionMetrics.codeChanges`
- `SUBMIT` → Add to `submissions`, `isAnalyzing: true`
- `MASTERY_UPDATE` → Update `mastery`, `isAnalyzing: false`
- `PREDICTION_READY` → Update `predictions`
- `RECOMMENDATIONS_UPDATE` → Replace `recommendations`
- `SESSION_END` → Set `endTime`, mark as `completed`

**Validation Rules**:
- Session timeout: 2 hours of inactivity
- Code change detection: Every 5 seconds or 100 characters
- Auto-save submissions: Every 60 seconds if code changed
- Prediction cache: 5 minutes for same assignment

## 2. UI State Models

### 2.1 UISettingsState
Global UI preferences and layout configuration.

```typescript
interface UISettingsState {
  theme: ThemeSettings;
  layout: LayoutSettings;
  accessibility: AccessibilitySettings;
  notifications: NotificationSettings;
  performance: PerformanceSettings;
}

interface ThemeSettings {
  mode: 'light' | 'dark' | 'system';
  primaryColor: string;
  accentColor: string;
  font: 'inter' | 'roboto' | 'fira-code';
  fontSize: number; // base font size in px
  codeFont: 'fira-code' | 'jetbrains-mono' | 'monaco';
}

interface LayoutSettings {
  sidebarCollapsed: boolean;
  editorLayout: 'split' | 'full' | 'focused';
  panels: PanelVisibility[];
  density: 'comfortable' | 'compact' | 'minimal';
  animations: boolean;
}

interface PanelVisibility {
  name: 'explorer' | 'terminal' | 'problems' | 'output';
  visible: boolean;
  size: number; // percentage
}

interface AccessibilitySettings {
  highContrast: boolean;
  reduceMotion: boolean;
  keyboardNavigation: boolean;
  screenReader: boolean;
  fontSizeMultiplier: number; // 1.0 = normal
}

interface NotificationSettings {
  realtime: boolean;
  email: boolean;
  desktop: boolean;
  sound: boolean;
  mutedChannels: string[];
}

interface PerformanceSettings {
  lazyLoading: boolean;
  prefetching: boolean;
  animationReduce: boolean;
  virtualScrolling: boolean;
}
```

**State Transitions**:
- `THEME_CHANGE` → Update `theme.mode`
- `LAYOUT_TOGGLE` → Toggle sidebar/panel visibility
- `ACCESSIBILITY_TOGGLE` → Update accessibility settings
- `NOTIFICATION_CHANGE` → Update notification preferences

### 2.2 UIComponentState
Component-specific UI states.

```typescript
interface UIComponentState {
  modals: ModalState[];
  toasts: ToastState[];
  dropdowns: DropdownState[];
  tooltips: TooltipState[];
  loadingStates: LoadingState[];
}

interface ModalState {
  id: string;
  type: 'confirmation' | 'form' | 'info' | 'warning';
  title: string;
  content: any;
  isOpen: boolean;
  props?: Record<string, any>;
}

interface ToastState {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number; // ms
  progress: number; // 0-1 for auto-dismiss
}

interface DropdownState {
  id: string;
  isOpen: boolean;
  selected?: string;
  position?: { x: number; y: number };
}

interface TooltipState {
  id: string;
  visible: boolean;
  content: string;
  position: { x: number; y: number };
}

interface LoadingState {
  id: string;
  isLoading: boolean;
  message?: string;
  progress?: number; // 0-100
}
```

## 3. API State Models

### 3.1 APIRequestState
Tracks API request lifecycle and caching.

```typescript
interface APIRequestState {
  requests: APIRequest[];
  cache: APICache[];
  rateLimits: RateLimit[];
  retries: RetryState[];
}

interface APIRequest {
  id: string;
  endpoint: string;
  method: HTTPMethod;
  status: 'pending' | 'success' | 'error' | 'retrying';
  data?: any;
  error?: APIError;
  startTime: Date;
  endTime?: Date;
  duration?: number; // ms
}

interface APICache {
  key: string;
  endpoint: string;
  data: any;
  timestamp: Date;
  ttl: Date; // Time to live
  stale: boolean;
}

interface RateLimit {
  endpoint: string;
  remaining: number;
  reset: Date;
  limit: number;
}

interface RetryState {
  requestId: string;
  attempt: number;
  maxAttempts: number;
  backoff: number; // ms
  lastError?: string;
}
```

## 4. State Management Architecture

### 4.1 Context + Reducer Pattern
```typescript
// Example: RealTimeContext.tsx
const RealTimeContext = createContext<{
  state: RealTimeState;
  dispatch: React.Dispatch<RealTimeAction>;
} | null>(null);

// Reducer
function realTimeReducer(state: RealTimeState, action: RealTimeAction): RealTimeState {
  switch (action.type) {
    case 'CONNECTION_ESTABLISHED':
      return { ...state, connection: 'connected' };
    case 'EVENT_RECEIVED':
      return {
        ...state,
        events: [...state.events.slice(-99), action.event],
        lastEvent: action.event,
        metrics: {
          ...state.metrics,
          messagesReceived: state.metrics.messagesReceived + 1
        }
      };
    // ... other cases
  }
}
```

### 4.2 State Persistence
- **AuthState**: HTTP-only cookies (secure)
- **UISettingsState**: LocalStorage (encrypted)
- **EditorState**: IndexedDB (large content)
- **SessionState**: Server-side session store (Redis)

### 4.3 State Synchronization
- **Optimistic Updates**: Immediate UI updates + server confirmation
- **Conflict Resolution**: Last-write-wins with server timestamp
- **Offline Support**: Queue changes, sync when online

## 5. Performance Optimizations

### 5.1 Memoization Strategy
```typescript
// Use memo for expensive calculations
const masteryLevel = useMemo(() => calculateMasteryLevel(mastery), [mastery]);

// Use callback for event handlers
const handleEvent = useCallback((event: RealTimeEvent) => {
  // Process event
}, [dependencies]);

// Use selector pattern for large states
const filteredEvents = useSelector(
  (state: AppState) => state.realTime.events.filter(filter),
  [filter]
);
```

### 5.2 Virtualization
- **List Virtualization**: For events, submissions (react-window)
- **Monaco Virtualization**: Only render visible lines
- **Image Lazy Loading**: For avatars, thumbnails

### 5.3 Bundle Optimization
- **Code Splitting**: Route-based, component-based
- **Monaco Lazy Loading**: Dynamic import on editor route
- **Dependency Optimization**: Tree-shaking unused code

## 6. Type Safety & Validation

### 6.1 Runtime Validation
```typescript
// Zod schemas for runtime validation
const AuthStateSchema = z.object({
  isAuthenticated: z.boolean(),
  user: UserSchema.nullable(),
  token: z.string().nullable(),
  // ... other fields
});

// Validation utility
const validateAuthState = (state: unknown): AuthState => {
  return AuthStateSchema.parse(state);
};
```

### 6.2 TypeScript Generics
```typescript
// Generic API response handler
interface APIResponse<T> {
  data: T;
  status: number;
  timestamp: Date;
}

// Generic state container
interface StateContainer<T> {
  data: T;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}
```

## 7. Testing Models

### 7.1 Mock Data Generators
```typescript
// Factory functions for testing
const createMockAuthState = (overrides?: Partial<AuthState>): AuthState => ({
  isAuthenticated: true,
  user: createMockUser(),
  token: 'mock-token',
  // ... defaults
});

const createMockRealTimeEvent = (type: EventType): RealTimeEvent => ({
  id: `event-${Date.now()}`,
  type,
  data: {},
  timestamp: new Date(),
  priority: 'normal',
  source: 'mastery-engine'
});
```

### 7.2 State Transition Tests
```typescript
describe('AuthState transitions', () => {
  it('should handle login success', () => {
    const action = { type: 'LOGIN_SUCCESS', user: mockUser };
    const newState = authReducer(initialState, action);

    expect(newState.isAuthenticated).toBe(true);
    expect(newState.user).toEqual(mockUser);
    expect(newState.error).toBeNull();
  });
});
```

## 8. State Migration Strategy

### 8.1 Versioned State
```typescript
const STATE_VERSION = '1.0.0';

interface VersionedState<T> {
  version: string;
  data: T;
  migratedAt: Date;
}
```

### 8.2 Migration Rules
- **Minor version**: Backward compatible
- **Major version**: Requires migration script
- **Critical update**: Force reset state

## 9. State Management Libraries

### 9.1 Primary Libraries
- **React Context**: For app-wide state (auth, UI settings)
- **React Query**: For server state (API data, caching)
- **Zustand**: For complex local state (editor, real-time)
- **Immer**: For immutable state updates
- **Zod**: For runtime validation

### 9.2 Library Selection Rationale
- **React Query**: Handles caching, background updates, optimistic updates
- **Zustand**: Lightweight, TypeScript-friendly, devtools support
- **Immer**: Simplifies immutable updates, reduces boilerplate
- **Zod**: Runtime type safety, excellent DX

## 10. State Performance Budget

### 10.1 Memory Limits
- **AuthState**: < 5KB
- **EditorState**: < 100KB (content dependent)
- **RealTimeState**: < 500KB (events buffer)
- **LearningSessionState**: < 200KB

### 10.2 Update Frequency
- **UI Settings**: Rare (user action)
- **Auth**: Occasional (login/logout)
- **Editor**: Frequent (every keystroke, debounced)
- **RealTime**: Continuous (SSE events)
- **Session**: Frequent (submissions, analytics)

### 10.3 Update Latency
- **State Update**: < 16ms (one frame)
- **Re-render**: < 32ms (two frames)
- **Persist to Storage**: < 100ms (async)

---

## Integration Points

This data model integrates with:
- **Backend APIs** (Mastery Engine) via REST
- **Real-time events** via SSE (Dapr Pub/Sub)
- **Kong Gateway** for authentication and routing
- **MCP Skills** for Monaco config generation
- **Monaco Editor** for content editing
- **Language Server Protocol** for Python diagnostics

All models are designed for TypeScript strict mode and follow functional programming principles (immutability, pure functions).