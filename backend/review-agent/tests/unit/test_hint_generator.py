"""
Unit tests for Hint Generation Service
Tests algorithmic analysis without LLM dependency
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from services.hint_generator import (
    HintGenerator,
    generate_hint_with_mcp,
    check_mcp_connection,
    HintContext
)


@pytest.mark.unit
class TestHintGenerator:
    """Test the hint generator algorithmic logic"""

    def test_hint_generator_initialization(self, mock_hint_generator):
        """Test generator initializes correctly"""
        assert mock_hint_generator.mcp_connected is False

    def test_analyze_error_patterns_off_by_one(self, mock_hint_generator):
        """Test detection of off-by-one errors"""
        code = "for i in range(len(nums) + 1):"
        analysis = mock_hint_generator.analyze_error_patterns(code, "off_by_one", "python")

        assert "off_by_one" in analysis["detected_patterns"]
        assert len(analysis["likely_causes"]) > 0
        assert analysis["difficulty"] == "easy"

    def test_analyze_error_patterns_syntax(self, mock_hint_generator):
        """Test syntax error pattern detection"""
        code = "def func(x"
        analysis = mock_hint_generator.analyze_error_patterns(code, "syntax", "python")

        assert len(analysis["likely_causes"]) > 0
        assert analysis["difficulty"] == "easy"

    def test_analyze_error_patterns_logic(self, mock_hint_generator):
        """Test logic error pattern detection"""
        code = "if x > y: return y"
        analysis = mock_hint_generator.analyze_error_patterns(code, "logic", "python")

        assert len(analysis["likely_causes"]) > 0
        assert analysis["difficulty"] == "medium"

    def test_analyze_error_patterns_runtime(self, mock_hint_generator):
        """Test runtime error patterns"""
        code = "print(NoneType.value)"
        analysis = mock_hint_generator.analyze_error_patterns(code, "runtime", "python")

        assert any("null" in cause.lower() or "none" in cause.lower() for cause in analysis["likely_causes"])

    def test_determine_hint_level_adaptive(self, mock_hint_generator):
        """Test adaptive hint level determination"""
        # Should increase level with more previous hints
        level1 = mock_hint_generator.determine_hint_level("subtle", 0, 0.5, "medium")
        level2 = mock_hint_generator.determine_hint_level("subtle", 1, 0.5, "medium")
        level3 = mock_hint_generator.determine_hint_level("subtle", 2, 0.5, "medium")

        assert level1 == "subtle"
        assert level2 == "medium"
        assert level3 == "direct"

    def test_determine_hint_level_mastery(self, mock_hint_generator):
        """Test hint level based on mastery"""
        # Low mastery should result in more direct hints
        level = mock_hint_generator.determine_hint_level("subtle", 0, 0.2, "medium")
        assert level == "direct"

        # High mastery can use subtle hints
        level = mock_hint_generator.determine_hint_level("subtle", 0, 0.8, "medium")
        assert level == "subtle"

    def test_construct_hint_text_off_by_one(self, mock_hint_generator):
        """Test hint text construction for off-by-one errors"""
        analysis = {"detected_patterns": ["off_by_one"], "suggested_approach": ["Check boundaries"]}
        text = mock_hint_generator.construct_hint_text(analysis, "medium", "python")

        assert len(text) > 10
        assert "boundar" in text.lower() or "range" in text.lower()

    def test_construct_hint_text_syntax(self, mock_hint_generator):
        """Test hint text for syntax errors"""
        analysis = {"detected_patterns": ["indentation"], "suggested_approach": ["Check indentation"]}
        text = mock_hint_generator.construct_hint_text(analysis, "direct", "python")

        assert "indent" in text.lower()

    def test_construct_hint_text_level_difference(self, mock_hint_generator):
        """Test that different levels produce different hint lengths"""
        analysis = {"detected_patterns": [], "suggested_approach": ["Test with examples"]}

        subtle = mock_hint_generator.construct_hint_text(analysis, "subtle", "python")
        medium = mock_hint_generator.construct_hint_text(analysis, "medium", "python")
        direct = mock_hint_generator.construct_hint_text(analysis, "direct", "python")

        # Length should generally increase with directness
        assert len(direct) >= len(medium) >= len(subtle)

    def test_estimate_time(self, mock_hint_generator):
        """Test time estimation"""
        easy_subtle = mock_hint_generator.estimate_time("subtle", "easy")
        hard_direct = mock_hint_generator.estimate_time("direct", "hard")

        assert easy_subtle < hard_direct
        assert easy_subtle > 0
        assert hard_direct > 0

    def test_get_next_steps(self, mock_hint_generator):
        """Test next steps generation"""
        analysis = {"detected_patterns": ["off_by_one"], "suggested_approach": ["Check boundaries"]}

        steps_subtle = mock_hint_generator.get_next_steps(analysis, "subtle")
        steps_direct = mock_hint_generator.get_next_steps(analysis, "direct")

        assert len(steps_subtle) <= 1
        assert len(steps_direct) <= 3
        assert len(steps_direct) >= len(steps_subtle)

    def test_calculate_mastery(self, mock_hint_generator):
        """Test mastery calculation"""
        # High hint count = low mastery
        mastery_high_hints = mock_hint_generator.calculate_mastery(3, None)
        mastery_low_hints = mock_hint_generator.calculate_mastery(0, None)

        assert mastery_high_hints < mastery_low_hints

        # With history
        history = {"avg_assessment_score": 0.9}
        mastery_with_history = mock_hint_generator.calculate_mastery(0, history)
        assert mastery_with_history == 0.9


@pytest.mark.unit
class TestMCPIntegration:
    """Test MCP integration for hints"""

    @pytest.mark.asyncio
    async def test_get_llm_enhancement(self, mock_hint_generator):
        """Test LLM enhancement function"""
        code = "def func(x):\n    return x"
        context = {"topic": "functions"}
        hint_context = HintContext(
            error_type="syntax",
            difficulty_level="medium",
            previous_hints=0,
            language="python",
            student_mastery=0.5
        )

        enhancement = await mock_hint_generator.get_llm_enhancement(code, context, hint_context)

        assert "text" in enhancement
        assert "level" in enhancement
        assert "estimated_time" in enhancement

    @pytest.mark.asyncio
    async def test_check_mcp_connection(self, mock_hint_generator):
        """Test MCP health check"""
        result = await mock_hint_generator.check_mcp_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_hint_generator_mock_mode(self):
        """Test that generator works in mock mode without real MCP"""
        with patch('services.hint_generator.get_hint_generator') as mock_get:
            mock_generator = AsyncMock()
            mock_generator.check_mcp_connection.return_value = True
            mock_get.return_value = mock_generator

            result = await check_mcp_connection()
            assert result is True


@pytest.mark.unit
class TestGenerateHintWithMCP:
    """Test the main hint generation function"""

    @pytest.mark.asyncio
    async def test_generate_hint_success(self, sample_hint_request):
        """Test successful hint generation"""
        with patch('services.hint_generator.get_hint_generator') as mock_get:
            mock_generator = AsyncMock()
            mock_generator.analyze_error_patterns.return_value = {
                "detected_patterns": ["off_by_one"],
                "likely_causes": ["boundary error"],
                "difficulty": "easy",
                "suggested_approach": ["Check range"]
            }
            mock_generator.determine_hint_level.return_value = "medium"
            mock_generator.construct_hint_text.return_value = "Check your loop boundaries"
            mock_generator.estimate_time.return_value = 10
            mock_generator.get_next_steps.return_value = ["Test with small inputs"]
            mock_generator.get_llm_enhancement.return_value = {
                "text": "Enhanced hint",
                "level": "medium",
                "estimated_time": 10,
                "category": "off_by_one",
                "next_steps": ["Test"]
            }
            mock_generator.calculate_mastery.return_value = 0.6
            mock_get.return_value = mock_generator

            result = await generate_hint_with_mcp(**sample_hint_request)

            assert "text" in result
            assert "level" in result
            assert "estimated_time" in result
            assert result["level"] == "medium"

    @pytest.mark.asyncio
    async def test_generate_hint_different_levels(self):
        """Test hint generation with different levels"""
        request = {
            "student_code": "x = 5",
            "problem_context": {},
            "error_type": "syntax",
            "student_id": "test",
            "language": "python",
            "hint_level": "direct",
            "previous_hints": 0
        }

        with patch('services.hint_generator.get_hint_generator') as mock_get:
            mock_generator = AsyncMock()
            mock_generator.analyze_error_patterns.return_value = {
                "detected_patterns": [], "likely_causes": [], "difficulty": "easy", "suggested_approach": []
            }
            mock_generator.determine_hint_level.return_value = "direct"
            mock_generator.construct_hint_text.return_value = "Direct hint text"
            mock_generator.estimate_time.return_value = 5
            mock_generator.get_next_steps.return_value = ["Step 1"]
            mock_generator.get_llm_enhancement.return_value = {"text": "Enhanced", "level": "direct", "estimated_time": 5, "category": "syntax", "next_steps": ["Step 1"]}
            mock_generator.calculate_mastery.return_value = 0.7
            mock_get.return_value = mock_generator

            result = await generate_hint_with_mcp(**request)
            assert result["level"] == "direct"

    @pytest.mark.asyncio
    async def test_generate_hint_with_previous_attempts(self):
        """Test hint generation with multiple previous attempts"""
        request = {
            "student_code": "def func(): pass",
            "problem_context": {},
            "error_type": "logic",
            "student_id": "test",
            "language": "python",
            "hint_level": "subtle",
            "previous_hints": 2  # Should bump to direct
        }

        with patch('services.hint_generator.get_hint_generator') as mock_get:
            mock_generator = AsyncMock()
            mock_generator.analyze_error_patterns.return_value = {
                "detected_patterns": [], "likely_causes": [], "difficulty": "medium", "suggested_approach": []
            }
            mock_generator.determine_hint_level.return_value = "direct"  # Adaptive
            mock_generator.construct_hint_text.return_value = "Direct hint"
            mock_generator.estimate_time.return_value = 10
            mock_generator.get_next_steps.return_value = ["Step 1"]
            mock_generator.get_llm_enhancement.return_value = {
                "text": "Direct hint", "level": "direct", "estimated_time": 10, "category": "logic", "next_steps": ["Step 1"]
            }
            mock_generator.calculate_mastery.return_value = 0.4
            mock_get.return_value = mock_generator

            result = await generate_hint_with_mcp(**request)
            assert result["level"] == "direct"


@pytest.mark.unit
class TestHintContext:
    """Test the HintContext dataclass"""

    def test_hint_context_creation(self):
        """Test HintContext can be created"""
        context = HintContext(
            error_type="syntax",
            difficulty_level="medium",
            previous_hints=1,
            language="python",
            student_mastery=0.6
        )

        assert context.error_type == "syntax"
        assert context.difficulty_level == "medium"
        assert context.previous_hints == 1
        assert context.student_mastery == 0.6

    def test_hint_context_defaults(self):
        """Test HintContext with default values"""
        context = HintContext(
            error_type="logic",
            difficulty_level="subtle",
            previous_hints=0,
            language="python"
        )

        assert context.student_mastery == 0.5  # Default


@pytest.mark.unit
class TestHintTemplates:
    """Test hint template selection and formatting"""

    def test_hint_templates_exist(self, mock_hint_generator):
        """Verify hint templates are available"""
        assert "python" in mock_hint_generator.HINT_TEMPLATES
        assert "syntax" in mock_hint_generator.HINT_TEMPLATES["python"]

    def test_hint_template_selection(self, mock_hint_generator):
        """Test appropriate template selection"""
        # Template for off-by-one
        analysis = {"detected_patterns": ["off_by_one"], "suggested_approach": []}
        text = mock_hint_generator.construct_hint_text(analysis, "medium", "python")

        # Should contain relevant keywords
        assert any(word in text.lower() for word in ["boundar", "rang", "loop"])

    def test_python_specific_patterns(self, mock_hint_generator):
        """Test Python-specific hint patterns"""
        python_patterns = mock_hint_generator.ISSUE_PATTERNS

        assert "off_by_one" in python_patterns
        assert "indentation" in python_patterns
        assert "import" in python_patterns


@pytest.mark.unit
class TestErrorHandling:
    """Test error conditions in hint generation"""

    def test_analyze_error_patterns_unknown_error_type(self, mock_hint_generator):
        """Test analysis with unknown error type"""
        analysis = mock_hint_generator.analyze_error_patterns("code", "unknown_type", "python")

        # Should still return valid structure
        assert "detected_patterns" in analysis
        assert "likely_causes" in analysis

    def test_construct_hint_text_empty_analysis(self, mock_hint_generator):
        """Test hint construction with minimal analysis"""
        analysis = {"detected_patterns": [], "suggested_approach": []}
        text = mock_hint_generator.construct_hint_text(analysis, "subtle", "python")

        assert len(text) > 0  # Should still produce hint


@pytest.mark.unit
class TestHintEfficiency:
    """Test hint generation efficiency"""

    @pytest.mark.asyncio
    async def test_hint_generation_speed(self, sample_hint_request):
        """Test that hint generation is fast"""
        import time

        start_time = time.time()

        with patch('services.hint_generator.get_hint_generator') as mock_get:
            mock_generator = AsyncMock()
            mock_generator.analyze_error_patterns.return_value = {
                "detected_patterns": [], "likely_causes": [], "difficulty": "easy", "suggested_approach": []
            }
            mock_generator.determine_hint_level.return_value = "medium"
            mock_generator.construct_hint_text.return_value = "Quick hint"
            mock_generator.estimate_time.return_value = 5
            mock_generator.get_next_steps.return_value = ["Test"]
            mock_generator.get_llm_enhancement.return_value = {
                "text": "Hint", "level": "medium", "estimated_time": 5, "category": "general", "next_steps": ["Test"]
            }
            mock_generator.calculate_mastery.return_value = 0.5
            mock_get.return_value = mock_generator

            await generate_hint_with_mcp(**sample_hint_request)

        duration = time.time() - start_time
        assert duration < 2.0  # Should be fast