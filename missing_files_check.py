#!/usr/bin/env python3
"""
Quick check for missing critical files
"""

import os
from pathlib import Path

base_path = Path("F:/Courses/Hamza/Hackathon-3/backend/triage-service/src")

critical_files = [
    # Phase 1
    "api/routes.py",
    "api/middleware/tracing.py",
    "api/middleware/rate_limiter.py",
    "api/middleware/sanitization.py",
    "config/openai_config.py",

    # Phase 2
    "services/dapr_tracing.py",
    "services/circuit_breaker_monitor.py",
    "services/dead_letter_queue.py",

    # Phase 3
    "services/jwt_validator.py",
    "services/kafka_publisher.py",
    "services/dapr_tracing_injector.py",
    "api/middleware/authorization.py",
    "services/security_reporter.py",
    "services/audit_logger.py",
]

print("Checking for missing critical files:")
print("=" * 60)

missing = []
for file in critical_files:
    full_path = base_path / file
    exists = full_path.exists()
    status = "[OK]" if exists else "[MISSING]"
    print(f"{status} {file}")
    if not exists:
        missing.append(file)

print(f"\nMissing files: {len(missing)}/{len(critical_files)}")
if missing:
    print("\nMissing:")
    for m in missing:
        print(f"  - {m}")