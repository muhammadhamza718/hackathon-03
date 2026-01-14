"""
Unit tests for Quality Scoring Service
Tests algorithmic analysis without LLM dependency
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from services.quality_scoring import (
    QualityScoringEngine,
    assess_code_quality_with_mcp,
    check_mcp_connection,
    CodeAnalysis
)


@pytest.mark.unit
class TestQualityScoringEngine:
    """Test the quality scoring engine algorithmic analysis"""

    def test_engine_initialization(self, mock_quality_engine):
        """Test engine initializes correctly"""
        assert mock_quality_engine.mcp_connected is False
        assert mock_quality_engine.QUALITY_WEIGHTS["syntax"] == 0.15
        assert mock_quality_engine.QUALITY_WEIGHTS["logic"] == 0.35

    def test_analyze_code_structure_valid_python(self, mock_quality_engine):
        """Test analysis of valid Python code"""
        code = """
def calculate_sum(a, b):
    '''Add two numbers'''
    return a + b
"""
        analysis = mock_quality_engine.analyze_code_structure(code, "python")

        assert isinstance(analysis, CodeAnalysis)
        assert analysis.syntax_score > 0.7
        assert analysis.logic_score > 0.7
        assert analysis.style_score > 0.5
        assert "functions" in analysis.concepts_covered
        assert "Good function structure" in analysis.strengths

    def test_analyze_code_structure_syntax_error(self, mock_quality_engine):
        """Test detection of syntax errors"""
        code = """
def broken_function(x
    return x  # Missing colon
"""
        analysis = mock_quality_engine.analyze_code_structure(code, "python")

        assert analysis.syntax_score < 0.7
        assert len(analysis.issues) > 0
        assert any("Missing colons" in issue for issue in analysis.issues)

    def test_analyze_code_structure_nested_loops(self, mock_quality_engine):
        """Test detection of nested loops"""
        code = """
for i in range(5):
    for j in range(3):
        print(i, j)
"""
        analysis = mock_quality_engine.analyze_code_structure(code, "python")

        assert analysis.efficiency_score < 0.8
        assert any("nested" in issue.lower() for issue in analysis.issues)

    def test_analyze_code_structure_long_lines(self, mock_quality_engine):
        """Test detection of long lines"""
        code = "x = " + "1 + " * 30 + "1"  # Create a very long line

        analysis = mock_quality_engine.analyze_code_structure(code, "python")

        assert len(analysis.issues) > 0
        assert any("lines exceed" in issue for issue in analysis.issues)

    def test_detect_concepts_python(self, mock_quality_engine):
        """Test concept detection for Python"""
        code = """
class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, x):
        return self.value + x

    def process(self, items):
        return [item * 2 for item in items]
