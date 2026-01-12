"""
OpenAI Router Configuration Management
Elite Implementation Standard v2.0.0

Supports feature flags, model selection, timeout config, and hybrid mode settings.
"""

from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum


class RouterMode(Enum):
    """Router operation modes"""
    PURE_SKILL = "pure_skill"  # 98.7% efficiency, no LLM
    HYBRID = "hybrid"  # LLM for complex cases, skills for simple
    FALLBACK_ONLY = "fallback_only"  # Only use skills, ignore LLM completely


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI router operations"""

    # OpenAI API Configuration
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"  # Cheapest model for glue logic

    # Operational Mode
    mode: RouterMode = RouterMode.PURE_SKILL  # Default: skills-first for 98.7% efficiency

    # Performance Limits
    max_hybrid_tokens: int = 500  # Only use LLM for very complex cases
    llm_timeout: int = 5  # Seconds
    skills_timeout: int = 1  # Seconds

    # Fallback Configuration
    enable_fallback: bool = True
    fallback_confidence_threshold: float = 0.3  # Use LLM below this confidence

    # Hybrid Mode Settings
    min_query_length_for_llm: int = 10  # Words
    complex_query_multiplier: float = 1.5  # More likely to use LLM

    # Efficiency Monitoring
    target_efficiency: float = 0.90  # 90% token efficiency minimum
    max_llm_usage_percentage: float = 0.05  # Max 5% LLM calls

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create config from environment variables with sensible defaults"""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        mode_str = os.getenv("ROUTER_MODE", "pure_skill")

        try:
            mode = RouterMode(mode_str)
        except ValueError:
            mode = RouterMode.PURE_SKILL

        return cls(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            mode=mode,
            max_hybrid_tokens=int(os.getenv("MAX_HYBRID_TOKENS", "500")),
            llm_timeout=int(os.getenv("LLM_TIMEOUT", "5")),
            skills_timeout=int(os.getenv("SKILLS_TIMEOUT", "1")),
            enable_fallback=os.getenv("ENABLE_FALLBACK", "true").lower() == "true",
            fallback_confidence_threshold=float(os.getenv("FALLBACK_THRESHOLD", "0.3")),
            min_query_length_for_llm=int(os.getenv("MIN_QUERY_LENGTH", "10")),
            target_efficiency=float(os.getenv("TARGET_EFFICIENCY", "0.90")),
            max_llm_usage_percentage=float(os.getenv("MAX_LLM_USAGE", "0.05"))
        )

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for logging"""
        return {
            "mode": self.mode.value,
            "model": self.model,
            "max_hybrid_tokens": self.max_hybrid_tokens,
            "llm_timeout": self.llm_timeout,
            "skills_timeout": self.skills_timeout,
            "enable_fallback": self.enable_fallback,
            "fallback_threshold": self.fallback_confidence_threshold,
            "target_efficiency": self.target_efficiency,
            "max_llm_usage": self.max_llm_usage_percentage
        }

    def is_hybrid_enabled(self) -> bool:
        """Check if hybrid mode is available and configured"""
        return (
            self.mode == RouterMode.HYBRID and
            self.api_key is not None and
            self.max_hybrid_tokens > 0
        )

    def should_use_llm(self, query: str, skill_confidence: float) -> bool:
        """Determine if LLM should be used based on configuration"""
        if not self.is_hybrid_enabled():
            return False

        if skill_confidence >= 0.4:  # Good skill result, no need for LLM
            return False

        if skill_confidence < self.fallback_confidence_threshold:
            # Low confidence, check query complexity
            query_words = len(query.split())
            if query_words >= self.min_query_length_for_llm:
                return True

        return False


# Default configuration instance
default_config = OpenAIConfig.from_env()


if __name__ == "__main__":
    # Test configuration
    config = OpenAIConfig.from_env()
    print("=== OpenAI Router Configuration ===")
    print(f"Mode: {config.mode.value}")
    print(f"Model: {config.model}")
    print(f"Hybrid Enabled: {config.is_hybrid_enabled()}")
    print(f"Target Efficiency: {config.target_efficiency:.1%}")
    print(f"Max LLM Usage: {config.max_llm_usage_percentage:.1%}")

    # Test decision logic
    test_cases = [
        ("simple query", 0.9),
        ("complex technical question with multiple concepts", 0.2),
        ("what is polymorphism", 0.7)
    ]

    print("\n=== Decision Test ===")
    for query, confidence in test_cases:
        should_use = config.should_use_llm(query, confidence)
        print(f"'{query}' (confidence: {confidence}) -> Use LLM: {should_use}")