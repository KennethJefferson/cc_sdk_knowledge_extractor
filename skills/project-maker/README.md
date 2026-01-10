# Project Maker

**The Crown Jewel of CCKnowledgeExtractor**

Transform validated course content into complete, production-ready code projects.

## Overview

Project Maker is the most powerful skill in CCKnowledgeExtractor. It analyzes ALL your validated course assets - transcripts, documentation, code samples, and extracted text - then synthesizes them into fully functional, well-documented projects that you can build and run immediately.

Unlike simple code extractors, Project Maker:

- **Understands Context** - Analyzes content across multiple files to understand the full picture
- **Discovers Projects** - Automatically identifies hands-on projects from instructional content
- **Generates Complete Implementations** - Produces working code with all dependencies
- **Creates Professional Documentation** - README, USAGE, CHANGELOG, and CLAUDE.md for every project
- **Handles Multiple Projects** - One course can yield multiple distinct projects

## Features

### Intelligent Discovery

- Recognizes project-start patterns ("Let's build...", "We'll create...")
- Groups related content by topic and feature
- Identifies tech stack from code patterns and mentions
- Assesses complexity (beginner/intermediate/advanced)

### Multi-Language Support

| Language | Config | Output |
|----------|--------|--------|
| **Rust** | Cargo.toml | Complete Rust project with modules |
| **TypeScript** | package.json + tsconfig | Type-safe Node.js project |
| **JavaScript** | package.json | Node.js/React project |
| **Python** | requirements.txt | FastAPI/Flask/CLI project |

### Framework Detection

- **Frontend**: React, Vue, Angular, Svelte
- **Backend**: Express, FastAPI, Flask, Django
- **GUI**: Iced (Rust), Tauri, Electron
- **Databases**: SQLite, PostgreSQL, MongoDB

### Professional Output

Every generated project includes:

```
Project_YourProjectName/
├── README.md           # Overview, setup, features
├── USAGE.md            # Detailed usage guide
├── CHANGELOG.md        # Version history
├── CLAUDE.md           # AI assistant instructions
├── .gitignore          # Language-appropriate ignores
├── <config>            # package.json/Cargo.toml/requirements.txt
├── src/                # Source code
│   └── ...
└── tests/              # Test files (when applicable)
```

## Quick Start

```bash
# Generate projects from a course
ccke -i ./my-courses -ccg Project

# With verbose output
ccke -i ./my-courses -ccg Project -v

# Preview without generating
ccke -i ./my-courses -ccg Project --dry-run
```

## How It Works

```
1. SCAN      Read all files from __cc_validated_files/
             Parse transcripts, docs, code samples
                            ↓
2. DISCOVER  Identify distinct projects
             Detect tech stack and complexity
             Map source files to projects
                            ↓
3. PLAN      Determine file structure
             Identify dependencies
             Plan implementation order
                            ↓
4. GENERATE  Create project directories
             Generate config, source, tests, docs
             Ensure everything is runnable
                            ↓
5. REPORT    Output summary with file counts
             List any warnings or issues
             Provide next steps
```

## Example Output

Given a Rust GUI course with transcripts about building a property manager:

```
Project Maker Complete!
==================================================
  Projects generated: 1
  Projects failed:    0
  Output:             __ccg_Project/

  ✓ Project_RustPropertyManager
    Files: 8
    Path:  __ccg_Project/Project_RustPropertyManager
```

The generated project:

```
Project_RustPropertyManager/
├── README.md                 # Full documentation
├── USAGE.md                  # Usage guide
├── CHANGELOG.md              # v0.1.0 entry
├── CLAUDE.md                 # AI instructions
├── .gitignore                # Rust ignores
├── Cargo.toml                # Dependencies (iced, rusqlite, serde)
└── src/
    ├── main.rs               # Iced GUI application
    └── lib.rs                # Library modules
```

## Configuration

Project Maker reads from the course's validated files directory:

```
<course>/
└── CODE/
    └── __cc_validated_files/   ← Input
        ├── lesson1.srt
        ├── lesson2.srt
        ├── code_example.rs
        └── notes.md
```

And outputs to:

```
<course>/
└── CODE/
    └── __ccg_Project/          ← Output
        ├── discovery.json
        ├── generation.log
        └── Project_<Name>/
            └── ...
```

## Best Practices

1. **Provide Rich Content** - More transcripts and code samples = better projects
2. **Include Code Examples** - Actual code in content improves generation quality
3. **Use Multiple File Types** - Mix of SRT, MD, and code files work best
4. **Review and Enhance** - Generated projects are starting points; enhance as needed

## Limitations

- Generated code follows patterns from content but may need refinement
- Complex multi-service architectures may require manual integration
- Some framework-specific features may need manual implementation
- Test coverage is basic; add comprehensive tests as needed

## See Also

- [Usage Guide](Usage.md) - Detailed activation phrases and examples
- [SKILL.md](SKILL.md) - Technical specification