"""
        concepts = mock_quality_engine._detect_concepts(code, "python")

        assert "classes" in concepts
        assert "functions" in concepts
        assert "loops" in concepts  # list comprehension counts as loop
        assert "comprehensions" in concepts

    def test_check_best_practices_python(self, mock_quality_engine):
        """Test best practices detection"""
        code = '''
def func(x):
    """Docstring here"""
    if x > 0:
        return x
    else:
        return 0
'''
        practices = mock_quality_engine._check_best_practices(code, "python")

        assert any("documentation" in p.lower() for p in practices)

    def test_calculate_overall_score(self, mock_quality_engine):
        """Test overall score calculation"""
        analysis = CodeAnalysis(
            syntax_score=0.9,
            logic_score=0.8,
            style_score=0.7,
            efficiency_score=0.85,
            concepts_covered=["functions", "loops"],
            best_practices=["docs"],
            issues=["minor"],
            strengths=["good"]
        )

        score = mock_quality_engine._calculate_overall_score(analysis)
        assert 0.0 <= score <= 1.0
        assert score == pytest.approx(0.80, 0.05)  # Weighted average

    def test_generate_testing_suggestions(self, mock_quality_engine):
        """Test testing suggestions generation"""
        concepts = ["functions", "loops", "exceptions"]
        suggestions = mock_quality_engine._generate_testing_suggestions(concepts)

        assert len(suggestions) > 0
        assert any("input types" in s for s in suggestions)
        assert any("branch conditions" in s for s in suggestions)

    def test_generate_optimization_suggestions(self, mock_quality_engine):
        """Test optimization suggestions"""
        issues = ["Nested loops detected", "Large function detected"]
        suggestions = mock_quality_engine._generate_optimization_suggestions(issues)

        assert len(suggestions) > 0
        assert any("flattening" in s.lower() or "breaking" in s.lower() for s in suggestions)


@pytest.mark.unit
class TestMCPConnection:
    """Test MCP connection handling"""

    @pytest.mark.asyncio
    async def test_check_mcp_connection(self, mock_quality_engine):
        """Test MCP health check"""
        with patch.object(mock_quality_engine, 'check_mcp_connection', new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await mock_quality_engine.check_mcp_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_mcp_service_function(self):
        """Test the public check_mcp_connection function"""
        with patch('services.quality_scoring.get_quality_engine') as mock_get:
            mock_engine = AsyncMock()
            mock_engine.check_mcp_connection.return_value = True
            mock_get.return_value = mock_engine

            result = await check_mcp_connection()
            assert result is True


@pytest.mark.unit
class TestAssessCodeQuality:
    """Test the main assessment function"""

    @pytest.mark.asyncio
    async def test_assess_code_quality_success(self, sample_student_code, sample_problem_context):
        """Test successful quality assessment"""
        with patch('services.quality_scoring.get_quality_engine') as mock_get:
            mock_engine = AsyncMock()
            mock_engine.analyze_code_structure.return_value = CodeAnalysis(
                syntax_score=0.9, logic_score=0.8, style_score=0.7, efficiency_score=0.85,
                concepts_covered=["functions"], best_practices=["docs"], issues=["minor"], strengths=["good"]
            )
            mock_engine._calculate_overall_score.return_value = 0.8
            mock_engine.get_llm_enhancement.return_value = {
                "concept_score": 0.8, "structure_score": 0.75, "efficiency_score": 0.85,
                "category_scores": {"correctness": 0.9, "readability": 0.7},
                "testing_suggestions": ["Test edge cases"],
                "optimization_suggestions": ["None needed"]
            }
            mock_get.return_value = mock_engine

            result = await assess_code_quality_with_mcp(
                student_code=sample_student_code,
                context=sample_problem_context,
                student_id="test_student"
            )

            assert result["score"] == 0.8
            assert "factors" in result
            assert "strengths" in result
            assert "improvements" in result

    @pytest.mark.asyncio
    async def test_assess_code_quality_empty_code(self):
        """Test assessment with empty code"""
        with pytest.raises(Exception):
            await assess_code_quality_with_mcp(
                student_code="",
                context={},
                student_id="test_student"
            )

    @pytest.mark.asyncio
    async def test_assess_code_quality_with_custom_rubric(self, sample_student_code):
        """Test assessment with custom rubric"""
        custom_rubric = {"weight_adjustments": {"style": 0.2}}

        with patch('services.quality_scoring.get_quality_engine') as mock_get:
            mock_engine = AsyncMock()
            mock_engine.analyze_code_structure.return_value = CodeAnalysis(
                syntax_score=0.8, logic_score=0.7, style_score=0.6, efficiency_score=0.8,
                concepts_covered=["functions"], best_practices=[], issues=[], strengths=[]
            )
            mock_engine._calculate_overall_score.return_value = 0.75
            mock_engine.get_llm_enhancement.return_value = {}
            mock_get.return_value = mock_engine

            result = await assess_code_quality_with_mcp(
                student_code=sample_student_code,
                context={},
                student_id="test_student",
                custom_rubric=custom_rubric
            )

            assert 0.0 <= result["score"] <= 1.0


@pytest.mark.unit
class TestCodeAnalysis:
    """Test the CodeAnalysis dataclass"""

    def test_code_analysis_creation(self):
        """Test CodeAnalysis can be created"""
        analysis = CodeAnalysis(
            syntax_score=0.9,
            logic_score=0.8,
            style_score=0.7,
            efficiency_score=0.85,
            concepts_covered=["functions", "loops"],
            best_practices=["documentation"],
            issues=["missing_error_handling"],
            strengths=["good_naming"]
        )

        assert analysis.syntax_score == 0.9
        assert analysis.concepts_covered == ["functions", "loops"]
        assert "documentation" in analysis.best_practices


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_analyze_code_structure_javascript(self, mock_quality_engine):
        """Test JavaScript code analysis"""
        code = "function add(a, b) { return a + b; }"
        analysis = mock_quality_engine.analyze_code_structure(code, "javascript")

        assert analysis is not None
        assert "functions" in analysis.concepts_covered

    def test_analyze_code_structure_java(self, mock_quality_engine):
        """Test Java code analysis"""
        code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""
        analysis = mock_quality_engine.analyze_code_structure(code, "java")

        assert analysis is not None
        assert "classes" in analysis.concepts_covered

    def test_analyze_code_structure_empty(self, mock_quality_engine):
        """Test empty code analysis"""
        analysis = mock_quality_engine.analyze_code_structure("", "python")

        assert analysis.syntax_score == 1.0  # No issues in empty code
        assert len(analysis.concepts_covered) == 0

    def test_apply_custom_rubric_edge_cases(self):
        """Test custom rubric application"""
        from services.quality_scoring import apply_custom_rubric

        # No rubric
        result = apply_custom_rubric(0.75, {})
        assert result == 0.75

        # With adjustments
        result = apply_custom_rubric(0.75, {"weight_adjustments": {"style": 0.5}})
        assert 0.0 <= result <= 1.0


@pytest.mark.unit
class TestPerformance:
    """Performance-related tests"""

    @pytest.mark.asyncio
    async def test_assessment_performance(self, sample_student_code):
        """Test that assessment is reasonably fast"""
        import time

        start_time = time.time()

        with patch('services.quality_scoring.get_quality_engine') as mock_get:
            mock_engine = AsyncMock()
            mock_engine.analyze_code_structure.return_value = CodeAnalysis(
                syntax_score=0.8, logic_score=0.7, style_score=0.6, efficiency_score=0.8,
                concepts_covered=["functions"], best_practices=[], issues=[], strengths=[]
            )
            mock_engine._calculate_overall_score.return_value = 0.7
            mock_engine.get_llm_enhancement.return_value = {"concept_score": 0.7, "structure_score": 0.65, "efficiency_score": 0.8, "category_scores": {}, "testing_suggestions": [], "optimization_suggestions": []}
            mock_get.return_value = mock_engine

            await assess_code_quality_with_mcp(
                student_code=sample_student_code,
                context={},
                student_id="test_student"
            )

        duration = time.time() - start_time
        assert duration < 2.0  # Should complete within 2 seconds