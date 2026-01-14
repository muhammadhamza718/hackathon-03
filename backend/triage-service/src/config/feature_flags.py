"""
Feature Flags Configuration
Elite Implementation Standard v2.0.0

Manages feature flags for routing behavior and system configuration.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FeatureFlags:
    """Feature flags configuration"""

    # Routing behavior
    enable_openai_router: bool = True
    enable_skill_library: bool = True
    enable_fallback_to_skill: bool = True

    # Dapr configuration
    enable_circuit_breaker: bool = True
    enable_retry_policy: bool = True
    enable_dead_letter_queue: bool = True

    # Security features
    enable_jwt_validation: bool = True
    enable_rate_limiting: bool = True
    enable_request_sanitization: bool = True

    # Monitoring & Observability
    enable_distributed_tracing: bool = True
    enable_prometheus_metrics: bool = True
    enable_audit_logging: bool = True

    # Performance tuning
    enable_connection_pooling: bool = True
    enable_response_caching: bool = False  # Currently disabled for consistency
    enable_concurrent_processing: bool = True

    # Experimental features
    enable_batch_processing: bool = False
    enable_ml_classifier: bool = False


class FeatureFlagManager:
    """Manages feature flags from environment and configuration"""

    def __init__(self, config_file: Optional[str] = None):
        self.flags = FeatureFlags()
        self._load_from_env()

        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)

    def _load_from_env(self):
        """Load feature flags from environment variables"""
        env_prefix = "LEARNFLOW_FEATURE_"

        # Map environment variables to feature flags
        flag_mapping = {
            "ENABLE_OPENAI_ROUTER": "enable_openai_router",
            "ENABLE_SKILL_LIBRARY": "enable_skill_library",
            "ENABLE_FALLBACK": "enable_fallback_to_skill",
            "ENABLE_CIRCUIT_BREAKER": "enable_circuit_breaker",
            "ENABLE_RETRY": "enable_retry_policy",
            "ENABLE_DLQ": "enable_dead_letter_queue",
            "ENABLE_JWT": "enable_jwt_validation",
            "ENABLE_RATE_LIMIT": "enable_rate_limiting",
            "ENABLE_SANITIZATION": "enable_request_sanitization",
            "ENABLE_TRACING": "enable_distributed_tracing",
            "ENABLE_METRICS": "enable_prometheus_metrics",
            "ENABLE_AUDIT": "enable_audit_logging",
            "ENABLE_CONNECTION_POOL": "enable_connection_pooling",
            "ENABLE_CACHING": "enable_response_caching",
            "ENABLE_CONCURRENT": "enable_concurrent_processing",
            "ENABLE_BATCH": "enable_batch_processing",
            "ENABLE_ML": "enable_ml_classifier",
        }

        for env_var, flag_name in flag_mapping.items():
            value = os.getenv(f"{env_prefix}{env_var}")
            if value is not None:
                setattr(self.flags, flag_name, value.lower() in ("true", "1", "yes"))

    def _load_from_file(self, config_file: str):
        """Load feature flags from JSON file"""
        import json

        try:
            with open(config_file, 'r') as f:
                data = json.load(f)

            for key, value in data.items():
                if hasattr(self.flags, key):
                    setattr(self.flags, key, bool(value))
        except Exception as e:
            print(f"Warning: Could not load feature flags from {config_file}: {e}")

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return getattr(self.flags, flag_name, False)

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags as dictionary"""
        return {
            k: v for k, v in vars(self.flags).items()
            if not k.startswith('_')
        }

    def enable_flag(self, flag_name: str):
        """Enable a feature flag"""
        if hasattr(self.flags, flag_name):
            setattr(self.flags, flag_name, True)

    def disable_flag(self, flag_name: str):
        """Disable a feature flag"""
        if hasattr(self.flags, flag_name):
            setattr(self.flags, flag_name, False)

    def get_routing_strategy(self) -> Dict[str, Any]:
        """Get current routing strategy based on flags"""
        strategy = {
            "primary": [],
            "fallback": []
        }

        if self.flags.enable_openai_router:
            strategy["primary"].append("openai")

        if self.flags.enable_skill_library:
            strategy["primary"].append("skill")

        if self.flags.enable_fallback_to_skill:
            strategy["fallback"].append("skill")

        return strategy

    def get_resilience_config(self) -> Dict[str, Any]:
        """Get resilience configuration based on flags"""
        config = {}

        if self.flags.enable_circuit_breaker:
            config["circuit_breaker"] = {
                "enabled": True,
                "failure_threshold": 5,
                "timeout_seconds": 30,
                "half_open_max_calls": 3
            }

        if self.flags.enable_retry_policy:
            config["retry"] = {
                "enabled": True,
                "max_attempts": 3,
                "backoff": "exponential",
                "base_delay_ms": 100,
                "max_delay_ms": 400
            }

        if self.flags.enable_dead_letter_queue:
            config["dead_letter_queue"] = {
                "enabled": True,
                "topic": "learning.events.dlq"
            }

        return config

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration based on flags"""
        config = {}

        if self.flags.enable_jwt_validation:
            config["jwt"] = {
                "enabled": True,
                "required_claims": ["sub", "exp", "iss"],
                "algorithm": "HS256"
            }

        if self.flags.enable_rate_limiting:
            config["rate_limiting"] = {
                "enabled": True,
                "requests_per_minute": 100,
                "requests_per_hour": 5000
            }

        if self.flags.enable_request_sanitization:
            config["sanitization"] = {
                "enabled": True,
                "max_input_length": 1000,
                "block_sql_injection": True,
                "block_xss": True
            }

        return config

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration based on flags"""
        config = {}

        if self.flags.enable_distributed_tracing:
            config["tracing"] = {
                "enabled": True,
                "provider": "dapr",
                "sample_rate": 1.0
            }

        if self.flags.enable_prometheus_metrics:
            config["metrics"] = {
                "enabled": True,
                "endpoint": "/metrics",
                "export_interval_seconds": 30
            }

        if self.flags.enable_audit_logging:
            config["audit"] = {
                "enabled": True,
                "log_level": "INFO",
                "include_request_body": False,
                "include_response_body": False
            }

        return config

    def __str__(self):
        """String representation of current flags"""
        flags = self.get_all_flags()
        enabled = sum(flags.values())
        total = len(flags)

        return f"FeatureFlags({enabled}/{total} enabled): {flags}"


