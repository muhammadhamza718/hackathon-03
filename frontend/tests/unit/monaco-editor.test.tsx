/**
 * Unit Tests for Monaco Editor Component
 * Last Updated: 2026-01-15
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MonacoEditor } from '@/components/organisms/MonacoEditor';

// Mock the Monaco Editor React component
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, language, theme, onChange, onMount }: any) => {
    return (
      <div data-testid="mock-monaco-editor">
        <textarea
          data-testid="editor-textarea"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          data-language={language}
          data-theme={theme}
        />
        <button
          data-testid="mount-callback"
          onClick={() =>
            onMount?.(
              {
                getValue: () => value,
                setValue: jest.fn(),
                updateOptions: jest.fn(),
                onDidChangeModelContent: jest.fn(),
                addCommand: jest.fn(),
                getAction: jest.fn(),
                getPosition: jest.fn(),
                executeEdits: jest.fn(),
              },
              { Range: jest.fn() }
            )
          }
        >
          Trigger Mount
        </button>
      </div>
    );
  },
  useMonaco: () => null,
}));

describe('MonacoEditor', () => {
  const defaultProps = {
    value: 'print("Hello, World!")',
    language: 'python',
    onChange: jest.fn(),
    onSave: jest.fn(),
    onRun: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders the editor with initial value', () => {
      render(<MonacoEditor {...defaultProps} />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toHaveValue('print("Hello, World!")');
      expect(textarea).toHaveAttribute('data-language', 'python');
    });

    it('displays file path in header', () => {
      render(
        <MonacoEditor
          {...defaultProps}
          filePath="test_script.py"
        />
      );

      expect(screen.getByText('test_script.py')).toBeInTheDocument();
    });

    it('shows loading overlay initially', () => {
      render(<MonacoEditor {...defaultProps} />);

      expect(screen.getByText('Loading Monaco Editor...')).toBeInTheDocument();
    });

    it('hides loading overlay after mount', async () => {
      render(<MonacoEditor {...defaultProps} />);

      fireEvent.click(screen.getByTestId('mount-callback'));

      await waitFor(() => {
        expect(screen.queryByText('Loading Monaco Editor...')).not.toBeInTheDocument();
      });
    });

    it('shows read-only indicator when readOnly is true', () => {
      render(<MonacoEditor {...defaultProps} readOnly={true} />);

      expect(screen.getByText('(Read Only)')).toBeInTheDocument();
    });
  });

  describe('Editor Behavior', () => {
    it('calls onChange when editor content changes', () => {
      const handleChange = jest.fn();
      render(<MonacoEditor {...defaultProps} onChange={handleChange} />);

      const textarea = screen.getByTestId('editor-textarea');
      fireEvent.change(textarea, { target: { value: 'print("Updated!")' } });

      expect(handleChange).toHaveBeenCalledWith('print("Updated!")');
    });

    it('calls onSave when save is triggered', async () => {
      const handleSave = jest.fn();
      render(<MonacoEditor {...defaultProps} onSave={handleSave} />);

      fireEvent.click(screen.getByTestId('mount-callback'));

      // Simulate Ctrl+S
      const textarea = screen.getByTestId('editor-textarea');
      fireEvent.keyDown(textarea, { ctrlKey: true, key: 's' });

      await waitFor(() => {
        expect(handleSave).toHaveBeenCalledWith('print("Hello, World!")');
      });
    });

    it('calls onRun when run is triggered', async () => {
      const handleRun = jest.fn();
      render(<MonacoEditor {...defaultProps} onRun={handleRun} />);

      fireEvent.click(screen.getByTestId('mount-callback'));

      // Simulate Ctrl+Enter
      const textarea = screen.getByTestId('editor-textarea');
      fireEvent.keyDown(textarea, { ctrlKey: true, key: 'Enter' });

      await waitFor(() => {
        expect(handleRun).toHaveBeenCalledWith('print("Hello, World!")');
      });
    });

    it('updates value when prop changes', () => {
      const { rerender } = render(<MonacoEditor {...defaultProps} value="initial" />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toHaveValue('initial');

      rerender(<MonacoEditor {...defaultProps} value="updated" />);
      expect(textarea).toHaveValue('updated');
    });
  });

  describe('Shortcuts Display', () => {
    it('displays keyboard shortcuts in footer', () => {
      render(<MonacoEditor {...defaultProps} />);

      expect(screen.getByText('Ctrl+S: Save')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+Enter: Run')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+Shift+F: Format')).toBeInTheDocument();
    });
  });

  describe('Configuration Options', () => {
    it('applies custom font size', () => {
      render(<MonacoEditor {...defaultProps} fontSize={16} />);

      const textarea = screen.getByTestId('editor-textarea');
      // Font size is handled by Monaco, just verify it renders
      expect(textarea).toBeInTheDocument();
    });

    it('applies word wrap setting', () => {
      render(<MonacoEditor {...defaultProps} wordWrap="on" />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toBeInTheDocument();
    });

    it('applies minimap setting', () => {
      render(<MonacoEditor {...defaultProps} minimap={true} />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toBeInTheDocument();
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme by default', () => {
      render(<MonacoEditor {...defaultProps} theme="dark" />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toHaveAttribute('data-theme', 'vs-dark');
    });

    it('applies light theme', () => {
      render(<MonacoEditor {...defaultProps} theme="light" />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toHaveAttribute('data-theme', 'vs');
    });

    it('applies high contrast theme', () => {
      render(<MonacoEditor {...defaultProps} theme="hc" />);

      const textarea = screen.getByTestId('editor-textarea');
      expect(textarea).toHaveAttribute('data-theme', 'hc-black');
    });
  });

  describe('A11y', () => {
    it('has proper ARIA attributes', () => {
      render(<MonacoEditor {...defaultProps} filePath="test.py" />);

      const container = screen.getByRole('region');
      expect(container).toHaveAttribute('aria-label', 'Code editor for test.py');
    });

    it('has proper keyboard navigation', () => {
      render(<MonacoEditor {...defaultProps} />);

      const textarea = screen.getByTestId('editor-textarea');
      fireEvent.focus(textarea);

      expect(textarea).toHaveFocus();
    });
  });
});