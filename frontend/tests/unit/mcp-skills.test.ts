/**
 * MCP Skills Unit Tests
 * Unit tests for MCP skill integration
 * Task: T125
 *
 * Last Updated: 2026-01-15
 */

import { MonacoConfigSkill } from '../../skills/monaco-config';
import { SSEHandlerSkill } from '../../skills/sse-handler';
import { MCPClient, invokeSkill, monacoConfigSkill, sseHandlerSkill } from '@/lib/mcp/client';
import { MCPCache, SkillCacheManager } from '@/lib/mcp/cache';

// Mock console methods to reduce test noise
const originalError = console.error;
const originalWarn = console.warn;
const originalLog = console.log;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
  console.log = jest.fn();
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
  console.log = originalLog;
});

describe('MCP Skills Integration - T120-T126', () => {
  describe('T120: Monaco Config Skill', () => {
    let skill: MonacoConfigSkill;

    beforeEach(() => {
      skill = new MonacoConfigSkill();
    });

    it('should generate basic Python configuration', () => {
      const config = skill.generate_config('python', 'vs-dark');

      expect(config).toBeDefined();
      expect(config.language).toBe('python');
      expect(config.theme).toBe('vs-dark');
      expect(config.fontSize).toBe(14);
      expect(config.automaticLayout).toBe(true);
      expect(config._metadata).toBeDefined();
      expect(config._metadata.language).toBe('python');
    });

    it('should generate JavaScript configuration', () => {
      const config = skill.generate_config('javascript', 'vs-dark');

      expect(config.language).toBe('javascript');
      expect(config.tabSize).toBe(2);
    });

    it('should handle invalid language', () => {
      expect(() => {
        skill.generate_config('invalid-language', 'vs-dark');
      }).toThrow('Unsupported language: invalid-language');
    });

    it('should apply layout settings', () => {
      const config = skill.generate_config('python', 'vs-dark', 'minimal');

      expect(config.minimap).toBe(false);
      expect(config.lineNumbers).toBe('off');
      expect(config.folding).toBe(false);
    });

    it('should apply custom settings', () => {
      const customSettings = {
        fontSize: 16,
        wordWrap: 'on',
        minimap: false,
      };

      const config = skill.generate_config('python', 'vs-dark', undefined, undefined, customSettings);

      expect(config.fontSize).toBe(16);
      expect(config.wordWrap).toBe('on');
      expect(config.minimap).toBe(false);
    });

    it('should generate recommended config for student level', () => {
      const config = skill.get_recommended_config('beginner', 'python', 'low');

      expect(config).toBeDefined();
      expect(config._recommendations).toBeDefined();
      expect(config.theme).toBe('vs-light'); // Beginners get light theme
      expect(config.minimap).toBe(false); // Lightweight for beginners
    });

    it('should generate productive config for advanced students', () => {
      const config = skill.get_recommended_config('advanced', 'javascript', 'high');

      expect(config.minimap).toBe(true);
      expect(config.quickSuggestions).toBe(true);
      expect(config.formatOnType).toBe(true);
    });
  });

  describe('T121: SSE Handler Skill', () => {
    let skill: SSEHandlerSkill;

    beforeEach(() => {
      skill = new SSEHandlerSkill();
    });

    it('should process mastery update event', () => {
      const rawEvent = {
        id: 'test-001',
        type: 'mastery_update',
        timestamp: '2026-01-15T10:00:00Z',
        source: 'backend',
        topic: 'algebra',
        score: 0.85,
        previousScore: 0.75,
        confidence: 0.9,
      };

      const processed = skill.process_event(rawEvent);

      expect(processed).toBeDefined();
      expect(processed?.type).toBe('mastery_update');
      expect(processed?.data.topic).toBe('algebra');
      expect(processed?.data.currentScore).toBe(0.85);
      expect(processed?.data.improvement).toBe(0.1);
      expect(processed?.display.variant).toBe('success');
    });

    it('should process recommendation event', () => {
      const rawEvent = {
        id: 'test-002',
        type: 'recommendation',
        timestamp: '2026-01-15T10:01:00Z',
        source: 'ai_engine',
        recommendationType: 'exercise',
        priority: 'high',
        topic: 'calculus',
        title: 'Practice derivatives',
        description: 'Work on derivative problems',
        estimatedTime: 20,
      };

      const processed = skill.process_event(rawEvent);

      expect(processed).toBeDefined();
      expect(processed?.type).toBe('recommendation');
      expect(processed?.data.type).toBe('exercise');
      expect(processed?.data.topic).toBe('calculus');
      expect(processed?.priority).toBe('high');
      expect(processed?.display.icon).toBe('🎯');
    });

    it('should handle error events', () => {
      const rawEvent = {
        id: 'test-003',
        type: 'error',
        timestamp: '2026-01-15T10:02:00Z',
        source: 'system',
        errorCode: 'NETWORK_ERROR',
        message: 'Connection lost',
        severity: 'error',
      };

      const processed = skill.process_event(rawEvent);

      expect(processed).toBeDefined();
      expect(processed?.type).toBe('error');
      expect(processed?.priority).toBe('high'); // Errors are always high priority
      expect(processed?.data.errorCode).toBe('NETWORK_ERROR');
      expect(processed?.display.variant).toBe('error');
    });

    it('should filter events based on priority', () => {
      const eventFilter = {
        priorities: ['high'],
      };

      skill.add_filter('high_only', eventFilter);

      const lowPriorityEvent = {
        id: 'test-004',
        type: 'progress',
        priority: 'low',
        timestamp: '2026-01-15T10:03:00Z',
        source: 'backend',
        progress: 50,
        total: 100,
      };

      const processed = skill.process_event(lowPriorityEvent);
      expect(processed).toBeNull(); // Should be filtered out

      const highPriorityEvent = {
        id: 'test-005',
        type: 'error',
        priority: 'high',
        timestamp: '2026-01-15T10:04:00Z',
        source: 'system',
      };

      const processedHigh = skill.process_event(highPriorityEvent);
      expect(processedHigh).toBeDefined(); // Should pass filter
    });

    it('should batch process events', () => {
      const events = [
        {
          id: 'batch-001',
          type: 'mastery_update',
          topic: 'algebra',
          score: 0.8,
          previousScore: 0.7,
        },
        {
          id: 'batch-002',
          type: 'recommendation',
          recommendationType: 'quiz',
          topic: 'calculus',
        },
        {
          id: 'batch-003',
          type: 'error',
          errorCode: 'TEST_ERROR',
        },
      ];

      const processed = skill.batch_process_events(events);

      expect(processed).toHaveLength(3);
      expect(processed[0].type).toBe('mastery_update');
      expect(processed[1].type).toBe('recommendation');
      expect(processed[2].type).toBe('error');
    });

    it('should handle malformed events gracefully', () => {
      const malformedEvent = null;

      const processed = skill.process_event(malformedEvent);
      expect(processed).toBeNull();
    });

    it('should determine correct priorities', () => {
      const highPriorityEvent = {
        type: 'error',
        severity: 'critical',
      };

      const lowPriorityEvent = {
        type: 'heartbeat',
      };

      const normalPriorityEvent = {
        type: 'mastery_update',
      };

      // We need to access the private method indirectly through processing
      const processed1 = skill.process_event(highPriorityEvent);
      expect(processed1?.priority).toBe('high');

      const processed2 = skill.process_event(lowPriorityEvent);
      expect(processed2?.priority).toBe('low');

      const processed3 = skill.process_event(normalPriorityEvent);
      expect(processed3?.priority).toBe('normal');
    });
  });

  describe('T122: MCP Client', () => {
    let client: MCPClient;

    beforeEach(() => {
      client = new MCPClient();
      client.clearCache();
    });

    it('should invoke monaco-config skill', async () => {
      const response = await client.invokeSkill({
        skill: 'monaco-config',
        action: 'generate',
        params: { language: 'python', theme: 'vs-dark' },
      });

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(response.data.language).toBe('python');
      expect(response.metadata.skill).toBe('monaco-config');
    });

    it('should invoke sse-handler skill', async () => {
      const testEvent = {
        id: 'test-001',
        type: 'mastery_update',
        topic: 'algebra',
        score: 0.8,
        previousScore: 0.7,
      };

      const response = await client.invokeSkill({
        skill: 'sse-handler',
        action: 'process',
        params: { event: testEvent },
      });

      expect(response.success).toBe(true);
      expect(response.data).toBeDefined();
      expect(response.data.type).toBe('mastery_update');
    });

    it('should handle skill errors gracefully', async () => {
      const response = await client.invokeSkill({
        skill: 'unknown-skill',
        action: 'test',
        params: {},
      });

      expect(response.success).toBe(false);
      expect(response.error).toBeDefined();
    });

    it('should cache responses', async () => {
      const request = {
        skill: 'monaco-config',
        action: 'generate',
        params: { language: 'python', theme: 'vs-dark' },
      };

      // First call - should execute
      const response1 = await client.invokeSkill(request);
      expect(response1.success).toBe(true);

      // Second call - should use cache
      const response2 = await client.invokeSkill(request);
      expect(response2.success).toBe(true);
      expect(response2.metadata.executionTime).toBe(0); // Cached = 0 execution time
    });

    it('should clear cache', async () => {
      const request = {
        skill: 'monaco-config',
        action: 'generate',
        params: { language: 'python' },
      };

      await client.invokeSkill(request);
      client.clearCache();

      // Should execute again
      const response = await client.invokeSkill(request);
      expect(response.metadata.executionTime).toBeGreaterThan(0);
    });
  });

  describe('T123: MCP Integration Hooks', () => {
    let mockClient: MCPClient;

    beforeEach(() => {
      mockClient = new MCPClient();
      jest.spyOn(mockClient, 'invokeSkill').mockResolvedValue({
        success: true,
        data: { test: 'data' },
        metadata: {
          skill: 'test',
          executionTime: 10,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });
    });

    it('should expose monaco config skill', () => {
      expect(monacoConfigSkill.generate).toBeDefined();
      expect(monacoConfigSkill.optimize).toBeDefined();
      expect(monacoConfigSkill.transform).toBeDefined();
    });

    it('should expose sse handler skill', () => {
      expect(sseHandlerSkill.process).toBeDefined();
      expect(sseHandlerSkill.batch).toBeDefined();
      expect(sseHandlerSkill.filter).toBeDefined();
      expect(sseHandlerSkill.transform).toBeDefined();
    });
  });

  describe('T124: MCP Caching System', () => {
    let cache: MCPCache;
    let cacheManager: SkillCacheManager;

    beforeEach(() => {
      cache = new MCPCache({ maxEntries: 100, maxAge: 1000 });
      cacheManager = new SkillCacheManager({ maxEntries: 100, maxAge: 1000 });
    });

    it('should cache and retrieve data', () => {
      const key = 'test:key:abc123';
      const data = { result: 'cached data' };

      cache.set(key, data, {
        skill: 'test',
        action: 'key',
        version: '1.0.0',
      });

      const cached = cache.get(key);
      expect(cached?.data).toEqual(data);
      expect(cached?.isStale).toBe(false);
    });

    it('should handle cache miss', () => {
      const cached = cache.get('nonexistent:key');
      expect(cached).toBeNull();
    });

    it('should handle stale data', async () => {
      const key = 'test:stale';
      const data = { result: 'stale data' };

      // Set with very short TTL
      cache.set(key, data, { skill: 'test', action: 'stale', version: '1.0.0' }, 10);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 50));

      const cached = cache.get(key);
      expect(cached).toBeDefined();
      expect(cached?.isStale).toBe(true);
    });

    it('should clear cache', () => {
      cache.set('key1', { data: '1' }, { skill: 'test', action: '1', version: '1.0.0' });
      cache.set('key2', { data: '2' }, { skill: 'test', action: '2', version: '1.0.0' });

      expect(cache.getStats().size).toBe(2);

      cache.clear();
      expect(cache.getStats().size).toBe(0);
    });

    it('should generate cache keys from parameters', () => {
      const key = cache.generateKey('test-skill', 'test-action', { foo: 'bar', baz: 123 });
      expect(key).toContain('test-skill');
      expect(key).toContain('test-action');
      expect(key).toMatch(/^[a-zA-Z0-9_-]+$/); // Base64 encoded
    });

    it('should handle parameter variations', () => {
      const key1 = cache.generateKey('skill', 'action', { a: 1, b: 2 });
      const key2 = cache.generateKey('skill', 'action', { b: 2, a: 1 });

      expect(key1).toBe(key2); // Should be same key regardless of parameter order
    });

    it('should clean expired entries', async () => {
      // Add entries with different TTLs
      cache.set('short', { data: 'short' }, { skill: 'test', action: 'short', version: '1.0.0' }, 10);
      cache.set('long', { data: 'long' }, { skill: 'test', action: 'long', version: '1.0.0' }, 1000);

      expect(cache.getStats().size).toBe(2);

      // Wait for short entry to expire
      await new Promise(resolve => setTimeout(resolve, 50));

      // Clean should remove expired entries
      const cleaned = (cache as any).clean();
      expect(cleaned).toBe(1);
      expect(cache.getStats().size).toBe(1);
    });

    it('should export and import cache data', () => {
      cache.set('key1', { data: '1' }, { skill: 'test', action: '1', version: '1.0.0' });
      cache.set('key2', { data: '2' }, { skill: 'test', action: '2', version: '1.0.0' });

      const exported = cache.export();
      expect(exported).toHaveLength(2);

      const newCache = new MCPCache();
      newCache.import(exported);
      expect(newCache.getStats().size).toBe(2);
    });

    it('should cache skill responses', () => {
      cacheManager.setSkillCache('monaco-config', 'generate', { language: 'python' }, {
        language: 'python',
        theme: 'vs-dark',
      });

      const cached = cacheManager.getSkillCache('monaco-config', 'generate', { language: 'python' });
      expect(cached?.data).toBeDefined();
      expect(cached?.data.language).toBe('python');
    });

    it('should invalidate skill cache', () => {
      cacheManager.setSkillCache('monaco-config', 'generate', { language: 'python' }, { test: 'data' });
      cacheManager.setSkillCache('monaco-config', 'optimize', { config: {} }, { test: 'data' });

      expect(cacheManager.getSkillStats('monaco-config').count).toBe(2);

      cacheManager.invalidateSkill('monaco-config');
      expect(cacheManager.getSkillStats('monaco-config').count).toBe(0);
    });

    it('should prewarm cache', () => {
      cacheManager.prewarmSkill('monaco-config', 'generate', { language: 'python' }, {
        language: 'python',
        theme: 'vs-dark',
      });

      const cached = cacheManager.getSkillCache('monaco-config', 'generate', { language: 'python' });
      expect(cached?.data).toBeDefined();
    });

    it('should handle localStorage persistence', () => {
      const persistentCache = new MCPCache({ persistToStorage: true });
      const key = 'persistent:key';
      const data = { persistent: true };

      persistentCache.set(key, data, { skill: 'test', action: 'persistent', version: '1.0.0' });

      // Check localStorage
      const stored = localStorage.getItem('mcp_cache_v1');
      expect(stored).toBeTruthy();

      // Create new cache instance
      const newCache = new MCPCache({ persistToStorage: true });
      const retrieved = newCache.get(key);
      expect(retrieved?.data).toEqual(data);
    });
  });

  describe('T126: MCP Documentation', () => {
    it('should have proper skill documentation', () => {
      const monacoSkill = new MonacoConfigSkill();
      const sseSkill = new SSEHandlerSkill();

      // Check that skills have proper methods
      expect(typeof monacoSkill.generate_config).toBe('function');
      expect(typeof monacoSkill.get_recommended_config).toBe('function');

      expect(typeof sseSkill.process_event).toBe('function');
      expect(typeof sseSkill.batch_process_events).toBe('function');
      expect(typeof sseSkill.add_filter).toBe('function');
    });

    it('should follow MCP skill interface', () => {
      const client = new MCPClient();

      // Check that client has required methods
      expect(typeof client.invokeSkill).toBe('function');
      expect(typeof client.clearCache).toBe('function');

      // Check that skill helpers exist
      expect(typeof monacoConfigSkill.generate).toBe('function');
      expect(typeof sseHandlerSkill.process).toBe('function');
    });
  });
});

