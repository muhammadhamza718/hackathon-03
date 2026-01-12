---
name: docusaurus-deploy
description: Build and deploy Docusaurus documentation. Use for LearnFlow project documentation.
---

# Docusaurus Documentation Deployment

## When to Use

- User asks to deploy the project documentation site.
- Updating the documentation with new skill tutorials.

## Instructions

1. **Initialize Project:** If not present, run `npx create-docusaurus@latest docs classic`.
2. **Build Site:** Execute `./scripts/build.sh`.
3. **Deploy:** Execute `./scripts/deploy.sh <target_env>`.

## Validation

- [ ] Docusaurus build folder contains `index.html`.
- [ ] Site is accessible at the target URL.
