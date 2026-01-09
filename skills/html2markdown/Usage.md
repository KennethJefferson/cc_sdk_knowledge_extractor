# Usage Guide

## Command Line (pandoc directly)

### Basic Conversion
```bash
pandoc -f html -t gfm input.html -o output.md
```

### With Line Wrapping
```bash
# Wrap at 80 characters
pandoc -f html -t gfm --wrap=auto --columns=80 input.html -o output.md

# No wrapping (default)
pandoc -f html -t gfm --wrap=none input.html -o output.md
```

## Batch Processing Script

### Basic Usage
```bash
python scripts/html2markdown.py /path/to/directory
```

This converts all `.html` and `.htm` files in the directory (recursively), placing `.md` files alongside the source files.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir DIR` | Output directory | Same as input file |
| `--flatten` | Flatten output to single directory | Off |
| `--wrap MODE` | Line wrap: none, auto, preserve | none |
| `--format FMT` | Output: markdown, gfm, commonmark | markdown |
| `--exclude PATTERN` | Glob pattern to exclude | None |
| `--strip-elements` | Remove script, style, nav, header, footer | Off |

### Examples

#### Convert to separate output directory
```bash
python scripts/html2markdown.py ./course --output-dir ./course_markdown
```

#### Flatten all files to single directory
```bash
python scripts/html2markdown.py ./course --output-dir ./output --flatten
```

#### Use GitHub-Flavored Markdown (recommended)
```bash
python scripts/html2markdown.py ./course --format gfm
```

#### Strip navigation and boilerplate
```bash
python scripts/html2markdown.py ./course --strip-elements --format gfm
```

#### Exclude certain patterns
```bash
python scripts/html2markdown.py ./course --exclude "**/node_modules/**" --exclude "**/vendor/**"
```

#### Full example with all options
```bash
python scripts/html2markdown.py ./course \
    --output-dir ./processed \
    --format gfm \
    --strip-elements \
    --wrap none \
    --exclude "**/templates/**"
```

## Output Formats

| Format | Flag | Notes |
|--------|------|-------|
| GitHub Flavored | `gfm` | **Recommended** — Clean, portable output |
| Standard Markdown | `markdown` | May include pandoc-specific div syntax |
| CommonMark | `commonmark` | Strict CommonMark compliance |
| Plain text | `plain` | Text only, no formatting |

## Integration with Preprocessing Pipeline

For course preprocessing workflows, convert HTML files first, then concatenate the resulting markdown files:

```bash
# Convert all HTML to markdown
python scripts/html2markdown.py ./course --format gfm --strip-elements

# Concatenate with separator (example)
find ./course -name "*.md" -exec sh -c 'echo "===================="; echo "FILE: {}"; echo "===================="; cat {}' \; > course_output.txt
```

## Troubleshooting

### Malformed HTML
Pandoc handles most issues. For severely broken HTML:
```bash
tidy -q -ashtml input.html | pandoc -f html -t gfm -o output.md
```

### Character Encoding Issues
```bash
pandoc -f html -t gfm --metadata encoding=utf-8 input.html -o output.md
```

### Missing beautifulsoup4
If using `--strip-elements` without beautifulsoup4 installed:
```bash
pip install beautifulsoup4
```
