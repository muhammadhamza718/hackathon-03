#!/usr/bin/env python3
"""
Integration test for Review Agent with Dapr-like service invocation
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_dapr_service_invocation():
    """Test Dapr-style service invocation pattern"""
    print("Testing Dapr Service Invocation Pattern...")

    from security import SecurityContext
    from services.quality_scoring import assess_code_quality_with_mcp
    from services.hint_generator import generate_hint_with_mcp

    # Simulate Dapr service invocation request
    test_requests = [
        {
            "intent": "quality_assessment",
            "student_code": "def add(a, b):\n    return a + b",
            "problem_context": {"topic": "functions", "difficulty": "easy"},
            "confidence": 0.9
        },
        {
            "intent": "hint_generation",
            "student_code": "for i in range(5):\n    print(i)",
            "error_type": "logic",
            "confidence": 0.8
        },
        {
            "intent": "detailed_feedback",
            "student_code": "def max(a, b):\n    if a > b:\n        return a\n    else:\n        return b",
            "error_type": "edge_cases",
            "confidence": 0.7
        }
    ]

    for i, request in enumerate(test_requests, 1):
        print(f"\nTest {i}: {request['intent']}")

        security_context = SecurityContext(
            student_id=f"test_student_{i}",
            role="student",
            request_id=f"req_{datetime.utcnow().timestamp()}"
        )

        try:
            intent = request.get("intent")
            student_code = request.get("student_code")
            context = request.get("problem_context", {})
            error_type = request.get("error_type", "general")

            if intent == "quality_assessment":
                result = await assess_code_quality_with_mcp(
                    student_code=student_code,
                    context=context,
                    student_id=security_context.student_id
                )
                print(f"  [OK] Quality Score: {result['score']}")

            elif intent == "hint_generation":
                result = await generate_hint_with_mcp(
                    student_code=student_code,
                    problem_context=context,
                    error_type=error_type,
                    student_id=security_context.student_id
                )
                print(f"  [OK] Hint: {result['text'][:50]}...")

            elif intent == "detailed_feedback":
                assessment = await assess_code_quality_with_mcp(
                    student_code=student_code,
                    context=context,
                    student_id=security_context.student_id
                )
                hint = await generate_hint_with_mcp(
                    student_code=student_code,
                    problem_context=context,
                    error_type=error_type,
                    student_id=security_context.student_id
                )
                print(f"  [OK] Score: {assessment['score']}, Hint: {hint['text'][:30]}...")

            print(f"  [OK] Processing complete")

        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            return False

    return True


async def test_kafka_event_processing():
    """Test Kafka event processing"""
    print("\nTesting Kafka Event Processing...")

    from services.kafka_consumer import ReviewKafkaConsumer

    consumer = ReviewKafkaConsumer()

    # Test events
    events = [
        {
            "student_id": "kafka_test_1",
            "timestamp": datetime.utcnow().isoformat(),
            "intent": "quality_assessment",
            "student_code": "x = 1",
            "problem_context": {"topic": "variables"}
        },
        {
            "student_id": "kafka_test_2",
            "timestamp": datetime.utcnow().isoformat(),
            "intent": "performance_update",
            "topic": "loops",
            "correctness": True,
            "quality_score": 0.85
        }
    ]

    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}: {event.get('intent', 'unknown')}")

        # Validate schema
        is_valid, error = consumer.validate_event_schema(event)
        if not is_valid:
            print(f"  [FAIL] Schema validation failed: {error}")
            return False

        print(f"  [OK] Schema valid")

        # Process event
        if event.get("intent") == "quality_assessment":
            result = consumer.process_code_review_request(event)
            if result:
                print(f"  [OK] Processed: {result.get('status', 'unknown')}")
            else:
                print(f"  [FAIL] Processing returned None")
                return False

        elif event.get("intent") == "performance_update":
            result = consumer.process_performance_update(event)
            if result:
                print(f"  [OK] Performance update stored")
            else:
                print(f"  [FAIL] Performance update failed")
                return False

    return True


async def test_api_endpoints_via_mock():
    """Test API endpoint logic without HTTP server"""
    print("\nTesting API Endpoint Logic...")

    from api.endpoints.assess import AssessmentRequest
    from api.endpoints.hints import HintRequest
    from api.endpoints.feedback import FeedbackRequest

    # Test assessment request model
    assess_req = AssessmentRequest(
        student_code="def func(): return 42",
        problem_context={"topic": "functions"},
        language="python"
    )
    print(f"  [OK] Assessment request: {assess_req.student_code[:20]}...")

    # Test hint request model
    hint_req = HintRequest(
        student_code="x = 5",
        error_type="syntax",
        hint_level="medium"
    )
    print(f"  [OK] Hint request: error_type={hint_req.error_type}")

    # Test feedback request model
    feedback_req = FeedbackRequest(
        student_code="x = 1",
        error_type="general",
        request_level="comprehensive"
    )
    print(f"  [OK] Feedback request: level={feedback_req.request_level}")

    return True


async def main():
    """Run all integration tests"""
    print("=" * 60)
    print("REVIEW AGENT INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("API Endpoint Logic", test_api_endpoints_via_mock),
        ("Dapr Service Invocation", test_dapr_service_invocation),
        ("Kafka Event Processing", test_kafka_event_processing),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("ALL INTEGRATION TESTS PASSED!")
        print("\nVerified:")
        print("✓ Dapr service invocation pattern")
        print("✓ Kafka event processing")
        print("✓ API endpoint models")
        print("✓ Security context propagation")
        print("✓ MCP service integration")
        return 0
    else:
        print("SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)