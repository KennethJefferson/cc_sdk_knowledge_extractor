---
name: quiz-generator
description: Generate quiz/exam content from validated files. Input is path to __cc_validated_files/ folder containing extracted text. Output is quiz markdown in __ccg_Exam/ folder. Generates multiple choice, short answer, and true/false questions. Use after content extraction pipeline completes to create assessment materials.
---

# Quiz Generator

Generate quiz/exam content from extracted course materials.

## Quick Start

```bash
# Generate quiz from validated files
python scripts/quiz_generate.py ./course/__cc_validated_files/

# Specify output directory
python scripts/quiz_generate.py ./validated -o ./output/__ccg_Exam/

# Control question counts
python scripts/quiz_generate.py ./validated --mc 20 --sa 10 --tf 10

# Generate specific topic quiz
python scripts/quiz_generate.py ./validated --topic "Chapter 3"
```

## Output Structure

```
__ccg_Exam/
├── quiz_full.md           # Complete quiz
├── quiz_mc.md             # Multiple choice only
├── quiz_sa.md             # Short answer only
├── quiz_tf.md             # True/false only
└── answer_key.md          # Answer key (separate file)
```

## Question Types

### Multiple Choice (MC)
```markdown
1. What is the primary function of X?

   a) Option A
   b) Option B
   c) Option C (correct)
   d) Option D
```

### Short Answer (SA)
```markdown
1. Explain the relationship between X and Y.

   _Expected answer: [2-3 sentences about relationship]_
```

### True/False (TF)
```markdown
1. Statement about concept X. (True/False)

   Answer: True
```

## CLI Reference

```
python scripts/quiz_generate.py INPUT_DIR [OPTIONS]

Arguments:
  INPUT_DIR             Path to __cc_validated_files/ folder

Options:
  -o, --output DIR      Output directory (default: ../__ccg_Exam/)
  --mc COUNT            Number of multiple choice questions (default: 15)
  --sa COUNT            Number of short answer questions (default: 5)
  --tf COUNT            Number of true/false questions (default: 10)
  --topic TOPIC         Filter to specific topic/chapter
  --difficulty LEVEL    easy|medium|hard (default: medium)
  --format FMT          Output format: markdown|json (default: markdown)
  --seed INT            Random seed for reproducibility
  -j, --json            Output results as JSON
```

## Content Analysis

The generator:
1. Reads all text files from validated folder
2. Extracts key concepts, definitions, relationships
3. Identifies factual statements for T/F questions
4. Creates distractor options for MC questions
5. Generates open-ended prompts for SA questions

## Integration

Typical pipeline:
```bash
# 1. Extract content from source files
python file_router.py source.pdf --json  # Routes to pdf skill

# 2. PDF skill extracts text to __cc_validated_files/
# (handled by pdf/docx/etc. skills)

# 3. Generate quiz from extracted content
python quiz_generate.py ./__cc_validated_files/ -o ./__ccg_Exam/
```

## Notes

- Requires sufficient content for meaningful questions
- Questions are generated based on extracted text patterns
- For best results, ensure validated files contain clean text
- Use --seed for reproducible quiz generation
