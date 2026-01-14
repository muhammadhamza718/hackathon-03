"""
Integration tests for Error Pattern Matching
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.pattern_matching import pattern_matcher

def test_pattern_detection_index_error():
    """Test Index Out of Range pattern detection"""
    pattern = pattern_matcher.detect_pattern("IndexError: list index out of range")
    assert pattern is not None
    pattern_name, pattern_data = pattern
    assert pattern_name == "index_out_of_range"
    assert pattern_data["pattern_id"] == "ERR-001"

def test_pattern_detection_syntax_error():
    """Test Syntax Error pattern detection"""
    pattern = pattern_matcher.detect_pattern("SyntaxError: invalid syntax")
    assert pattern is not None
    pattern_name, pattern_data = pattern
    assert pattern_name == "syntax_error"

def test_pattern_suggestions():
    """Test getting suggestions for patterns"""
    suggestions = pattern_matcher.get_suggestions("ERR-001")
    assert len(suggestions) > 0
    assert any("bounds" in s.lower() for s in suggestions)

def test_complexity_analysis():
    """Test code complexity analysis"""
    code = """
def hello():
    if True:
        for i in range(10):
            print(i)
"""
    complexity = pattern_matcher.analyze_complexity(code)
    assert complexity["lines_of_code"] >= 5
    assert complexity["function_count"] == 1
    assert complexity["cyclomatic_complexity"] >= 2

if __name__ == "__main__":
    pytest.main([__file__])