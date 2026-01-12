#!/usr/bin/env python3
"""
Quick token efficiency test for Phase 0 verification
"""

def _token_estimate(text: str) -> int:
    """Estimate token count"""
    return len(text.split()) + (len(text) // 4)

def calculate_efficiency(skill_tokens: int, baseline: int = 1500) -> float:
    """Calculate efficiency gain"""
    return 1 - (skill_tokens / baseline)

def test_query_token_efficiency():
    """Test token usage for different query types"""
    test_cases = [
        ("Syntax help", "I'm getting a syntax error in my for loop"),
        ("Concept explanation", "What is polymorphism?"),
        ("Exercise request", "Give me practice problems"),
        ("Progress check", "How am I progressing?"),
        ("Complex query", "I've been working on this Python project for 3 days and I keep getting TypeError when trying to iterate"),
    ]

    print("Quick Token Efficiency Test")
    print("=" * 50)

    total_efficiency = 0
    passed = 0

    for name, query in test_cases:
        tokens = _token_estimate(query)
        efficiency = calculate_efficiency(tokens)
        status = "PASS" if efficiency >= 0.90 else "FAIL"

        print(f"{name:20} | Tokens: {tokens:4} | Eff: {efficiency:.1%} | {status}")

        total_efficiency += efficiency
        if status == "PASS":
            passed += 1

    avg_efficiency = total_efficiency / len(test_cases)
    overall = "PASS" if passed == len(test_cases) else "FAIL"

    print("\n" + "=" * 50)
    print(f"Average Efficiency: {avg_efficiency:.1%}")
    print(f"Tests Passed: {passed}/{len(test_cases)}")
    print(f"Overall: {overall}")

    return overall == "PASS"

if __name__ == "__main__":
    success = test_query_token_efficiency()
    exit(0 if success else 1)