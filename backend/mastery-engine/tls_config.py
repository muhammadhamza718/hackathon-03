"""
TLS Configuration for Production Deployments
============================================

SSL/TLS configuration for secure communication in production environments.
This file provides configuration utilities for production-ready deployments.
"""

import os
import ssl
from typing import Optional, Dict, Any


class TLSConfig:
    """TLS configuration manager for production deployments"""

    @staticmethod
    def get_ssl_context() -> Optional[ssl.SSLContext]:
        """
        Create SSL context for HTTPS server

        Returns:
            SSLContext if TLS is configured, None otherwise
        """
        cert_file = os.getenv("TLS_CERT_FILE")
        key_file = os.getenv("TLS_KEY_FILE")

        if not cert_file or not key_file:
            return None

        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            raise FileNotFoundError(f"TLS certificate or key file not found")

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_file, key_file)

        # Security hardening
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.options |= ssl.OP_NO_SSLv2
        ssl_context.options |= ssl.OP_NO_SSLv3
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1

        return ssl_context

    @staticmethod
    def get_uvicorn_ssl_config() -> Dict[str, Any]:
        """
        Get SSL configuration for Uvicorn server

        Returns:
            Dict with ssl_keyfile and ssl_certfile if TLS is enabled
        """
        cert_file = os.getenv("TLS_CERT_FILE")
        key_file = os.getenv("TLS_KEY_FILE")

        if cert_file and key_file:
            return {
                "ssl_keyfile": key_file,
                "ssl_certfile": cert_file,
                "ssl_ciphers": "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384"
            }

        return {}

    @staticmethod
    def is_production_tls_enabled() -> bool:
        """Check if production TLS is configured"""
        return bool(os.getenv("TLS_CERT_FILE") and os.getenv("TLS_KEY_FILE"))

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get security headers for HTTPS responses

        Returns:
            Dict of security headers
        """
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        # Add Content Security Policy if enabled
        if os.getenv("ENABLE_CSP", "true").lower() == "true":
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        return headers


def get_uvicorn_config():
    """
    Get complete Uvicorn configuration

    Returns:
        Dict with server configuration
    """
    config = {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8005")),
        "reload": os.getenv("ENVIRONMENT", "development") == "development",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
    }

    # Add TLS config if enabled
    ssl_config = TLSConfig.get_uvicorn_ssl_config()
    if ssl_config:
        config.update(ssl_config)
        config["ssl_keyfile_password"] = os.getenv("TLS_KEY_PASSWORD")  # Optional

    # Worker configuration for production
    workers = os.getenv("UVICORN_WORKERS")
    if workers and os.getenv("ENVIRONMENT") == "production":
        config["workers"] = int(workers)

    # Timeout configuration
    timeout_keep_alive = os.getenv("UVICORN_TIMEOUT_KEEP_ALIVE")
    if timeout_keep_alive:
        config["timeout_keep_alive"] = int(timeout_keep_alive)

    return config


# Production security checklist
PRODUCTION_CHECKLIST = {
    "required": [
        "JWT_SECRET is not default",
        "TLS certificates configured",
        "Database credentials secure",
        "Firewall rules applied",
        "Monitoring enabled",
        "Backup strategy in place"
    ],
    "recommended": [
        "Rate limiting enabled",
        "WAF configured",
        "DDoS protection enabled",
        "Regular security audits",
        "Log aggregation",
        "Secret rotation"
    ]
}


def validate_production_config():
    """
    Validate production configuration

    Returns:
        Tuple (is_valid, issues_list)
    """
    issues = []

    # Check JWT secret
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or jwt_secret == "dev-secret-change-in-production":
        issues.append("JWT_SECRET must be changed from default")

    # Check TLS
    if not TLSConfig.is_production_tls_enabled():
        issues.append("TLS certificates not configured")

    # Check environment
    env = os.getenv("ENVIRONMENT")
    if env != "production":
        issues.append(f"ENVIRONMENT should be 'production', currently '{env}'")

    # Check logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    if log_level.upper() not in ["INFO", "WARNING", "ERROR"]:
        issues.append("LOG_LEVEL should be INFO, WARNING, or ERROR in production")

    return len(issues) == 0, issues