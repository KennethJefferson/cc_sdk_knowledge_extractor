# html2markdown

A skill for converting HTML files to Markdown using pandoc.

## Overview

This skill provides tools for converting HTML files to clean Markdown format, suitable for preprocessing pipelines where HTML content needs to be extracted as readable text.

## Requirements

- Python 3.10+
- pandoc
- beautifulsoup4 (optional, for element stripping)

## Installation

```bash
# Install pandoc (Ubuntu/Debian)
sudo apt-get install pandoc

# Install optional Python dependency
pip install beautifulsoup4
```

## Quick Start

### Single File
```bash
pandoc -f html -t gfm input.html -o output.md
```

### Batch Processing
```bash
python scripts/html2markdown.py /path/to/directory
```

## Features

- Single file and batch conversion
- Multiple output formats (GFM, CommonMark, plain text)
- Optional stripping of script, style, nav, header, footer elements
- Preserves directory structure or flattens output
- Handles malformed HTML gracefully

## Documentation

- [Usage Guide](Usage.md) — Detailed usage instructions and examples
- [Changelog](CHANGELOG.md) — Version history and changes

## License

See LICENSE for details.
