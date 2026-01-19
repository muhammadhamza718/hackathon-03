# MCP Skills Documentation

**Task**: T126 | **Last Updated**: 2026-01-15

## Overview

This document provides comprehensive documentation for Model Context Protocol (MCP) skills integration in the Real-Time Frontend project. MCP skills enable intelligent automation and context-aware processing across the application.

## Architecture

### MCP Skill System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │Components   │  │Hooks         │  │Utility Functions │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          │                                  │
│                    ┌─────▼──────┐                          │
│                    │MCP Client  │                          │
│                    │Wrapper     │                          │
│                    └─────┬──────┘                          │
│                          │                                  │
│                    ┌─────▼──────┐                          │
│                    │Skill Cache │                          │
│                    │Manager     │                          │
│                    └─────┬──────┘                          │
│                          │                                  │
│              ┌───────────┼───────────┐                     │
│              │           │           │                     │
│        ┌─────▼──┐  ┌─────▼──┐  ┌─────▼──┐                │
│        │Monaco  │  │SSE     │  │Other   │                │
│        │Config  │  │Handler │  │Skills  │                │
│        │Skill   │  │Skill   │  │        │                │
│        └────────┘  └────────┘  └────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Skills

### 1. Monaco Config Skill (T120)

**File**: `skills/monaco-config.py`

**Purpose**: Generates optimized Monaco Editor configurations based on user preferences, context, and performance requirements.

#### Features

- **Language Support**: Python, JavaScript, TypeScript, Markdown
- **Theme Management**: VS Dark, VS Light, High Contrast
- **Layout Presets**: Minimal, Standard, Expanded
- **Student-Level Optimization**: Beginner, Intermediate, Advanced
- **Performance Tuning**: Lightweight vs Productive modes

#### Usage Examples

**Basic Configuration**:
```typescript
import { monacoConfigSkill } from '@/lib/mcp/client';

const config = await monacoConfigSkill.generate({
  language: 'python',
  theme: 'vs-dark',
  fontSize: 14,
  minimap: true,
});
```

**Intelligent Configuration**:
```typescript
const client = getMCPClient();

const response = await client.invokeSkill({
  skill: 'monaco-config',
  action: 'generate',
  params: {
    language: 'javascript',
    theme: 'vs-dark',
    useCase: 'productive',
  },
});

// Response includes recommendations
const config = response.data;
console.log(config._recommendations);
```

**Student-Level Optimization**:
```typescript
const skill = new MonacoConfigSkill();

// Beginner - lightweight configuration
const beginnerConfig = skill.get_recommended_config(
  'beginner',
  'python',
  'low'
);

// Advanced - full-featured configuration
const advancedConfig = skill.get_recommended_config(
  'advanced',
  'javascript',
  'high'
);
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `language` | string | `'python'` | Programming language |
| `theme` | string | `'vs-dark'` | Editor theme |
| `fontSize` | number | `14` | Font size in pixels |
| `wordWrap` | string | `'off'` | Word wrap mode |
| `minimap` | boolean | `true` | Show minimap |
| `lineNumbers` | string | `'on'` | Line numbers display |
| `folding` | boolean | `true` | Code folding |
| `formatOnPaste` | boolean | `false` | Format on paste |
| `formatOnType` | boolean | `true` | Format while typing |
| `tabSize` | number | `4` | Tab size |
| `quickSuggestions` | boolean | `true` | Quick suggestions |
| `automaticLayout` | boolean | `true` | Auto-resize |

#### Layout Presets

**Minimal**:
- Minimap: `false`
- Line numbers: `off`
- Folding: `false`
- Context menu: `false`

**Expanded**:
- Minimap: `true`
- Line numbers: `on`
- Folding: `true`
- Word wrap: `on`

#### Performance Considerations

- **Caching**: Configurations are cached for 10 minutes
- **Optimization**: Automatic optimization based on file size and complexity
- **Memory**: Lightweight configs for large files

### 2. SSE Handler Skill (T121)

**File**: `skills/sse-handler.py`

**Purpose**: Processes Server-Sent Events and transforms them for frontend consumption with intelligent filtering and display configuration.

#### Features

- **Event Classification**: Mastery, Recommendations, Alerts, Progress, Errors
- **Priority Management**: High, Normal, Low
- **Intelligent Filtering**: Type, priority, source, student ID based
- **Display Configuration**: Automatic UI variant selection
- **Batch Processing**: Efficient processing of multiple events

#### Event Types

**Mastery Update**:
```json
{
  "id": "mastery_001",
  "type": "mastery_update",
  "topic": "algebra",
  "score": 0.85,
  "previousScore": 0.75,
  "confidence": 0.9
}
```

**Recommendation**:
```json
{
  "id": "rec_001",
  "type": "recommendation",
  "recommendationType": "exercise",
  "topic": "calculus",
  "priority": "high",
  "title": "Practice derivatives",
  "estimatedTime": 20
}
```

**Alert**:
```json
{
  "id": "alert_001",
  "type": "alert",
  "alertType": "performance",
  "severity": "warning",
  "message": "High memory usage detected"
}
```

#### Usage Examples

**Process Single Event**:
```typescript
import { sseHandlerSkill } from '@/lib/mcp/client';

