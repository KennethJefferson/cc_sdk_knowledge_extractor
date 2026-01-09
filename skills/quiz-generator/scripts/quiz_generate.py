#!/usr/bin/env python3
"""
Quiz Generator - Generate quizzes from extracted course content.

Usage:
    python quiz_generate.py INPUT_DIR [OPTIONS]
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Optional


def load_content(input_dir: str) -> list[dict]:
    """Load all text content from validated files directory."""
    content = []
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Load text files
    for text_file in input_path.rglob("*.txt"):
        try:
            text = text_file.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                content.append({"source": str(text_file), "text": text})
        except Exception:
            continue

    # Load markdown files
    for md_file in input_path.rglob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                content.append({"source": str(md_file), "text": text})
        except Exception:
            continue

    # Load SRT files (subtitle transcripts)
    for srt_file in input_path.rglob("*.srt"):
        try:
            text = srt_file.read_text(encoding="utf-8", errors="replace")
            # Clean SRT format - remove timestamps and numbers
            lines = []
            for line in text.split("\n"):
                line = line.strip()
                # Skip timestamp lines and sequence numbers
                if re.match(r"^\d+$", line):
                    continue
                if re.match(r"^\d{2}:\d{2}:\d{2}", line):
                    continue
                if line:
                    lines.append(line)
            cleaned_text = " ".join(lines)
            if cleaned_text.strip():
                content.append({"source": str(srt_file), "text": cleaned_text})
        except Exception:
            continue

    # Load CSV files (extract text content)
    for csv_file in input_path.rglob("*.csv"):
        try:
            text = csv_file.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                content.append({"source": str(csv_file), "text": text})
        except Exception:
            continue

    return content


def clean_text(text: str) -> str:
    """Clean up text by removing artifacts and normalizing whitespace."""
    # Replace literal \n with spaces
    text = text.replace("\\n", " ")
    # Remove markdown headers
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove markdown bullets
    text = re.sub(r"^[\-\*]\s*", "", text, flags=re.MULTILINE)
    # Remove markdown emphasis
    text = re.sub(r"\*+([^*]+)\*+", r"\1", text)
    text = re.sub(r"_+([^_]+)_+", r"\1", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_concepts(content: list[dict]) -> list[dict]:
    """Extract key concepts and facts from content."""
    concepts = []

    for item in content:
        text = clean_text(item["text"])

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 500:
                continue

            # Heuristics for "important" sentences
            importance_keywords = [
                "is defined as",
                "refers to",
                "means",
                "important",
                "key",
                "primary",
                "main",
                "must",
                "should",
                "always",
                "never",
                "the purpose of",
                "is used to",
                "allows",
                "enables",
                "provides",
                "consists of",
                "includes",
                "represents",
            ]

            is_important = any(kw in sentence.lower() for kw in importance_keywords)

            # Check if starts with capital (likely a statement)
            starts_with_capital = bool(
                re.match(r"^[A-Z]", sentence)
                and not sentence.startswith(("The ", "A ", "An ", "This ", "That "))
            )

            if is_important:
                concepts.append(
                    {"text": sentence, "source": item["source"], "type": "definition"}
                )
            elif starts_with_capital and len(sentence) > 30:
                concepts.append(
                    {"text": sentence, "source": item["source"], "type": "fact"}
                )
            elif len(sentence) > 50 and any(
                word in sentence.lower()
                for word in ["because", "therefore", "however", "while", "when"]
            ):
                concepts.append(
                    {"text": sentence, "source": item["source"], "type": "explanation"}
                )

    return concepts


def generate_mc_question(concept: dict, all_concepts: list[dict]) -> Optional[dict]:
    """Generate a multiple choice question from a concept."""
    text = concept["text"]

    # Need at least 4 concepts for distractors
    if len(all_concepts) < 4:
        return None

    # Create question from statement
    question_templates = [
        f"Which statement best describes: {text[:60]}...?",
        f"What is true about: {text[:60]}...?",
        f"Complete the following: {text[:40]}...",
    ]

    question = random.choice(question_templates)
    correct = text

    # Get distractors from other concepts
    other_concepts = [c["text"] for c in all_concepts if c["text"] != text]
    if len(other_concepts) < 3:
        return None

    distractors = random.sample(other_concepts, min(3, len(other_concepts)))

    options = [correct] + distractors[:3]
    random.shuffle(options)
    correct_index = options.index(correct)

    return {
        "type": "mc",
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "correct_letter": chr(ord("a") + correct_index),
    }


def generate_tf_question(concept: dict) -> dict:
    """Generate a true/false question from a concept."""
    text = concept["text"]

    # 50% chance of making it false by simple transformation
    is_true = random.choice([True, False])

    if is_true:
        statement = text
    else:
        # Simple negation strategies
        negation_patterns = [
            (" is ", " is not "),
            (" are ", " are not "),
            (" can ", " cannot "),
            (" will ", " will not "),
            (" has ", " does not have "),
            (" have ", " do not have "),
            ("always", "never"),
            ("must", "should not"),
        ]

        statement = text
        for old, new in negation_patterns:
            if old in statement.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                statement = pattern.sub(new, statement, count=1)
                break
        else:
            # Fallback: prepend negation
            statement = f"It is incorrect that {text[0].lower()}{text[1:]}"

    return {
        "type": "tf",
        "statement": statement,
        "answer": is_true,
    }


def generate_sa_question(concept: dict) -> dict:
    """Generate a short answer question from a concept."""
    text = concept["text"]

    prompts = [
        f"Explain: {text[:50]}...",
        f"Describe in your own words: {text[:50]}...",
        f"What is the significance of: {text[:50]}...",
        f"How would you explain: {text[:50]}...?",
    ]

    return {
        "type": "sa",
        "question": random.choice(prompts),
        "expected_answer": text,
    }


def format_quiz_markdown(
    questions: list[dict], include_answers: bool = False, title: str = "Quiz"
) -> str:
    """Format questions as markdown."""
    lines = [f"# {title}\n"]

    mc_questions = [q for q in questions if q["type"] == "mc"]
    tf_questions = [q for q in questions if q["type"] == "tf"]
    sa_questions = [q for q in questions if q["type"] == "sa"]

    if mc_questions:
        lines.append("\n## Multiple Choice\n")
        for i, q in enumerate(mc_questions, 1):
            lines.append(f"**{i}.** {q['question']}\n")
            for j, opt in enumerate(q["options"]):
                letter = chr(ord("a") + j)
                # Truncate long options
                opt_text = opt[:150] + "..." if len(opt) > 150 else opt
                lines.append(f"   {letter}) {opt_text}")
            lines.append("")
            if include_answers:
                lines.append(f"   **Answer: {q['correct_letter']}**\n")

    if tf_questions:
        lines.append("\n## True/False\n")
        for i, q in enumerate(tf_questions, 1):
            statement = q["statement"][:200] + "..." if len(q["statement"]) > 200 else q["statement"]
            lines.append(f"**{i}.** {statement}")
            lines.append("")
            if include_answers:
                lines.append(f"   **Answer: {'True' if q['answer'] else 'False'}**\n")

    if sa_questions:
        lines.append("\n## Short Answer\n")
        for i, q in enumerate(sa_questions, 1):
            lines.append(f"**{i}.** {q['question']}")
            lines.append("")
            if include_answers:
                answer = q["expected_answer"][:200] + "..." if len(q["expected_answer"]) > 200 else q["expected_answer"]
                lines.append(f"   *Expected: {answer}*\n")

    return "\n".join(lines)


def generate_quiz(
    input_dir: str,
    output_dir: str,
    mc_count: int = 15,
    sa_count: int = 5,
    tf_count: int = 10,
    seed: Optional[int] = None,
) -> dict:
    """Generate quiz from content directory."""
    if seed is not None:
        random.seed(seed)

    # Load and analyze content
    try:
        content = load_content(input_dir)
    except FileNotFoundError as e:
        return {"error": str(e)}

    if not content:
        return {"error": "No content found in input directory"}

    concepts = extract_concepts(content)
    if len(concepts) < 10:
        return {
            "error": f"Insufficient concepts extracted ({len(concepts)}). Need at least 10.",
            "concepts_found": len(concepts),
        }

    random.shuffle(concepts)

    # Generate questions
    questions = []

    # Multiple choice
    mc_generated = 0
    for concept in concepts:
        if mc_generated >= mc_count:
            break
        q = generate_mc_question(concept, concepts)
        if q:
            questions.append(q)
            mc_generated += 1

    # True/False
    tf_start = mc_count
    for i, concept in enumerate(concepts[tf_start : tf_start + tf_count * 2]):
        if len([x for x in questions if x["type"] == "tf"]) >= tf_count:
            break
        questions.append(generate_tf_question(concept))

    # Short Answer
    sa_start = tf_start + tf_count
    for i, concept in enumerate(concepts[sa_start : sa_start + sa_count]):
        questions.append(generate_sa_question(concept))

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Write quiz files
    quiz_content = format_quiz_markdown(questions, include_answers=False, title="Quiz")
    (out_path / "quiz_full.md").write_text(quiz_content, encoding="utf-8")

    answer_key = format_quiz_markdown(questions, include_answers=True, title="Answer Key")
    (out_path / "answer_key.md").write_text(answer_key, encoding="utf-8")

    # Write separate files by type
    mc_only = [q for q in questions if q["type"] == "mc"]
    if mc_only:
        mc_content = format_quiz_markdown(mc_only, include_answers=False, title="Multiple Choice")
        (out_path / "quiz_mc.md").write_text(mc_content, encoding="utf-8")

    tf_only = [q for q in questions if q["type"] == "tf"]
    if tf_only:
        tf_content = format_quiz_markdown(tf_only, include_answers=False, title="True/False")
        (out_path / "quiz_tf.md").write_text(tf_content, encoding="utf-8")

    sa_only = [q for q in questions if q["type"] == "sa"]
    if sa_only:
        sa_content = format_quiz_markdown(sa_only, include_answers=False, title="Short Answer")
        (out_path / "quiz_sa.md").write_text(sa_content, encoding="utf-8")

    return {
        "status": "success",
        "input_dir": str(Path(input_dir).absolute()),
        "output_dir": str(out_path.absolute()),
        "content_files_processed": len(content),
        "concepts_extracted": len(concepts),
        "question_counts": {
            "mc": len([q for q in questions if q["type"] == "mc"]),
            "tf": len([q for q in questions if q["type"] == "tf"]),
            "sa": len([q for q in questions if q["type"] == "sa"]),
            "total": len(questions),
        },
        "files_created": [
            "quiz_full.md",
            "answer_key.md",
            "quiz_mc.md",
            "quiz_tf.md",
            "quiz_sa.md",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Quiz Generator - Generate quizzes from extracted course content"
    )
    parser.add_argument("input_dir", nargs="?", help="Path to __cc_validated_files/ folder")
    parser.add_argument("-o", "--output", help="Output directory (default: ../__ccg_Exam/)")
    parser.add_argument(
        "--mc", type=int, default=15, help="Number of multiple choice questions"
    )
    parser.add_argument(
        "--sa", type=int, default=5, help="Number of short answer questions"
    )
    parser.add_argument(
        "--tf", type=int, default=10, help="Number of true/false questions"
    )
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.input_dir:
        parser.print_help()
        return 1

    # Default output directory
    input_path = Path(args.input_dir)
    if args.output:
        output_dir = args.output
    else:
        output_dir = str(input_path.parent / "__ccg_Exam")

    result = generate_quiz(
        args.input_dir,
        output_dir,
        mc_count=args.mc,
        sa_count=args.sa,
        tf_count=args.tf,
        seed=args.seed,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        print(f"Quiz generated successfully!")
        print(f"  Input: {result['input_dir']}")
        print(f"  Output: {result['output_dir']}")
        print(f"  Content files: {result['content_files_processed']}")
        print(f"  Concepts extracted: {result['concepts_extracted']}")
        print(f"  Questions generated:")
        counts = result["question_counts"]
        print(f"    Multiple Choice: {counts['mc']}")
        print(f"    True/False: {counts['tf']}")
        print(f"    Short Answer: {counts['sa']}")
        print(f"    Total: {counts['total']}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
