#!/usr/bin/env python3
"""
SOP Generator - Generate Standard Operating Procedures from course content.

Usage:
    python sop_generate.py <input_dir> -o <output_dir> [--json]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from datetime import datetime


def clean_text(text: str) -> str:
    """Clean up text by removing artifacts and normalizing whitespace."""
    text = text.replace("\\n", " ")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"_+([^_]+)_+", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_procedures(content: str, filename: str) -> list[dict[str, Any]]:
    """Extract procedural content from text."""
    procedures = []

    # Patterns that indicate procedural content
    step_patterns = [
        r"(?:step\s*\d+[:\.\)]\s*)(.+)",
        r"(?:first|second|third|then|next|finally)[,:\s]+(.+)",
        r"(?:\d+[:\.\)]\s*)(.+)",
        r"(?:to\s+\w+\s*,?\s*)(.+)",
    ]

    # Action verbs that start procedures
    action_verbs = [
        "click", "select", "open", "close", "create", "delete", "enter", "type",
        "navigate", "go to", "press", "run", "execute", "install", "configure",
        "set up", "download", "upload", "save", "load", "import", "export",
        "copy", "paste", "drag", "drop", "right-click", "double-click",
        "check", "uncheck", "enable", "disable", "start", "stop", "restart",
        "build", "compile", "deploy", "test", "verify", "confirm", "ensure",
        "add", "remove", "update", "modify", "edit", "change", "define",
        "initialize", "connect", "disconnect", "login", "logout", "authenticate"
    ]

    lines = content.split("\n")
    current_procedure = None
    steps = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts a new procedure (heading or strong statement)
        if re.match(r"^#{1,3}\s+", line) or re.match(r"^[A-Z][^.!?]*:$", line):
            if current_procedure and len(steps) >= 3:
                procedures.append({
                    "title": current_procedure,
                    "steps": steps,
                    "source": filename
                })
            current_procedure = re.sub(r"^#+\s*", "", line).strip(": ")
            steps = []
            continue

        # Check if line is a step
        clean_line = clean_text(line).lower()
        is_step = False

        # Check for numbered steps
        if re.match(r"^\d+[:\.\)]\s*", line):
            is_step = True
            line = re.sub(r"^\d+[:\.\)]\s*", "", line)

        # Check for action verbs
        for verb in action_verbs:
            if clean_line.startswith(verb) or f" {verb} " in clean_line:
                is_step = True
                break

        if is_step and len(line) > 10:
            steps.append(clean_text(line))

    # Don't forget last procedure
    if current_procedure and len(steps) >= 3:
        procedures.append({
            "title": current_procedure,
            "steps": steps,
            "source": filename
        })

    # If no structured procedures found, try to extract from general content
    if not procedures:
        # Look for imperative sentences
        imperative_steps = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            clean_line = clean_text(line).lower()
            for verb in action_verbs:
                if clean_line.startswith(verb):
                    imperative_steps.append(clean_text(line))
                    break

        if len(imperative_steps) >= 3:
            # Create a procedure from the filename
            title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
            procedures.append({
                "title": f"{title} Procedure",
                "steps": imperative_steps,
                "source": filename
            })

    return procedures


def extract_terms(content: str) -> dict[str, str]:
    """Extract terms and definitions from content."""
    terms = {}

    # Pattern: "Term: definition" or "Term - definition"
    patterns = [
        r"^([A-Z][a-zA-Z\s]+):\s+(.+)$",
        r"^([A-Z][a-zA-Z\s]+)\s+-\s+(.+)$",
        r"\*\*([^*]+)\*\*:\s+(.+)",
        r"\"([^\"]+)\"\s+(?:is|means|refers to)\s+(.+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for term, definition in matches:
            term = term.strip()
            definition = clean_text(definition)
            if len(term) > 2 and len(definition) > 10:
                terms[term] = definition

    return terms


def generate_sop_file(procedure: dict[str, Any], index: int) -> str:
    """Generate a single SOP markdown file."""
    title = procedure["title"]
    steps = procedure["steps"]
    source = procedure["source"]

    content = f"""# SOP: {title}

**Document ID:** SOP-{index:03d}
**Source:** {source}
**Generated:** {datetime.now().strftime("%Y-%m-%d")}

---

## Purpose

This procedure documents the steps required to {title.lower()}.

## Scope

This SOP applies to users who need to perform {title.lower()} operations.

## Prerequisites

- Access to required systems/tools
- Basic understanding of the domain
- Necessary permissions/credentials

---

## Procedure

"""

    for i, step in enumerate(steps, 1):
        content += f"""### Step {i}

{step}

"""

    content += """---

## Verification

Confirm that all steps have been completed successfully by:
- Reviewing the expected outcomes
- Testing the results
- Documenting any deviations

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Step fails | Prerequisites not met | Review prerequisites section |
| Unexpected result | Input error | Verify inputs and retry |
| Access denied | Permission issue | Contact administrator |

## Related Procedures

- See README.md for complete procedure index

---