// Integration tests for MCP skills
describe('MCP Skills Integration Tests', () => {
  it('should generate Monaco config and process it through SSE handler', async () => {
    const client = new MCPClient();

    // Generate Monaco config
    const configResponse = await client.invokeSkill({
      skill: 'monaco-config',
      action: 'generate',
      params: { language: 'python', theme: 'vs-dark' },
    });

    expect(configResponse.success).toBe(true);
    expect(configResponse.data).toBeDefined();

    // Transform config as if it were an event
    const sseResponse = await client.invokeSkill({
      skill: 'sse-handler',
      action: 'transform',
      params: {
        event: {
          type: 'config_update',
          data: configResponse.data,
          title: 'Editor Configuration Updated',
        },
      },
    });

    expect(sseResponse.success).toBe(true);
    expect(sseResponse.data).toBeDefined();
    expect(sseResponse.data.display).toBeDefined();
  });

  it('should handle batch event processing with filtering', async () => {
    const client = new MCPClient();

    const events = [
      { type: 'mastery_update', topic: 'algebra', score: 0.8, priority: 'normal' },
      { type: 'recommendation', topic: 'calculus', priority: 'high' },
      { type: 'progress', progress: 50, priority: 'low' },
      { type: 'error', errorCode: 'TEST', priority: 'high' },
    ];

    const response = await client.invokeSkill({
      skill: 'sse-handler',
      action: 'batch',
      params: { events },
    });

    expect(response.success).toBe(true);
    expect(response.data).toHaveLength(4);
  });
});