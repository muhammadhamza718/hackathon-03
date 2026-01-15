/**
 * Editor State Management with Zustand
 * Last Updated: 2026-01-15
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface EditorState {
  // Editor content and configuration
  code: string;
  language: string;
  fileName: string;

  // Editor UI state
  isEditorReady: boolean;
  isCodeDirty: boolean;
  isSaving: boolean;

  // Editor settings
  fontSize: number;
  wordWrap: 'on' | 'off';
  minimap: boolean;
  theme: 'light' | 'dark' | 'high-contrast';

  // Selection and cursor
  selection?: {
    start: { line: number; column: number };
    end: { line: number; column: number };
  };

  // Diagnostics and errors
  diagnostics: Array<{
    line: number;
    column: number;
    message: string;
    severity: 'error' | 'warning' | 'info';
  }>;

  // History for undo/redo (simplified)
  history: string[];
  historyIndex: number;

  // Actions
  setCode: (code: string) => void;
  setLanguage: (language: string) => void;
  setFileName: (name: string) => void;
  setEditorReady: (ready: boolean) => void;
  setFontSize: (size: number) => void;
  setWordWrap: (wrap: 'on' | 'off') => void;
  setMinimap: (enabled: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'high-contrast') => void;
  setDiagnostics: (diagnostics: Array<{ line: number; column: number; message: string; severity: 'error' | 'warning' | 'info' }>) => void;
  clearDiagnostics: () => void;

  // History management
  saveToHistory: () => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;

  // File operations
  saveCode: () => Promise<void>;
  clearCode: () => void;

  // Selection management
  setSelection: (start: { line: number; column: number }, end: { line: number; column: number }) => void;
  clearSelection: () => void;

  // Reset
  reset: () => void;
}

const MAX_HISTORY_SIZE = 50; // Maximum number of history states to keep

export const useEditorStore = create<EditorState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        code: '# Write your Python code here...\n\ndef hello_world():\n    print("Hello, World!")\n',
        language: 'python',
        fileName: 'main.py',
        isEditorReady: false,
        isCodeDirty: false,
        isSaving: false,
        fontSize: 14,
        wordWrap: 'on',
        minimap: false,
        theme: 'dark',
        diagnostics: [],
        history: [],
        historyIndex: -1,

        // Code and content setters
        setCode: (code) => {
          const { code: currentCode } = get();
          if (code !== currentCode) {
            set({
              code,
              isCodeDirty: true,
            });
          }
        },

        setLanguage: (language) => set({ language }),
        setFileName: (fileName) => set({ fileName }),

        // Editor readiness
        setEditorReady: (isEditorReady) => set({ isEditorReady }),

        // Editor settings
        setFontSize: (fontSize) => set({ fontSize }),
        setWordWrap: (wordWrap) => set({ wordWrap }),
        setMinimap: (minimap) => set({ minimap }),
        setTheme: (theme) => set({ theme }),

        // Diagnostics
        setDiagnostics: (diagnostics) => set({ diagnostics }),
        clearDiagnostics: () => set({ diagnostics: [] }),

        // History management
        saveToHistory: () => {
          const { code, history, historyIndex } = get();
          const newHistory = history.slice(0, historyIndex + 1); // Remove any redo states
          const updatedHistory = [...newHistory, code];

          // Limit history size
          if (updatedHistory.length > MAX_HISTORY_SIZE) {
            updatedHistory.shift(); // Remove oldest entry
          }

          set({
            history: updatedHistory,
            historyIndex: updatedHistory.length - 1,
            isCodeDirty: true,
          });
        },

        undo: () => {
          const { history, historyIndex } = get();
          if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            set({
              code: history[newIndex],
              historyIndex: newIndex,
              isCodeDirty: true,
            });
          }
        },

        redo: () => {
          const { history, historyIndex } = get();
          if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            set({
              code: history[newIndex],
              historyIndex: newIndex,
              isCodeDirty: true,
            });
          }
        },

        canUndo: () => {
          const { historyIndex } = get();
          return historyIndex > 0;
        },

        canRedo: () => {
          const { history, historyIndex } = get();
          return historyIndex < history.length - 1;
        },

        // File operations
        saveCode: async () => {
          const { code, fileName, language } = get();
          set({ isSaving: true });

          try {
            // In production, this would save to backend
            // const response = await api.post('/code/save', { code, fileName, language });

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500));

            console.log('Code saved:', { fileName, language, codeLength: code.length });

            set({
              isCodeDirty: false,
              isSaving: false,
            });

            // Save to history after successful save
            get().saveToHistory();
          } catch (error) {
            console.error('Failed to save code:', error);
            set({ isSaving: false });
            throw error;
          }
        },

        clearCode: () => {
          set({
            code: '',
            isCodeDirty: false,
            diagnostics: [],
          });
        },

        // Selection management
        setSelection: (start, end) => {
          set({ selection: { start, end } });
        },

        clearSelection: () => {
          set({ selection: undefined });
        },

        // Reset
        reset: () => {
          set({
            code: '# Write your Python code here...\n\ndef hello_world():\n    print("Hello, World!")\n',
            language: 'python',
            fileName: 'main.py',
            isCodeDirty: false,
            isSaving: false,
            diagnostics: [],
            selection: undefined,
            history: [],
            historyIndex: -1,
          });
        },
      }),
      {
        name: 'editor-storage', // localStorage key
        partialize: (state) => ({
          // Persist only these fields
          code: state.code,
          language: state.language,
          fileName: state.fileName,
          fontSize: state.fontSize,
          wordWrap: state.wordWrap,
          minimap: state.minimap,
          theme: state.theme,
          history: state.history,
          historyIndex: state.historyIndex,
        }),
      }
    ),
    {
      name: 'EditorStore',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);

// Derived state selectors
export const useEditorSelectors = {
  // Get current code
  useCode: () => useEditorStore((state) => state.code),

  // Get editor configuration
  useConfig: () =>
    useEditorStore((state) => ({
      language: state.language,
      fontSize: state.fontSize,
      wordWrap: state.wordWrap,
      minimap: state.minimap,
      theme: state.theme,
    })),

  // Get editor status
  useStatus: () =>
    useEditorStore((state) => ({
      isEditorReady: state.isEditorReady,
      isCodeDirty: state.isCodeDirty,
      isSaving: state.isSaving,
    })),

  // Get diagnostics
  useDiagnostics: () => useEditorStore((state) => state.diagnostics),

  // Get history status
  useHistory: () =>
    useEditorStore((state) => ({
      canUndo: state.canUndo(),
      canRedo: state.canRedo(),
      historyLength: state.history.length,
      historyIndex: state.historyIndex,
    })),

  // Get selection
  useSelection: () => useEditorStore((state) => state.selection),
};

// Helper functions for common operations
export const editorActions = {
  // Update code and save to history
  updateCode: (code: string) => {
    const state = useEditorStore.getState();
    const previousCode = state.code;

    // Update code
    state.setCode(code);

    // If change is significant, save to history
    if (Math.abs(code.length - previousCode.length) > 3 ||
        code.split('\n').length !== previousCode.split('\n').length) {
      // Debounced history save would be better here
      // For now, we'll save on manual trigger
    }
  },

  // Auto-save with debounce
  autoSave: debounce(() => {
    const state = useEditorStore.getState();
    if (state.isCodeDirty && state.isEditorReady) {
      state.saveCode().catch(console.error);
    }
  }, 2000),

  // Format code (placeholder for future implementation)
  formatCode: async () => {
    const { code, language } = useEditorStore.getState();

    // In production, this would call a formatting service
    // For now, we'll use basic Python formatting
    if (language === 'python') {
      try {
        // Simple Python formatting (basic indentation fix)
        const lines = code.split('\n');
        const formatted = lines.map(line => line.trimEnd()).join('\n');

        useEditorStore.getState().setCode(formatted);
      } catch (error) {
        console.error('Formatting failed:', error);
      }
    }
  },
};

// Utility function for debouncing
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}