const processed = await sseHandlerSkill.process(event);
console.log(processed.display); // Ready for UI
```

**Batch Processing**:
```typescript
const processedEvents = await sseHandlerSkill.batch(rawEvents);

// Returns array with display configurations
processedEvents.forEach(event => {
  showToast(event.display.title, event.display.message);
});
```

**Event Filtering**:
```typescript
// Only show high-priority events
const filtered = await sseHandlerSkill.filter(events, {
  priorities: ['high'],
  types: ['error', 'recommendation'],
});
```

**Real-time Event Transformation**:
```typescript
const { sse } = useMCP();

useEffect(() => {
  const unsubscribe = subscribeToEvents(async (rawEvent) => {
    const processed = await sse.processEvent(rawEvent, { userId: studentId });

    // Update UI with processed event
    addEventToFeed(processed);
  });

  return unsubscribe;
}, []);
```

#### Display Configuration

Each processed event includes a `display` object:

```typescript
interface DisplayConfig {
  title: string;           // Notification title
  message: string;         // User-friendly message
  variant: string;         // UI variant: 'success' | 'warning' | 'error' | 'info'
  icon: string;           // Emoji icon
  duration: number;       // Display duration in ms
  actions?: string[];     // Available actions
  showProgress?: boolean; // Show progress indicator
}
```

#### Event Filtering

**Filter by Priority**:
```typescript
const filter = {
  priorities: ['high', 'normal'],
};
```

**Filter by Type**:
```typescript
const filter = {
  types: ['mastery_update', 'recommendation'],
};
```

**Filter by Source**:
```typescript
const filter = {
  sources: ['backend', 'ai_engine'],
};
```

**Filter by Student**:
```typescript
const filter = {
  student_ids: ['student_123', 'student_456'],
};
```

**Regex Filtering**:
```typescript
const filter = {
  regex_patterns: [
    '.*algebra.*',
    '.*calculus.*',
  ],
};
```

### 3. MCP Client Integration (T122)

**File**: `src/lib/mcp/client.ts`

**Purpose**: Provides TypeScript client wrapper for invoking MCP skills from frontend components.

#### Core Functions

**`invokeSkill<T>(skill, action, params, context)`**:
```typescript
import { invokeSkill } from '@/lib/mcp/client';

const result = await invokeSkill('monaco-config', 'generate', {
  language: 'python',
  theme: 'vs-dark',
});
```

**`getMCPClient()`**:
```typescript
import { getMCPClient } from '@/lib/mcp/client';

