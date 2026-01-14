#!/usr/bin/env python3
"""
Dapr-Kafka Connectivity Test
Verifies that Dapr components can communicate with Kafka cluster
Elite Implementation Standard v2.0.0
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp


async def test_dapr_health():
    """Test Dapr sidecar health"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3500/v1.0/healthz")
            if response.status_code == 200:
                print("[PASS] Dapr sidecar is healthy")
                return True
            else:
                print(f"[FAIL] Dapr health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"[FAIL] Cannot connect to Dapr: {e}")
        return False


async def test_kafka_pubsub():
    """Test Kafka pub/sub via Dapr"""
    try:
        with DaprClient() as dapr:
            # Publish a test event
            test_event = {
                "event_id": "test-connectivity-001",
                "event_type": "test.connection",
                "student_id": "test-student",
                "component": "connectivity-test",
                "scores": {"completion": 1.0, "quiz": 1.0, "quality": 1.0, "consistency": 1.0},
                "mastery": 1.0,
                "idempotency_key": "test-001"
            }

            result = dapr.publish_event(
                pubsub_name="kafka-pubsub",
                topic_name="learning.events",
                data=json.dumps(test_event),
                data_content_type="application/json"
            )

            print("[PASS] Kafka pubsub test event published successfully")
            return True

    except Exception as e:
        print(f"[FAIL] Kafka pubsub test failed: {e}")
        return False


async def test_state_store():
    """Test Dapr state store (Redis)"""
    try:
        with DaprClient() as dapr:
            # Save test state
            test_key = "connectivity-test-key"
            test_value = {"status": "healthy", "timestamp": "2026-01-13T10:00:00Z"}

            dapr.save_state(
                store_name="statestore-redis",
                key=test_key,
                value=json.dumps(test_value)
            )

            # Retrieve test state
            state = dapr.get_state(
                store_name="statestore-redis",
                key=test_key
            )

            if state.data:
                print("[PASS] State store test successful")
                return True
            else:
                print("[FAIL] State store returned no data")
                return False

    except Exception as e:
        print(f"[FAIL] State store test failed: {e}")
        return False


async def main():
    """Run all connectivity tests"""
    print("=== Dapr-Kafka Connectivity Test ===")
    print("Testing infrastructure components...")

    results = []

    # Test 1: Dapr Health
    print("\n[1/3] Testing Dapr sidecar health...")
    results.append(await test_dapr_health())

    # Test 2: Kafka Pub/Sub
    print("\n[2/3] Testing Kafka pub/sub connectivity...")
    results.append(await test_kafka_pubsub())

    # Test 3: State Store
    print("\n[3/3] Testing Dapr state store...")
    results.append(await test_state_store())

    # Summary
    print(f"\n=== Results ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("All infrastructure connectivity tests passed!")
        return 0
    else:
        print("Some infrastructure tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))