#!/usr/bin/env python3
import subprocess
import json
import sys

def check_kafka_ready():
    try:
        # Check pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "kafka", "-l", "strimzi.io/name=my-cluster-kafka", "-o", "json"],
            capture_output=True, text=True, check=True
        )
        pods = json.loads(result.stdout).get("items", [])
        
        if not pods:
            print("✗ No Kafka pods found.")
            return False
            
        running = all(p["status"]["phase"] == "Running" for p in pods)
        
        if running:
            print(f"✓ All {len(pods)} Kafka pods are Running.")
            return True
        else:
            print("✗ Kafka pods are not yet ready.")
            return False
            
    except Exception as e:
        print(f"✗ Error checking Kafka status: {e}")
        return False

if __name__ == "__main__":
    if check_kafka_ready():
        sys.exit(0)
    else:
        sys.exit(1)
