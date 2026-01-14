"""
Problem Generation Endpoint
Exercise Agent
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, List
import json

router = APIRouter(tags=["generation"])

class ProblemGenerationRequest(BaseModel):
    topic: str
    difficulty: str = Query("beginner", enum=["beginner", "intermediate", "advanced"])
    context: Optional[Dict] = None
    student_level: Optional[str] = "beginner"

class ProblemResponse(BaseModel):
    topic: str
    difficulty: str
    problem: str
    hints: List[str]
    test_cases: Optional[List[Dict]]
    estimated_time: int  # in minutes
    generated_at: str

@router.post("/", response_model=ProblemResponse)
async def generate_problem(request: ProblemGenerationRequest):
    """
    Generate adaptive programming exercise for a specific topic and difficulty
    """
    try:
        # Use MCP problem generator
        from services.problem_generator import generate_problem_with_mcp

        problem_data = await generate_problem_with_mcp(
            topic=request.topic,
            difficulty=request.difficulty,
            student_progress=request.context or {}
        )

        return ProblemResponse(
            topic=request.topic,
            difficulty=request.difficulty,
            problem=problem_data["description"],
            hints=problem_data.get("hints", []),
            test_cases=problem_data.get("test_cases", []),
            estimated_time=problem_data.get("estimated_time", 15),
            generated_at="2026-01-14T10:30:00Z"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Problem generation failed: {str(e)}")

@router.post("/batch")
async def generate_problem_batch(requests: List[ProblemGenerationRequest]):
    """
    Generate multiple problems in batch
    """
    problems = []
    for req in requests:
        try:
            from services.problem_generator import generate_problem_with_mcp
            problem_data = await generate_problem_with_mcp(
                topic=req.topic,
                difficulty=req.difficulty,
                student_progress=req.context or {}
            )
            problems.append({
                "topic": req.topic,
                "difficulty": req.difficulty,
                "problem": problem_data["description"],
                "hints": problem_data.get("hints", []),
                "test_cases": problem_data.get("test_cases", []),
                "status": "success"
            })
        except Exception as e:
            problems.append({
                "topic": req.topic,
                "difficulty": req.difficulty,
                "status": "error",
                "error": str(e)
            })
    return {"problems": problems}

@router.get("/topics")
async def get_available_topics():
    """
    Get list of available programming topics for exercise generation
    """
    topics = [
        "variables",
        "loops",
        "conditionals",
        "functions",
        "arrays",
        "strings",
        "objects",
        "recursion",
        "classes",
        "algorithms"
    ]
    return {"topics": topics}

@router.post("/with-visual")
async def generate_visual_problem(request: ProblemGenerationRequest):
    """
    Generate problem with visual/diagram elements
    """
    from services.problem_generator import generate_problem_with_mcp

    problem = await generate_problem_with_mcp(
        topic=request.topic,
        difficulty=request.difficulty,
        student_progress=request.context or {}
    )

    return {
        "problem": problem,
        "visual_elements": {
            "diagram_type": "flowchart",
            "code_visual": "syntax_highlighted",
            "visualization_url": f"/visualize/{request.topic.replace(' ', '-')}"
        }
    }

async def generate_concept_explanation(concept: str, level: str, context: Dict, style: str):
    """Generate explanation using knowledge base"""
    # Placeholder for problem generation logic
    problems = {
        "loops": {
            "beginner": {
                "description": "Write a loop that prints numbers from 1 to 5",
                "hints": ["Use the range() function", "Remember loop syntax"],
                "test_cases": [{"input": "", "expected": "1\n2\n3\n4\n5\n"}],
                "estimated_time": 10
            },
            "intermediate": {
                "description": "Sum all even numbers between 1 and 100",
                "hints": ["Use modulus operator", "Accumulate sum in variable"],
                "test_cases": [{"input": "", "expected": "2550"}],
                "estimated_time": 15
            }
        },
        "functions": {
            "beginner": {
                "description": "Write a function that adds two numbers",
                "hints": ["Use def keyword", "Return the sum"],
                "test_cases": [{"input": "add(2, 3)", "expected": "5"}],
                "estimated_time": 12
            }
        }
    }

    level_key = level.lower()
    concept_key = concept.lower().replace(" ", "_")

    default_response = {
        "description": f"Write a {concept} exercise at {level} level",
        "hints": ["Start simple", "Test your solution"],
        "test_cases": [],
        "estimated_time": 15
    }

    return problems.get(concept_key, {}).get(level_key, default_response)