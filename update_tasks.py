#!/usr/bin/env python3
"""
Update tasks.md to mark completed tasks
"""

import re
import os

def update_tasks_file():
    tasks_file = "specs/001-learnflow-architecture/tasks.md"

    # Read the current file
    with open(tasks_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Tasks to mark as [x] (completed)
    # Based on our work and previous verification results

    tasks_to_complete = [
        # Phase 1 - we created routes.py and modularized
        "**[1.6]** Create main API routes (POST /api/v1/triage)",
        "**[1.10]** Create health and metrics endpoints",
        "**[1.14]** Create router performance tests",

        # Phase 2 - we verified these exist
        "**[2.6]** Connect routing logic to API routes",
        "**[2.10]** Create Dapr integration test suite",
        "**[2.11]** Create circuit breaker chaos tests",
        "**[2.12]** Create network failure simulation tests",
        "**[2.13]** Create retry logic verification tests",

        # Phase 3 - we created these security tests
        "**[3.13]** Create JWT validation test suite",
        "**[3.14]** Create injection attack prevention tests",
        "**[3.15]** Create end-to-end security flow test"
    ]

    # Mark as complete
    for task in tasks_to_complete:
        # Find the line and replace [ ] with [x]
        pattern = r'(- \[ \]' + re.escape(task[4:]) + r')'  # Skip "- [ ] **["
        replacement = r'- [x]' + task[4:]

        if task.startswith("**[1.") or task.startswith("**[2.") or task.startswith("**[3."):
            # Find the specific pattern
            original = r'- \[ \]\*\*\[' + task.split('[')[1].split(']')[0] + r'\]\*\*' + re.escape(task.split(']')[1])
            replacement = r'- [x]**[' + task.split('[')[1].split(']')[0] + r']**' + task.split(']')[1]

        # Try to find and replace
        old_pattern = r'- \[ \]' + re.escape(task)
        new_pattern = r'- [x]' + task

        content = content.replace(old_pattern, new_pattern)

    # Write updated content
    with open(tasks_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("tasks.md updated with completed tasks")

if __name__ == "__main__":
    update_tasks_file()