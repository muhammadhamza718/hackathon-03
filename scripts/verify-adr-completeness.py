#!/usr/bin/env python3
"""
ADR Completeness Verification Script
LearnFlow Milestone 1: Infrastructure & Common Schema

Validates ADR contains all required sections per constitution
"""

import argparse
import os
import sys

def check_adr_sections(file_path):
    """Check if ADR contains all required sections"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_sections = [
            "# ADR-",
            "## Context",
            "## Decision",
            "## Consequences",
            "## Validation"
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        # Check for numbered ADR (must be ADR-XXX)
        lines = content.split('\n')
        first_line = lines[0] if lines else ""
        if not first_line.startswith("# ADR-"):
            missing_sections.append("ADR numbering format")

        return len(missing_sections) == 0, missing_sections

    except Exception as e:
        return False, [str(e)]


def main():
    parser = argparse.ArgumentParser(description="ADR Completeness Validation")
    parser.add_argument("--adr", required=True, help="Path to ADR file")

    args = parser.parse_args()

    print("ADR Completeness Verification")
    print("=" * 50)

    if not os.path.exists(args.adr):
        print(f"ADR file not found: {args.adr}")
        return 1

    valid, missing = check_adr_sections(args.adr)

    if valid:
        print(f"PASS: {os.path.basename(args.adr)}")
        print("All required sections present")
        print("- Context: PASS")
        print("- Decision: PASS")
        print("- Consequences: PASS")
        print("- Validation: PASS")
        return 0
    else:
        print(f"FAIL: {os.path.basename(args.adr)}")
        print("Missing sections:")
        for section in missing:
            print(f"  - {section}")
        return 1


if __name__ == "__main__":
    sys.exit(main())