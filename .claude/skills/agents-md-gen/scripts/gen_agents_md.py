#!/usr/bin/env python3
import os
import argparse
import json

def analyze_repo(path):
    tech_stack = []
    if os.path.exists(os.path.join(path, "package.json")):
        tech_stack.append("Node.js/JavaScript")
    if os.path.exists(os.path.join(path, "requirements.txt")):
        tech_stack.append("Python")
    if os.path.exists(os.path.join(path, "go.mod")):
        tech_stack.append("Go")
    
    structure = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and not item.startswith("."):
            structure.append(item)
            
    return {
        "tech_stack": tech_stack,
        "structure": structure
    }

def generate_agents_md(path, analysis):
    root_content = f"""# Project Agents Guide

## Project Snapshot
Tech Stack: {', '.join(analysis['tech_stack'])}
This repository uses a hierarchical AGENTS.md structure for optimal AI context.

## JIT Index
### Folder Structure
{chr(10).join([f'- {item}/ -> [see {item}/AGENTS.md]({item}/AGENTS.md)' for item in analysis['structure']])}

## Setup Commands
- Install: `npm install` or `pip install -r requirements.txt`
"""
    with open(os.path.join(path, "AGENTS.md"), "w") as f:
        f.write(root_content)
    print("✓ Generated root AGENTS.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    
    cwd = os.getcwd()
    analysis = analyze_repo(cwd)
    
    if args.analyze:
        print(json.dumps(analysis, indent=2))
    elif args.generate:
        generate_agents_md(cwd, analysis)
