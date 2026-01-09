#!/usr/bin/env python3
"""
Summary Generator - Generate structured documentation from course content.

Usage:
    python summary_generate.py INPUT_DIR [OPTIONS]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional


def clean_text(text: str) -> str:
    """Clean up text by removing artifacts and normalizing whitespace."""
    text = text.replace("\\n", " ")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\-\*]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"_+([^_]+)_+", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_content(input_dir: str) -> list[dict]:
    """Load all text content from validated files directory."""
    content = []
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    extensions = ["*.txt", "*.md", "*.srt", "*.csv"]
    for ext in extensions:
        for file_path in input_path.rglob(ext):
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                if text.strip():
                    content.append({
                        "source": str(file_path),
                        "filename": file_path.name,
                        "text": clean_text(text)
                    })
            except Exception:
                continue

    return content


def extract_topics(content: list[dict], max_topics: int = 20) -> list[dict]:
    """Extract main topics from content."""
    topics = []
    all_text = " ".join(item["text"] for item in content)

    # Extract sentences that look like topic definitions
    sentences = re.split(r"[.!?]+", all_text)

    topic_indicators = [
        r"^([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+(?:is|are|refers to|means|defines)",
        r"(?:The\s+)?([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:is defined as|represents|provides)",
        r"^([A-Z][a-z]+(?:\s+[a-z]+)*)\s*[-:]\s*",
    ]

    seen_topics = set()
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 500:
            continue

        for pattern in topic_indicators:
            match = re.search(pattern, sentence)
            if match:
                topic_name = match.group(1).strip()
                if topic_name.lower() not in seen_topics and len(topic_name) > 3:
                    seen_topics.add(topic_name.lower())
                    topics.append({
                        "name": topic_name,
                        "description": sentence,
                        "related_sentences": []
                    })
                    break

        if len(topics) >= max_topics:
            break

    # Find related sentences for each topic
    for topic in topics:
        topic_words = set(topic["name"].lower().split())
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            sentence_words = set(sentence.lower().split())
            if topic_words & sentence_words and sentence != topic["description"]:
                topic["related_sentences"].append(sentence)
                if len(topic["related_sentences"]) >= 5:
                    break

    return topics


def extract_definitions(content: list[dict]) -> list[dict]:
    """Extract key terms and definitions."""
    definitions = []
    all_text = " ".join(item["text"] for item in content)
    sentences = re.split(r"[.!?]+", all_text)

    definition_patterns = [
        r"([A-Z][a-z]+(?:\s+[a-z]+)*)\s+is defined as\s+(.+)",
        r"([A-Z][a-z]+(?:\s+[a-z]+)*)\s+refers to\s+(.+)",
        r"([A-Z][a-z]+(?:\s+[a-z]+)*)\s+means\s+(.+)",
        r"([A-Z][a-z]+(?:\s+[a-z]+)*)\s+is\s+(?:a|an|the)\s+(.+)",
    ]

    seen_terms = set()
    for sentence in sentences:
        sentence = sentence.strip()
        for pattern in definition_patterns:
            match = re.search(pattern, sentence)
            if match:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                if term.lower() not in seen_terms and len(definition) > 10:
                    seen_terms.add(term.lower())
                    definitions.append({
                        "term": term,
                        "definition": definition[:200]
                    })
                break

    return definitions[:30]  # Limit to 30 definitions


def extract_key_points(content: list[dict]) -> list[str]:
    """Extract key points and facts."""
    key_points = []
    all_text = " ".join(item["text"] for item in content)
    sentences = re.split(r"[.!?]+", all_text)

    importance_keywords = [
        "important", "key", "essential", "must", "should", "always",
        "never", "critical", "fundamental", "primary", "main"
    ]

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 30 or len(sentence) > 300:
            continue
        if any(kw in sentence.lower() for kw in importance_keywords):
            key_points.append(sentence)
            if len(key_points) >= 20:
                break

    return key_points


def generate_readme(
    course_name: str,
    topics: list[dict],
    definitions: list[dict],
    key_points: list[str],
    include_toc: bool = True
) -> str:
    """Generate the main README/overview document."""
    lines = [f"# {course_name} - Course Summary\n"]

    if include_toc and topics:
        lines.append("## Table of Contents\n")
        for i, topic in enumerate(topics, 1):
            safe_name = re.sub(r"[^a-z0-9]+", "-", topic["name"].lower())
            lines.append(f"{i}. [{topic['name']}](topics/topic_{i:02d}.md)")
        lines.append("")

    lines.append("## Overview\n")
    lines.append(f"This summary covers {len(topics)} main topics with {len(definitions)} key definitions.\n")

    if key_points:
        lines.append("## Key Points\n")
        for point in key_points[:10]:
            lines.append(f"- {point}")
        lines.append("")

    if topics:
        lines.append("## Topics Covered\n")
        for topic in topics:
            lines.append(f"### {topic['name']}\n")
            lines.append(f"{topic['description']}\n")

    return "\n".join(lines)


def generate_glossary(definitions: list[dict]) -> str:
    """Generate glossary document."""
    lines = ["# Glossary\n"]
    lines.append("Key terms and definitions from the course material.\n")

    sorted_defs = sorted(definitions, key=lambda x: x["term"].lower())
    current_letter = ""

    for defn in sorted_defs:
        first_letter = defn["term"][0].upper()
        if first_letter != current_letter:
            current_letter = first_letter
            lines.append(f"\n## {current_letter}\n")

        lines.append(f"**{defn['term']}**: {defn['definition']}\n")

    return "\n".join(lines)


def generate_topic_file(topic: dict, index: int) -> str:
    """Generate individual topic file."""
    lines = [f"# {topic['name']}\n"]
    lines.append(f"{topic['description']}\n")

    if topic["related_sentences"]:
        lines.append("## Details\n")
        for sentence in topic["related_sentences"]:
            lines.append(f"- {sentence}\n")

    lines.append(f"\n---\n*Topic {index}*")
    return "\n".join(lines)


def generate_quick_reference(
    topics: list[dict],
    definitions: list[dict],
    key_points: list[str]
) -> str:
    """Generate quick reference guide."""
    lines = ["# Quick Reference Guide\n"]

    lines.append("## Key Concepts\n")
    for topic in topics[:10]:
        lines.append(f"- **{topic['name']}**: {topic['description'][:100]}...")

    lines.append("\n## Important Terms\n")
    for defn in definitions[:10]:
        lines.append(f"- **{defn['term']}**: {defn['definition'][:80]}...")

    lines.append("\n## Remember\n")
    for point in key_points[:5]:
        lines.append(f"- {point}")

    return "\n".join(lines)


def generate_study_guide(
    course_name: str,
    topics: list[dict],
    definitions: list[dict],
    key_points: list[str]
) -> str:
    """Generate comprehensive study guide."""
    lines = [f"# {course_name} - Study Guide\n"]

    lines.append("## Introduction\n")
    lines.append("This study guide provides a comprehensive overview of the course material.\n")

    lines.append("## Main Topics\n")
    for i, topic in enumerate(topics, 1):
        lines.append(f"### {i}. {topic['name']}\n")
        lines.append(f"{topic['description']}\n")
        if topic["related_sentences"]:
            lines.append("**Key Points:**")
            for sent in topic["related_sentences"][:3]:
                lines.append(f"- {sent}")
            lines.append("")

    lines.append("## Key Definitions\n")
    for defn in definitions[:15]:
        lines.append(f"- **{defn['term']}**: {defn['definition']}")
    lines.append("")

    lines.append("## Important Facts\n")
    for point in key_points:
        lines.append(f"- {point}")

    return "\n".join(lines)


def generate_summary(
    input_dir: str,
    output_dir: str,
    format_type: str = "detailed",
    include_toc: bool = True,
    max_topics: int = 20,
) -> dict:
    """Generate summary documentation from content directory."""
    try:
        content = load_content(input_dir)
    except FileNotFoundError as e:
        return {"error": str(e)}

    if not content:
        return {"error": "No content found in input directory"}

    # Extract information
    topics = extract_topics(content, max_topics)
    definitions = extract_definitions(content)
    key_points = extract_key_points(content)

    if len(topics) < 2 and len(definitions) < 3:
        return {
            "error": f"Insufficient content for summary. Found {len(topics)} topics and {len(definitions)} definitions.",
            "topics_found": len(topics),
            "definitions_found": len(definitions)
        }

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    topics_path = out_path / "topics"
    topics_path.mkdir(exist_ok=True)

    # Derive course name from input directory
    course_name = Path(input_dir).parent.name
    if course_name in ["CODE", "__cc_validated_files"]:
        course_name = Path(input_dir).parent.parent.name

    files_created = []

    # Generate README
    readme = generate_readme(course_name, topics, definitions, key_points, include_toc)
    (out_path / "README.md").write_text(readme, encoding="utf-8")
    files_created.append("README.md")

    # Generate glossary
    if definitions:
        glossary = generate_glossary(definitions)
        (out_path / "glossary.md").write_text(glossary, encoding="utf-8")
        files_created.append("glossary.md")

    # Generate topic files
    for i, topic in enumerate(topics, 1):
        topic_content = generate_topic_file(topic, i)
        topic_file = topics_path / f"topic_{i:02d}.md"
        topic_file.write_text(topic_content, encoding="utf-8")
        files_created.append(f"topics/topic_{i:02d}.md")

    # Generate quick reference
    quick_ref = generate_quick_reference(topics, definitions, key_points)
    (out_path / "quick_reference.md").write_text(quick_ref, encoding="utf-8")
    files_created.append("quick_reference.md")

    # Generate study guide
    study_guide = generate_study_guide(course_name, topics, definitions, key_points)
    (out_path / "study_guide.md").write_text(study_guide, encoding="utf-8")
    files_created.append("study_guide.md")

    return {
        "status": "success",
        "input_dir": str(Path(input_dir).absolute()),
        "output_dir": str(out_path.absolute()),
        "course_name": course_name,
        "content_files_processed": len(content),
        "topics_extracted": len(topics),
        "definitions_extracted": len(definitions),
        "key_points_extracted": len(key_points),
        "files_created": files_created,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Summary Generator - Generate documentation from course content"
    )
    parser.add_argument("input_dir", nargs="?", help="Path to __cc_validated_files/ folder")
    parser.add_argument("-o", "--output", help="Output directory (default: ../__ccg_Summary/)")
    parser.add_argument(
        "--format", choices=["overview", "detailed", "quick"],
        default="detailed", help="Output format"
    )
    parser.add_argument("--toc", action="store_true", help="Include table of contents")
    parser.add_argument(
        "--max-topics", type=int, default=20,
        help="Maximum number of topics to extract"
    )
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.input_dir:
        parser.print_help()
        return 1

    input_path = Path(args.input_dir)
    if args.output:
        output_dir = args.output
    else:
        output_dir = str(input_path.parent / "__ccg_Summary")

    result = generate_summary(
        args.input_dir,
        output_dir,
        format_type=args.format,
        include_toc=args.toc,
        max_topics=args.max_topics,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        print(f"Summary generated successfully!")
        print(f"  Course: {result['course_name']}")
        print(f"  Input: {result['input_dir']}")
        print(f"  Output: {result['output_dir']}")
        print(f"  Topics: {result['topics_extracted']}")
        print(f"  Definitions: {result['definitions_extracted']}")
        print(f"  Files created: {len(result['files_created'])}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
