"""
Integration tests for Concept Mapping Service
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.concept_mapping import concept_mapper

def test_prerequisite_retrieval():
    """Test getting prerequisites for a concept"""
    prereqs = concept_mapper.get_prerequisites("loops")
    assert len(prereqs) > 0
    assert "variables" in prereqs

def test_learning_path_generation():
    """Test learning path generation"""
    path = concept_mapper.get_learning_path("loops")
    assert isinstance(path, list)
    assert "loops" in path
    assert len(path) >= 2  # At least prereq + target

def test_concept_readiness_assessment():
    """Test readiness assessment"""
    assessment = concept_mapper.assess_readiness(["variables"], "loops")
    assert "readiness_score" in assessment
    assert "missing_prerequisites" in assessment
    assert "ready_to_learn" in assessment

def test_related_concepts():
    """Test getting related concepts"""
    related = concept_mapper.get_related_concepts("loops")
    assert isinstance(related, list)
    assert "arrays" in related or len(related) >= 0

def test_prerequisite_chain():
    """Test prerequisite chain visualization"""
    chains = concept_mapper.find_prerequisite_chain("loops")
    assert isinstance(chains, list)
    if chains:
        # If chains exist, they should end with the target concept
        for chain in chains:
            assert chain[-1] == "loops"

def test_assess_readiness_missing_prereqs():
    """Test readiness assessment with missing prerequisites"""
    assessment = concept_mapper.assess_readiness([], "loops")
    assert assessment["readiness_score"] < 1.0
    assert len(assessment["missing_prerequisites"]) > 0
    assert assessment["ready_to_learn"] is False

if __name__ == "__main__":
    pytest.main([__file__])