# Format Selection Guide

Choosing the right output format for LLM synthesis workflows.

## Format Comparison

### CSV
**Tokens:** Low (no structural overhead)
**Best when:**
- Processing with pandas/code before LLM
- Data will be summarized programmatically
- Need Excel/spreadsheet compatibility

**LLM consideration:** Raw CSV in prompts wastes tokens on commas/quotes. Pre-process to markdown or summarize first.

### JSON
**Tokens:** Medium (keys repeated per row)
**Best when:**
- Data has nested structures
- Will be processed programmatically
- Need type preservation (numbers vs strings)

**LLM consideration:** Good for structured extraction tasks. Include schema separately to avoid redundant key names.

### Markdown
**Tokens:** Medium (table formatting)
**Best when:**
- Direct inclusion in LLM context
- Human review needed
- Data is tabular and readable

**LLM consideration:** Most natural for LLM comprehension. Use `--max-rows` to limit context size.

## Token Optimization Tips

1. **Extract schema separately** (`--schema`) - describe structure once, not per-row
2. **Filter tables** (`--tables`) - only extract what's needed
3. **Limit rows** (`--max-rows`) - sample data often sufficient for synthesis
4. **Summarize first** - for large tables, summarize with code before LLM processing

## Recommended Workflow for Course Synthesis

```bash
# Step 1: Extract with schema
python scripts/db_extract.py course.db -f markdown --schema -o ./extracted

# Step 2: Review _schema.md to understand structure

# Step 3: Include relevant .md files in LLM context for synthesis
```
