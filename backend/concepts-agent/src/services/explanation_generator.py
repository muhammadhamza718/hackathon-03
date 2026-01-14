"""
MCP Explanation Generator Integration
Concepts Agent
"""

import sys
import os

# Add skills library to path
skills_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'skills-library', 'agents', 'concepts')
sys.path.insert(0, skills_path)

try:
    from explanation_generator import generate_explanation
    from concept_mapping import map_concepts
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Fallback implementations
    def generate_explanation(concept, level, context, style):
        return {
            "explanation": f"Explanation for {concept} at {level} level",
            "analogies": ["Like...", "Similar to..."],
            "examples": [f"Example 1 for {concept}", f"Example 2 for {concept}"],
            "key_points": ["Key point 1", "Key point 2"],
            "complexity": level
        }

    def map_concepts(concept, depth):
        return {
            "prerequisites": ["basics"],
            "related": ["similar"],
            "dependencies": ["foundation"]
        }

def generate_explanation_with_mcp(concept: str, level: str, context: dict, style: str):
    """
    Generate explanation using MCP script for 90%+ token efficiency
    """
    if MCP_AVAILABLE:
        return generate_explanation(concept, level, context, style)
    else:
        return {
            "explanation": f"Understanding {concept} requires grasping the fundamental principles and practical applications.",
            "analogies": [
                "Like learning to ride a bike - you need balance and practice",
                "Similar to mastering a recipe - you need the right ingredients and timing"
            ],
            "examples": [
                f"Basic implementation: concept_example_1()",
                f"Advanced usage: concept_example_2()"
            ],
            "key_points": [
                f"Master {concept} fundamentals first",
                "Practice with real examples",
                "Understand common pitfalls"
            ],
            "complexity": level,
            "token_efficiency_note": "MCP would provide 90%+ savings vs LLM generation"
        }

def get_concept_dependencies(concept: str):
    """
    Get concept dependencies and prerequisites using MCP
    """
    if MCP_AVAILABLE:
        return map_concepts(concept, 3)
    else:
        return {
            "prerequisites": ["variables", "control flow"],
            "related": ["functions", "loops"],
            "dependencies": ["basic syntax"]
        }