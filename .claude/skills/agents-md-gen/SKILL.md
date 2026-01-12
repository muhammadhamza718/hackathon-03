---
name: agents-md-gen
description: Generate hierarchical AGENTS.md structures for codebases. Use when user asks to create AGENTS.md files or analyze codebase for AI agent documentation.
---

# AGENTS.md Generator

## When to Use

- User asks to create or update `AGENTS.md` files.
- Setting up AI-friendly project documentation for a new or existing repository.

## Instructions

1. **Analyze Repository**: Run `python3 scripts/gen_agents_md.py --analyze`.
2. **Generate Files**: Once the analysis is confirmed, run `python3 scripts/gen_agents_md.py --generate`.

## Validation

- [ ] Root `AGENTS.md` is present and contains JIT index hints.
- [ ] Major sub-folders (apps, services) have their own `AGENTS.md` if applicable.

See [REFERENCE.md](./REFERENCE.md) for hierarchical documentation principles.
