# CCKnowledgeExtractor

A Bun/TypeScript CLI application for extracting and repurposing educational course content. Processes transcripts, documents, code, databases, and images using Python skills, then generates new content (quizzes, exams, summaries, SOPs, projects) via Claude Agent SDK.

## Features

- **Multi-course batch processing** - Process entire course libraries at once
- **Multiple generators in one run** - Comma-separated types: `-ccg Exam,Project,SOP`
- **GitHub sync** - Auto-push generated assets to GitHub repos
- **Parallel worker pools** - Configurable concurrency for scanning and processing
- **Intelligent file routing** - Magic byte detection with extension fallback
- **Progress visualization** - Animated spinners and progress bars
- **Dry-run mode** - Preview changes without modifying files
- **Config file support** - Project-level defaults via `.cckrc.json`

## Requirements

- [Bun](https://bun.sh) v1.0+
- Python 3.8+
- GitHub CLI (`gh`) for GitHub sync feature
- External tools (optional):
  - Tesseract OCR (for image text extraction)
  - 7-Zip (for archive extraction)
  - Pandoc (for HTML conversion)

## Installation

```bash
# Clone the repository
git clone https://github.com/KennethJefferson/cc_sdk_knowledge_extractor.git
cd cc_sdk_knowledge_extractor

# Install dependencies
bun install
```

## Quick Start

```bash
# Generate a quiz from course content
bun run src/index.ts -i ./my-courses -ccg Exam

# Generate multiple content types at once
bun run src/index.ts -i ./my-courses -ccg Exam,Project,SOP

# Generate all content types
bun run src/index.ts -i ./my-courses -ccg all

# With GitHub sync (creates repos for each generated asset)
bun run src/index.ts -i ./my-courses -ccg Project --github-sync=true

# Preview what would be processed (dry-run)
bun run src/index.ts -i ./my-courses -ccg Exam --dry-run

# With verbose output
bun run src/index.ts -i ./my-courses -ccg Exam -v
```

## Documentation

- [Usage Guide](Usage.md) - Detailed CLI options and examples
- [Changelog](CHANGELOG.md) - Version history and changes

## Supported File Types

| Category | Extensions |
|----------|------------|
| Text | .txt, .md, .srt, .vtt |
| Code | .py, .js, .ts, .cpp, .java, .cs, .go, .rs, .rb, .php |
| Documents | .pdf, .docx, .pptx, .xlsx |
| Images | .png, .jpg, .jpeg, .gif, .bmp, .tiff |
| Archives | .zip, .rar, .7z, .tar, .gz |
| Databases | .db, .sqlite, .sqlite3 |
| Web | .html, .htm |

## Output Structure

```
<course>/
├── lesson1.srt
├── lesson2.srt
└── CODE/
    ├── __cc_validated_files/     # Extracted text content
    │   ├── lesson1.srt           # Copied as-is
    │   ├── lesson2.srt
    │   └── project_main.cpp      # Flattened paths
    ├── __ccg_Exam/               # Generated quiz content
    │   ├── quiz.md
    │   └── answer_key.md
    ├── __ccg_Project/            # Generated project
    │   └── Project_<Name>/
    ├── __ccg_Sop/                # Generated SOPs
    │   └── README.md
    └── error_20260109_143022.log # Processing errors
```

## Content Generators

| Type | Aliases | Output |
|------|---------|--------|
| Exam | exam, quiz | Multiple choice, short answer, true/false questions |
| Summary | summary, docs | README, glossary, study guide, topic files |
| SOP | sop, procedure | Standard Operating Procedures with checklists |
| Project | project, make | Complete project scaffolding from transcripts |

## GitHub Sync

When `--github-sync=true` is specified, each generated asset is pushed to its own GitHub repository:

- **Naming**: `ccg_{Type}_{SynthesizedName}` (e.g., `ccg_Project_RustPropertyManager`)
- **Visibility**: Public
- **Description**: Auto-generated from asset metadata
- **Prerequisites**: GitHub CLI authenticated (`gh auth login`)

## License

MIT

## Contributing

Contributions welcome! Please read the codebase overview in [CLAUDE.md](CLAUDE.md) first.
