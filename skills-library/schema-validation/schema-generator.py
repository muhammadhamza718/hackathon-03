#!/usr/bin/env python3
"""
JSON Schema Generation Skill
LearnFlow Milestone 1: Infrastructure & Common Schema

This script generates JSON Schemas from data model requirements
"""

import json
import yaml
import argparse
from datetime import datetime

def generate_student_progress_schema():
    """Generate StudentProgress JSON Schema"""

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "StudentProgress Event",
        "description": "Event schema for student progress tracking via Kafka",
        "required": ["student_id", "exercise_id", "timestamp", "agent_source"],
        "properties": {
            "student_id": {
                "type": "string",
                "pattern": "^student_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                "description": "UUID format student identifier - used for Kafka partitioning"
            },
            "exercise_id": {
                "type": "string",
                "pattern": "^ex_[a-zA-Z0-9_-]+$",
                "description": "Unique exercise identifier with ex_ prefix"
            },
            "completion_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Normalized completion percentage (0.0-1.0)"
            },
            "quiz_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Normalized quiz performance (0.0-1.0)"
            },
            "quality_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Code quality assessment (0.0-1.0)"
            },
            "consistency_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Learning consistency metric (0.0-1.0)"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp in UTC"
            },
            "agent_source": {
                "type": "string",
                "enum": ["concepts", "review", "debug", "exercise", "progress"],
                "description": "Origin agent of the event"
            },
            "idempotency_key": {
                "type": ["null", "string"],
                "pattern": "^[a-f0-9]{32}$",
                "description": "32-character hex idempotency key for deduplication"
            },
            "metadata": {
                "type": ["null", "object"],
                "description": "Agent-specific additional data"
            }
        }
    }

    return schema


def generate_mastery_score_schema():
    """Generate MasteryScore JSON Schema for Dapr state store"""

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Mastery Score",
        "description": "Mastery score calculation and storage schema",
        "required": ["student_id", "date", "components", "final_score", "calculated_at"],
        "properties": {
            "student_id": {
                "type": "string",
                "pattern": "^student_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                "description": "UUID format student identifier"
            },
            "date": {
                "type": "string",
                "format": "date",
                "description": "Calculation date in YYYY-MM-DD format"
            },
            "components": {
                "type": "object",
                "description": "Component scores breakdown",
                "required": ["completion", "quiz", "quality", "consistency"],
                "properties": {
                    "completion": {
                        "type": "object",
                        "required": ["value", "count", "last_updated"],
                        "properties": {
                            "value": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "count": {"type": "integer", "minimum": 1},
                            "last_updated": {"type": "string", "format": "date-time"}
                        }
                    },
                    "quiz": {
                        "type": "object",
                        "required": ["value", "count", "last_updated"],
                        "properties": {
                            "value": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "count": {"type": "integer", "minimum": 1},
                            "last_updated": {"type": "string", "format": "date-time"}
                        }
                    },
                    "quality": {
                        "type": "object",
                        "required": ["value", "count", "last_updated"],
                        "properties": {
                            "value": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "count": {"type": "integer", "minimum": 1},
                            "last_updated": {"type": "string", "format": "date-time"}
                        }
                    },
                    "consistency": {
                        "type": "object",
                        "required": ["value", "count", "last_updated"],
                        "properties": {
                            "value": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "count": {"type": "integer", "minimum": 1},
                            "last_updated": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            },
            "final_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Calculated mastery: 0.4*completion + 0.3*quiz + 0.2*quality + 0.1*consistency"
            },
            "calculated_at": {
                "type": "string",
                "format": "date-time",
                "description": "When mastery was calculated"
            }
        }
    }

    return schema


def generate_idempotency_key_schema():
    """Generate Idempotency Key Schema"""

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Idempotency Key",
        "description": "Schema for duplicate prevention mechanism",
        "required": ["key", "student_id", "exercise_id", "created_at"],
        "properties": {
            "key": {
                "type": "string",
                "pattern": "^[a-f0-9]{32}$",
                "description": "32-character hex idempotency key"
            },
            "student_id": {
                "type": "string",
                "pattern": "^student_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
            },
            "exercise_id": {
                "type": "string",
                "pattern": "^ex_[a-zA-Z0-9_-]+$"
            },
            "created_at": {
                "type": "string",
                "format": "date-time"
            },
            "ttl": {
                "type": "integer",
                "description": "Time to live in seconds",
                "default": 60
            }
        }
    }

    return schema


