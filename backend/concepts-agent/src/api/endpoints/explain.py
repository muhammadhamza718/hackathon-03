"""
Explanation Generation Endpoint
Concepts Agent
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, List
import json

router = APIRouter(tags=["explanation"])

class ExplanationRequest(BaseModel):
    concept: str
    student_level: str = "beginner"
    context: Optional[Dict] = None
    preferred_style: Optional[str] = "simple"

class ExplanationResponse(BaseModel):
    concept: str
    explanation: str
    analogies: List[str]
    examples: List[str]
    key_points: List[str]
    complexity_level: str
    generated_at: str

@router.post("/", response_model=ExplanationResponse)
async def generate_explanation(request: ExplanationRequest):
    """
    Generate detailed explanation for a concept
    """
    try:
        # This would integrate with MCP explanation generator
        explanation_data = await generate_concept_explanation(
            request.concept,
            request.student_level,
            request.context or {},
            request.preferred_style
        )

        return ExplanationResponse(
            concept=request.concept,
            explanation=explanation_data["explanation"],
            analogies=explanation_data.get("analogies", []),
            examples=explanation_data.get("examples", []),
            key_points=explanation_data.get("key_points", []),
            complexity_level=explanation_data.get("complexity", "intermediate"),
            generated_at="2026-01-14T10:30:00Z"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")

@router.post("/with-visual")
async def generate_visual_explanation(request: ExplanationRequest):
    """
    Generate explanation with visual/diagram concepts
    """
    explanation = await generate_explanation(request)

    return {
        "explanation": explanation,
        "visual_elements": {
            "diagram_type": "concept_map",
            "relationships": ["prerequisite", "dependency", "related"],
            "visualization_url": f"/diagrams/{request.concept.replace(' ', '-')}"
        }
    }

async def generate_concept_explanation(concept: str, level: str, context: Dict, style: str):
    """Generate explanation using knowledge base"""
    # Placeholder for MCP explanation generator
    explanations = {
        "variables": {
            "explanation": "Variables are like labeled containers that store data values in programming",
            "analogies": ["Like a storage box with a label", "Similar to a jar with a name"],
            "examples": ["x = 5", "name = 'Alice'", "count = 10"],
            "key_points": ["Must be unique", "Case sensitive", "Descriptive names help"]
        },
        "loops": {
            "explanation": "Loops repeat a block of code multiple times",
            "analogies": ["Like doing jumping jacks multiple times", "Similar to washing dishes one by one"],
            "examples": ["for i in range(5):", "while condition:"],
            "key_points": ["Avoid infinite loops", "Use counters", "Break when needed"]
        }
    }

    default_response = {
        "explanation": f"{concept} is a fundamental programming concept that allows...",
        "analogies": ["Like...", "Similar to..."],
        "examples": [f"{concept} example 1", f"{concept} example 2"],
        "key_points": ["Point 1", "Point 2"],
        "complexity": level
    }

    return explanations.get(concept.lower().replace(" ", "_"), default_response)