const client = getMCPClient();
const response = await client.invokeSkill({
  skill: 'monaco-config',
  action: 'generate',
  params: { language: 'python' },
});
```

#### React Hooks

**`useMCP()`**:
```typescript
import { useMCP } from '@/components/mcp/MCPIntegration';

function MyComponent() {
  const { invoke, isReady, cacheStats } = useMCP();

  if (!isReady) return <div>MCP not available</div>;

  const handleInvoke = async () => {
    const result = await invoke('monaco-config', 'generate', { language: 'python' });
  };
}
```

**`useMCPSkill<T>()`**:
```typescript
import { useMCPSkill } from '@/components/mcp/MCPIntegration';

function MonacoEditor() {
  const { data, isLoading, invoke } = useMCPSkill({
    skill: 'monaco-config',
    action: 'generate',
  });

  if (isLoading) return <div>Loading config...</div>;

  return <MonacoEditor config={data} />;
}
```

**`useMonacoConfig()`**:
```typescript
import { useMonacoConfig } from '@/components/mcp/MCPIntegration';

function EditorComponent() {
  const { config, isLoading, optimize } = useMonacoConfig({
    language: 'python',
    useCase: 'productive',
  });

  const handleOptimize = () => {
    optimize(config);
  };

  return <MonacoEditor options={config} />;
}
```

**`useSSEHandler()`**:
```typescript
import { useSSEHandler } from '@/components/mcp/MCPIntegration';

function EventFeed() {
  const { processEvent, isReady } = useSSEHandler();
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (!isReady) return;

    const subscription = sseClient.subscribe(async (rawEvent) => {
      const processed = await processEvent(rawEvent);
      setEvents(prev => [processed, ...prev]);
    });

    return () => subscription.unsubscribe();
  }, [isReady, processEvent]);

  return <EventList events={events} />;
}
```

#### Provider Integration

**App Setup**:
```tsx
import { MCPProvider } from '@/components/mcp/MCPIntegration';

export default function App({ children }) {
  return (
    <MCPProvider enabled={true}>
      {children}
      <MCPStatus /> {/* Optional status display */}
    </MCPProvider>
  );
}
```

### 4. MCP Caching System (T124)

**File**: `src/lib/mcp/cache.ts`

**Purpose**: Provides intelligent caching for MCP skill responses with LRU eviction, TTL management, and persistence.

#### Cache Features

- **LRU Eviction**: Automatically removes least recently used entries
- **TTL Management**: Time-based expiration with stale-while-revalidate
- **Persistence**: Optional localStorage persistence
- **Skill-Specific TTLs**: Different cache durations per skill
- **Statistics**: Hit rates, memory usage, entry counts

#### Usage Examples

**Basic Caching**:
```typescript
import { MCPCache } from '@/lib/mcp/cache';

const cache = new MCPCache({
  maxEntries: 1000,
  maxAge: 5 * 60 * 1000, // 5 minutes
  persistToStorage: true,
});

// Cache a response
cache.set('monaco-config:generate:abc123', config, {
  skill: 'monaco-config',
  action: 'generate',
  version: '1.0.0',
});

// Retrieve
const cached = cache.get('monaco-config:generate:abc123');
if (cached && !cached.isStale) {
  return cached.data;
}
```

**Skill Cache Manager**:
```typescript
import { SkillCacheManager } from '@/lib/mcp/cache';

const cacheManager = new SkillCacheManager({
  maxEntries: 1000,
  maxAge: 5 * 60 * 1000,
});

// Configure skill-specific TTLs
cacheManager.configureSkill('monaco-config', { ttl: 10 * 60 * 1000 });
cacheManager.configureSkill('sse-handler', { ttl: 2 * 60 * 1000 });

// Cache skill response
cacheManager.setSkillCache(
  'monaco-config',
  'generate',
  { language: 'python' },
  config
);

// Retrieve
const cached = cacheManager.getSkillCache(
  'monaco-config',
  'generate',
  { language: 'python' }
);
```

**React Hook**:
```typescript
import { useMCPCache } from '@/lib/mcp/cache';

