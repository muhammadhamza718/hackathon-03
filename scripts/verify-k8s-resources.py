#!/usr/bin/env python3
"""
Kubernetes Resources Verification Script
LearnFlow Milestone 1: Infrastructure & Common Schema

Validates Kubernetes manifests for syntax and best practices
"""

import yaml
import argparse
import os
import sys

def validate_k8s_manifest(file_path):
    """Validate a Kubernetes manifest file"""
    try:
        with open(file_path, 'r') as f:
            manifests = list(yaml.safe_load_all(f))

        valid = True
        errors = []

        for i, manifest in enumerate(manifests):
            if not manifest:
                continue

            # Required fields
            if "apiVersion" not in manifest:
                errors.append(f"Manifest {i}: Missing apiVersion")
                valid = False
                continue

            if "kind" not in manifest:
                errors.append(f"Manifest {i}: Missing kind")
                valid = False
                continue

            if "metadata" not in manifest:
                errors.append(f"Manifest {i}: Missing metadata")
                valid = False
                continue

            # Basic structure validation
            kind = manifest["kind"]
            if kind == "Deployment" and "spec" not in manifest:
                errors.append(f"Manifest {i}: Deployment missing spec")
                valid = False
            elif kind == "Service" and "spec" not in manifest:
                errors.append(f"Manifest {i}: Service missing spec")
                valid = False
            elif kind == "StatefulSet" and "spec" not in manifest:
                errors.append(f"Manifest {i}: StatefulSet missing spec")
                valid = False
            elif kind == "Job" and "spec" not in manifest:
                errors.append(f"Manifest {i}: Job missing spec")
                valid = False
            elif kind == "ConfigMap" and "data" not in manifest:
                errors.append(f"Manifest {i}: ConfigMap missing data")
                valid = False
            elif kind == "Namespace" and "metadata" not in manifest:
                errors.append(f"Manifest {i}: Namespace missing metadata")
                valid = False

        return valid, errors

    except Exception as e:
        return False, [str(e)]


def main():
    parser = argparse.ArgumentParser(description="Kubernetes Manifest Validation")
    parser.add_argument("--manifests", default="infrastructure/k8s", help="K8s manifests directory")
    parser.add_argument("--check", choices=["syntax", "resources", "all"], default="all", help="Type of validation")

    args = parser.parse_args()

    print("Kubernetes Resources Validation")
    print("=" * 50)

    if not os.path.exists(args.manifests):
        print(f"Manifests directory not found: {args.manifests}")
        return 1

    all_valid = True

    # Walk through directory recursively
    for root, dirs, files in os.walk(args.manifests):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, args.manifests)

                print(f"\nChecking {rel_path}:")

                valid, errors = validate_k8s_manifest(file_path)

                if valid:
                    print("  Syntax: PASS")
                else:
                    print("  Syntax: FAIL")
                    for error in errors:
                        print(f"    - {error}")
                    all_valid = False

    print("\n" + "=" * 50)
    if all_valid:
        print("OVERALL: PASS - All K8s manifests valid")
        return 0
    else:
        print("OVERALL: FAIL - Some K8s manifests invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())