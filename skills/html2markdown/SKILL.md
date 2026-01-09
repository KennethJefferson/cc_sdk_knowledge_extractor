---
name: html2markdown
description: Convert HTML files to Markdown using pandoc. Use when processing HTML files for text extraction, converting web content to readable markdown, or batch converting HTML files in a course/project directory to markdown format for downstream processing.
---

# HTML to Markdown Conversion

Convert HTML files to clean Markdown using pandoc.

## Quick Start

### Single File
```bash
pandoc -f html -t markdown input.html -o output.md
```

### With Options
```bash
# Wrap lines at 80 characters
pandoc -f html -t markdown --wrap=auto --columns=80 input.html -o output.md

# No line wrapping (preserves original flow)
pandoc -f html -t markdown --wrap=none input.html -o output.md

# GitHub-flavored markdown
pandoc -f html -t gfm input.html -o output.md
```

## Batch Processing

Use `scripts/html2markdown.py` for batch conversion:

```bash
python scripts/html2markdown.py /path/to/root/directory
```

Options:
- `--output-dir`: Specify output directory (default: in-place with .md extension)
- `--flatten`: Flatten all output to single directory
- `--wrap`: Line wrapping mode (none, auto, preserve)

## Output Formats

| Format | Flag | Use Case |
|--------|------|----------|
| GitHub Flavored | `-t gfm` | **Recommended** - cleaner output |
| Standard Markdown | `-t markdown` | Pandoc extensions, may include div syntax |
| CommonMark | `-t commonmark` | Strict CommonMark |
| Plain text | `-t plain` | Text only, no formatting |

**Note:** Standard markdown (`-t markdown`) may include pandoc-specific syntax like `::: {role="main"}` div markers. Use `-t gfm` for cleaner, more portable output.

## Common Issues

### Malformed HTML
Pandoc handles most malformed HTML gracefully. For severely broken HTML, preprocess with:
```bash
tidy -q -ashtml input.html | pandoc -f html -t markdown -o output.md
```

### Character Encoding
Force UTF-8 encoding:
```bash
pandoc -f html -t markdown --metadata encoding=utf-8 input.html -o output.md
```

### Stripping Unwanted Elements
Pandoc converts everything. To strip scripts/styles before conversion:
```python
from bs4 import BeautifulSoup

with open('input.html', 'r') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
    tag.decompose()

clean_html = str(soup)
# Then pass clean_html to pandoc via stdin
```

## Integration with Preprocessing Pipeline

For course preprocessing workflows, the batch script outputs files suitable for concatenation into a single `*_output.txt` file with custom separators.
