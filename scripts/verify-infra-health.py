#!/usr/bin/env python3
"""
Infrastructure Health Verification Script
LearnFlow Milestone 1: Infrastructure & Common Schema

Verification script for infrastructure components
"""

import json
import argparse
import os
import sys

def check_kafka_health():
    """Verify Kafka setup files exist and are configured correctly"""
    print("Checking Kafka health...")

    required_files = [
        "infrastructure/k8s/kafka/kafka-statefulset.yaml",
        "infrastructure/k8s/kafka/kafka-service.yaml",
        "infrastructure/k8s/kafka/kafka-topics-job.yaml"
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"ERROR: Missing {file_path}")
            return False

    # Verify topic configuration
    try:
        with open("infrastructure/k8s/kafka/kafka-setup-metadata.json", "r") as f:
            metadata = json.load(f)

        if metadata["config"]["partitions"] != 12:
            print(f"ERROR: Expected 12 partitions, got {metadata['config']['partitions']}")
            return False

        if "learning.events" not in metadata["config"]["topics"]:
            print("ERROR: learning.events topic not configured")
            return False

        print("Kafka: PASS (12 partitions, topics configured)")
        return True

    except Exception as e:
        print(f"ERROR: Failed to verify Kafka config: {e}")
        return False


def check_dapr_health():
    """Verify Dapr components exist"""
    print("Checking Dapr health...")

    # Since we haven't created Dapr components yet, this will initially fail
    # but will pass once T018-T020 are completed
    dapr_components = [
        "infrastructure/dapr/components/redis-statestore.yaml",
        "infrastructure/dapr/components/kafka-pubsub.yaml",
        "infrastructure/dapr/components/service-invocation.yaml"
    ]

    missing_files = []
    for file_path in dapr_components:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"Dapr: PENDING (missing: {', '.join(missing_files)})")
        return "PENDING"

    print("Dapr: PASS (all components configured)")
    return True


def check_postgres_health():
    """Verify PostgreSQL configuration"""
    print("Checking PostgreSQL health...")

    # Check for PostgreSQL deployment files
    pg_files = [
        "infrastructure/k8s/postgres-deployment.yaml",
        "infrastructure/postgres/init.sql"
    ]

    missing_files = []
    for file_path in pg_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"PostgreSQL: PENDING (missing: {', '.join(missing_files)})")
        return "PENDING"

    print("PostgreSQL: PASS (configuration ready)")
    return True


def check_schemas_health():
    """Verify schema files exist"""
    print("Checking Schema health...")

    schema_files = [
        "contracts/schemas/student-progress.schema.json",
        "contracts/schemas/mastery-score.schema.json",
        "contracts/avro/student-progress-event.avsc"
    ]

    missing_files = []
    for file_path in schema_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"Schemas: PENDING (missing: {', '.join(missing_files)})")
        return "PENDING"

    print("Schemas: PASS (JSON and Avro schemas present)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Infrastructure Health Verification")
    parser.add_argument("--service", choices=["kafka", "dapr", "postgres", "schemas", "all"],
                       default="all", help="Service to check")
    parser.add_argument("--check", help="Specific check to perform")

    args = parser.parse_args()

    print(f"LearnFlow Infrastructure Health Check")
    print("=" * 50)

    results = {}

    if args.service in ["kafka", "all"]:
        results["kafka"] = check_kafka_health()

    if args.service in ["dapr", "all"]:
        results["dapr"] = check_dapr_health()

    if args.service in ["postgres", "all"]:
        results["postgres"] = check_postgres_health()

    if args.service in ["schemas", "all"]:
        results["schemas"] = check_schemas_health()

    print("=" * 50)

    # Determine overall status
    all_pass = all(v is True for v in results.values())
    any_pending = any(v == "PENDING" for v in results.values())

    if all_pass:
        print("OVERALL: PASS - All services healthy")
        return 0
    elif any_pending:
        print("OVERALL: PENDING - Infrastructure deployment in progress")
        return 1
    else:
        print("OVERALL: FAIL - Some services not healthy")
        return 1


if __name__ == "__main__":
    sys.exit(main())