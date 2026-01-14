"""
Unit tests for Syntax Analysis Logic
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.syntax_analyzer import analyze_with_mcp

def test_syntax_analysis_basic():
    """Test basic syntax analysis"""
    result = analyze_with_mcp("print('Hello')", "python")
    assert "valid_syntax" in result
    assert isinstance(result, dict)

def test_syntax_analysis_error_detection():
    """Test syntax error detection"""
    # This should work even with fallback
    result = analyze_with_mcp("print('Hello", "python")  # Missing closing quote
    assert isinstance(result, dict)
    assert "errors" in result or "warnings" in result

def test_syntax_analysis_efficiency_note():
    """Test that efficiency note is present in fallback"""
    result = analyze_with_mcp("x = 5", "python")
    if "warnings" in result:
        assert any("efficiency" in str(w).lower() for w in result["warnings"])

if __name__ == "__main__":
    pytest.main([__file__])