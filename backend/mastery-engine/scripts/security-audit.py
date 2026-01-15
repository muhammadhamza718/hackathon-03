#!/usr/bin/env python3
"""
Mastery Engine Security Audit Script
====================================

Comprehensive security audit for the Mastery Engine service.
Checks for common vulnerabilities, configuration issues, and best practices.

Usage:
    python scripts/security-audit.py
    python scripts/security-audit.py --fix --dry-run
"""

import os
import sys
import subprocess
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
import shutil


class SecurityAudit:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"
        self.docs_dir = project_root / "docs"
        self.scripts_dir = project_root / "scripts"

        self.issues = []
        self.warnings = []
        self.passed = []
        self.severity_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

    def run_all_checks(self):
        """Run all security checks"""
        print("SECURITY: Starting Mastery Engine Security Audit")
        print("=" * 60)

        # Dependency scanning
        print("\n1. Checking dependencies...")
        self.check_dependencies()

        # Secrets scanning
        print("\n2. Scanning for secrets...")
        self.check_secrets()

        # Input validation
        print("\n3. Checking input validation...")
        self.check_input_validation()

        # Authentication & Authorization
        print("\n4. Checking authentication...")
        self.check_authentication()

        # Environment configuration
        print("\n5. Checking environment configuration...")
        self.check_environment_config()

        # Docker security
        print("\n6. Checking Docker configuration...")
        self.check_docker_security()

        # Kubernetes security
        print("\n7. Checking Kubernetes manifests...")
        self.check_kubernetes_security()

        # Data protection
        print("\n8. Checking data protection...")
        self.check_data_protection()

        # Logging & monitoring
        print("\n9. Checking logging & monitoring...")
        self.check_logging()

        # Network security
        print("\n10. Checking network security...")
        self.check_network_security()

    def check_dependencies(self):
        """Check for vulnerable dependencies"""
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.add_issue("CRITICAL", "Missing requirements.txt")
            return

        print("  [INFO] Checking Python dependencies...")

        # Read requirements
        with open(requirements_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Known vulnerabilities (simplified - in production use pip-audit or safety)
        vulnerable_packages = {
            "flask": "<2.0.0",
            "django": "<3.2.0",
            "urllib3": "<1.26.0",
            "requests": "<2.25.0",
            "cryptography": "<3.4.0",
            "pyjwt": "<2.1.0"
        }

        for line in lines:
            for pkg, vuln_range in vulnerable_packages.items():
                if pkg in line.lower():
                    version = re.search(r'==([0-9.]+)', line)
                    if version:
                        current = version.group(1)
                        if self._is_version_vulnerable(current, vuln_range):
                            self.add_issue("HIGH", f"Vulnerable package: {line}")

        self.add_passed("Dependencies checked (basic)")

    def check_secrets(self):
        """Scan for hardcoded secrets"""
        print("  Scanning source code for secrets...")

        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'jwt[_-]?secret\s*=\s*["\'][^"\']+["\']',
            r'private[_-]?key\s*=\s*["\'][^"\']+["\']'
        ]

        # Check main files
        files_to_check = [
            self.src_dir / "main.py",
            self.src_dir / "security.py",
            self.src_dir / "services" / "state_manager.py"
        ]

        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # Exclude environment variable patterns
                            if "os.getenv" not in match.group(0):
                                self.add_issue("HIGH", f"Potential hardcoded secret in {file_path.name}: {match.group(0)}")

        # Check environment examples
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
                if "dev-secret-change-me" in content:
                    self.add_warning("Default development secret found in .env.example")

        self.add_passed("Secrets scan completed")

    def check_input_validation(self):
        """Check input validation in endpoints"""
        print("  Checking input validation...")

        # Check mastery endpoints
        mastery_endpoints = self.src_dir / "api" / "endpoints" / "mastery.py"
        if mastery_endpoints.exists():
            with open(mastery_endpoints, 'r') as f:
                content = f.read()

            # Check for Pydantic models
            if "from pydantic import" in content:
                self.add_passed("Using Pydantic models for validation")
            else:
                self.add_issue("MEDIUM", "Mastery endpoints not using Pydantic validation")

            # Check for sanitization
            if "sanitize" in content.lower() or "escape" in content.lower():
                self.add_passed("Input sanitization found")
            else:
                self.add_warning("No explicit sanitization found in mastery endpoints")

        self.add_passed("Input validation check completed")

    def check_authentication(self):
        """Check authentication and authorization"""
        print("  Checking authentication...")

        security_file = self.src_dir / "security.py"
        if not security_file.exists():
            self.add_issue("CRITICAL", "No security module found")
            return

        with open(security_file, 'r') as f:
            content = f.read()

        # Check for JWT validation
        if "jwt.decode" in content or "validate_jwt" in content:
            self.add_passed("JWT validation implemented")
        else:
            self.add_issue("HIGH", "No JWT validation found")

        # Check for RBAC
        if "role" in content.lower() or "permission" in content.lower():
            self.add_passed("Role-based access control found")
        else:
            self.add_issue("MEDIUM", "No RBAC implementation found")

        # Check for proper password hashing
        if "bcrypt" in content.lower() or "argon2" in content.lower():
            self.add_passed("Proper password hashing used")
        elif "password" in content.lower():
            self.add_issue("HIGH", "Password handling may not be secure")

        self.add_passed("Authentication check completed")

    def check_environment_config(self):
        """Check environment configuration"""
        print("  Checking environment configuration...")

        # Check for missing .env.example
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            self.add_issue("MEDIUM", "Missing .env.example template")

        # Check main.py for environment handling
        main_file = self.src_dir / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Check for JWT secret handling
            if "os.getenv('JWT_SECRET'" in content:
                self.add_passed("JWT_SECRET uses environment variable")
            else:
                self.add_issue("HIGH", "JWT_SECRET not using environment variable")

            # Check for LOG_LEVEL
            if "LOG_LEVEL" in content:
                self.add_passed("Configurable log level")
            else:
                self.add_warning("Fixed log level")

        self.add_passed("Environment configuration check completed")

    def check_docker_security(self):
        """Check Docker security configuration"""
        print("  Checking Docker security...")

        dockerfile = self.project_root / "Dockerfile"
        if not dockerfile.exists():
            self.add_issue("MEDIUM", "Dockerfile not found")
            return

        with open(dockerfile, 'r') as f:
            content = f.read()

        # Check for non-root user
        if "USER" in content and "root" not in content:
            self.add_passed("Non-root user configured")
        else:
            self.add_issue("HIGH", "Container runs as root")

        # Check for multi-stage build
        if "FROM" in content and "AS" in content:
            self.add_passed("Multi-stage build used")
        else:
            self.add_warning("Single-stage build (larger image)")

        # Check for health check
        if "HEALTHCHECK" in content:
            self.add_passed("Health check configured")
        else:
            self.add_issue("MEDIUM", "No health check configured")

        # Check for secrets in Dockerfile
        if re.search(r'ENV.*SECRET|ENV.*PASSWORD', content, re.IGNORECASE):
            self.add_issue("CRITICAL", "Secrets found in Dockerfile")

        self.add_passed("Docker security check completed")

    def check_kubernetes_security(self):
        """Check Kubernetes security manifests"""
        print("  Checking Kubernetes security...")

        deployment = self.project_root / "k8s" / "deployment.yaml"
        if not deployment.exists():
            self.add_issue("MEDIUM", "Kubernetes deployment not found")
            return

        with open(deployment, 'r') as f:
            content = f.read()

        # Check for resource limits
        if "resources:" in content and "limits:" in content and "requests:" in content:
            self.add_passed("Resource limits configured")
        else:
            self.add_issue("MEDIUM", "No resource limits configured")

        # Check for security context
        if "securityContext:" in content:
            self.add_passed("Security context configured")
        else:
            self.add_warning("No security context configured")

        # Check for Dapr sidecar
        if "daprd" in content.lower() or "dapr.io" in content:
            self.add_passed("Dapr sidecar integration")
        else:
            self.add_warning("No Dapr sidecar configuration")

        # Check for read-only root filesystem (optional but good)
        if "readOnlyRootFilesystem" in content:
            self.add_passed("Read-only root filesystem")
        else:
            self.add_warning("Writable root filesystem")

        self.add_passed("Kubernetes security check completed")

    def check_data_protection(self):
        """Check data protection measures"""
        print("  Checking data protection...")

        # Check GDPR compliance in compliance endpoints
        compliance_file = self.src_dir / "api" / "endpoints" / "compliance.py"
        if compliance_file.exists():
            with open(compliance_file, 'r') as f:
                content = f.read()

            if "delete" in content.lower() and "export" in content.lower():
                self.add_passed("GDPR deletion and export endpoints found")
            else:
                self.add_issue("MEDIUM", "Missing GDPR compliance endpoints")

        # Check state manager for TTL
        state_manager = self.src_dir / "services" / "state_manager.py"
        if state_manager.exists():
            with open(state_manager, 'r') as f:
                content = f.read()

            if "ttl" in content.lower() or "ttl_days" in content.lower():
                self.add_passed("Data retention policy (TTL) implemented")
            else:
                self.add_issue("MEDIUM", "No data retention policy")

        # Check for encryption of sensitive data
        if "encrypt" in content.lower() or "crypt" in content.lower():
            self.add_passed("Encryption found")
        else:
            self.add_warning("No explicit encryption found")

        self.add_passed("Data protection check completed")

    def check_logging(self):
        """Check logging and monitoring"""
        print("  Checking logging & monitoring...")

        main_file = self.src_dir / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Check for structured logging
            if "json" in content.lower() or "structured" in content.lower():
                self.add_passed("Structured logging configured")
            else:
                self.add_warning("No structured logging")

            # Check for correlation IDs
            if "correlation" in content.lower() or "request.id" in content.lower():
                self.add_passed("Correlation ID tracking")
            else:
                self.add_warning("No correlation ID tracking")

            # Check for metrics endpoint
            if "metrics" in content:
                self.add_passed("Metrics endpoint exposed")
            else:
                self.add_issue("MEDIUM", "No metrics endpoint")

        # Check for audit logging in security
        security_file = self.src_dir / "security.py"
        if security_file.exists():
            with open(security_file, 'r') as f:
                content = f.read()

            if "audit" in content.lower():
                self.add_passed("Audit logging implemented")
            else:
                self.add_warning("No audit logging")

        self.add_passed("Logging check completed")

    def check_network_security(self):
        """Check network security configuration"""
        print("  Checking network security...")

        main_file = self.src_dir / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Check for CORS
            if "CORSMiddleware" in content:
                self.add_passed("CORS middleware configured")
            else:
                self.add_warning("No CORS middleware")

            # Check for rate limiting
            if "limiter" in content.lower() or "rate" in content.lower():
                self.add_passed("Rate limiting configured")
            else:
                self.add_issue("MEDIUM", "No rate limiting")

            # Check for security headers
            if "security_headers" in content.lower():
                self.add_passed("Security headers middleware")
            else:
                self.add_warning("No security headers middleware")

        # Check TLS configuration
        tls_config = self.project_root / "tls_config.py"
        if tls_config.exists():
            self.add_passed("TLS configuration found")
        else:
            self.add_warning("No TLS configuration file")

        self.add_passed("Network security check completed")

    def _is_version_vulnerable(self, current: str, vulnerable_range: str) -> bool:
        """Check if version is vulnerable based on range"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            # Simplified comparison - in production use proper version parsing
            if vulnerable_range.startswith("<") and len(current_parts) > 0:
                # Check major version (simplified)
                required = vulnerable_range[1:].split('.')
                for i, (c, r) in enumerate(zip(current_parts, required)):
                    if c < int(r):
                        return True
                    elif c > int(r):
                        return False
                # Equal versions - not vulnerable if exact match
                return len(current_parts) <= len(required)
        except:
            pass
        return False

    def add_issue(self, severity: str, message: str):
        """Add security issue"""
        self.issues.append({"severity": severity, "message": message})
        print(f"  ❌ {severity}: {message}")

    def add_warning(self, message: str):
        """Add warning"""
        self.warnings.append({"message": message})
        print(f"  ⚠️  WARNING: {message}")

    def add_passed(self, message: str):
        """Add passed check"""
        self.passed.append({"message": message})
        print(f"  ✅ {message}")

    def generate_report(self):
        """Generate final audit report"""
        print("\n" + "=" * 60)
        print("SECURITY AUDIT REPORT")
        print("=" * 60)

        # Count by severity
        critical = len([i for i in self.issues if i["severity"] == "CRITICAL"])
        high = len([i for i in self.issues if i["severity"] == "HIGH"])
        medium = len([i for i in self.issues if i["severity"] == "MEDIUM"])
        low = len([i for i in self.issues if i["severity"] == "LOW"])

        print(f"\n📊 Summary:")
        print(f"  Issues: {len(self.issues)}")
        print(f"    Critical: {critical}")
        print(f"    High: {high}")
        print(f"    Medium: {medium}")
        print(f"    Low: {low}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Passed: {len(self.passed)}")

        # List issues by severity
        if self.issues:
            print(f"\n🔍 Issues Found:")
            for severity in self.severity_levels:
                severity_issues = [i for i in self.issues if i["severity"] == severity]
                if severity_issues:
                    print(f"\n{severity} ({len(severity_issues)}):")
                    for issue in severity_issues:
                        print(f"  - {issue['message']}")

        # List warnings
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning['message']}")

        # Overall assessment
        print(f"\n🎯 Assessment:")
        if critical > 0:
            print("  ❌ CRITICAL: Critical vulnerabilities found. Do NOT deploy.")
            return False
        elif high > 0:
            print("  ⚠️  HIGH: High severity issues found. Fix before production.")
            return False
        elif medium > 0:
            print("  ⚠️  MEDIUM: Medium issues found. Consider fixing before production.")
            return True
        else:
            print("  ✅ PASS: No critical or high issues found. Good to proceed.")
            return True

    def save_report(self, filename: str = "security-audit-report.json"):
        """Save detailed report to file"""
        report = {
            "issues": self.issues,
            "warnings": self.warnings,
            "passed": self.passed,
            "summary": {
                "total_issues": len(self.issues),
                "total_warnings": len(self.warnings),
                "total_passed": len(self.passed),
                "by_severity": {
                    severity: len([i for i in self.issues if i["severity"] == severity])
                    for severity in self.severity_levels
                }
            }
        }

        with open(self.project_root / filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Detailed report saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Security audit for Mastery Engine")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues (dry-run by default)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed")
    parser.add_argument("--output", help="Output report filename")

    args = parser.parse_args()

    # Check if running from project directory
    project_root = Path.cwd()
    if not (project_root / "requirements.txt").exists():
        # Try to find project root
        current = Path(__file__).parent
        project_root = current.parent

    audit = SecurityAudit(project_root)
    audit.run_all_checks()
    success = audit.generate_report()

    if args.output:
        audit.save_report(args.output)
    else:
        audit.save_report()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()