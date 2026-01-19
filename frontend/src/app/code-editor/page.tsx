/**
 * Code Editor Page
 * Full-screen code editor with real-time feedback panel
 * Last Updated: 2026-01-15
 */

"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useSSE } from '@/lib/sse';
import { useEditorStore } from '@/store/editor-store';
import { useAuth } from '@/hooks/useAuth';

// Dynamically import Monaco Editor to avoid server-side rendering issues
const MonacoEditor = dynamic(
  () => import('@/components/organisms/MonacoEditor').then((mod) => mod.MonacoEditor),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-zinc-600 dark:text-zinc-400">Loading Editor...</p>
        </div>
      </div>
    ),
  }
);

// Available assignments for selection
const ASSIGNMENTS = [
  { id: '1', title: 'Hello World Function', difficulty: 'easy', topic: 'Basics' },
  { id: '2', title: 'Fibonacci Sequence', difficulty: 'medium', topic: 'Recursion' },
  { id: '3', title: 'Binary Search Tree', difficulty: 'hard', topic: 'Data Structures' },
  { id: '4', title: 'Sorting Algorithms', difficulty: 'medium', topic: 'Algorithms' },
  { id: '5', title: 'Graph Traversal', difficulty: 'hard', topic: 'Graph Theory' },
];

export default function CodeEditorPage() {
  const router = useRouter();
  const { user } = useAuth();
  const sse = useSSE();

  // Editor state
  const [selectedAssignment, setSelectedAssignment] = useState(ASSIGNMENTS[0]);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFeedback, setShowFeedback] = useState(true);
  const [masteryUpdate, setMasteryUpdate] = useState<any>(null);

  // Editor store actions
  const { code, setCode, saveCode, isCodeDirty, editorInstance } = useEditorStore();

  // Subscribe to real-time feedback
  useEffect(() => {
    const unsubscribe = sse.subscribe('feedback-received', (event) => {
      console.log('Feedback received:', event);

      // Parse feedback data
      const feedback = {
        id: event.id,
        timestamp: new Date(event.timestamp),
        type: event.data.type || 'general',
        message: event.data.message || 'No message provided',
        line: event.data.line,
        column: event.data.column,
        severity: event.data.severity || 'info',
      };

      setTestResults(prev => [feedback, ...prev].slice(0, 10));

      // Show toast notification
      showToast('New feedback received!', 'info');
    });

    const unsubscribeMastery = sse.subscribe('mastery-updated', (event) => {
      console.log('Mastery update received:', event);
      setMasteryUpdate({
        score: event.data.score,
        topic: event.data.topic,
        change: event.data.change,
      });

      showToast(`Mastery updated: ${event.data.topic} +${event.data.change}%`, 'success');

      // Clear after 5 seconds
      setTimeout(() => setMasteryUpdate(null), 5000);
    });

    return () => {
      unsubscribe();
      unsubscribeMastery();
    };
  }, [sse]);

  // Auto-save functionality
  useEffect(() => {
    if (!isCodeDirty) return;

    const autoSaveTimer = setTimeout(() => {
      saveCode().catch(console.error);
    }, 3000); // Auto-save after 3 seconds of inactivity

    return () => clearTimeout(autoSaveTimer);
  }, [code, isCodeDirty, saveCode]);

  // Handle code submission
  const handleSubmit = async () => {
    if (!code || isSubmitting) return;

    setIsSubmitting(true);
    setTestResults([]);

    try {
      // In production, this would call your backend API
      // For demo, we simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Simulate test results
      const mockResults = [
        {
          id: 'test-1',
          type: 'test',
          message: 'Test case 1 passed: Function returns correct output',
          severity: 'success',
          timestamp: new Date(),
        },
        {
          id: 'test-2',
          type: 'test',
          message: 'Test case 2 passed: Handles edge cases',
          severity: 'success',
          timestamp: new Date(),
        },
        {
          id: 'test-3',
          type: 'test',
          message: 'Performance: O(n log n) complexity confirmed',
          severity: 'info',
          timestamp: new Date(),
        },
      ];

      setTestResults(mockResults);
      showToast('Code submitted successfully!', 'success');

      // Trigger auto-save
      await saveCode();

    } catch (error) {
      console.error('Submission failed:', error);
      setTestResults([{
        id: 'error',
        type: 'error',
        message: 'Submission failed. Please try again.',
        severity: 'error',
        timestamp: new Date(),
      }]);
      showToast('Submission failed', 'warning');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle code execution/run
  const handleRun = async (codeToRun: string) => {
    if (!codeToRun || isRunning) return;

    setIsRunning(true);
    setTestResults([]);

    try {
      // In production, this would execute code in a sandbox
      // For demo, we simulate execution
      await new Promise(resolve => setTimeout(resolve, 800));

      const mockOutput = [
        {
          id: 'run-1',
          type: 'output',
          message: 'Running code...',
          severity: 'info',
          timestamp: new Date(),
        },
        {
          id: 'run-2',
          type: 'output',
          message: 'Output: Hello, World!',
          severity: 'success',
          timestamp: new Date(),
        },
        {
          id: 'run-3',
          type: 'output',
          message: 'Execution time: 45ms',
          severity: 'info',
          timestamp: new Date(),
        },
      ];

      setTestResults(mockOutput);
      showToast('Code executed successfully!', 'success');

    } catch (error) {
      console.error('Execution failed:', error);
      setTestResults([{
        id: 'error',
        type: 'error',
        message: 'Execution failed: Syntax error detected',
        severity: 'error',
        timestamp: new Date(),
      }]);
      showToast('Execution failed', 'warning');
    } finally {
      setIsRunning(false);
    }
  };

  // Handle save
  const handleSave = async () => {
    try {
      await saveCode();
      showToast('Code saved successfully!', 'success');
    } catch (error) {
      console.error('Save failed:', error);
      showToast('Save failed', 'warning');
    }
  };

  // Handle format
  const handleFormat = () => {
    if (editorInstance) {
      editorInstance.getAction('editor.action.formatDocument')?.run();
      showToast('Code formatted', 'info');
    }
  };

  // Handle clear
  const handleClear = () => {
    setCode('');
    setTestResults([]);
    showToast('Editor cleared', 'info');
  };

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Ctrl/Cmd + S: Save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    }

    // Ctrl/Cmd + Enter: Run
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRun(code);
    }

    // Ctrl/Cmd + Shift + F: Format
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'f') {
      e.preventDefault();
      handleFormat();
    }
  }, [code]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <div className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
              Code Editor
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Write and test your Python code with real-time feedback
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Assignment Selector */}
      <div className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-6 py-3">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Select Assignment
            </label>
            <select
              value={selectedAssignment.id}
              onChange={(e) => {
                const assignment = ASSIGNMENTS.find(a => a.id === e.target.value);
                if (assignment) setSelectedAssignment(assignment);
              }}
              className="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {ASSIGNMENTS.map((assignment) => (
                <option key={assignment.id} value={assignment.id}>
                  {assignment.title} ({assignment.difficulty}) - {assignment.topic}
                </option>
              ))}
            </select>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2 px-4 py-2 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
            <span className={`w-2 h-2 rounded-full ${
              sse.getConnectionStatus().isConnected
                ? 'bg-green-500 animate-pulse'
                : 'bg-red-500'
            }`} />
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {sse.getConnectionStatus().isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex h-[calc(100vh-180px)]">
        {/* Editor Panel */}
        <div className={`flex-1 flex flex-col ${showFeedback ? 'w-2/3' : 'w-full'}`}>
          {/* Toolbar */}
          <div className="bg-zinc-100 dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isRunning
                    ? 'bg-zinc-400 text-white cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {isRunning ? (
                  <>
                    <span className="animate-spin">⟳</span>
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <span>▶</span>
                    <span>Run</span>
                  </>
                )}
              </button>

              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isSubmitting
                    ? 'bg-zinc-400 text-white cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <span className="animate-spin">⟳</span>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <span>📤</span>
                    <span>Submit</span>
                  </>
                )}
              </button>

              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium bg-zinc-800 text-white hover:bg-zinc-900 dark:bg-zinc-700 dark:hover:bg-zinc-600 transition-colors"
              >
                <span>💾</span>
                <span>Save</span>
                {isCodeDirty && <span className="w-2 h-2 bg-yellow-400 rounded-full" />}
              </button>

              <button
                onClick={handleFormat}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium bg-zinc-200 text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 transition-colors"
              >
                <span>✨</span>
                <span>Format</span>
              </button>

              <button
                onClick={handleClear}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium bg-zinc-200 text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 transition-colors"
              >
                <span>🗑️</span>
                <span>Clear</span>
              </button>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowFeedback(!showFeedback)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  showFeedback
                    ? 'bg-blue-600 text-white'
                    : 'bg-zinc-200 text-zinc-800 hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                <span>💬</span>
                <span>{showFeedback ? 'Hide Feedback' : 'Show Feedback'}</span>
              </button>
            </div>
          </div>

          {/* Editor */}
          <div className="flex-1 overflow-hidden">
            <MonacoEditor
              value={code}
              language="python"
              theme="dark"
              fontSize={14}
              wordWrap="on"
              minimap={true}
              onChange={(value) => setCode(value || '')}
              onSave={handleSave}
              onRun={handleRun}
              filePath={`${selectedAssignment.title.replace(/\s+/g, '_')}.py`}
              height="100%"
            />
          </div>

          {/* Action Hints */}
          <div className="bg-zinc-100 dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800 px-4 py-2 text-xs text-zinc-600 dark:text-zinc-400 flex items-center gap-4">
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-zinc-800 rounded border border-zinc-300 dark:border-zinc-700">Ctrl+S</kbd> Save</span>
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-zinc-800 rounded border border-zinc-300 dark:border-zinc-700">Ctrl+Enter</kbd> Run</span>
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-zinc-800 rounded border border-zinc-300 dark:border-zinc-700">Ctrl+Shift+F</kbd> Format</span>
          </div>
        </div>

        {/* Feedback Panel */}
        {showFeedback && (
          <div className="w-1/3 bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 flex flex-col">
            {/* Panel Header */}
            <div className="px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
              <h2 className="font-bold text-zinc-900 dark:text-zinc-100">
                Real-Time Feedback
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Live updates from automated testing
              </p>
            </div>

            {/* Mastery Update Banner */}
            {masteryUpdate && (
              <div className="mx-4 mt-4 p-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg animate-pulse">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎯</span>
                  <div>
                    <p className="font-bold">
                      Mastery Updated: {masteryUpdate.topic}
                    </p>
                    <p className="text-sm opacity-90">
                      +{masteryUpdate.change}% (Current: {masteryUpdate.score}%)
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Test Results */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {testResults.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-3">📊</div>
                  <p className="text-zinc-600 dark:text-zinc-400">
                    No test results yet
                  </p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-500 mt-1">
                    Run or submit your code to see feedback
                  </p>
                </div>
              ) : (
                testResults.map((result) => (
                  <div
                    key={result.id}
                    className={`p-3 rounded-lg border ${
                      result.severity === 'success'
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                        : result.severity === 'error'
                        ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                        : result.severity === 'warning'
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                        : 'bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-lg">
                        {result.severity === 'success' && '✅'}
                        {result.severity === 'error' && '❌'}
                        {result.severity === 'warning' && '⚠️'}
                        {result.severity === 'info' && 'ℹ️'}
                      </span>
                      <div className="flex-1">
                        <p className={`text-sm font-medium ${
                          result.severity === 'success'
                            ? 'text-green-800 dark:text-green-200'
                            : result.severity === 'error'
                            ? 'text-red-800 dark:text-red-200'
                            : result.severity === 'warning'
                            ? 'text-yellow-800 dark:text-yellow-200'
                            : 'text-zinc-800 dark:text-zinc-200'
                        }`}>
                          {result.message}
                        </p>
                        {result.line && (
                          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                            Line {result.line}, Column {result.column}
                          </p>
                        )}
                        <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1">
                          {new Date(result.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Connection Health */}
            <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
              <div className="text-xs text-zinc-600 dark:text-zinc-400">
                <div className="flex items-center justify-between mb-1">
                  <span>Connection:</span>
                  <span className={`font-bold ${
                    sse.getConnectionStatus().isConnected
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {sse.getConnectionStatus().isConnected ? 'Healthy' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex items-center justify-between mb-1">
                  <span>Events:</span>
                  <span className="font-bold text-zinc-900 dark:text-zinc-100">
                    {sse.state.eventCount}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Last Event:</span>
                  <span className="font-bold text-zinc-900 dark:text-zinc-100">
                    {sse.getConnectionStatus().lastEvent
                      ? new Date(sse.getConnectionStatus().lastEvent!).toLocaleTimeString()
                      : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to show toast notifications
function showToast(message: string, type: 'success' | 'info' | 'warning' = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const colors = {
    success: 'bg-green-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500',
  };

  toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-y-0 opacity-100 pointer-events-auto`;
  toast.textContent = message;

  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  }, 10);

  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}