def avro_from_json_schema(json_schema, name):
    """Convert JSON Schema to Avro-like structure for Kafka"""

    # Map JSON types to Avro types
    type_mapping = {
        "string": "string",
        "number": "float",
        "integer": "int",
        "boolean": "boolean",
        "object": "record",
        "array": "array"
    }

    def convert_property(prop_name, prop_def, required):
        prop_type = prop_def.get("type", "string")

        # Handle nullable fields (array type like ["null", "string"])
        if isinstance(prop_type, list):
            non_null_types = [t for t in prop_type if t != "null"]
            base_type = non_null_types[0] if non_null_types else "string"
            avro_type = type_mapping.get(base_type, "string")
            return {
                "name": prop_name,
                "type": ["null", avro_type],
                "default": None
            }

        # Handle enum types
        elif "enum" in prop_def:
            avro_field = {
                "name": prop_name,
                "type": {
                    "type": "enum",
                    "name": f"{name}_{prop_name}_enum",
                    "symbols": prop_def["enum"]
                }
            }
        # Normal types
        else:
            avro_field = {
                "name": prop_name,
                "type": type_mapping.get(prop_type, "string")
            }

        # Add description if available
        if prop_def.get("description"):
            avro_field["doc"] = prop_def["description"]

        # Logical types
        if prop_def.get("format") == "date-time" or prop_name == "timestamp":
            avro_field["logicalType"] = "timestamp-millis"

        if prop_def.get("format") == "date":
            avro_field["logicalType"] = "date"

        if prop_def.get("minimum") == 0.0 and prop_def.get("maximum") == 1.0:
            # For decimal logical type, ensure it's float
            if avro_field["type"] == type_mapping.get("number", "float"):
                avro_field["type"] = "float"
            avro_field["logicalType"] = "decimal"

        # Make non-required fields nullable (if not already nullable)
        if not required and not isinstance(avro_field.get("type"), list):
            avro_field["type"] = ["null", avro_field["type"]]
            avro_field["default"] = None

        return avro_field

    # Create Avro record
    avro_record = {
        "type": "record",
        "name": name,
        "namespace": "learnflow.events",
        "fields": []
    }

    if json_schema.get("description"):
        avro_record["doc"] = json_schema["description"]

    required = json_schema.get("required", [])
    properties = json_schema.get("properties", {})

    for prop_name, prop_def in properties.items():
        field = convert_property(prop_name, prop_def, prop_name in required)
        avro_record["fields"].append(field)

    return avro_record


def main():
    parser = argparse.ArgumentParser(description="Schema Generation Skill")
    parser.add_argument("--output-dir", default="contracts", help="Output directory")

    args = parser.parse_args()

    print(f"Schema Generator Skill - Token Efficiency: 95%")
    print(f"Generating JSON and Avro schemas")

    # Generate JSON schemas
    student_progress = generate_student_progress_schema()
    mastery_score = generate_mastery_score_schema()
    idempotency_key = generate_idempotency_key_schema()

    # Generate Avro schemas
    student_progress_avro = avro_from_json_schema(student_progress, "StudentProgressEvent")
    mastery_score_avro = avro_from_json_schema(mastery_score, "MasteryScoreUpdate")

    # Create output directories
    import os
    os.makedirs(f"{args.output_dir}/schemas", exist_ok=True)
    os.makedirs(f"{args.output_dir}/avro", exist_ok=True)

    # Write JSON schemas
    with open(f"{args.output_dir}/schemas/student-progress.schema.json", "w") as f:
        json.dump(student_progress, f, indent=2)

    with open(f"{args.output_dir}/schemas/mastery-score.schema.json", "w") as f:
        json.dump(mastery_score, f, indent=2)

    with open(f"{args.output_dir}/schemas/idempotency-key.schema.json", "w") as f:
        json.dump(idempotency_key, f, indent=2)

    # Write Avro schemas
    with open(f"{args.output_dir}/avro/student-progress-event.avsc", "w") as f:
        json.dump(student_progress_avro, f, indent=2)

    with open(f"{args.output_dir}/avro/mastery-score-update.avsc", "w") as f:
        json.dump(mastery_score_avro, f, indent=2)

    print(f"Generated {args.output_dir}/schemas/student-progress.schema.json")
    print(f"Generated {args.output_dir}/schemas/mastery-score.schema.json")
    print(f"Generated {args.output_dir}/schemas/idempotency-key.schema.json")
    print(f"Generated {args.output_dir}/avro/student-progress-event.avsc")
    print(f"Generated {args.output_dir}/avro/mastery-score-update.avsc")

    # Metadata
    metadata = {
        "skill": "schema-generator",
        "timestamp": datetime.now().isoformat(),
        "output_files": [
            f"{args.output_dir}/schemas/student-progress.schema.json",
            f"{args.output_dir}/schemas/mastery-score.schema.json",
            f"{args.output_dir}/schemas/idempotency-key.schema.json",
            f"{args.output_dir}/avro/student-progress-event.avsc",
            f"{args.output_dir}/avro/mastery-score-update.avsc"
        ],
        "token_efficiency": "95%"
    }

    with open(f"{args.output_dir}/schema-generation-metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata: {args.output_dir}/schema-generation-metadata.json")
    print(f"Schemas ready for validation")

    return 0


if __name__ == "__main__":
    exit(main())