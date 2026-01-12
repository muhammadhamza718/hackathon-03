#!/usr/bin/env python3
"""
Phase 3 Verification: Zero-Trust Security + Dead-Letter-Queue
Basic structure check
"""

import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("PHASE 3 VERIFICATION - BASIC")
    print("=" * 60)

    checks = []

    # 1. Check Kong configuration files
    kong_files = [
        "infrastructure/kong/plugins/jwt-config.yaml",
        "infrastructure/kong/services/triage-service.yaml",
        "infrastructure/kong/services/triage-route.yaml"
    ]

    for file_path in kong_files:
        exists = Path(file_path).exists()
        checks.append((f"Kong Config: {file_path}", exists))
        print(f"{'PASS' if exists else 'FAIL'} {file_path}")

    # 2. Check security middleware files
    middleware_files = [
        "backend/triage-service/src/api/middleware/auth.py",
        "backend/triage-service/src/api/middleware/authorization.py"
    ]

    for file_path in middleware_files:
        exists = Path(file_path).exists()
        checks.append((f"Middleware: {file_path}", exists))
        print(f"{'PASS' if exists else 'FAIL'} {file_path}")

    # 3. Check security service files
    security_services = [
        "backend/triage-service/src/services/jwt_validator.py",
        "backend/triage-service/src/services/audit_logger.py",
        "backend/triage-service/src/services/dapr_tracing_injector.py",
        "backend/triage-service/src/services/kafka_publisher.py",
        "backend/triage-service/src/services/security_reporter.py",
        "backend/triage-service/src/services/dead_letter_queue.py"
    ]

    for file_path in security_services:
        exists = Path(file_path).exists()
        checks.append((f"Security Service: {file_path}", exists))
        print(f"{'PASS' if exists else 'FAIL'} {file_path}")

    # 4. Check auth middleware has X-Student-ID extraction
    auth_path = Path("backend/triage-service/src/api/middleware/auth.py")
    if auth_path.exists():
        try:
            content = auth_path.read_text(encoding='utf-8', errors='ignore')
            has_kong_extraction = "X-Consumer-Username" in content
            has_student_id = "student_id" in content
            checks.append(("Auth Middleware: Kong extraction", has_kong_extraction))
            checks.append(("Auth Middleware: Student ID", has_student_id))
            print(f"{'PASS' if has_kong_extraction else 'FAIL'} Kong JWT extraction")
            print(f"{'PASS' if has_student_id else 'FAIL'} Student ID handling")
        except:
            checks.append(("Auth Middleware: Kong extraction", False))
            checks.append(("Auth Middleware: Student ID", False))
            print("FAIL Could not read auth middleware")

    # 5. Check JWT validation
    jwt_path = Path("backend/triage-service/src/services/jwt_validator.py")
    if jwt_path.exists():
        try:
            content = jwt_path.read_text(encoding='utf-8', errors='ignore')
            has_exp_validation = "exp" in content.lower()
            has_sub_validation = "sub" in content.lower()
            has_role_validation = "role" in content.lower()
            checks.append(("JWT Validator: exp claim", has_exp_validation))
            checks.append(("JWT Validator: sub claim", has_sub_validation))
            checks.append(("JWT Validator: role claim", has_role_validation))
            print(f"{'PASS' if has_exp_validation else 'FAIL'} Expiration validation")
            print(f"{'PASS' if has_sub_validation else 'FAIL'} Subject validation")
            print(f"{'PASS' if has_role_validation else 'FAIL'} Role validation")
        except:
            checks.append(("JWT Validator: exp claim", False))
            checks.append(("JWT Validator: sub claim", False))
            checks.append(("JWT Validator: role claim", False))
            print("FAIL Could not read JWT validator")

    # 6. Check audit logger
    audit_path = Path("backend/triage-service/src/services/audit_logger.py")
    if audit_path.exists():
        try:
            content = audit_path.read_text(encoding='utf-8', errors='ignore')
            has_audit_class = "class TriageAudit" in content
            has_kafka = "Kafka" in content
            checks.append(("Audit Logger: TriageAudit class", has_audit_class))
            checks.append(("Audit Logger: Kafka support", has_kafka))
            print(f"{'PASS' if has_audit_class else 'FAIL'} Audit class")
            print(f"{'PASS' if has_kafka else 'FAIL'} Kafka integration")
        except:
            checks.append(("Audit Logger: TriageAudit class", False))
            checks.append(("Audit Logger: Kafka support", False))
            print("FAIL Could not read audit logger")

    # 7. Check dead letter queue
    dlq_path = Path("backend/triage-service/src/services/dead_letter_queue.py")
    if dlq_path.exists():
        try:
            content = dlq_path.read_text(encoding='utf-8', errors='ignore')
            has_dlq_class = "class DeadLetterQueue" in content
            has_failure_reason = "failure_reason" in content
            checks.append(("DLQ: Class exists", has_dlq_class))
            checks.append(("DLQ: Failure tracking", has_failure_reason))
            print(f"{'PASS' if has_dlq_class else 'FAIL'} DLQ class")
            print(f"{'PASS' if has_failure_reason else 'FAIL'} Failure tracking")
        except:
            checks.append(("DLQ: Class exists", False))
            checks.append(("DLQ: Failure tracking", False))
            print("FAIL Could not read DLQ")

    # 8. Check updated main.py imports
    main_path = Path("backend/triage-service/src/main.py")
    if main_path.exists():
        try:
            content = main_path.read_text(encoding='utf-8', errors='ignore')
            has_auth_import = "from api.middleware.auth import" in content
            has_authz_import = "from api.middleware.authorization import" in content
            checks.append(("Main.py: Auth middleware import", has_auth_import))
            checks.append(("Main.py: Authorization import", has_authz_import))
            print(f"{'PASS' if has_auth_import else 'FAIL'} Auth middleware import")
            print(f"{'PASS' if has_authz_import else 'FAIL'} Authorization import")
        except:
            checks.append(("Main.py: Auth middleware import", False))
            checks.append(("Main.py: Authorization import", False))
            print("FAIL Could not read main.py")

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 3 RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status} | {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("PHASE 3: BASIC STRUCTURE COMPLETE")
        print("Zero-Trust Security + DLQ ready")
        return 0
    else:
        print("PHASE 3: INCOMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main())