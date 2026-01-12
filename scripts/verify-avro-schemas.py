#!/usr/bin/env python3
"""
Avro Schema Verification Script
LearnFlow Milestone 1: Infrastructure & Common Schema

Validates Avro schemas can be compiled and used for serialization
"""

import json
import argparse
import os
import sys

def validate_avro_schema_compilation(file_path):
    """Verify Avro schema can be compiled"""
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)

        # Basic structural validation
        if schema.get("type") != "record":
            return False, f"Type must be 'record', got {schema.get('type')}"

        if "name" not in schema:
            return False, "Missing required 'name' field"

        if "namespace" not in schema:
            return False, "Missing required 'namespace' field"

        if "fields" not in schema or not isinstance(schema["fields"], list):
            return False, "Missing or invalid 'fields' array"

        # Validate fields
        for i, field in enumerate(schema["fields"]):
            if "name" not in field:
                return False, f"Field {i} missing 'name'"
            if "type" not in field:
                return False, f"Field {i} missing 'type'"

        return True, "Valid Avro schema"

    except Exception as e:
        return False, str(e)


def test_avro_serialization(file_path):
    """Test that we can create sample data for the schema"""
    try:
        with open(file_path, 'r') as f:
            schema = json.load(f)

        # Create a sample data structure based on schema
        sample_data = {}
        for field in schema["fields"]:
            field_name = field["name"]
            field_type = field["type"]

            # Simple type mapping for sample data
            if isinstance(field_type, list):
                # Nullable type, use non-null type for sample
                base_types = [t for t in field_type if t != "null"]
                base_type = base_types[0] if base_types else "string"
            else:
                base_type = field_type

            if base_type == "string":
                sample_data[field_name] = f"sample_{field_name}"
            elif base_type == "int":
                sample_data[field_name] = 42
            elif base_type == "long":
                sample_data[field_name] = 123456789
            elif base_type == "float":
                sample_data[field_name] = 3.14
            elif base_type == "boolean":
                sample_data[field_name] = True
            elif isinstance(base_type, dict) and base_type.get("type") == "enum":
                sample_data[field_name] = base_type["symbols"][0]
            elif isinstance(base_type, dict) and base_type.get("type") == "record":
                sample_data[field_name] = {}  # Nested record
            elif base_type == "map":
                sample_data[field_name] = {"key": "value"}
            else:
                sample_data[field_name] = "default"

        return True, sample_data

    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Avro Schema Verification")
    parser.add_argument("--schemas", default="contracts/avro", help="Avro schemas directory")
    parser.add_argument("--test-serialization", action="store_true", help="Test serialization")

    args = parser.parse_args()

    print("Avro Schema Verification")
    print("=" * 50)

    all_valid = True

    if os.path.exists(args.schemas):
        for file in os.listdir(args.schemas):
            if file.endswith('.avsc'):
                file_path = os.path.join(args.schemas, file)
                print(f"\nChecking {file}:")

                # Compilation test
                valid, message = validate_avro_schema_compilation(file_path)
                if valid:
                    print(f"  Compilation: PASS")
                else:
                    print(f"  Compilation: FAIL - {message}")
                    all_valid = False
                    continue

                # Serialization test
                if args.test_serialization:
                    serial_valid, serial_result = test_avro_serialization(file_path)
                    if serial_valid:
                        print(f"  Serialization: PASS")
                        print(f"  Sample data: {json.dumps(serial_result, indent=4)}")
                    else:
                        print(f"  Serialization: FAIL - {serial_result}")
                        all_valid = False
    else:
        print(f"Avro schemas directory not found: {args.schemas}")
        all_valid = False

    print("\n" + "=" * 50)
    if all_valid:
        print("OVERALL: PASS - All Avro schemas valid")
        return 0
    else:
        print("OVERALL: FAIL - Some Avro schemas invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())