*This SOP was auto-generated from course content. Review and validate before use in production.*
"""

    return content


def generate_quick_reference(procedures: list[dict[str, Any]]) -> str:
    """Generate a quick reference checklist."""
    content = """# Quick Reference Guide

Condensed checklists for all procedures. Use full SOPs for detailed instructions.

---

"""

    for i, proc in enumerate(procedures, 1):
        content += f"""## {proc['title']}

"""
        for j, step in enumerate(proc["steps"], 1):
            # Truncate long steps for quick reference
            short_step = step[:80] + "..." if len(step) > 80 else step
            content += f"- [ ] **Step {j}:** {short_step}\n"
        content += "\n---\n\n"

    return content


def generate_glossary(terms: dict[str, str]) -> str:
    """Generate a glossary file."""
    content = """# Glossary

Terms and definitions used throughout these procedures.

---

"""

    if not terms:
        content += "*No specific terms were extracted. Add terms manually as needed.*\n"
    else:
        for term in sorted(terms.keys()):
            content += f"**{term}**\n: {terms[term]}\n\n"

    return content


def generate_readme(procedures: list[dict[str, Any]], output_dir: str) -> str:
    """Generate the main README with navigation."""
    content = f"""# Standard Operating Procedures

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

This directory contains {len(procedures)} Standard Operating Procedures extracted from course content.

---

## Procedure Index

| ID | Procedure | Steps | Source |
|----|-----------|-------|--------|
"""

    for i, proc in enumerate(procedures, 1):
        safe_title = proc["title"].replace("|", "-")
        filename = f"SOP-{i:03d}_{proc['title'][:30].replace(' ', '_')}.md"
        content += f"| SOP-{i:03d} | [{safe_title}](procedures/{filename}) | {len(proc['steps'])} | {proc['source']} |\n"

    content += """

---

## Quick Links

- [Quick Reference](quick_reference.md) - Condensed checklists
- [Glossary](glossary.md) - Terms and definitions

## Usage

1. Browse the procedure index above
2. Click on a procedure to view detailed steps
3. Use quick reference for checklists during execution
4. Consult glossary for term definitions

## Notes

- These SOPs were auto-generated from course content
- Review and validate procedures before production use
- Update version numbers when making changes
- Maintain change history for audit purposes
"""

    return content


def main():
    parser = argparse.ArgumentParser(description="Generate SOPs from course content")
    parser.add_argument("input_dir", help="Directory containing validated files")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--min-steps", type=int, default=3, help="Minimum steps per procedure")

    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output)

    if not input_path.exists():
        result = {"success": False, "error": f"Input directory not found: {input_path}"}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Collect all text content
    all_procedures = []
    all_terms = {}

    extensions = {".txt", ".md", ".srt", ".vtt", ".py", ".js", ".ts", ".cpp", ".java", ".cs"}

    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Extract procedures
                procedures = extract_procedures(content, file_path.name)
                all_procedures.extend(procedures)

                # Extract terms
                terms = extract_terms(content)
                all_terms.update(terms)

            except Exception as e:
                continue

    if not all_procedures:
        result = {"success": False, "error": "No procedural content found in input files"}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Filter procedures by minimum steps
    all_procedures = [p for p in all_procedures if len(p["steps"]) >= args.min_steps]

    if not all_procedures:
        result = {"success": False, "error": f"No procedures with at least {args.min_steps} steps found"}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    procedures_dir = output_path / "procedures"
    procedures_dir.mkdir(exist_ok=True)

    # Generate individual SOP files
    generated_files = []
    for i, proc in enumerate(all_procedures, 1):
        sop_content = generate_sop_file(proc, i)
        safe_title = re.sub(r"[^\w\s-]", "", proc["title"])[:30].replace(" ", "_")
        filename = f"SOP-{i:03d}_{safe_title}.md"
        file_path = procedures_dir / filename
        file_path.write_text(sop_content, encoding="utf-8")
        generated_files.append(str(file_path))

    # Generate README
    readme_content = generate_readme(all_procedures, str(output_path))
    readme_path = output_path / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    generated_files.append(str(readme_path))

    # Generate quick reference
    quick_ref_content = generate_quick_reference(all_procedures)
    quick_ref_path = output_path / "quick_reference.md"
    quick_ref_path.write_text(quick_ref_content, encoding="utf-8")
    generated_files.append(str(quick_ref_path))

    # Generate glossary
    glossary_content = generate_glossary(all_terms)
    glossary_path = output_path / "glossary.md"
    glossary_path.write_text(glossary_content, encoding="utf-8")
    generated_files.append(str(glossary_path))

    result = {
        "success": True,
        "procedures_count": len(all_procedures),
        "terms_count": len(all_terms),
        "files_generated": generated_files,
        "output_directory": str(output_path)
    }

    if args.json:
        print(json.dumps(result))
    else:
        print(f"Generated {len(all_procedures)} SOPs in {output_path}")
        print(f"  - {len(generated_files)} files created")
        print(f"  - {len(all_terms)} terms in glossary")


if __name__ == "__main__":
    main()
