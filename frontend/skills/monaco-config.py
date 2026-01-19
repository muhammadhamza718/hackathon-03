#!/usr/bin/env python3
"""
Monaco Editor Configuration Skill
Generates optimized Monaco Editor configurations based on user preferences and context
Task: T120

Last Updated: 2026-01-15
"""

import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EditorTheme(Enum):
    """Editor theme options"""
    VS_DARK = "vs-dark"
    VS_LIGHT = "vs"
    HC_BLACK = "hc-black"


class Language(Enum):
    """Supported languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    MARKDOWN = "markdown"


class EditorLayout(Enum):
    """Editor layout options"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    EXPANDED = "expanded"


@dataclass
class EditorConfig:
    """Monaco Editor configuration dataclass"""
    language: str
    theme: str
    fontSize: int
    wordWrap: str
    minimap: bool
    lineNumbers: str
    folding: bool
    formatOnPaste: bool
    formatOnType: bool
    scrollBeyondLastLine: bool
    automaticLayout: bool
    tabSize: int
    insertSpaces: bool
    detectIndentation: bool
    renderWhitespace: str
    cursorBlinking: str
    cursorSmoothCaretAnimation: str
    smoothScrolling: bool
    contextmenu: bool
    quickSuggestions: bool
    suggestOnTriggerCharacters: bool
    acceptSuggestionOnEnter: str
    parameterHints: bool
    foldingHighlight: bool
    foldingStrategy: str
    showFoldingControls: str
    unfoldOnClickAfterEndOfLine: bool
    glyphMargin: bool
    linkedEditing: bool
    renderValidationDecorations: str
    scrollbar: Dict[str, Any]


