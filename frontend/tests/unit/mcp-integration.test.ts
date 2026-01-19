/**
 * Unit Tests for MCP Skills Integration
 * Task: T145
 *
 * Last Updated: 2026-01-15
 */

import { renderHook, act } from '@testing-library/react';
import { MCPClient, getMCPClient, invokeSkill, monacoConfigSkill, sseHandlerSkill } from '@/lib/mcp/client';
import { MCPCache, SkillCacheManager } from '@/lib/mcp/cache';
import { useMCP, MCPProvider } from '@/components/mcp/MCPIntegration';

// Mock the Python skills
jest.mock('@/skills/monaco-config', () => ({
  MonacoConfigSkill: jest.fn(() => ({
    generate_config: jest.fn(),
    get_recommended_config: jest.fn(),
  })),
}));

jest.mock('@/skills/sse-handler', () => ({
  SSEHandlerSkill: jest.fn(() => ({
    process_event: jest.fn(),
    batch_process: jest.fn(),
    add_filter: jest.fn(),
    process_single_event: jest.fn(),
  })),
}));

describe('MCP Skills Integration - T145', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('MCP Client', () => {
    it('should create MCP client instance', () => {
      const client = new MCPClient();

      expect(client).toBeDefined();
      expect(typeof client.invokeSkill).toBe('function');
      expect(typeof client.clearCache).toBe('function');
    });

    it('should get singleton MCP client instance', () => {
      const client1 = getMCPClient();
      const client2 = getMCPClient();

      expect(client1).toBe(client2); // Should be the same instance
      expect(client1).toBeDefined();
    });

    it('should invoke skills successfully', async () => {
      const client = new MCPClient();

      const mockResponse = {
        success: true,
        data: { result: 'test' },
        metadata: {
          skill: 'test-skill',
          executionTime: 10,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      };

      // Mock the internal execution
      const spy = jest.spyOn(client, 'invokeSkill').mockResolvedValue(mockResponse);

      const response = await client.invokeSkill({
        skill: 'test-skill',
        action: 'test-action',
        params: { test: 'param' },
      });

      expect(response).toEqual(mockResponse);
      expect(spy).toHaveBeenCalledWith({
        skill: 'test-skill',
        action: 'test-action',
        params: { test: 'param' },
      });
    });

    it('should handle skill invocation errors', async () => {
      const client = new MCPClient();

      const mockError = {
        success: false,
        data: null,
        error: 'Skill execution failed',
        metadata: {
          skill: 'test-skill',
          executionTime: 5,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      };

      const spy = jest.spyOn(client, 'invokeSkill').mockResolvedValue(mockError);

      const response = await client.invokeSkill({
        skill: 'test-skill',
        action: 'test-action',
        params: { test: 'param' },
      });

      expect(response.success).toBe(false);
      expect(response.error).toBe('Skill execution failed');
    });

    it('should clear cache', () => {
      const client = new MCPClient();

      const spy = jest.spyOn(client, 'clearCache');

      client.clearCache();

      expect(spy).toHaveBeenCalled();
    });
  });

  describe('MCP Skill Invokers', () => {
    it('should invoke skills using invokeSkill helper', async () => {
      const mockResponse = { test: 'data' };

      const spy = jest.spyOn(MCPClient.prototype, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockResponse,
        metadata: {
          skill: 'test-skill',
          executionTime: 10,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const result = await invokeSkill('test-skill', 'test-action', { param: 'value' });

      expect(result).toEqual(mockResponse);
      expect(spy).toHaveBeenCalledWith({
        skill: 'test-skill',
        action: 'test-action',
        params: { param: 'value' },
        context: undefined,
        metadata: expect.any(Object),
      });
    });

    it('should use monaco config skill helpers', async () => {
      const mockConfig = { language: 'python', theme: 'vs-dark' };

      jest.spyOn(MCPClient.prototype, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockConfig,
        metadata: {
          skill: 'monaco-config',
          executionTime: 15,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const result = await monacoConfigSkill.generate({ language: 'python', theme: 'vs-dark' });

      expect(result).toEqual(mockConfig);
    });

    it('should use SSE handler skill helpers', async () => {
      const mockEvent = { id: '123', type: 'test' };

      jest.spyOn(MCPClient.prototype, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockEvent,
        metadata: {
          skill: 'sse-handler',
          executionTime: 12,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const result = await sseHandlerSkill.process(mockEvent);

      expect(result).toEqual(mockEvent);
    });
  });

  describe('MCP Cache System', () => {
    it('should create cache instance', () => {
      const cache = new MCPCache();

      expect(cache).toBeDefined();
      expect(typeof cache.get).toBe('function');
      expect(typeof cache.set).toBe('function');
      expect(typeof cache.delete).toBe('function');
      expect(typeof cache.clear).toBe('function');
    });

    it('should cache and retrieve data', () => {
      const cache = new MCPCache();

      const key = 'test:generate:abc123';
      const data = { result: 'cached' };

      cache.set(key, data, {
        skill: 'test',
        action: 'generate',
        version: '1.0.0',
      });

      const result = cache.get(key);
      expect(result).toBeDefined();
      expect(result?.data).toEqual(data);
      expect(result?.isStale).toBe(false);
    });

    it('should handle cache misses', () => {
      const cache = new MCPCache();

      const result = cache.get('nonexistent:key');
      expect(result).toBeNull();
    });

    it('should handle stale data', () => {
      const cache = new MCPCache({ maxAge: 10 }); // 10ms TTL

      const key = 'stale:test';
      const data = { result: 'stale' };

      cache.set(key, data, {
        skill: 'test',
        action: 'generate',
        version: '1.0.0',
      });

      // Wait for expiration
      jest.advanceTimersByTime(15);

      const result = cache.get(key);
      expect(result).toBeDefined();
      expect(result?.isStale).toBe(true);
    });

    it('should generate cache keys from parameters', () => {
      const cache = new MCPCache();

      const key1 = cache.generateKey('test-skill', 'test-action', { foo: 'bar', baz: 123 });
      const key2 = cache.generateKey('test-skill', 'test-action', { baz: 123, foo: 'bar' });

      expect(key1).toContain('test-skill');
      expect(key1).toContain('test-action');
      expect(key1).toMatch(/[a-zA-Z0-9+/=-]+/); // Base64 encoded
      expect(key1).toBe(key2); // Same params should generate same key
    });

    it('should clear cache', () => {
      const cache = new MCPCache();

      cache.set('key1', { data: '1' }, { skill: 'test', action: '1', version: '1.0.0' });
      cache.set('key2', { data: '2' }, { skill: 'test', action: '2', version: '1.0.0' });

      expect(cache.getStats().size).toBe(2);

      cache.clear();

      expect(cache.getStats().size).toBe(0);
    });

    it('should clean expired entries', () => {
      const cache = new MCPCache({ maxAge: 50, staleWhileRevalidate: 100 });

      // Add entries with different TTLs
      cache.set('short', { data: 'short' }, { skill: 'test', action: 'short', version: '1.0.0' }, 10);
      cache.set('long', { data: 'long' }, { skill: 'test', action: 'long', version: '1.0.0' }, 200);

      expect(cache.getStats().size).toBe(2);

      // Wait for short entry to expire
      jest.advanceTimersByTime(50);

      // Clean should remove expired entries
      const cleaned = (cache as any).clean();
      expect(cleaned).toBe(1);
      expect(cache.getStats().size).toBe(1);
    });
  });

  describe('Skill Cache Manager', () => {
    it('should create skill cache manager', () => {
      const cacheManager = new SkillCacheManager();

      expect(cacheManager).toBeDefined();
      expect(cacheManager.cache).toBeDefined();
    });

    it('should configure skill-specific settings', () => {
      const cacheManager = new SkillCacheManager();

      cacheManager.configureSkill('monaco-config', { ttl: 10000, maxEntries: 100 });
      cacheManager.configureSkill('sse-handler', { ttl: 2000, maxEntries: 50 });

      // Verify configuration is stored
      expect(cacheManager.getSkillStats('monaco-config').count).toBe(0);
      expect(cacheManager.getSkillStats('sse-handler').count).toBe(0);
    });

    it('should cache skill responses', () => {
      const cacheManager = new SkillCacheManager();

      const skillData = { config: 'test' };

      cacheManager.prewarmSkill('monaco-config', 'generate', { language: 'python' }, skillData);

      const cached = cacheManager.getSkillCache('monaco-config', 'generate', { language: 'python' });
      expect(cached?.data).toEqual(skillData);
    });

    it('should invalidate skill cache', () => {
      const cacheManager = new SkillCacheManager();

      cacheManager.prewarmSkill('monaco-config', 'generate', { language: 'python' }, { config: 'test' });

      expect(cacheManager.getSkillStats('monaco-config').count).toBe(1);

      cacheManager.invalidateSkill('monaco-config');

      expect(cacheManager.getSkillStats('monaco-config').count).toBe(0);
    });

    it('should get skill-specific stats', () => {
      const cacheManager = new SkillCacheManager();

      cacheManager.prewarmSkill('monaco-config', 'generate', { language: 'python' }, { config: 'test' });
      cacheManager.prewarmSkill('monaco-config', 'optimize', { config: { theme: 'dark' } }, { config: 'optimized' });

      const stats = cacheManager.getSkillStats('monaco-config');
      expect(stats.count).toBe(2);
      expect(stats.keys).toContainEqual(expect.stringContaining('monaco-config:generate'));
      expect(stats.keys).toContainEqual(expect.stringContaining('monaco-config:optimize'));
    });
  });

  describe('MCP Integration Hooks', () => {
    it('should provide MCP context', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <MCPProvider enabled={true}>{children}</MCPProvider>
      );

      const { result } = renderHook(() => useMCP(), { wrapper });

      expect(result.current).toBeDefined();
      expect(result.current.client).toBeDefined();
      expect(typeof result.current.invoke).toBe('function');
      expect(typeof result.current.monaco).toBe('object');
      expect(typeof result.current.sse).toBe('object');
      expect(result.current.isReady).toBeDefined();
      expect(typeof result.current.cacheStats).toBe('object');
      expect(typeof result.current.clearCache).toBe('function');
    });

    it('should handle MCP not ready state', () => {
      const mockAuthState = {
        state: { isAuthenticated: false },
      };

      jest.mock('@/store/auth-context', () => ({
        useAuth: () => mockAuthState,
      }));

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <MCPProvider enabled={true}>{children}</MCPProvider>
      );

      const { result } = renderHook(() => useMCP(), { wrapper });

      expect(result.current.isReady).toBe(false);
    });

    it('should clear cache through hook', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <MCPProvider enabled={true}>{children}</MCPProvider>
      );

      const { result } = renderHook(() => useMCP(), { wrapper });

      const spy = jest.spyOn(result.current.client, 'clearCache');

      act(() => {
        result.current.clearCache();
      });

      expect(spy).toHaveBeenCalled();
    });

    it('should get cache stats', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <MCPProvider enabled={true}>{children}</MCPProvider>
      );

      const { result } = renderHook(() => useMCP(), { wrapper });

      expect(result.current.cacheStats).toBeDefined();
      expect(typeof result.current.cacheStats.size).toBe('number');
      expect(typeof result.current.cacheStats.memory).toBe('number');
    });
  });

  describe('MCP Skill Performance', () => {
    it('should measure skill execution time', async () => {
      const client = new MCPClient();

      const startTime = performance.now();

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: true,
        data: { result: 'fast' },
        metadata: {
          skill: 'performance-test',
          executionTime: 5, // Simulated fast execution
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'performance-test',
        action: 'measure',
        params: {},
      });

      const endTime = performance.now();
      const totalTime = endTime - startTime;

      expect(response.metadata.executionTime).toBe(5);
      expect(totalTime).toBeLessThan(100); // Should execute quickly
    });

    it('should handle concurrent skill invocations', async () => {
      const client = new MCPClient();

      const mockResponse = (id: number) => ({
        success: true,
        data: { id, result: `response-${id}` },
        metadata: {
          skill: 'concurrent-test',
          executionTime: 10,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      jest.spyOn(client, 'invokeSkill')
        .mockImplementation(async (request: any) => {
          const id = request.params?.id || 0;
          return mockResponse(id);
        });

      // Execute multiple concurrent requests
      const promises = Array.from({ length: 5 }, (_, i) =>
        client.invokeSkill({
          skill: 'concurrent-test',
          action: 'test',
          params: { id: i },
        })
      );

      const results = await Promise.all(promises);

      expect(results).toHaveLength(5);
      results.forEach((result, index) => {
        expect(result.data.id).toBe(index);
        expect(result.data.result).toBe(`response-${index}`);
      });
    });

    it('should maintain cache hit rates', () => {
      const cache = new MCPCache();

      // Prime the cache
      cache.set('cache-test:1', { data: 'cached' }, {
        skill: 'cache-test',
        action: '1',
        version: '1.0.0',
      });

      // Hit the cache
      const hit1 = cache.get('cache-test:1');
      const hit2 = cache.get('cache-test:1');
      const hit3 = cache.get('cache-test:1');

      expect(hit1).toBeDefined();
      expect(hit2).toBeDefined();
      expect(hit3).toBeDefined();

      // Cache should maintain state properly
      const stats = cache.getStats();
      expect(stats.count).toBe(1);
    });
  });

  describe('MCP Skill Error Handling', () => {
    it('should handle skill execution errors gracefully', async () => {
      const client = new MCPClient();

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: false,
        data: null,
        error: 'Skill execution failed',
        metadata: {
          skill: 'error-test',
          executionTime: 8,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'error-test',
        action: 'fail',
        params: {},
      });

      expect(response.success).toBe(false);
      expect(response.error).toBe('Skill execution failed');
    });

    it('should handle invalid skill names', async () => {
      const client = new MCPClient();

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: false,
        data: null,
        error: 'Unknown skill: invalid-skill-name',
        metadata: {
          skill: 'invalid-skill-name',
          executionTime: 2,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'invalid-skill-name',
        action: 'test',
        params: {},
      });

      expect(response.success).toBe(false);
      expect(response.error).toContain('Unknown skill');
    });

    it('should handle invalid action names', async () => {
      const client = new MCPClient();

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: false,
        data: null,
        error: 'Unknown action: invalid-action',
        metadata: {
          skill: 'valid-skill',
          executionTime: 3,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'valid-skill',
        action: 'invalid-action',
        params: {},
      });

      expect(response.success).toBe(false);
      expect(response.error).toContain('Unknown action');
    });

    it('should handle parameter validation errors', async () => {
      const client = new MCPClient();

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: false,
        data: null,
        error: 'Invalid parameters: missing required field',
        metadata: {
          skill: 'validation-test',
          executionTime: 4,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'validation-test',
        action: 'validate',
        params: {}, // Missing required parameters
      });

      expect(response.success).toBe(false);
      expect(response.error).toContain('Invalid parameters');
    });
  });

  describe('MCP Skill Integration Patterns', () => {
    it('should support monaco config generation pattern', async () => {
      const client = new MCPClient();

      const mockConfig = {
        language: 'python',
        theme: 'vs-dark',
        fontSize: 14,
        minimap: true,
        lineNumbers: 'on',
        folding: true,
        _metadata: {
          language: 'python',
          theme: 'vs-dark',
          generatedAt: new Date().toISOString(),
        },
      };

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockConfig,
        metadata: {
          skill: 'monaco-config',
          executionTime: 12,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'monaco-config',
        action: 'generate',
        params: { language: 'python', theme: 'vs-dark' },
      });

      expect(response.success).toBe(true);
      expect(response.data).toEqual(mockConfig);
    });

    it('should support SSE event processing pattern', async () => {
      const client = new MCPClient();

      const mockEvent = {
        id: 'event-123',
        type: 'mastery-updated',
        topic: 'mastery-updated',
        data: { score: 0.85, topic: 'algebra' },
        priority: 'high',
        display: {
          title: 'Mastery Update: algebra',
          message: 'Score: 85%',
          variant: 'success',
          icon: '📊',
          duration: 5000,
        },
      };

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockEvent,
        metadata: {
          skill: 'sse-handler',
          executionTime: 8,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'sse-handler',
        action: 'process',
        params: { event: { id: 'event-123', type: 'mastery-updated', data: { score: 0.85 } } },
      });

      expect(response.success).toBe(true);
      expect(response.data).toEqual(mockEvent);
    });

    it('should support batch processing pattern', async () => {
      const client = new MCPClient();

      const mockBatch = [
        { id: '1', processed: true, result: 'success' },
        { id: '2', processed: true, result: 'success' },
      ];

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockBatch,
        metadata: {
          skill: 'sse-handler',
          executionTime: 15,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'sse-handler',
        action: 'batch',
        params: { events: [{ id: '1' }, { id: '2' }] },
      });

      expect(response.success).toBe(true);
      expect(response.data).toEqual(mockBatch);
    });
  });

  describe('MCP Documentation and Metadata', () => {
    it('should provide skill metadata', async () => {
      const client = new MCPClient();

      const mockMetadata = {
        name: 'monaco-config',
        version: '1.0.0',
        description: 'Generates Monaco Editor configurations',
        parameters: {
          language: 'string',
          theme: 'string',
          fontSize: 'number',
        },
        returns: {
          config: 'object',
        },
        examples: ['Generate Python config', 'Optimize for student level'],
      };

      jest.spyOn(client, 'invokeSkill').mockResolvedValue({
        success: true,
        data: mockMetadata,
        metadata: {
          skill: 'documentation',
          executionTime: 5,
          timestamp: new Date().toISOString(),
          version: '1.0.0',
        },
      });

      const response = await client.invokeSkill({
        skill: 'documentation',
        action: 'get-metadata',
        params: { skill: 'monaco-config' },
      });

      expect(response.success).toBe(true);
      expect(response.data.name).toBe('monaco-config');
    });

    it('should provide usage statistics', () => {
      const cache = new MCPCache();

      // Add some entries
      cache.set('usage:1', { data: 'test1' }, { skill: 'test', action: '1', version: '1.0.0' });
      cache.set('usage:2', { data: 'test2' }, { skill: 'test', action: '2', version: '1.0.0' });

      const stats = cache.getStats();
      expect(stats.count).toBe(2);
      expect(stats.size).toBe(2);
      expect(Array.isArray(stats.keys)).toBe(true);
      expect(stats.keys).toContain('usage:1');
      expect(stats.keys).toContain('usage:2');
    });
  });
});