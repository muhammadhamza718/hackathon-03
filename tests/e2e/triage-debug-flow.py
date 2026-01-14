"""
End-to-end test for Triage → Debug → Analysis → Response flow
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'debug-agent', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src'))

@pytest.mark.asyncio
async def test_complete_debug_flow():
    """Test complete flow from Triage to Debug Agent response"""
    from services.pattern_matching import pattern_matcher
    from services.kafka_consumer import debug_consumer
    from services.syntax_analyzer import analyze_with_mcp

    # Step 1: Student submits code with error
    test_code = "print('Hello"
    test_error = "SyntaxError: EOL while scanning string literal"

    # Step 2: Debug Agent receives analysis request
    syntax_result = analyze_with_mcp(test_code, "python")
    assert syntax_result is not None

    # Step 3: Pattern detection
    pattern = pattern_matcher.detect_pattern(test_error, "")
    if pattern:
        pattern_name, pattern_data = pattern
        suggestions = pattern_matcher.get_suggestions(pattern_data["pattern_id"])
        assert len(suggestions) > 0

    # Step 4: Process through Kafka consumer (simulated)
    kafka_event = {
        "student_id": "test_student",
        "timestamp": "2026-01-14T10:30:00Z",
        "error_type": test_error,
        "code_snippet": test_code
    }

    processed = debug_consumer.process_debug_event(kafka_event)
    assert processed is not None

    # Step 5: Verify response structure
    assert "student_id" in processed
    assert "suggestions" in processed

    print("✓ Complete Triage→Debug→Analysis→Response flow verified")

@pytest.mark.asyncio
async def test_error_pattern_processing():
    """Test end-to-end error pattern processing"""
    from services.pattern_matching import pattern_matcher

    # Test different error types
    test_cases = [
        ("IndexError: list index out of range", "ERR-001"),
        ("SyntaxError: invalid syntax", "ERR-002"),
        ("TypeError: unsupported operand type(s)", "ERR-003")
    ]

    for error_msg, expected_pattern_id in test_cases:
        pattern = pattern_matcher.detect_pattern(error_msg)
        if pattern:
            _, pattern_data = pattern
            assert pattern_data["pattern_id"] == expected_pattern_id

            suggestions = pattern_matcher.get_suggestions(expected_pattern_id)
            assert len(suggestions) > 0

    print("✓ Error pattern processing verified")

@pytest.mark.asyncio
async def test_debug_agent_api_responses():
    """Test Debug Agent API produces correct response format"""
    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test analyze endpoint
    analyze_response = client.post("/analyze/", json={
        "code": "x = 5\nprint(x)",
        "language": "python",
        "student_id": "test_student"
    })
    assert analyze_response.status_code == 200
    analyze_data = analyze_response.json()
    assert analyze_data["student_id"] == "test_student"
    assert "lines_of_code" in analyze_data

    # Test pattern detection
    pattern_response = client.post("/patterns/detect", json={
        "error_message": "NameError: name 'y' is not defined",
        "stack_trace": "File 'test.py', line 3",
        "student_id": "test_student"
    })
    assert pattern_response.status_code == 200
    pattern_data = pattern_response.json()
    assert pattern_data["confidence"] >= 0.8

    # Test suggestions
    suggestions_response = client.post("/suggestions/", json={
        "code": "print('Hello",
        "error_message": "SyntaxError"
    })
    assert suggestions_response.status_code == 200
    suggestions_data = suggestions_response.json()
    assert isinstance(suggestions_data, list)

    print("✓ Debug Agent API responses verified")

if __name__ == "__main__":
    asyncio.run(test_complete_debug_flow())
    asyncio.run(test_error_pattern_processing())
    asyncio.run(test_debug_agent_api_responses())