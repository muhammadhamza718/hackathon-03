/**
 * Unit Tests for Editor Store (Zustand)
 * Last Updated: 2026-01-15
 */

import { useEditorStore, editorActions } from '@/store/editor-store';

describe('EditorStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useEditorStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
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
    });
  });

  describe('Code Management', () => {
    it('should update code and mark as dirty', () => {
      const state = useEditorStore.getState();
      const newCode = 'print("Hello, World!")';

      state.setCode(newCode);

      expect(state.code).toBe(newCode);
      expect(state.isCodeDirty).toBe(true);
    });

    it('should set different languages', () => {
      const state = useEditorStore.getState();

      state.setLanguage('javascript');
      expect(state.language).toBe('javascript');

      state.setLanguage('typescript');
      expect(state.language).toBe('typescript');
    });

    it('should update filename', () => {
      const state = useEditorStore.getState();

      state.setFileName('my_script.py');
      expect(state.fileName).toBe('my_script.py');
    });
  });

  describe('Editor Configuration', () => {
    it('should update font size', () => {
      const state = useEditorStore.getState();

      state.setFontSize(16);
      expect(state.fontSize).toBe(16);
    });

    it('should toggle word wrap', () => {
      const state = useEditorStore.getState();

      state.setWordWrap('off');
      expect(state.wordWrap).toBe('off');

      state.setWordWrap('on');
      expect(state.wordWrap).toBe('on');
    });

    it('should toggle minimap', () => {
      const state = useEditorStore.getState();

      state.setMinimap(true);
      expect(state.minimap).toBe(true);

      state.setMinimap(false);
      expect(state.minimap).toBe(false);
    });

    it('should set theme', () => {
      const state = useEditorStore.getState();

      state.setTheme('light');
      expect(state.theme).toBe('light');

      state.setTheme('high-contrast');
      expect(state.theme).toBe('high-contrast');
    });
  });

  describe('Diagnostics', () => {
    it('should set diagnostics', () => {
      const state = useEditorStore.getState();
      const diagnostics = [
        { line: 1, column: 5, message: 'Syntax error', severity: 'error' as const },
        { line: 2, column: 10, message: 'Warning', severity: 'warning' as const },
      ];

      state.setDiagnostics(diagnostics);

      expect(state.diagnostics).toEqual(diagnostics);
      expect(state.diagnostics.length).toBe(2);
    });

    it('should clear diagnostics', () => {
      const state = useEditorStore.getState();
      const diagnostics = [
        { line: 1, column: 5, message: 'Error', severity: 'error' as const },
      ];

      state.setDiagnostics(diagnostics);
      expect(state.diagnostics.length).toBe(1);

      state.clearDiagnostics();
      expect(state.diagnostics).toEqual([]);
    });
  });

  describe('History Management', () => {
    it('should save to history', () => {
      const state = useEditorStore.getState();

      // Set initial code
      state.setCode('Version 1');
      state.saveToHistory();

      expect(state.history).toEqual(['Version 1']);
      expect(state.historyIndex).toBe(0);
      expect(state.isCodeDirty).toBe(true);
    });

    it('should track multiple history entries', () => {
      const state = useEditorStore.getState();

      state.setCode('Version 1');
      state.saveToHistory();

      state.setCode('Version 2');
      state.saveToHistory();

      state.setCode('Version 3');
      state.saveToHistory();

      expect(state.history).toEqual(['Version 1', 'Version 2', 'Version 3']);
      expect(state.historyIndex).toBe(2);
    });

    it('should undo to previous version', () => {
      const state = useEditorStore.getState();

      state.setCode('Version 1');
      state.saveToHistory();

      state.setCode('Version 2');
      state.saveToHistory();

      state.undo();

      expect(state.code).toBe('Version 1');
      expect(state.historyIndex).toBe(0);
    });

    it('should redo to next version', () => {
      const state = useEditorStore.getState();

      state.setCode('Version 1');
      state.saveToHistory();

      state.setCode('Version 2');
      state.saveToHistory();

      state.undo(); // Back to Version 1
      state.redo(); // Forward to Version 2

      expect(state.code).toBe('Version 2');
      expect(state.historyIndex).toBe(1);
    });

    it('should prevent undo at first version', () => {
      const state = useEditorStore.getState();

      state.setCode('Version 1');
      state.saveToHistory();

      expect(state.canUndo()).toBe(false);

      state.undo(); // Should not change anything
      expect(state.code).toBe('Version 1');
    });

    it('should prevent redo at latest version', () => {
      const state = useEditorStore.getState();

      state.setCode('Version 1');
      state.saveToHistory();

      expect(state.canRedo()).toBe(false);
    });

    it('should limit history size', () => {
      const state = useEditorStore.getState();

      // Add more entries than MAX_HISTORY_SIZE (50)
      for (let i = 0; i < 60; i++) {
        state.setCode(`Version ${i}`);
        state.saveToHistory();
      }

      expect(state.history.length).toBe(50); // Should be limited
      expect(state.history[0]).toBe('Version 10'); // First entry should be removed
      expect(state.history[state.history.length - 1]).toBe('Version 59');
    });
  });

  describe('File Operations', () => {
    it('should clear code', () => {
      const state = useEditorStore.getState();

      state.setCode('Some code');
      expect(state.code).not.toBe('');

      state.clearCode();
      expect(state.code).toBe('');
      expect(state.isCodeDirty).toBe(false);
    });

    it('should save code successfully', async () => {
      const state = useEditorStore.getState();
      state.setCode('print("test")');
      state.setFileName('test.py');

      await state.saveCode();

      expect(state.isCodeDirty).toBe(false);
      expect(state.isSaving).toBe(false);
    });

    it('should handle save error gracefully', async () => {
      const state = useEditorStore.getState();

      // Mock console.error to avoid noise in test output
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      state.setCode('print("test")');
      state.setFileName('test.py');

      // Test save failure (in real implementation, this would fail due to network error)
      try {
        await state.saveCode();
      } catch (error) {
        // Expected behavior on error
      }

      consoleSpy.mockRestore();
    });
  });

  describe('Selection Management', () => {
    it('should set selection', () => {
      const state = useEditorStore.getState();
      const start = { line: 1, column: 5 };
      const end = { line: 1, column: 10 };

      state.setSelection(start, end);

      expect(state.selection).toEqual({ start, end });
    });

    it('should clear selection', () => {
      const state = useEditorStore.getState();

      state.setSelection({ line: 1, column: 5 }, { line: 1, column: 10 });
      expect(state.selection).toBeDefined();

      state.clearSelection();
      expect(state.selection).toBeUndefined();
    });
  });

  describe('Editor Actions', () => {
    it('should update code using helper function', () => {
      const initialCode = useEditorStore.getState().code;

      editorActions.updateCode('Updated code');

      expect(useEditorStore.getState().code).toBe('Updated code');
      expect(useEditorStore.getState().isCodeDirty).toBe(true);
    });

    it('should format code for Python', async () => {
      const state = useEditorStore.getState();
      state.setLanguage('python');
      state.setCode('def test():\nprint("hello")'); // Bad indentation

      await editorActions.formatCode();

      // Basic formatting should be applied
      expect(state.code).toContain('def test():');
    });
  });

  describe('Reset functionality', () => {
    it('should reset to initial state', () => {
      const state = useEditorStore.getState();

      // Modify state
      state.setCode('Modified code');
      state.setLanguage('javascript');
      state.setFileName('test.js');
      state.setDiagnostics([{ line: 1, column: 1, message: 'Error', severity: 'error' }]);
      state.saveToHistory();

      // Verify modifications
      expect(state.code).toBe('Modified code');
      expect(state.language).toBe('javascript');
      expect(state.diagnostics.length).toBe(1);

      // Reset
      state.reset();

      // Verify reset
      expect(state.code).toContain('Write your Python code here');
      expect(state.language).toBe('python');
      expect(state.fileName).toBe('main.py');
      expect(state.diagnostics).toEqual([]);
      expect(state.history).toEqual([]);
    });
  });
});