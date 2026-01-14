"""
Error Pattern Detection Endpoint
Debug Agent
"""

from fastapi import APIRouter, Query
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/patterns", tags=["patterns"])

class PatternRequest(BaseModel):
    error_message: str
    stack_trace: str
    student_id: str

class DetectedPattern(BaseModel):
    pattern_id: str
    pattern_name: str
    confidence: float
    common_fixes: List[str]
    learning_resources: List[str]

@router.post("/detect", response_model=DetectedPattern)
async def detect_pattern(request: PatternRequest):
    """
    Detect error pattern from error message and stack trace
    """
    # Pattern detection logic (placeholder)
    error_lower = request.error_message.lower()

    if "indexerror" in error_lower or "out of range" in error_lower:
        pattern = DetectedPattern(
            pattern_id="ERR-001",
            pattern_name="Index Out of Range",
            confidence=0.95,
            common_fixes=[
                "Check array bounds before access",
                "Use len() to validate indices",
                "Handle empty collections"
            ],
            learning_resources=[
                "docs:array-indexing",
                "tutorial:common-errors"
            ]
        )
    elif "syntaxerror" in error_lower:
        pattern = DetectedPattern(
            pattern_id="ERR-002",
            pattern_name="Syntax Error",
            confidence=0.98,
            common_fixes=[
                "Check parentheses matching",
                "Verify indentation",
                "Review variable declarations"
            ],
            learning_resources=[
                "docs:syntax-basics",
                "video:python-syntax"
            ]
        )
    else:
        pattern = DetectedPattern(
            pattern_id="ERR-003",
            pattern_name="General Error",
            confidence=0.80,
            common_fixes=[
                "Read error message carefully",
                "Check stack trace",
                "Search for similar issues"
            ],
            learning_resources=[
                "docs:debugging",
                "tutorial:error-handling"
            ]
        )

    return pattern

@router.get("/common")
async def get_common_patterns(limit: int = Query(10, ge=1, le=100)):
    """
    Get most common error patterns across all students
    """
    patterns = [
        {
            "pattern_id": "ERR-001",
            "pattern_name": "Index Out of Range",
            "frequency": 142,
            "avg_resolution_time": "5m"
        },
        {
            "pattern_id": "ERR-002",
            "pattern_name": "Syntax Error",
            "frequency": 98,
            "avg_resolution_time": "3m"
        },
        {
            "pattern_id": "ERR-003",
            "pattern_name": "Type Error",
            "frequency": 76,
            "avg_resolution_time": "7m"
        }
    ]

    return {"patterns": patterns[:limit]}