function CachedComponent() {
  const { getCache, setCache, invalidateCache, getStats } = useMCPCache();

  const fetchData = async () => {
    const cached = getCache('monaco-config', 'generate', { language: 'python' });

    if (cached && !cached.isStale) {
      return cached.data;
    }

    const freshData = await fetchDataFromAPI();
    setCache('monaco-config', 'generate', { language: 'python' }, freshData);

    return freshData;
  };
}
```

**Cache-Aware Invoker**:
```typescript
import { invokeCachedSkill, SkillCacheManager } from '@/lib/mcp/cache';

const cacheManager = new SkillCacheManager();

const config = await invokeCachedSkill(
  'monaco-config',
  'generate',
  { language: 'python' },
  () => invokeSkill('monaco-config', 'generate', { language: 'python' }),
  cacheManager,
  10 * 60 * 1000 // 10 minutes TTL
);
```

#### Cache Statistics

```typescript
const stats = cacheManager.cache.getStats();
console.log({
  size: stats.size,        // Number of cached entries
  memory: stats.memory,    // Memory usage in bytes
  keys: stats.keys,        // Array of cache keys
});

// Hit rate monitoring
const metrics = new CacheMetrics();
metrics.recordHit();
metrics.recordMiss();
console.log(metrics.getMetrics());
```

#### Cache Worker

```typescript
import { CacheWorker } from '@/lib/mcp/cache';

const cacheManager = new SkillCacheManager();
const worker = new CacheWorker(cacheManager, 60000); // Clean every 60s

// Get statistics
const stats = worker.getStats();
```

### 5. Frontend Integration (T123)

**File**: `src/components/mcp/MCPIntegration.tsx`

**Purpose**: Provides React components and hooks for seamless MCP integration in UI components.

#### Component Examples

**MCP Status Display**:
```tsx
import { MCPStatus } from '@/components/mcp/MCPIntegration';

function AppLayout() {
  return (
    <>
      <MainContent />
      <MCPStatus /> {/* Shows cache stats and allows cache clearing */}
    </>
  );
}
```

**MCP Skill Button**:
```tsx
import { MCPSkillButton } from '@/components/mcp/MCPIntegration';

function OptimizedEditor() {
  return (
    <MCPSkillButton
      skill="monaco-config"
      action="optimize"
      params={{ config: currentConfig }}
      onSuccess={(optimized) => setConfig(optimized)}
      variant="primary"
    >
      Optimize Editor
    </MCPSkillButton>
  );
}
```

**MCP Event Processor**:
```tsx
import { MCPEventProcessor } from '@/components/mcp/MCPIntegration';

function EventFeed() {
  const [rawEvents, setRawEvents] = useState([]);
  const [processedEvents, setProcessedEvents] = useState([]);

  return (
    <>
      <MCPEventProcessor
        events={rawEvents}
        onProcessed={setProcessedEvents}
        filter={{ priorities: ['high', 'normal'] }}
      />
      <EventList events={processedEvents} />
    </>
  );
}
```

#### Enhanced Components

**With MCP HOC**:
```tsx
import { withMCPEnhanced } from '@/components/mcp/MCPIntegration';

const EnhancedMonacoEditor = withMCPEnhanced(
  MonacoEditor,
  {
    skill: 'monaco-config',
    action: 'enhance',
    preProcess: true,
  }
);

function EditorPage() {
  return <EnhancedMonacoEditor language="python" />;
}
```

**Intelligent Monaco Hook**:
```tsx
import { useIntelligentMonaco } from '@/components/mcp/MCPIntegration';

function SmartEditor() {
  const { config, isReady } = useIntelligentMonaco({
    language: 'python',
    studentLevel: 'intermediate',
    taskComplexity: 'medium',
  });

  if (!isReady || !config) {
    return <div>Generating intelligent configuration...</div>;
  }

  return <MonacoEditor options={config} />;
}
```

**MCP Analytics Hook**:
```tsx
import { useMCPAnalytics } from '@/components/mcp/MCPIntegration';

