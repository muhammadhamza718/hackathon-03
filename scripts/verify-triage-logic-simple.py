#!/usr/bin/env python3
"""
Simple verification for triage-logic skill
"""

import sys
import time
from pathlib import Path

def check_structure():
    """Check file structure"""
    base_dir = Path(__file__).parent.parent
    skills_dir = base_dir / "skills-library" / "triage-logic"

    required_files = [
        "skill-manifest.yaml",
        "intent-detection.py",
        "route-selection.py",
        "training_data/patterns.json"
    ]

    print("0.1: File Structure Verification")
    print("=" * 50)

    all_ok = True
    for file in required_files:
        path = skills_dir / file
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        print(f"{status} | Required file: {file}")
        if not exists:
            all_ok = False

    return all_ok

def test_intent_detection():
    """Test intent detection"""
    print("\n0.3: Intent Detection Testing")
    print("=" * 50)

    skills_dir = Path(__file__).parent.parent / "skills-library" / "triage-logic"
    sys.path.insert(0, str(skills_dir.parent))

    try:
        from triage_logic.intent_detection import classify_intent

        test_cases = [
            ("I'm getting a syntax error in my for loop", "syntax_help"),
            ("What is polymorphism in OOP?", "concept_explanation"),
            ("Can you give me practice exercises for loops?", "exercise_request"),
            ("How am I progressing in my Python course?", "progress_check"),
        ]

        correct = 0
        total_tokens = 0
        total_latency = 0

        for query, expected in test_cases:
            start = time.time()
            result = classify_intent(query)
            latency = (time.time() - start) * 1000

            is_correct = result['intent'] == expected
            if is_correct:
                correct += 1

            total_tokens += result['token_estimate']
            total_latency += latency

            status = "PASS" if is_correct else "FAIL"
            print(f"{status} | {expected}: {result['intent']} ({result['token_estimate']} tokens, {latency:.1f}ms)")

        accuracy = correct / len(test_cases)
        avg_tokens = total_tokens / len(test_cases)
        avg_latency = total_latency / len(test_cases)
        efficiency = (1500 - avg_tokens) / 1500

        print(f"\nMetrics:")
        print(f"  Accuracy: {accuracy:.1%} (target: 95%)")
        print(f"  Avg Tokens: {avg_tokens:.0f} (vs 1500 LLM)")
        print(f"  Avg Latency: {avg_latency:.1f}ms (target: 150ms)")
        print(f"  Efficiency: {efficiency:.1%} (target: 90%)")

        return accuracy >= 0.95 and efficiency >= 0.90

    except Exception as e:
        print(f"FAIL | Intent detection test: {e}")
        return False

def test_route_selection():
    """Test route selection"""
    print("\n0.4: Route Selection Testing")
    print("=" * 50)

    skills_dir = Path(__file__).parent.parent / "skills-library" / "triage-logic"
    sys.path.insert(0, str(skills_dir.parent))

    try:
        from triage_logic.route_selection import route_intent

        test_cases = [
            ("syntax_help", 0.92, "debug-agent"),
            ("concept_explanation", 0.88, "concepts-agent"),
            ("exercise_request", 0.95, "exercise-agent"),
            ("progress_check", 0.90, "progress-agent"),
        ]

        correct = 0
        for intent, confidence, expected in test_cases:
            result = route_intent(intent, confidence)
            is_correct = result['target_agent'] == expected
            if is_correct:
                correct += 1

            status = "PASS" if is_correct else "FAIL"
            print(f"{status} | {intent} -> {result['target_agent']} (priority: {result['priority']})")

        accuracy = correct / len(test_cases)
        print(f"\nRouting Accuracy: {accuracy:.1%} (target: 100%)")

        return accuracy == 1.0

    except Exception as e:
        print(f"FAIL | Route selection test: {e}")
        return False

def benchmark_efficiency():
    """Efficiency benchmark"""
    print("\n0.6-0.7: Efficiency Benchmark")
    print("=" * 50)

    skills_dir = Path(__file__).parent.parent / "skills-library" / "triage-logic"
    sys.path.insert(0, str(skills_dir.parent))

    try:
        from triage_logic.intent_detection import classify_intent

        queries = [
            "I'm getting a syntax error in my for loop",
            "What is polymorphism in object oriented programming?",
            "Can you give me some practice exercises for recursion?",
            "How am I progressing in my Python learning journey?",
            "My code doesn't work, can you help me debug it?",
        ]

        total_tokens = 0
        total_latency = 0

        for query in queries:
            start = time.time()
            result = classify_intent(query)
            latency = (time.time() - start) * 1000

            total_tokens += result['token_estimate']
            total_latency += latency

        avg_tokens = total_tokens / len(queries)
        avg_latency = total_latency / len(queries)
        efficiency = (1500 - avg_tokens) / 1500

        print(f"Total tokens (5 queries): {total_tokens}")
        print(f"LLM baseline (5 queries): {1500 * 5}")
        print(f"Average per query: {avg_tokens:.0f} tokens")
        print(f"Average latency: {avg_latency:.1f}ms")
        print(f"Efficiency: {efficiency:.1%} (target: 90%)")

        return efficiency >= 0.90 and avg_latency < 50

    except Exception as e:
        print(f"FAIL | Efficiency benchmark: {e}")
        return False

def main():
    """Run verification"""
    print("Triage-Logic Skill Verification")
    print("=" * 50)

    results = []

    # Run checks
    results.append(("File Structure", check_structure()))
    results.append(("Intent Detection", test_intent_detection()))
    results.append(("Route Selection", test_route_selection()))
    results.append(("Efficiency Benchmark", benchmark_efficiency()))

    # Summary
    print("\n" + "=" * 50)
    print("PHASE 0 QUALITY GATE")
    print("=" * 50)

    all_passed = all(r[1] for r in results)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} | {name}")

    print(f"\nRESULT: {'PASSED' if all_passed else 'FAILED'}")

    if all_passed:
        print("\nReady for Phase 1: FastAPI Service Implementation")
        print("Token efficiency maintained at 90%+")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())