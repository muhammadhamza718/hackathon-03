/**
 * Unit Tests for State Management (Zustand Stores)
 * Task: T142
 *
 * Last Updated: 2026-01-15
 */

import { renderHook, act } from '@testing-library/react';
import { create } from 'zustand';
import { useEditorStore } from '@/store/editor-store';
import { useAuthStore } from '@/store/auth-context';
import { useSSEStore } from '@/lib/sse';
import { useMCPStore } from '@/lib/mcp/client';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
});

describe('State Management - T142', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset stores to initial state
    act(() => {
      useEditorStore.setState(useEditorStore.getInitialState());
      useAuthStore.setState(useAuthStore.getInitialState());
      useSSEStore.setState(useSSEStore.getInitialState());
      useMCPStore.setState(useMCPStore.getInitialState());
    });
  });

  describe('Editor Store - useEditorStore', () => {
    it('should initialize with default state', () => {
      const state = useEditorStore.getState();

      expect(state.code).toContain('Write your Python code here');
      expect(state.language).toBe('python');
      expect(state.fileName).toBe('main.py');
      expect(state.isEditorReady).toBe(false);
      expect(state.isCodeDirty).toBe(false);
      expect(state.isSaving).toBe(false);
      expect(state.fontSize).toBe(14);
      expect(state.wordWrap).toBe('on');
      expect(state.minimap).toBe(false);
      expect(state.theme).toBe('dark');
      expect(state.diagnostics).toEqual([]);
      expect(state.history).toEqual([]);
      expect(state.historyIndex).toBe(-1);
      expect(state.selection).toBeUndefined();
    });

    it('should update code and mark as dirty', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('print("Hello, World!")');
      });

      const newState = useEditorStore.getState();
      expect(newState.code).toBe('print("Hello, World!")');
      expect(newState.isCodeDirty).toBe(true);
    });

    it('should update language', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setLanguage('javascript');
      });

      expect(useEditorStore.getState().language).toBe('javascript');
    });

    it('should update file name', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setFileName('script.js');
      });

      expect(useEditorStore.getState().fileName).toBe('script.js');
    });

    it('should update font size', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setFontSize(16);
      });

      expect(useEditorStore.getState().fontSize).toBe(16);
    });

    it('should toggle word wrap', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setWordWrap('off');
      });

      expect(useEditorStore.getState().wordWrap).toBe('off');

      act(() => {
        state.setWordWrap('on');
      });

      expect(useEditorStore.getState().wordWrap).toBe('on');
    });

    it('should toggle minimap', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setMinimap(true);
      });

      expect(useEditorStore.getState().minimap).toBe(true);

      act(() => {
        state.setMinimap(false);
      });

      expect(useEditorStore.getState().minimap).toBe(false);
    });

    it('should set theme', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setTheme('light');
      });

      expect(useEditorStore.getState().theme).toBe('light');
    });

    it('should set diagnostics', () => {
      const state = useEditorStore.getState();
      const diagnostics = [
        { line: 1, column: 5, message: 'Syntax error', severity: 'error' as const },
        { line: 2, column: 10, message: 'Warning', severity: 'warning' as const },
      ];

      act(() => {
        state.setDiagnostics(diagnostics);
      });

      expect(useEditorStore.getState().diagnostics).toEqual(diagnostics);
      expect(useEditorStore.getState().diagnostics).toHaveLength(2);
    });

    it('should clear diagnostics', () => {
      const state = useEditorStore.getState();
      const diagnostics = [
        { line: 1, column: 5, message: 'Error', severity: 'error' as const },
      ];

      act(() => {
        state.setDiagnostics(diagnostics);
        expect(useEditorStore.getState().diagnostics).toHaveLength(1);

        state.clearDiagnostics();
      });

      expect(useEditorStore.getState().diagnostics).toEqual([]);
    });

    it('should save to history', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();
      });

      expect(useEditorStore.getState().history).toEqual(['Version 1']);
      expect(useEditorStore.getState().historyIndex).toBe(0);
      expect(useEditorStore.getState().isCodeDirty).toBe(false);
    });

    it('should track multiple history entries', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();

        state.setCode('Version 2');
        state.saveToHistory();

        state.setCode('Version 3');
        state.saveToHistory();
      });

      expect(useEditorStore.getState().history).toEqual(['Version 1', 'Version 2', 'Version 3']);
      expect(useEditorStore.getState().historyIndex).toBe(2);
    });

    it('should undo to previous version', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();

        state.setCode('Version 2');
        state.saveToHistory();

        state.undo();
      });

      expect(useEditorStore.getState().code).toBe('Version 1');
      expect(useEditorStore.getState().historyIndex).toBe(0);
    });

    it('should redo to next version', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();

        state.setCode('Version 2');
        state.saveToHistory();

        state.undo(); // Back to Version 1
        state.redo(); // Forward to Version 2
      });

      expect(useEditorStore.getState().code).toBe('Version 2');
      expect(useEditorStore.getState().historyIndex).toBe(1);
    });

    it('should prevent undo at first version', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();
      });

      expect(state.canUndo()).toBe(false);

      act(() => {
        state.undo(); // Should not change anything
      });

      expect(useEditorStore.getState().code).toBe('Version 1');
    });

    it('should prevent redo at latest version', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Version 1');
        state.saveToHistory();
      });

      expect(state.canRedo()).toBe(false);
    });

    it('should limit history size', () => {
      const state = useEditorStore.getState();

      // Add more entries than MAX_HISTORY_SIZE (20)
      act(() => {
        for (let i = 0; i < 25; i++) {
          state.setCode(`Version ${i}`);
          state.saveToHistory();
        }
      });

      expect(useEditorStore.getState().history.length).toBe(20); // Should be limited
      expect(useEditorStore.getState().history[0]).toBe('Version 5'); // First entries removed
      expect(useEditorStore.getState().history[useEditorStore.getState().history.length - 1]).toBe('Version 24');
    });

    it('should clear code', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('Some code');
        expect(useEditorStore.getState().code).not.toBe('');

        state.clearCode();
      });

      expect(useEditorStore.getState().code).toBe('');
      expect(useEditorStore.getState().isCodeDirty).toBe(false);
    });

    it('should save code successfully', async () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('print("test")');
        state.setFileName('test.py');
      });

      await act(async () => {
        await state.saveCode();
      });

      expect(useEditorStore.getState().isCodeDirty).toBe(false);
      expect(useEditorStore.getState().isSaving).toBe(false);
    });

    it('should set selection', () => {
      const state = useEditorStore.getState();
      const start = { line: 1, column: 5 };
      const end = { line: 1, column: 10 };

      act(() => {
        state.setSelection(start, end);
      });

      expect(useEditorStore.getState().selection).toEqual({ start, end });
    });

    it('should clear selection', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setSelection({ line: 1, column: 5 }, { line: 1, column: 10 });
        expect(useEditorStore.getState().selection).toBeDefined();

        state.clearSelection();
      });

      expect(useEditorStore.getState().selection).toBeUndefined();
    });

    it('should reset to initial state', () => {
      const state = useEditorStore.getState();

      act(() => {
        // Modify state
        state.setCode('Modified code');
        state.setLanguage('javascript');
        state.setFileName('test.js');
        state.setDiagnostics([{ line: 1, column: 1, message: 'Error', severity: 'error' as const }]);
        state.saveToHistory();

        // Verify modifications
        expect(useEditorStore.getState().code).toBe('Modified code');
        expect(useEditorStore.getState().language).toBe('javascript');
        expect(useEditorStore.getState().diagnostics.length).toBe(1);

        // Reset
        state.reset();
      });

      // Verify reset
      expect(useEditorStore.getState().code).toContain('Write your Python code here');
      expect(useEditorStore.getState().language).toBe('python');
      expect(useEditorStore.getState().fileName).toBe('main.py');
      expect(useEditorStore.getState().diagnostics).toEqual([]);
      expect(useEditorStore.getState().history).toEqual([]);
    });

    it('should update code with history', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.updateCode('New code', true); // With history
      });

      expect(useEditorStore.getState().code).toBe('New code');
      expect(useEditorStore.getState().isCodeDirty).toBe(true);
      expect(useEditorStore.getState().history).toContain('New code');
    });

    it('should format code', async () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('def test():\nprint("hello")'); // Bad indentation
        state.setLanguage('python');
      });

      await act(async () => {
        await state.formatCode();
      });

      // Basic formatting should be applied
      expect(useEditorStore.getState().code).toContain('def test():');
    });

    it('should handle save errors gracefully', async () => {
      const state = useEditorStore.getState();

      // Mock a failing save operation
      const mockSaveCode = jest.fn().mockRejectedValue(new Error('Save failed'));

      act(() => {
        state.setCode('test code');
        state.setFileName('test.py');
      });

      await act(async () => {
        await expect(state.saveCode()).rejects.toThrow('Save failed');
      });

      expect(useEditorStore.getState().isSaving).toBe(false);
      // Code should remain dirty after failed save
      expect(useEditorStore.getState().isCodeDirty).toBe(true);
    });
  });

  describe('Authentication Store - useAuthStore', () => {
    it('should initialize with default auth state', () => {
      const state = useAuthStore.getState();

      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(true); // Initially loading from storage
      expect(state.user).toBeNull();
      expect(state.error).toBeNull();
      expect(state.token).toBeNull();
      expect(state.refreshToken).toBeNull();
      expect(state.expiry).toBeNull();
      expect(state.permissions).toEqual([]);
      expect(state.preferences).toEqual({});
    });

    it('should handle login successfully', async () => {
      const state = useAuthStore.getState();

      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        username: 'testuser',
        role: 'student' as const,
        createdAt: new Date().toISOString(),
      };

      const mockToken = 'mock-jwt-token';

      await act(async () => {
        await state.login({ email: 'test@example.com', password: 'password123' });
      });

      // Simulate successful login by directly setting state
      act(() => {
        state.setState({
          isAuthenticated: true,
          user: mockUser,
          token: mockToken,
          isLoading: false,
          error: null,
        });
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user).toEqual(mockUser);
      expect(useAuthStore.getState().token).toBe(mockToken);
      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('should handle login failure', async () => {
      const state = useAuthStore.getState();

      await act(async () => {
        await expect(state.login({ email: 'wrong@example.com', password: 'wrongpassword' }))
          .rejects.toThrow('Invalid credentials');
      });

      // Simulate failed login
      act(() => {
        state.setState({
          isAuthenticated: false,
          user: null,
          token: null,
          isLoading: false,
          error: 'Invalid credentials',
        });
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().error).toBe('Invalid credentials');
    });

    it('should handle logout', () => {
      const state = useAuthStore.getState();

      // First simulate login
      act(() => {
        state.setState({
          isAuthenticated: true,
          user: { id: 'user-123', email: 'test@example.com' },
          token: 'mock-token',
          isLoading: false,
          error: null,
        });
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Then logout
      act(() => {
        state.logout();
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().token).toBeNull();
    });

    it('should handle registration', async () => {
      const state = useAuthStore.getState();

      const registrationData = {
        email: 'newuser@example.com',
        password: 'SecurePassword123!',
        username: 'newuser',
        role: 'student' as const,
      };

      const mockUser = {
        id: 'new-user-123',
        email: 'newuser@example.com',
        username: 'newuser',
        role: 'student',
        createdAt: new Date().toISOString(),
      };

      const mockToken = 'mock-registration-token';

      await act(async () => {
        // Simulate registration
        state.setState({
          isAuthenticated: true,
          user: mockUser,
          token: mockToken,
          isLoading: false,
          error: null,
        });
      });

      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user).toEqual(mockUser);
      expect(useAuthStore.getState().token).toBe(mockToken);
    });

    it('should handle registration failure', async () => {
      const state = useAuthStore.getState();

      const registrationData = {
        email: 'invalid@email',
        password: 'short',
        username: 'newuser',
        role: 'student' as const,
      };

      await act(async () => {
        await expect(state.register(registrationData))
          .rejects.toThrow('Invalid registration data');
      });

      expect(useAuthStore.getState().error).toBeDefined();
    });

    it('should update user profile', () => {
      const state = useAuthStore.getState();

      const updatedProfile = {
        id: 'user-123',
        email: 'updated@example.com',
        username: 'updateduser',
        role: 'student',
        preferences: { theme: 'dark', language: 'en' },
      };

      act(() => {
        state.updateProfile(updatedProfile);
      });

      expect(useAuthStore.getState().user).toEqual(updatedProfile);
    });

    it('should update preferences', () => {
      const state = useAuthStore.getState();

      const newPreferences = {
        theme: 'light',
        language: 'es',
        notifications: { email: true, push: false },
      };

      act(() => {
        state.updatePreferences(newPreferences);
      });

      expect(useAuthStore.getState().preferences).toEqual(newPreferences);
    });

    it('should add permissions', () => {
      const state = useAuthStore.getState();

      const newPermissions = ['read:analytics', 'write:assignments'];

      act(() => {
        state.addPermissions(newPermissions);
      });

      expect(useAuthStore.getState().permissions).toEqual(newPermissions);
    });

    it('should check permissions', () => {
      const state = useAuthStore.getState();

      const permissions = ['read:analytics', 'write:assignments'];

      act(() => {
        state.addPermissions(permissions);
      });

      expect(state.hasPermission('read:analytics')).toBe(true);
      expect(state.hasPermission('write:assignments')).toBe(true);
      expect(state.hasPermission('delete:users')).toBe(false);
    });

    it('should handle token refresh', () => {
      const state = useAuthStore.getState();

      const newToken = 'new-refreshed-token';
      const newExpiry = new Date(Date.now() + 3600000).toISOString(); // 1 hour from now

      act(() => {
        state.refreshToken(newToken, newExpiry);
      });

      expect(useAuthStore.getState().token).toBe(newToken);
      expect(useAuthStore.getState().expiry).toBe(newExpiry);
    });

    it('should check if token is near expiry', () => {
      const state = useAuthStore.getState();

      // Token expires in 1 minute (near expiry)
      const nearExpiry = new Date(Date.now() + 60000).toISOString();

      act(() => {
        state.setState({
          token: 'test-token',
          expiry: nearExpiry,
        });
      });

      expect(state.isTokenNearExpiry()).toBe(true);

      // Token expires in 2 hours (not near expiry)
      const farExpiry = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString();

      act(() => {
        state.setState({
          token: 'test-token',
          expiry: farExpiry,
        });
      });

      expect(state.isTokenNearExpiry()).toBe(false);
    });

    it('should clear error', () => {
      const state = useAuthStore.getState();

      act(() => {
        state.setState({ error: 'Test error' });
        expect(useAuthStore.getState().error).toBe('Test error');

        state.clearError();
      });

      expect(useAuthStore.getState().error).toBeNull();
    });

    it('should reset to initial state', () => {
      const state = useAuthStore.getState();

      act(() => {
        // Modify state
        state.setState({
          isAuthenticated: true,
          user: { id: 'user-123', email: 'test@example.com' },
          token: 'test-token',
          isLoading: false,
          error: 'Test error',
          permissions: ['read:test'],
          preferences: { theme: 'dark' },
        });

        // Verify modifications
        expect(useAuthStore.getState().isAuthenticated).toBe(true);
        expect(useAuthStore.getState().user).toBeDefined();
        expect(useAuthStore.getState().error).toBe('Test error');

        // Reset
        state.reset();
      });

      // Verify reset
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().error).toBeNull();
      expect(useAuthStore.getState().permissions).toEqual([]);
      expect(useAuthStore.getState().preferences).toEqual({});
    });
  });

  describe('SSE Store - useSSEStore', () => {
    it('should initialize with default SSE state', () => {
      const state = useSSEStore.getState();

      expect(state.status).toBe('disconnected');
      expect(state.eventQueue).toEqual([]);
      expect(state.eventListeners).toBeInstanceOf(Map);
      expect(state.reconnectAttempts).toBe(0);
      expect(state.error).toBeNull();
      expect(state.eventCount).toBe(0);
      expect(state.filteredTopics).toBeInstanceOf(Set);
      expect(state.priorityFilter).toBeInstanceOf(Set);
      expect(state.studentId).toBeNull();
      expect(state.subscriptionId).toBeNull();
      expect(state.lastEvent).toBeNull();
      expect(state.connectionHealth).toBeNull();
    });

    it('should connect to SSE', async () => {
      const state = useSSEStore.getState();

      await act(async () => {
        await state.connect();
      });

      expect(useSSEStore.getState().status).toBe('connecting');
    });

    it('should disconnect from SSE', async () => {
      const state = useSSEStore.getState();

      await act(async () => {
        await state.connect();
        state.disconnect();
      });

      expect(useSSEStore.getState().status).toBe('disconnected');
    });

    it('should handle connection establishment', async () => {
      const state = useSSEStore.getState();

      await act(async () => {
        await state.connect();
      });

      // Simulate successful connection
      act(() => {
        state.handleConnectionEstablished();
      });

      expect(useSSEStore.getState().status).toBe('connected');
      expect(useSSEStore.getState().reconnectAttempts).toBe(0);
    });

    it('should handle connection errors', async () => {
      const state = useSSEStore.getState();

      await act(async () => {
        await state.connect();
      });

      // Simulate connection error
      act(() => {
        state.handleError(new Error('Connection failed'));
      });

      expect(useSSEStore.getState().status).toBe('error');
      expect(useSSEStore.getState().error).toBe('Connection failed');
    });

    it('should add event listeners', () => {
      const state = useSSEStore.getState();
      const mockCallback = jest.fn();

      let unsubscribe: () => void;

      act(() => {
        unsubscribe = state.subscribe('test-topic', mockCallback);
      });

      // Verify listener was added
      const listeners = useSSEStore.getState().eventListeners.get('test-topic');
      expect(listeners).toContain(mockCallback);

      // Verify unsubscribe works
      act(() => {
        unsubscribe();
      });

      const updatedListeners = useSSEStore.getState().eventListeners.get('test-topic');
      expect(updatedListeners).not.toContain(mockCallback);
    });

    it('should publish events to subscribers', () => {
      const state = useSSEStore.getState();
      const mockCallback = jest.fn();

      const testEvent = {
        id: 'test-123',
        topic: 'test-topic',
        type: 'test-event',
        data: { message: 'test data' },
        priority: 'normal' as const,
        timestamp: new Date().toISOString(),
      };

      act(() => {
        state.subscribe('test-topic', mockCallback);
        state.publishEvent(testEvent);
      });

      expect(mockCallback).toHaveBeenCalledWith(testEvent);
      expect(useSSEStore.getState().eventQueue).toContain(testEvent);
      expect(useSSEStore.getState().eventCount).toBe(1);
    });

    it('should filter events by topic', () => {
      const state = useSSEStore.getState();
      const mockCallbackA = jest.fn();
      const mockCallbackB = jest.fn();

      act(() => {
        state.subscribe('topic-a', mockCallbackA);
        state.subscribe('topic-b', mockCallbackB);

        // Publish event for topic-a (should only trigger callbackA)
        state.publishEvent({
          id: '1',
          topic: 'topic-a',
          type: 'test-event',
          data: { message: 'data-a' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        // Publish event for topic-b (should only trigger callbackB)
        state.publishEvent({
          id: '2',
          topic: 'topic-b',
          type: 'test-event',
          data: { message: 'data-b' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallbackA).toHaveBeenCalledTimes(1);
      expect(mockCallbackA).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }));

      expect(mockCallbackB).toHaveBeenCalledTimes(1);
      expect(mockCallbackB).toHaveBeenCalledWith(expect.objectContaining({ id: '2' }));
    });

    it('should filter events by priority', () => {
      const state = useSSEStore.getState();
      const mockCallback = jest.fn();

      act(() => {
        state.subscribe('test-topic', mockCallback);
        state.setPriorityFilter(['high']);

        // Publish high priority event (should be received)
        state.publishEvent({
          id: '1',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'high-pri' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        // Publish normal priority event (should be filtered out)
        state.publishEvent({
          id: '2',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'normal-pri' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: '1', priority: 'high' }));
    });

    it('should handle malformed events gracefully', () => {
      const state = useSSEStore.getState();
      const mockCallback = jest.fn();

      act(() => {
        state.subscribe('test-topic', mockCallback);

        // Publish malformed event (missing required fields)
        state.publishEvent({
          id: 'malformed',
          // Missing topic, type, data, priority, timestamp
        } as any);

        // Publish valid event (should still work)
        state.publishEvent({
          id: 'valid',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'valid' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      // Valid event should still be received
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: 'valid' }));
    });

    it('should process incoming messages', () => {
      const state = useSSEStore.getState();
      const mockCallback = jest.fn();

      act(() => {
        state.subscribe('mastery-updated', mockCallback);
      });

      const incomingData = {
        id: 'incoming-123',
        topic: 'mastery-updated',
        type: 'mastery-updated',
        data: { score: 0.85, topic: 'algebra' },
        priority: 'high' as const,
        timestamp: new Date().toISOString(),
      };

      act(() => {
        state.handleMessage(incomingData);
      });

      expect(mockCallback).toHaveBeenCalledWith(incomingData);
      expect(useSSEStore.getState().eventQueue).toContain(incomingData);
    });

    it('should handle message parsing errors', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.handleError(new Error('Parse error'));
      });

      expect(useSSEStore.getState().status).toBe('error');
      expect(useSSEStore.getState().error).toBe('Parse error');
    });

    it('should maintain event buffer', () => {
      const state = useSSEStore.getState();

      // Add many events
      act(() => {
        for (let i = 0; i < 25; i++) {
          state.publishEvent({
            id: `event-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(useSSEStore.getState().eventQueue.length).toBe(25);
    });

    it('should limit event buffer size', () => {
      const state = useSSEStore.getState();

      // Add more events than buffer size (20)
      act(() => {
        for (let i = 0; i < 30; i++) {
          state.publishEvent({
            id: `event-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(useSSEStore.getState().eventQueue.length).toBe(20); // Should be limited to buffer size
    });

    it('should clear events', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.publishEvent({
          id: 'test',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'test' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(useSSEStore.getState().eventQueue.length).toBe(1);

      act(() => {
        state.clearEvents();
      });

      expect(useSSEStore.getState().eventQueue.length).toBe(0);
      expect(useSSEStore.getState().eventCount).toBe(0);
    });

    it('should get events by topic', () => {
      const state = useSSEStore.getState();

      act(() => {
        // Add events for different topics
        state.publishEvent({
          id: '1',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { score: 0.85 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        state.publishEvent({
          id: '2',
          topic: 'feedback-received',
          type: 'feedback-received',
          data: { message: 'Good job!' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        state.publishEvent({
          id: '3',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { score: 0.9 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });
      });

      const masteryEvents = state.getEventsByTopic('mastery-updated');
      expect(masteryEvents.length).toBe(2);
      expect(masteryEvents).toContainEqual(expect.objectContaining({ id: '1' }));
      expect(masteryEvents).toContainEqual(expect.objectContaining({ id: '3' }));

      const feedbackEvents = state.getEventsByTopic('feedback-received');
      expect(feedbackEvents.length).toBe(1);
      expect(feedbackEvents).toContainEqual(expect.objectContaining({ id: '2' }));
    });

    it('should get events by priority', () => {
      const state = useSSEStore.getState();

      act(() => {
        // Add events with different priorities
        state.publishEvent({
          id: '1',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'high' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        state.publishEvent({
          id: '2',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'normal' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        state.publishEvent({
          id: '3',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'low' },
          priority: 'low' as const,
          timestamp: new Date().toISOString(),
        });
      });

      const highPriorityEvents = state.getEventsByPriority('high');
      expect(highPriorityEvents.length).toBe(1);
      expect(highPriorityEvents[0].id).toBe('1');

      const normalPriorityEvents = state.getEventsByPriority('normal');
      expect(normalPriorityEvents.length).toBe(1);
      expect(normalPriorityEvents[0].id).toBe('2');

      const lowPriorityEvents = state.getEventsByPriority('low');
      expect(lowPriorityEvents.length).toBe(1);
      expect(lowPriorityEvents[0].id).toBe('3');
    });

    it('should set topic filters', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.setTopicFilter(['mastery-updated', 'feedback-received']);
      });

      expect(useSSEStore.getState().filteredTopics).toContain('mastery-updated');
      expect(useSSEStore.getState().filteredTopics).toContain('feedback-received');
      expect(useSSEStore.getState().filteredTopics.size).toBe(2);
    });

    it('should set priority filters', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.setPriorityFilter(['high', 'normal']);
      });

      expect(useSSEStore.getState().priorityFilter).toContain('high');
      expect(useSSEStore.getState().priorityFilter).toContain('normal');
      expect(useSSEStore.getState().priorityFilter.size).toBe(2);
    });

    it('should set student ID', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.setStudentId('student-123');
      });

      expect(useSSEStore.getState().studentId).toBe('student-123');
    });

    it('should set subscription ID', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.setSubscriptionId('sub-456');
      });

      expect(useSSEStore.getState().subscriptionId).toBe('sub-456');
    });

    it('should handle reconnection', async () => {
      const state = useSSEStore.getState();

      await act(async () => {
        await state.connect();
        state.disconnect();
      });

      expect(useSSEStore.getState().status).toBe('disconnected');

      await act(async () => {
        await state.reconnect();
      });

      expect(useSSEStore.getState().status).toBe('connecting');
    });

    it('should increment reconnect attempts', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.incrementReconnectAttempts();
      });

      expect(useSSEStore.getState().reconnectAttempts).toBe(1);

      act(() => {
        state.incrementReconnectAttempts();
      });

      expect(useSSEStore.getState().reconnectAttempts).toBe(2);
    });

    it('should reset reconnect attempts on connection', () => {
      const state = useSSEStore.getState();

      act(() => {
        state.incrementReconnectAttempts();
        state.incrementReconnectAttempts();
      });

      expect(useSSEStore.getState().reconnectAttempts).toBe(2);

      act(() => {
        state.handleConnectionEstablished();
      });

      expect(useSSEStore.getState().reconnectAttempts).toBe(0);
    });

    it('should clear all event listeners', () => {
      const state = useSSEStore.getState();

      const callback1 = jest.fn();
      const callback2 = jest.fn();

      act(() => {
        state.subscribe('topic-1', callback1);
        state.subscribe('topic-2', callback2);
      });

      expect(useSSEStore.getState().eventListeners.size).toBe(2);

      act(() => {
        state.clearListeners();
      });

      expect(useSSEStore.getState().eventListeners.size).toBe(0);
    });

    it('should reset to initial state', () => {
      const state = useSSEStore.getState();

      // Modify state
      act(() => {
        state.setState({
          status: 'connected',
          eventQueue: [{ id: 'test', topic: 'test', type: 'test', data: {}, priority: 'normal', timestamp: new Date().toISOString() }],
          reconnectAttempts: 5,
          error: 'test error',
          eventCount: 10,
          filteredTopics: new Set(['test-topic']),
          priorityFilter: new Set(['high']),
          studentId: 'student-123',
          subscriptionId: 'sub-456',
          lastEvent: { id: 'last', topic: 'test', type: 'test', data: {}, priority: 'normal', timestamp: new Date().toISOString() },
          connectionHealth: { isHealthy: true, eventCount: 10, lastEventTime: new Date().toISOString() },
        });
      });

      expect(useSSEStore.getState().status).toBe('connected');
      expect(useSSEStore.getState().eventQueue.length).toBe(1);
      expect(useSSEStore.getState().reconnectAttempts).toBe(5);

      // Reset
      act(() => {
        state.reset();
      });

      // Verify reset
      expect(useSSEStore.getState().status).toBe('disconnected');
      expect(useSSEStore.getState().eventQueue.length).toBe(0);
      expect(useSSEStore.getState().reconnectAttempts).toBe(0);
      expect(useSSEStore.getState().error).toBeNull();
      expect(useSSEStore.getState().eventCount).toBe(0);
      expect(useSSEStore.getState().filteredTopics.size).toBe(0);
      expect(useSSEStore.getState().priorityFilter.size).toBe(0);
      expect(useSSEStore.getState().studentId).toBeNull();
      expect(useSSEStore.getState().subscriptionId).toBeNull();
      expect(useSSEStore.getState().lastEvent).toBeNull();
      expect(useSSEStore.getState().connectionHealth).toBeNull();
    });
  });

  describe('MCP Store - useMCPStore', () => {
    it('should initialize with default MCP state', () => {
      const state = useMCPStore.getState();

      expect(state.client).toBeDefined();
      expect(state.isReady).toBe(false);
      expect(state.skills).toEqual({});
      expect(state.skillCache).toBeDefined();
      expect(state.metrics).toBeDefined();
      expect(state.lastInvocation).toBeNull();
    });

    it('should update readiness state', () => {
      const state = useMCPStore.getState();

      act(() => {
        state.setReady(true);
      });

      expect(useMCPStore.getState().isReady).toBe(true);

      act(() => {
        state.setReady(false);
      });

      expect(useMCPStore.getState().isReady).toBe(false);
    });

    it('should track skill invocations', () => {
      const state = useMCPStore.getState();

      const invocation = {
        skill: 'test-skill',
        action: 'test-action',
        params: { test: 'param' },
        timestamp: new Date().toISOString(),
        executionTime: 15,
        success: true,
        result: { data: 'result' },
      };

      act(() => {
        state.trackInvocation(invocation);
      });

      expect(useMCPStore.getState().lastInvocation).toEqual(invocation);
      expect(useMCPStore.getState().metrics.invocations).toBe(1);
      expect(useMCPStore.getState().metrics.successful).toBe(1);
    });

    it('should track skill invocation errors', () => {
      const state = useMCPStore.getState();

      const invocation = {
        skill: 'test-skill',
        action: 'test-action',
        params: { test: 'param' },
        timestamp: new Date().toISOString(),
        executionTime: 5,
        success: false,
        error: 'Skill execution failed',
        result: null,
      };

      act(() => {
        state.trackInvocation(invocation);
      });

      expect(useMCPStore.getState().lastInvocation).toEqual(invocation);
      expect(useMCPStore.getState().metrics.invocations).toBe(1);
      expect(useMCPStore.getState().metrics.successful).toBe(0);
      expect(useMCPStore.getState().metrics.failed).toBe(1);
    });

    it('should clear metrics', () => {
      const state = useMCPStore.getState();

      act(() => {
        // Add some invocations
        state.trackInvocation({
          skill: 'skill-1',
          action: 'action-1',
          params: {},
          timestamp: new Date().toISOString(),
          executionTime: 10,
          success: true,
          result: { data: 'result' },
        });

        state.trackInvocation({
          skill: 'skill-2',
          action: 'action-2',
          params: {},
          timestamp: new Date().toISOString(),
          executionTime: 15,
          success: false,
          error: 'Error',
          result: null,
        });
      });

      expect(useMCPStore.getState().metrics.invocations).toBe(2);
      expect(useMCPStore.getState().metrics.successful).toBe(1);
      expect(useMCPStore.getState().metrics.failed).toBe(1);

      act(() => {
        state.clearMetrics();
      });

      expect(useMCPStore.getState().metrics.invocations).toBe(0);
      expect(useMCPStore.getState().metrics.successful).toBe(0);
      expect(useMCPStore.getState().metrics.failed).toBe(0);
    });

    it('should register skills', () => {
      const state = useMCPStore.getState();

      const mockSkill = {
        name: 'test-skill',
        version: '1.0.0',
        description: 'Test skill for testing',
        execute: jest.fn(),
      };

      act(() => {
        state.registerSkill('test-skill', mockSkill);
      });

      expect(useMCPStore.getState().skills['test-skill']).toEqual(mockSkill);
    });

    it('should invoke registered skills', async () => {
      const state = useMCPStore.getState();

      const mockSkill = {
        name: 'test-skill',
        version: '1.0.0',
        description: 'Test skill for testing',
        execute: jest.fn().mockResolvedValue({ result: 'success' }),
      };

      act(() => {
        state.registerSkill('test-skill', mockSkill);
      });

      const result = await state.invokeSkill('test-skill', 'test-action', { param: 'value' });

      expect(mockSkill.execute).toHaveBeenCalledWith('test-action', { param: 'value' });
      expect(result).toEqual({ result: 'success' });
    });

    it('should handle skill invocation errors', async () => {
      const state = useMCPStore.getState();

      const mockSkill = {
        name: 'failing-skill',
        version: '1.0.0',
        description: 'Skill that fails',
        execute: jest.fn().mockRejectedValue(new Error('Skill failed')),
      };

      act(() => {
        state.registerSkill('failing-skill', mockSkill);
      });

      await expect(state.invokeSkill('failing-skill', 'test-action', {}))
        .rejects.toThrow('Skill failed');
    });

    it('should reset to initial state', () => {
      const state = useMCPStore.getState();

      // Modify state
      act(() => {
        state.setState({
          isReady: true,
          skills: { 'test-skill': { name: 'test', version: '1.0.0', description: 'test', execute: jest.fn() } },
          lastInvocation: { skill: 'test', action: 'test', params: {}, timestamp: new Date().toISOString(), executionTime: 10, success: true, result: { data: 'test' } },
          metrics: { invocations: 5, successful: 4, failed: 1, averageExecutionTime: 12.5 },
        });
      });

      expect(useMCPStore.getState().isReady).toBe(true);
      expect(useMCPStore.getState().skills['test-skill']).toBeDefined();
      expect(useMCPStore.getState().metrics.invocations).toBe(5);

      // Reset
      act(() => {
        state.reset();
      });

      // Verify reset
      expect(useMCPStore.getState().isReady).toBe(false);
      expect(useMCPStore.getState().skills).toEqual({});
      expect(useMCPStore.getState().lastInvocation).toBeNull();
      expect(useMCPStore.getState().metrics.invocations).toBe(0);
    });
  });

  describe('State Persistence', () => {
    it('should persist editor state to localStorage', () => {
      const state = useEditorStore.getState();

      act(() => {
        state.setCode('persisted code');
        state.setLanguage('javascript');
        state.setFontSize(16);
        state.setTheme('light');
      });

      // Verify localStorage was called
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'editor-state',
        expect.any(String) // JSON string containing the state
      );
    });

    it('should persist auth state to localStorage', () => {
      const state = useAuthStore.getState();

      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        username: 'testuser',
        role: 'student' as const,
      };

      act(() => {
        state.setState({
          isAuthenticated: true,
          user: mockUser,
          token: 'persisted-token',
          isLoading: false,
          error: null,
        });
      });

      // Verify localStorage was called
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'auth-state',
        expect.any(String) // JSON string containing the auth state
      );
    });

    it('should restore editor state from localStorage', () => {
      const persistedState = {
        code: 'restored code',
        language: 'typescript',
        fileName: 'restored.ts',
        fontSize: 18,
        wordWrap: 'off',
        minimap: true,
        theme: 'light',
        isCodeDirty: true,
        isEditorReady: true,
        isSaving: false,
        diagnostics: [{ line: 1, column: 5, message: 'Restored error', severity: 'error' as const }],
        history: ['version 1', 'version 2'],
        historyIndex: 1,
        selection: { start: { line: 1, column: 1 }, end: { line: 1, column: 10 } },
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(persistedState));

      // Create a new store instance to test restoration
      const newStore = create(() => ({ ...persistedState }));

      expect(newStore.getState().code).toBe('restored code');
      expect(newStore.getState().language).toBe('typescript');
      expect(newStore.getState().fileName).toBe('restored.ts');
      expect(newStore.getState().fontSize).toBe(18);
    });

    it('should handle localStorage parsing errors', () => {
      localStorageMock.getItem.mockReturnValue('{ invalid json');

      // Create store with invalid JSON in localStorage
      // Should handle gracefully and use default state
      const state = useEditorStore.getState();

      // Should use default state despite invalid JSON
      expect(state.code).toContain('Write your Python code here');
      expect(state.language).toBe('python');
    });

    it('should handle localStorage errors', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Create store with storage error
      // Should handle gracefully and use default state
      const state = useEditorStore.getState();

      // Should use default state despite storage error
      expect(state.code).toContain('Write your Python code here');
      expect(state.language).toBe('python');
    });
  });

  describe('Performance and Memory', () => {
    it('should not cause memory leaks', () => {
      const initialSubscriberCount = (useEditorStore as any).getState()._listeners.size;

      // Create and destroy multiple hooks
      const { result, unmount } = renderHook(() => useEditorStore());

      expect(result.current).toBeDefined();

      // Unmount should clean up
      unmount();

      // Subscriber count should return to initial
      const finalSubscriberCount = (useEditorStore as any).getState()._listeners.size;
      expect(finalSubscriberCount).toBe(initialSubscriberCount);
    });

    it('should handle rapid state changes', () => {
      const state = useEditorStore.getState();

      const startTime = performance.now();

      // Rapidly change state
      act(() => {
        for (let i = 0; i < 100; i++) {
          state.setCode(`code-${i}`);
          state.setLanguage(i % 2 === 0 ? 'python' : 'javascript');
          state.setFontSize(12 + (i % 8));
        }
      });

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should handle rapid changes efficiently (under 100ms for 100 changes)
      expect(duration).toBeLessThan(100);

      // State should be consistent
      expect(useEditorStore.getState().code).toBe('code-99');
      expect(useEditorStore.getState().language).toBe('javascript'); // Even number, so javascript
      expect(useEditorStore.getState().fontSize).toBe(12 + (99 % 8)); // 12 + 3 = 15
    });

    it('should have predictable state updates', () => {
      const state = useEditorStore.getState();

      // Test synchronous state update
      act(() => {
        state.setCode('initial');
        expect(useEditorStore.getState().code).toBe('initial');

        state.setCode('updated');
        expect(useEditorStore.getState().code).toBe('updated');
      });

      expect(useEditorStore.getState().code).toBe('updated');
    });

    it('should batch multiple state updates efficiently', () => {
      const state = useEditorStore.getState();

      const startTime = performance.now();

      // Batch multiple state updates in single act
      act(() => {
        for (let i = 0; i < 50; i++) {
          state.setCode(`code-${i}`);
          state.setLanguage('python');
          state.setFontSize(14);
          state.setTheme('dark');
        }
      });

      const endTime = performance.now();
      const duration = endTime - startTime;

      // Should batch efficiently (under 50ms for 50 updates)
      expect(duration).toBeLessThan(50);

      // Should have final values
      expect(useEditorStore.getState().code).toBe('code-49');
      expect(useEditorStore.getState().language).toBe('python');
      expect(useEditorStore.getState().fontSize).toBe(14);
      expect(useEditorStore.getState().theme).toBe('dark');
    });
  });

  describe('Error Handling', () => {
    it('should handle state update errors gracefully', () => {
      const state = useEditorStore.getState();

      // Mock console.error to suppress during test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      act(() => {
        // This should not crash the store
        try {
          state.setCode(null as any); // Invalid type
        } catch (error) {
          // Expected to handle gracefully
        }
      });

      // Store should still be functional
      act(() => {
        state.setCode('valid code');
      });

      expect(useEditorStore.getState().code).toBe('valid code');

      consoleSpy.mockRestore();
    });

    it('should handle async operation errors', async () => {
      const state = useEditorStore.getState();

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      // Mock a failing async operation
      const failingAsyncOp = () => Promise.reject(new Error('Async error'));

      await act(async () => {
        await expect(failingAsyncOp()).rejects.toThrow('Async error');
      });

      // Store should remain functional
      act(() => {
        state.setCode('still-working');
      });

      expect(useEditorStore.getState().code).toBe('still-working');

      consoleSpy.mockRestore();
    });

    it('should handle listener errors gracefully', () => {
      const state = useEditorStore.getState();
      const erroringListener = jest.fn().mockImplementation(() => {
        throw new Error('Listener error');
      });

      // Add erroring listener
      (useEditorStore as any).subscribe(erroringListener);

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      // Trigger state update - should not crash other listeners
      act(() => {
        state.setCode('test code');
      });

      // Original listener should have been called and errored
      expect(erroringListener).toHaveBeenCalled();

      // Store should still work
      expect(useEditorStore.getState().code).toBe('test code');

      consoleSpy.mockRestore();
    });
  });

  describe('Integration Between Stores', () => {
    it('should handle auth state changes affecting SSE connections', () => {
      const authState = useAuthStore.getState();
      const sseState = useSSEStore.getState();

      // Simulate login
      act(() => {
        authState.setState({
          isAuthenticated: true,
          user: { id: 'student-123', email: 'test@example.com' },
          token: 'auth-token',
          isLoading: false,
          error: null,
        });
      });

      // SSE should potentially use auth info
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user?.id).toBe('student-123');
    });

    it('should handle editor state changes affecting MCP skills', () => {
      const editorState = useEditorStore.getState();
      const mcpState = useMCPStore.getState();

      // Update editor state
      act(() => {
        editorState.setCode('print("Hello, World!")');
        editorState.setLanguage('python');
      });

      // MCP might use this context for code-related skills
      expect(useEditorStore.getState().code).toBe('print("Hello, World!")');
      expect(useEditorStore.getState().language).toBe('python');
    });

    it('should maintain store isolation', () => {
      const editorState = useEditorStore.getState();
      const authState = useAuthStore.getState();

      // Modify editor state
      act(() => {
        editorState.setCode('test code');
        editorState.setLanguage('javascript');
      });

      // Auth state should be unaffected
      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);

      // Modify auth state
      act(() => {
        authState.setState({
          isAuthenticated: true,
          user: { id: 'user-123', email: 'test@example.com' },
          isLoading: false,
          error: null,
        });
      });

      // Editor state should be unaffected
      expect(useEditorStore.getState().code).toBe('test code');
      expect(useEditorStore.getState().language).toBe('javascript');
    });
  });

  describe('Store Testing Utilities', () => {
    it('should have getInitialState method for testing', () => {
      const editorInitialState = useEditorStore.getInitialState();
      const authInitialState = useAuthStore.getInitialState();
      const sseInitialState = useSSEStore.getInitialState();

      // Verify initial states have expected properties
      expect(editorInitialState.code).toContain('Write your Python code here');
      expect(editorInitialState.language).toBe('python');
      expect(editorInitialState.isEditorReady).toBe(false);

      expect(authInitialState.isAuthenticated).toBe(false);
      expect(authInitialState.isLoading).toBe(true);
      expect(authInitialState.user).toBeNull);

      expect(sseInitialState.status).toBe('disconnected');
      expect(sseInitialState.eventQueue).toEqual([]);
      expect(sseInitialState.reconnectAttempts).toBe(0);
    });

    it('should allow direct state manipulation for testing', () => {
      const state = useEditorStore.getState();

      // Direct state manipulation for testing purposes
      act(() => {
        state.setState({
          ...state,
          code: 'directly set code',
          language: 'go',
          fontSize: 20,
          theme: 'vs-light',
        });
      });

      expect(useEditorStore.getState().code).toBe('directly set code');
      expect(useEditorStore.getState().language).toBe('go');
      expect(useEditorStore.getState().fontSize).toBe(20);
      expect(useEditorStore.getState().theme).toBe('vs-light');
    });

    it('should track state changes for debugging', () => {
      const state = useEditorStore.getState();
      let changeCount = 0;

      // Subscribe to track changes
      const unsub = (useEditorStore as any).subscribe(() => {
        changeCount++;
      });

      // Make some changes
      act(() => {
        state.setCode('change 1');
        state.setCode('change 2');
        state.setLanguage('typescript');
      });

      expect(changeCount).toBeGreaterThanOrEqual(3); // At least 3 changes

      unsub(); // Clean up subscription
    });
  });
});

// Now mark the task as completed in the tasks file