function Dashboard() {
  const { analyzeStudyPatterns, generateInsights } = useMCPAnalytics();

  useEffect(() => {
    async function loadInsights() {
      const patterns = await analyzeStudyPatterns(studyData);
      const insights = await generateInsights(patterns);
      setInsights(insights);
    }
    loadInsights();
  }, []);
}
```

### 6. MCP Skills Testing (T125)

**File**: `tests/unit/mcp-skills.test.ts`

**Purpose**: Comprehensive unit tests for all MCP skills and integration points.

#### Test Coverage

**Monaco Config Skill Tests**:
- ✅ Basic configuration generation
- ✅ Language-specific optimizations
- ✅ Layout presets application
- ✅ Custom settings merging
- ✅ Student-level recommendations
- ✅ Error handling for invalid languages

**SSE Handler Skill Tests**:
- ✅ Event processing by type
- ✅ Priority determination
- ✅ Event filtering
- ✅ Batch processing
- ✅ Display configuration generation
- ✅ Error event handling

**MCP Client Tests**:
- ✅ Skill invocation
- ✅ Response caching
- ✅ Error handling
- ✅ Cache clearing

**Cache System Tests**:
- ✅ Cache storage and retrieval
- ✅ TTL and expiration
- ✅ LRU eviction
- ✅ Persistence to localStorage
- ✅ Cache statistics

#### Running Tests

```bash
# Run MCP skill tests
npm test mcp-skills

# Run with coverage
npm test mcp-skills -- --coverage

# Run specific test suites
npm test mcp-skills -- --testNamePattern="Monaco Config"
```

## Performance Guidelines

### Caching Strategy

**Monaco Config**:
- Cache duration: 10 minutes
- Stale-while-revalidate: 30 seconds
- Pre-warm common configurations

**SSE Events**:
- Cache duration: 2 minutes (recent events only)
- Batch processing for efficiency
- Filter before processing

**Memory Management**:
- Max cache entries: 1000
- Auto-cleaning every 60 seconds
- Monitor cache hit rates

### Best Practices

**1. Cache Appropriate Data**:
```typescript
// ✅ Good - Cache generated configurations
const config = await monacoConfigSkill.generate({ language: 'python' });

// ❌ Avoid - Don't cache user-specific real-time data
const events = await sseHandlerSkill.process(event); // Don't cache
```

**2. Use Stale-While-Revalidate**:
```typescript
const cached = cache.get(key);
if (cached?.isStale) {
  // Return stale immediately, refresh in background
  fetchDataFresh().then(fresh => cache.set(key, fresh));
  return cached.data;
}
```

**3. Batch Process Events**:
```typescript
// ✅ Efficient - Batch processing
const processed = await sseHandlerSkill.batch(events);

// ❌ Inefficient - Individual processing
for (const event of events) {
  await sseHandlerSkill.process(event);
}
```

**4. Monitor Cache Performance**:
```typescript
const stats = cacheManager.getStats();
if (stats.hitRate < 70) {
  // Consider adjusting cache TTL or size
}
```

### Error Handling

**Skill Invocation Errors**:
```typescript
try {
  const result = await invokeSkill('monaco-config', 'generate', params);
} catch (error) {
  console.error('MCP skill failed:', error);
  // Fallback to default configuration
  return getDefaultConfig();
}
```

**Cache Errors**:
```typescript
try {
  cache.set(key, data, metadata);
} catch (error) {
  console.warn('Cache storage failed:', error);
  // Continue without cache
}
```

## Monitoring and Analytics

### Cache Metrics

```typescript
import { CacheMetrics } from '@/lib/mcp/cache';

const metrics = new CacheMetrics();

// Track cache usage
metrics.recordHit();
metrics.recordMiss();

// Get performance data
const data = metrics.getMetrics();
console.log(`Hit Rate: ${data.hitRate}%`);
```

### MCP Health Checks

```typescript
import { getMCPClient } from '@/lib/mcp/client';

