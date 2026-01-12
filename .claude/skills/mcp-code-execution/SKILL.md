---
name: mcp-code-execution
description: Pattern for efficient AI interaction using scripts instead of tool contexts. Use to optimize token usage in complex tasks.
---

# MCP Code Execution Pattern

## When to Use

- You need to process large amounts of data (e.g., K8s logs, CSVs, Large files).
- You want to reduce token usage by 80-98%.

## Instructions

1. **Identify the Task:** If the task involves heavy data processing, DO NOT use direct tool calls.
2. **Write a Script:** Create a Python or Bash script in the `scripts/` directory of the current skill.
3. **Execute and Report:** Run the script and only report the final success/failure or a minimal summary to the context.

## Example

Instead of `kubectl get pods -A` (huge output), run a script that counts pods and returns: `"✓ All 15 pods are Running."`

See [REFERENCE.md](./REFERENCE.md) for deeper strategy on script-based filtering.
