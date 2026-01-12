#!/usr/bin/env python3
"""
Schema Validation Verification Script
LearnFlow Milestone 1: Infrastructure & Common Schema

Validates JSON schemas for syntax and logical correctness
"""

import json
import argparse
import os
import sys
import jsonschema

def validate_json_schema(file_path):
    """Validate JSON schema file"""
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)

        # Validate against JSON Schema meta-schema
        jsonschema.Draft7Validator.check_schema(schema)
        print(f"PASS: {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"FAIL: {os.path.basename(file_path)} - {e}")
        return False


def validate_avro_schema(file_path):
    """Validate Avro schema file"""
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)

        # Basic Avro validation
        if schema.get("type") != "record":
            print(f"FAIL: {os.path.basename(file_path)} - Not a record type")
            return False

        if "name" not in schema:
            print(f"FAIL: {os.path.basename(file_path)} - Missing name")
            return False

        if "fields" not in schema or not isinstance(schema["fields"], list):
            print(f"FAIL: {os.path.basename(file_path)} - Missing or invalid fields")
            return False

        print(f"PASS: {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"FAIL: {os.path.basename(file_path)} - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Schema Validation")
    parser.add_argument("--schemas", default="contracts/schemas", help="JSON schemas directory")
    parser.add_argument("--avro", default="contracts/avro", help="Avro schemas directory")
    parser.add_argument("--test-data", help="Test data directory")

    args = parser.parse_args()

    print("Schema Validation Check")
    print("=" * 50)

    results = []

    # Check JSON schemas
    if os.path.exists(args.schemas):
        print(f"\nJSON Schemas ({args.schemas}):")
        for file in os.listdir(args.schemas):
            if file.endswith('.json'):
                file_path = os.path.join(args.schemas, file)
                results.append(validate_json_schema(file_path))
    else:
        print(f"JSON Schemas directory not found: {args.schemas}")
        results.append(False)

    # Check Avro schemas
    if os.path.exists(args.avro):
        print(f"\nAvro Schemas ({args.avro}):")
        for file in os.listdir(args.avro):
            if file.endswith('.avsc'):
                file_path = os.path.join(args.avro, file)
                results.append(validate_avro_schema(file_path))
    else:
        print(f"Avro Schemas directory not found: {args.avro}")
        results.append(False)

    print("\n" + "=" * 50)
    if all(results):
        print("OVERALL: PASS - All schemas valid")
        return 0
    else:
        print("OVERALL: FAIL - Some schemas invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())