# Global instance
_feature_manager = None


def get_feature_manager() -> FeatureFlagManager:
    """Get global feature flag manager instance"""
    global _feature_manager

    if _feature_manager is None:
        config_path = os.getenv("LEARNFLOW_FEATURE_FLAGS_FILE", "config/feature-flags.json")
        _feature_manager = FeatureFlagManager(config_path)

    return _feature_manager


def is_feature_enabled(flag_name: str) -> bool:
    """Quick check if a feature flag is enabled"""
    manager = get_feature_manager()
    return manager.is_enabled(flag_name)


def get_routing_strategy() -> Dict[str, Any]:
    """Get routing strategy"""
    manager = get_feature_manager()
    return manager.get_routing_strategy()


# Example configuration file (feature-flags.json):
EXAMPLE_CONFIG = {
    "enable_openai_router": True,
    "enable_skill_library": True,
    "enable_fallback_to_skill": True,
    "enable_circuit_breaker": True,
    "enable_retry_policy": True,
    "enable_dead_letter_queue": True,
    "enable_jwt_validation": True,
    "enable_rate_limiting": True,
    "enable_request_sanitization": True,
    "enable_distributed_tracing": True,
    "enable_prometheus_metrics": True,
    "enable_audit_logging": True,
    "enable_connection_pooling": True,
    "enable_response_caching": False,
    "enable_concurrent_processing": True,
    "enable_batch_processing": False,
    "enable_ml_classifier": False
}