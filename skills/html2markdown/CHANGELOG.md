# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-07

### Added
- Initial release of html2markdown skill
- SKILL.md with core conversion instructions
- Batch processing script (`scripts/html2markdown.py`)
  - Recursive HTML/HTM file discovery
  - Multiple output formats: markdown, gfm, commonmark
  - `--output-dir` option for custom output location (defaults to same directory as input)
  - `--flatten` option to flatten directory structure
  - `--wrap` option for line wrapping control (none, auto, preserve)
  - `--exclude` option for glob pattern exclusion
  - `--strip-elements` option to remove script, style, nav, header, footer elements
- README.md with overview and quick start
- Usage.md with detailed usage instructions and examples
- Support for beautifulsoup4 integration for HTML preprocessing