async function checkMCPHealth() {
  const client = getMCPClient();

  try {
    const response = await client.invokeSkill({
      skill: 'monaco-config',
      action: 'generate',
      params: { language: 'python' },
    });

    return response.success;
  } catch {
    return false;
  }
}
```

## Integration Points

### With Monaco Editor

```typescript
import { useIntelligentMonaco } from '@/components/mcp/MCPIntegration';

function EditorPage() {
  const { config } = useIntelligentMonaco({
    language: 'python',
    studentLevel: 'intermediate',
  });

  return <MonacoEditor options={config} />;
}
```

### With SSE Client

```typescript
import { useSSEHandler } from '@/components/mcp/MCPIntegration';

function RealTimeFeed() {
  const { processEvent } = useSSEHandler();

  useEffect(() => {
    const subscription = sseClient.subscribe(async (event) => {
      const processed = await processEvent(event);
      updateUI(processed);
    });
  }, []);
}
```

### With React Query

```typescript
import { useMCPSkill } from '@/components/mcp/MCPIntegration';

function DataComponent() {
  const { data, isLoading, error } = useMCPSkill({
    skill: 'monaco-config',
    action: 'generate',
    params: { language: 'python' },
    enabled: true,
    cacheTime: 10 * 60 * 1000,
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <MonacoEditor options={data} />;
}
```

## Troubleshooting

### Common Issues

**MCP Not Available**:
- Check `isReady` state before invoking skills
- Ensure user is authenticated
- Verify MCP client initialization

**Cache Misses**:
- Check cache TTL configuration
- Verify parameter hashing
- Monitor cache statistics

**Performance Issues**:
- Reduce cache size for memory-constrained environments
- Adjust TTL based on data freshness requirements
- Use batch processing for multiple events

### Debug Mode

```typescript
// Enable debug logging
const client = new MCPClient();
client.debug = true;

// Monitor cache operations
const cache = new MCPCache();
cache.on('set', (key) => console.log('Cache set:', key));
cache.on('get', (key) => console.log('Cache get:', key));
cache.on('miss', (key) => console.log('Cache miss:', key));
```

## Security Considerations

### Input Validation

All MCP skills validate input parameters:
- Language validation prevents injection attacks
- Parameter size limits prevent DoS
- Type checking ensures data integrity

### Cache Security

- Sensitive data should not be cached
- Cache keys are hashed to prevent injection
- localStorage persistence is optional and encrypted

### Authentication

MCP skills respect user authentication:
- Skills require valid JWT tokens
- User context is passed to skill execution
- Rate limiting applies to skill invocations

## Future Enhancements

### Planned Skills

1. **Study Pattern Analyzer** (`study-analyzer`)
   - Analyze study habits and patterns
   - Generate personalized recommendations

2. **Performance Predictor** (`performance-predictor`)
   - Predict future performance based on historical data
   - Generate study plans

3. **Insight Generator** (`insight-generator`)
   - Generate insights from raw data
   - Create actionable recommendations

### Integration Points

1. **Backend Integration**
   - Direct skill execution via API
   - Shared cache between frontend and backend

2. **ML Model Integration**
   - Integration with ML models for predictions
   - Real-time model updates

3. **Analytics Dashboard**
   - MCP skill usage analytics
   - Performance monitoring

## References

- **Task Documentation**: T120-T126
- **Implementation Files**:
  - `skills/monaco-config.py`
  - `skills/sse-handler.py`
  - `src/lib/mcp/client.ts`
  - `src/lib/mcp/cache.ts`
  - `src/components/mcp/MCPIntegration.tsx`
  - `tests/unit/mcp-skills.test.ts`

## Support

For issues or questions:
1. Check the implementation files for detailed comments
2. Review unit tests for usage examples
3. Consult the task specifications (T120-T126)
4. Monitor MCP status component for real-time diagnostics