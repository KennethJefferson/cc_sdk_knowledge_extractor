# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Multi-generator support** - Run multiple generators in one command
  - Comma-separated types: `-ccg Exam,Project,SOP`
  - `all` shorthand: `-ccg all` runs all generators
  - Each generator outputs to its own `__ccg_{Type}/` directory

- **GitHub sync** - Auto-push generated assets to GitHub repositories
  - New CLI flag: `--github-sync=true|false`
  - Creates one repository per generated asset
  - Repository naming: `ccg_{Type}_{SynthesizedName}`
  - Auto-generates .gitignore based on detected tech stack
  - Pushes new commit if repository already exists
  - Continues with warning on sync failure
  - Summary of sync results at end of run

- `project-maker` skill - Synthesize complete projects from course transcripts
  - Activation phrases: `Project`, `project`, `make`, `synthesize`
  - Discovers teachable projects from transcript content
  - Generates full project scaffolding with README, source files
  - Stopwords filter prevents duplicate words in project names

- `ccg-github-sync` skill - Push generated assets to GitHub
  - Invoked automatically when `--github-sync=true`
  - Supports Rust, Python, JavaScript, Go, Java, C# .gitignore templates
  - Uses `gh` CLI for repository operations

- `sop-generator` skill - Generate Standard Operating Procedures from course content
  - Activation phrases: `SOP`, `sop`, `procedure`, `procedures`, `standard-operating-procedure`
  - Outputs: README index, individual SOP files, quick reference checklists, glossary
  - Extracts procedures using action verbs and step patterns
  - Standard SOP format with purpose, scope, prerequisites, steps, verification

## [0.1.0] - 2026-01-09

### Added

- Initial release of CCKnowledgeExtractor CLI
- Multi-course batch processing with automatic course detection
- Parallel worker pools for scanning (`-sw`) and processing (`-w`)
- File routing by magic bytes with extension fallback
- Content generators:
  - `quiz-generator` - Multiple choice, short answer, true/false questions
  - `summary-generator` - README, glossary, study guide, topic files
- File processors:
  - Text passthrough (.txt, .md, .srt, .vtt)
  - Code passthrough (.py, .js, .ts, .cpp, .java, etc.)
  - PDF extraction via pdfplumber
  - DOCX/PPTX/XLSX extraction
  - Image OCR via pytesseract
  - Archive extraction via 7-Zip
  - HTML to Markdown via Pandoc
  - SQLite database extraction
- CLI options:
  - `-i, --input` - Input directory (required)
  - `-ccg, --ClaudeCodeGenerated` - Content type (required)
  - `-sw, --scanningworkers` - Scanning parallelism
  - `-w, --workers` - Processing parallelism
  - `-o, --output` - Output directory override
  - `-v, --verbose` - Debug output
  - `--dry-run` - Preview mode
  - `--init-config` - Generate sample config
- Configuration file support (`.cckrc.json`, `.cckrc`, `ccke.config.json`)
- Progress visualization with animated spinners and progress bars
- Dated error logs in course CODE directories
- TypeScript strict mode with comprehensive type definitions

### Technical

- Built with Bun runtime and TypeScript
- Commander.js for CLI parsing
- Python skills invoked via subprocess for efficiency
- Async queue with configurable worker pool
- Modular architecture with clear separation of concerns
