#!/usr/bin/env python3
"""
Quick Security Check for Mastery Engine
=======================================

Fast security validation script that checks critical security issues.
"""

import os
import re
import sys
from pathlib import Path

class QuickSecurityCheck:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.passed = []

    def check_all(self):
        """Run all quick checks"""
        print("=== QUICK SECURITY CHECK ===\n")

        self.check_secrets()
        self.check_environment()
        self.check_docker()
        self.check_jwt_secret()
        self.check_input_validation()

        self.print_results()

    def check_secrets(self):
        """Check for hardcoded secrets"""
        print("1. Scanning for hardcoded secrets...")

        # Common secret patterns
        patterns = [
            r'jwt_secret\s*=\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]

        files = ["src/main.py", "src/security.py"]
        for file_path in files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            if "os.getenv" not in content:
                                self.issues.append(f"Hardcoded secret in {file_path}")
                                return

        self.passed.append("No hardcoded secrets found")
        print("  PASS: No hardcoded secrets")

    def check_environment(self):
        """Check environment variable usage"""
        print("2. Checking environment configuration...")

        main_file = self.project_root / "src" / "main.py"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if "os.getenv('JWT_SECRET'" in content:
                self.passed.append("JWT_SECRET uses environment variables")
                print("  PASS: Environment variables used")
            else:
                self.issues.append("JWT_SECRET not using environment variables")
                print("  FAIL: Environment variables not used")
        else:
            self.warnings.append("main.py not found")
            print("  WARN: main.py not found")

    def check_docker(self):
        """Check Docker security"""
        print("3. Checking Docker security...")

        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            with open(dockerfile, 'r') as f:
                content = f.read()

            if "USER" in content and "root" not in content:
                self.passed.append("Non-root user in Dockerfile")
                print("  PASS: Non-root user configured")
            else:
                self.issues.append("Dockerfile runs as root")
                print("  FAIL: No non-root user")

            if "HEALTHCHECK" in content:
                self.passed.append("Health check in Dockerfile")
                print("  PASS: Health check configured")
            else:
                self.warnings.append("No health check in Dockerfile")
                print("  WARN: No health check")
        else:
            self.warnings.append("Dockerfile not found")
            print("  WARN: Dockerfile not found")

    def check_jwt_secret(self):
        """Check JWT secret configuration"""
        print("4. Checking JWT secret handling...")

        main_file = self.project_root / "src" / "main.py"
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for JWT secret handling
            if "JWT_SECRET" in content:
                if "os.getenv" in content:
                    self.passed.append("JWT_SECRET uses os.getenv()")
                    print("  PASS: JWT_SECRET properly configured")
                else:
                    self.issues.append("JWT_SECRET not using environment variable")
                    print("  FAIL: JWT_SECRET hardcoded")
            else:
                self.warnings.append("JWT_SECRET not found in main.py")
                print("  WARN: JWT_SECRET not found")
        else:
            self.warnings.append("main.py not found")
            print("  WARN: main.py not found")

    def check_input_validation(self):
        """Check for input validation"""
        print("5. Checking input validation...")

        # Check if Pydantic is imported
        files_to_check = [
            self.project_root / "src" / "api" / "endpoints" / "mastery.py",
            self.project_root / "src" / "models" / "mastery.py"
        ]

        found_pydantic = False
        for file_path in files_to_check:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "from pydantic import" in content or "import pydantic" in content:
                        found_pydantic = True
                        break

        if found_pydantic:
            self.passed.append("Pydantic models for validation")
            print("  PASS: Input validation using Pydantic")
        else:
            self.warnings.append("No Pydantic validation found")
            print("  WARN: Pydantic not found")

    def print_results(self):
        """Print final results"""
        print("\n" + "="*50)
        print("SECURITY CHECK SUMMARY")
        print("="*50)

        print(f"Passed: {len(self.passed)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Issues: {len(self.issues)}")

        if self.issues:
            print("\nISSUES:")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\nRESULT:", "PASS" if len(self.issues) == 0 else "FAIL")
        return len(self.issues) == 0


if __name__ == "__main__":
    project_root = Path.cwd()
    if not (project_root / "requirements.txt").exists():
        # Try parent directory
        project_root = Path(__file__).parent

    checker = QuickSecurityCheck(project_root)
    success = checker.check_all()

    sys.exit(0 if success else 1)