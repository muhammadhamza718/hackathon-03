"""
Error Pattern Matching Service
Debug Agent
"""

import re
from typing import Dict, List, Optional, Tuple

class PatternMatcher:
    """
    Service for detecting common error patterns in stack traces and error messages
    """

    # Common error patterns with regex
    PATTERNS = {
        "index_out_of_range": {
            "regex": r"(IndexError|index.*out of range|list index out of range)",
            "pattern_id": "ERR-001",
            "name": "Index Out of Range"
        },
        "syntax_error": {
            "regex": r"(SyntaxError|invalid syntax|unexpected token)",
            "pattern_id": "ERR-002",
            "name": "Syntax Error"
        },
        "type_error": {
            "regex": r"(TypeError|unsupported operand type|cannot concatenate)",
            "pattern_id": "ERR-003",
            "name": "Type Error"
        },
        "name_error": {
            "regex": r"(NameError|name.*is not defined|undefined variable)",
            "pattern_id": "ERR-004",
            "name": "Name Error"
        },
        "attribute_error": {
            "regex": r"(AttributeError|has no attribute|object has no property)",
            "pattern_id": "ERR-005",
            "name": "Attribute Error"
        }
    }

    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern["regex"], re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }

    def detect_pattern(self, error_message: str, stack_trace: str = "") -> Optional[Tuple[str, Dict]]:
        """
        Detect error pattern from error message and stack trace

        Returns:
            Tuple of (pattern_id, pattern_data) or None if no match
        """
        combined_text = f"{error_message} {stack_trace}"

        for pattern_name, compiled in self.compiled_patterns.items():
            if compiled.search(combined_text):
                return pattern_name, self.PATTERNS[pattern_name]

        return None

    def get_suggestions(self, pattern_id: str) -> List[str]:
        """
        Get common fixes for a specific error pattern
        """
        suggestions_map = {
            "ERR-001": [
                "Check array bounds with len() before access",
                "Use try/except for dynamic indexing",
                "Validate index against collection length"
            ],
            "ERR-002": [
                "Check parentheses and brackets matching",
                "Verify proper indentation (4 spaces)",
                "Use IDE syntax highlighting"
            ],
            "ERR-003": [
                "Check variable types with type()",
                "Use type hints in function signatures",
                "Convert explicitly with int(), str(), etc."
            ],
            "ERR-004": [
                "Check variable spelling",
                "Verify variable is defined in scope",
                "Check import statements"
            ],
            "ERR-005": [
                "Check object type and attributes",
                "Use dir() to list available attributes",
                "Verify import of required classes/modules"
            ]
        }

        return suggestions_map.get(pattern_id, ["Review error message and stack trace"])

    def analyze_complexity(self, code: str) -> Dict[str, float]:
        """
        Analyze code complexity metrics
        """
        lines = code.strip().split('\n')
        return {
            "lines_of_code": len(lines),
            "function_count": len([l for l in lines if l.strip().startswith("def ")]),
            "class_count": len([l for l in lines if l.strip().startswith("class ")]),
            "indentation_depth": self._calculate_max_indentation(lines),
            "cyclomatic_complexity": self._estimate_cyclomatic_complexity(lines)
        }

    def _calculate_max_indentation(self, lines: List[str]) -> int:
        """Calculate maximum indentation depth"""
        max_depth = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped and not stripped.startswith("#"):
                indent = len(line) - len(stripped)
                depth = indent // 4
                max_depth = max(max_depth, depth)
        return max_depth

    def _estimate_cyclomatic_complexity(self, lines: List[str]) -> int:
        """Estimate cyclomatic complexity"""
        complexity = 1  # Start with 1
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ["if ", "elif ", "for ", "while ", "and ", "or "]):
                complexity += 1
        return complexity

# Global service instance
pattern_matcher = PatternMatcher()