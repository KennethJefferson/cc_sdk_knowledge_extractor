---
name: summary-generator
description: Generate structured documentation and summaries from validated course files. Creates comprehensive study guides, topic overviews, and reference documentation. Input is path to __cc_validated_files/ folder. Output is markdown documentation in __ccg_Summary/ folder.
---

# Summary Generator

Generate structured documentation from extracted course materials.

## Quick Start

```bash
# Generate summary from validated files
python scripts/summary_generate.py ./course/__cc_validated_files/

# Specify output directory
python scripts/summary_generate.py ./validated -o ./output/__ccg_Summary/

# Control output format
python scripts/summary_generate.py ./validated --format detailed

# Include table of contents
python scripts/summary_generate.py ./validated --toc
```

## Output Structure

```
__ccg_Summary/
├── README.md              # Course overview and navigation
├── topics/
│   ├── topic_01.md        # Individual topic summaries
│   ├── topic_02.md
│   └── ...
├── glossary.md            # Key terms and definitions
├── quick_reference.md     # Condensed reference guide
└── study_guide.md         # Combined study material
```

## Output Formats

### Overview (default)
- Course introduction
- Main topics list
- Key concepts summary

### Detailed
- Full topic breakdowns
- Examples and explanations
- Cross-references between topics

### Quick Reference
- Bullet point summaries
- Essential facts only
- Optimized for quick lookup

## CLI Reference

```
python scripts/summary_generate.py INPUT_DIR [OPTIONS]

Arguments:
  INPUT_DIR             Path to __cc_validated_files/ folder

Options:
  -o, --output DIR      Output directory (default: ../__ccg_Summary/)
  --format FMT          Output format: overview|detailed|quick (default: detailed)
  --toc                 Include table of contents
  --max-topics N        Maximum number of topics to extract (default: 20)
  --min-content N       Minimum content length per topic (default: 100)
  -j, --json            Output results as JSON
```

## Content Analysis

The generator:
1. Reads all text files from validated folder
2. Identifies main topics and themes
3. Extracts key definitions and concepts
4. Organizes content hierarchically
5. Generates structured markdown documentation

## Integration

Invoke with -ccg flag:
```bash
ccke -i ./courses -ccg Summary
```