class MonacoConfigSkill:
    """Monaco Editor Configuration Generation Skill"""

    def __init__(self):
        self.logger = logger
        self.default_configs = self._initialize_default_configs()

    def _initialize_default_configs(self) -> Dict[str, Any]:
        """Initialize default configurations for different use cases"""
        return {
            "python_basic": EditorConfig(
                language="python",
                theme="vs-dark",
                fontSize=14,
                wordWrap="off",
                minimap=True,
                lineNumbers="on",
                folding=True,
                formatOnPaste=False,
                formatOnType=True,
                scrollBeyondLastLine=False,
                automaticLayout=True,
                tabSize=4,
                insertSpaces=True,
                detectIndentation=False,
                renderWhitespace="none",
                cursorBlinking="block",
                cursorSmoothCaretAnimation="off",
                smoothScrolling=True,
                contextmenu=True,
                quickSuggestions=True,
                suggestOnTriggerCharacters=True,
                acceptSuggestionOnEnter="on",
                parameterHints=True,
                foldingHighlight=True,
                foldingStrategy="indentation",
                showFoldingControls="mouseover",
                unfoldOnClickAfterEndOfLine=False,
                glyphMargin=True,
                linkedEditing=False,
                renderValidationDecorations="on",
                scrollbar={
                    "vertical": "auto",
                    "horizontal": "auto",
                    "handleMouseWheel": True,
                    "alwaysConsumeMouseWheel": False,
                },
            ),
            "python_lightweight": EditorConfig(
                language="python",
                theme="vs-light",
                fontSize=13,
                wordWrap="on",
                minimap=False,
                lineNumbers="on",
                folding=False,
                formatOnPaste=False,
                formatOnType=False,
                scrollBeyondLastLine=False,
                automaticLayout=True,
                tabSize=4,
                insertSpaces=True,
                detectIndentation=True,
                renderWhitespace="none",
                cursorBlinking="blink",
                cursorSmoothCaretAnimation="off",
                smoothScrolling=False,
                contextmenu=True,
                quickSuggestions=False,
                suggestOnTriggerCharacters=False,
                acceptSuggestionOnEnter="on",
                parameterHints=False,
                foldingHighlight=False,
                foldingStrategy="indentation",
                showFoldingControls="never",
                unfoldOnClickAfterEndOfLine=False,
                glyphMargin=False,
                linkedEditing=False,
                renderValidationDecorations="on",
                scrollbar={
                    "vertical": "hidden",
                    "horizontal": "hidden",
                    "handleMouseWheel": True,
                    "alwaysConsumeMouseWheel": False,
                },
            ),
            "javascript_full": EditorConfig(
                language="javascript",
                theme="vs-dark",
                fontSize=14,
                wordWrap="off",
                minimap=True,
                lineNumbers="on",
                folding=True,
                formatOnPaste=True,
                formatOnType=True,
                scrollBeyondLastLine=True,
                automaticLayout=True,
                tabSize=2,
                insertSpaces=True,
                detectIndentation=True,
                renderWhitespace="boundary",
                cursorBlinking="smooth",
                cursorSmoothCaretAnimation="on",
                smoothScrolling=True,
                contextmenu=True,
                quickSuggestions=True,
                suggestOnTriggerCharacters=True,
                acceptSuggestionOnEnter="on",
                parameterHints=True,
                foldingHighlight=True,
                foldingStrategy="auto",
                showFoldingControls="mouseover",
                unfoldOnClickAfterEndOfLine=False,
                glyphMargin=True,
                linkedEditing=False,
                renderValidationDecorations="on",
                scrollbar={
                    "vertical": "auto",
                    "horizontal": "auto",
                    "handleMouseWheel": True,
                    "alwaysConsumeMouseWheel": False,
                },
            ),
        }

    def generate_config(
        self,
        language: str,
        theme: Optional[str] = None,
        layout: Optional[str] = None,
        use_case: Optional[str] = None,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate Monaco Editor configuration

        Args:
            language: Programming language
            theme: Editor theme
            layout: Editor layout type
            use_case: Predefined use case (python_basic, python_lightweight, javascript_full)
            custom_settings: Additional custom settings

        Returns:
            Complete editor configuration
        """
        try:
            # Validate language
            try:
                Language(language)
            except ValueError:
                raise ValueError(f"Unsupported language: {language}. Supported: {[l.value for l in Language]}")

            # Get base configuration
            if use_case and use_case in self.default_configs:
                config = self.default_configs[use_case]
                # Override language if different
                if config.language != language:
                    config.language = language
            else:
                # Generate configuration based on language and use case
                config = self._create_language_specific_config(language, use_case)

            # Apply theme override
            if theme:
                try:
                    EditorTheme(theme)
                    config.theme = theme
                except ValueError:
                    self.logger.warning(f"Unknown theme: {theme}, using default")

            # Apply layout settings
            if layout:
                config = self._apply_layout_settings(config, layout)

            # Apply custom settings
            if custom_settings:
                config = self._apply_custom_settings(config, custom_settings)

            # Convert to dictionary
            config_dict = asdict(config)

            # Add metadata
            config_dict["_metadata"] = {
                "language": language,
                "theme": config.theme,
                "layout": layout or "standard",
                "use_case": use_case or "custom",
                "generated_at": self._get_timestamp(),
                "version": "1.0.0",
            }

            self.logger.info(f"Generated Monaco config for {language} with theme {config.theme}")
            return config_dict

        except Exception as e:
            self.logger.error(f"Error generating config: {e}")
            raise

    def _create_language_specific_config(self, language: str, use_case: Optional[str]) -> EditorConfig:
        """Create language-specific configuration"""
        base_config = self.default_configs["python_basic"]  # Start with Python base

        # Language-specific adjustments
        if language == "javascript" or language == "typescript":
            base_config.language = language
            base_config.tabSize = 2
            base_config.wordWrap = "off"
            base_config.minimap = True
            base_config.formatOnType = True
        elif language == "markdown":
            base_config.language = language
            base_config.wordWrap = "on"
            base_config.minimap = False
            base_config.formatOnType = False
            base_config.folding = False

        # Use case adjustments
        if use_case == "lightweight":
            base_config.minimap = False
            base_config.folding = False
            base_config.quickSuggestions = False
            base_config.scrollbar["vertical"] = "hidden"
            base_config.scrollbar["horizontal"] = "hidden"
        elif use_case == "productive":
            base_config.minimap = True
            base_config.folding = True
            base_config.quickSuggestions = True
            base_config.formatOnType = True

        return base_config

    def _apply_layout_settings(self, config: EditorConfig, layout: str) -> EditorConfig:
        """Apply layout-specific settings"""
        try:
            layout_enum = EditorLayout(layout)

            if layout_enum == EditorLayout.MINIMAL:
                config.minimap = False
                config.lineNumbers = "off"
                config.folding = False
                config.scrollbar["vertical"] = "hidden"
                config.contextmenu = False
                config.glyphMargin = False

            elif layout_enum == EditorLayout.EXPANDED:
                config.minimap = True
                config.lineNumbers = "on"
                config.folding = True
                config.wordWrap = "on"
                config.scrollBeyondLastLine = True

            # STANDARD keeps default settings

        except ValueError:
            self.logger.warning(f"Unknown layout: {layout}, using standard")

        return config

    def _apply_custom_settings(self, config: EditorConfig, custom_settings: Dict[str, Any]) -> EditorConfig:
        """Apply custom user settings"""
        try:
            for key, value in custom_settings.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    self.logger.warning(f"Unknown setting: {key}, ignoring")
        except Exception as e:
            self.logger.error(f"Error applying custom settings: {e}")

        return config

    def get_recommended_config(
        self,
        student_level: str,
        language: str,
        task_complexity: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get recommended configuration based on student context

        Args:
            student_level: Student proficiency level
            language: Programming language
            task_complexity: Task complexity level
            preferences: Student preferences

        Returns:
            Recommended configuration
        """
        # Determine use case based on student level and complexity
        if student_level in ["beginner", "novice"]:
            use_case = "python_lightweight"
        elif task_complexity in ["high", "complex"]:
            use_case = "javascript_full" if language in ["javascript", "typescript"] else "python_basic"
        else:
            use_case = "python_basic"

        # Get theme based on preferences
        theme = None
        if preferences:
            theme = preferences.get("theme", "vs-dark")

        config = self.generate_config(
            language=language,
            theme=theme,
            layout="standard",
            use_case=use_case,
            custom_settings=preferences,
        )

        # Add recommendations
        config["_recommendations"] = {
            "theme": f"Using {'dark' if theme == 'vs-dark' else 'light'} theme based on preferences",
            "minimap": f"Minimap {'enabled' if config['minimap'] else 'disabled'} for better performance",
            "word_wrap": f"Word wrap {'enabled' if config['wordWrap'] == 'on' else 'disabled'}",
            "suggestions": f"Code suggestions {'enabled' if config['quickSuggestions'] else 'disabled'}",
        }

        return config

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main function for testing the skill"""
    skill = MonacoConfigSkill()

    # Test cases
    test_cases = [
        {
            "name": "Python Basic",
            "language": "python",
            "theme": "vs-dark",
            "use_case": "python_basic",
        },
        {
            "name": "Python Lightweight",
            "language": "python",
            "theme": "vs-light",
            "use_case": "python_lightweight",
        },
        {
            "name": "JavaScript Full",
            "language": "javascript",
            "theme": "vs-dark",
            "use_case": "javascript_full",
        },
        {
            "name": "Beginner Student",
            "student_level": "beginner",
            "language": "python",
            "task_complexity": "low",
            "preferences": {"theme": "vs-light"},
        },
    ]

    print("=== Monaco Config Skill Test ===\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 40)

        try:
            if "student_level" in test_case:
                config = skill.get_recommended_config(
                    student_level=test_case["student_level"],
                    language=test_case["language"],
                    task_complexity=test_case["task_complexity"],
                    preferences=test_case.get("preferences"),
                )
            else:
                config = skill.generate_config(
                    language=test_case["language"],
                    theme=test_case.get("theme"),
                    use_case=test_case.get("use_case"),
                )

            print(json.dumps(config, indent=2, default=str))
            print("\n" + "=" * 40 + "\n")

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()