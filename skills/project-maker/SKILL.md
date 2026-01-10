# Project Maker Skill

Transform validated course content into complete, working code projects.

## Purpose

The Project Maker is the crown jewel of CCKnowledgeExtractor. It synthesizes ALL validated file assets (transcripts, documentation, code samples, images) into production-ready project implementations that can be built and run immediately.

Unlike simple code extractors, Project Maker:
- **Understands context** across multiple source files
- **Identifies teachable projects** from instructional content
- **Generates complete implementations** with all dependencies
- **Creates professional documentation** (README, USAGE, CHANGELOG, CLAUDE.md)
- **Handles multiple projects** per course intelligently

## Activation

Use the `-ccg` argument with any of these values:

| Phrase | Command |
|--------|---------|
| `Project` | `ccke -i ./courses -ccg Project` |
| `project` | `ccke -i ./courses -ccg project` |
| `Projects` | `ccke -i ./courses -ccg Projects` |
| `make` | `ccke -i ./courses -ccg make` |
| `synthesize` | `ccke -i ./courses -ccg synthesize` |
| `build-project` | `ccke -i ./courses -ccg build-project` |

## Input

Reads from: `<course>/CODE/__cc_validated_files/`

Supported file types:
- **Transcripts**: `.srt`, `.vtt` - Primary source of instructional content
- **Documentation**: `.md`, `.txt` - Supplementary guides and notes
- **Code Samples**: `.py`, `.js`, `.ts`, `.rs`, `.go`, `.java`, `.cpp`, `.cs`, `.rb`, `.php`
- **Extracted Text**: From PDFs, PPTX, DOCX, images (OCR)

## Output

Creates: `<course>/CODE/__ccg_Project/`

```
__ccg_Project/
├── discovery.json           # Project discovery manifest
├── generation.log           # Processing log
│
├── Project_<Name1>/         # First discovered project
│   ├── README.md            # Project overview & setup
│   ├── USAGE.md             # Detailed usage guide
│   ├── CHANGELOG.md         # Version history
│   ├── CLAUDE.md            # AI assistant instructions
│   ├── .gitignore           # Standard ignores
│   ├── package.json         # Dependencies (if JS/TS)
│   ├── requirements.txt     # Dependencies (if Python)
│   ├── Cargo.toml           # Dependencies (if Rust)
│   ├── src/                 # Source code
│   │   └── ...
│   └── tests/               # Test files
│       └── ...
│
└── Project_<Name2>/         # Second discovered project
    └── ...
```

## Discovery Phase

### Project Identification Signals

**Strong Positive Signals** (definitely a project):
- "Let's build...", "We'll create...", "Start a new project"
- Framework initialization: `npm create`, `cargo new`, `django-admin startproject`
- Multiple related files building toward a goal
- Progressive feature implementation across lessons

**Moderate Signals** (likely a project):
- Function/class implementations with real use cases
- Database schema definitions
- API endpoint implementations
- UI component building

**Negative Signals** (skip):
- Pure theory without implementation
- Syntax explanations with toy examples
- Course intro/outro content
- Quiz/assessment sections

### Tech Stack Detection

| Category | Detected By |
|----------|-------------|
| **Languages** | File extensions, import statements, syntax patterns |
| **Frameworks** | Import statements, project structure, config files |
| **Databases** | Connection strings, ORM usage, SQL patterns |
| **Tools** | CLI commands, configuration references |

### Complexity Assessment

| Level | Indicators |
|-------|------------|
| **Beginner** | Single module, basic CRUD, <5 files, no auth |
| **Intermediate** | Multiple modules, state management, API integration, basic auth |
| **Advanced** | Microservices, OAuth/JWT, real-time features, complex architecture |

## Generation Phase

### Code Quality Standards

1. **Type Safety**: Use TypeScript/type hints where applicable
2. **Error Handling**: Comprehensive error handling, no silent failures
3. **Documentation**: JSDoc/docstrings for public APIs
4. **Testing**: At least smoke tests for core functionality
5. **Security**: No hardcoded secrets, proper input validation

### File Generation Order

1. Configuration files (package.json, tsconfig, etc.)
2. Type definitions and interfaces
3. Core utilities and helpers
4. Data models and schemas
5. Business logic and services
6. Controllers/routes/handlers
7. UI components (if applicable)
8. Entry points and initialization
9. Tests
10. Documentation

### Documentation Standards

**README.md**:
- Project title and description
- Features list
- Prerequisites
- Installation steps
- Quick start guide
- Configuration options
- License

**USAGE.md**:
- Detailed usage examples
- API reference (if applicable)
- Configuration deep-dive
- Troubleshooting

**CLAUDE.md**:
- Project architecture overview
- Key patterns and conventions
- File organization
- Build/test commands
- Common modification scenarios

## Processing Workflow

```
1. SCAN
   └── Read all files from __cc_validated_files/
       ├── Parse SRT/VTT for instructional content
       ├── Parse MD/TXT for documentation
       └── Parse code files for examples

2. DISCOVER
   └── Identify distinct projects
       ├── Group related content by topic/feature
       ├── Detect tech stack for each project
       ├── Assess complexity level
       └── Map source files to projects

3. PLAN
   └── For each project:
       ├── Determine file structure
       ├── Identify dependencies
       ├── Plan implementation order
       └── Note cross-file relationships

4. GENERATE
   └── For each project:
       ├── Create project directory
       ├── Generate configuration files
       ├── Generate source code (in order)
       ├── Generate tests
       └── Generate documentation

5. VALIDATE
   └── For each project:
       ├── Check for missing imports
       ├── Verify file references
       ├── Ensure documentation completeness
       └── Log any issues

6. REPORT
   └── Output summary:
       ├── Projects generated
       ├── Files created per project
       ├── Warnings/issues encountered
       └── Next steps for user
```

## Naming Conventions

### Project Names

Pattern: `Project_<Framework><Feature><Qualifier>`

Examples:
- `Project_RustPropertyManager`
- `Project_ReactJobPortal`
- `Project_PythonFlaskBlogAuth`
- `Project_NodeExpressRestAPI`

Rules:
- Always prefix with `Project_`
- PascalCase throughout
- Primary language/framework first
- Main feature/purpose next
- Optional qualifier for clarity
- Maximum 50 characters

### File Names

- **Source**: Follow language conventions (snake_case for Python/Rust, camelCase for JS/TS)
- **Config**: Standard names (package.json, Cargo.toml, requirements.txt)
- **Docs**: UPPERCASE.md (README.md, USAGE.md, CHANGELOG.md, CLAUDE.md)

## Error Handling

### Graceful Degradation

If project generation fails partially:
1. Log the error to `generation.log`
2. Continue with remaining projects
3. Mark failed project in `discovery.json`
4. Report issues in final summary

### Common Issues

| Issue | Resolution |
|-------|------------|
| No projects found | Log reason, suggest content type change |
| Insufficient content | Generate partial with TODOs |
| Conflicting info | Use most recent/detailed source |
| Missing dependencies | Note in README prerequisites |

## JSON Schemas

### discovery.json

```json
{
  "course_path": "/path/to/course",
  "discovered_at": "2026-01-09T22:00:00Z",
  "version": "1.0",
  "source_files": {
    "transcripts": 21,
    "documentation": 3,
    "code_samples": 7
  },
  "projects": [
    {
      "id": "proj_001",
      "name": "Property Manager",
      "synthesized_name": "Project_RustPropertyManager",
      "description": "A Rust GUI application for managing properties with Iced framework",
      "source_files": ["lesson1.srt", "lesson2.srt", "main.rs"],
      "tech_stack": ["Rust", "Iced", "SQLite"],
      "complexity": "intermediate",
      "status": "generated",
      "output_path": "__ccg_Project/Project_RustPropertyManager",
      "files_created": 12,
      "generated_at": "2026-01-09T22:05:00Z"
    }
  ],
  "skipped_files": ["00_intro.srt", "99_conclusion.srt"],
  "warnings": [],
  "total_projects": 2,
  "successful": 2,
  "failed": 0
}
```

## Best Practices

1. **Read everything first** - Full context produces better output
2. **Group intelligently** - One project may span many lessons
3. **Preserve teaching order** - Features should build progressively
4. **Comment the why** - Explain non-obvious implementation choices
5. **Make it runnable** - Generated projects should work after dependency install
6. **Be complete** - No placeholder functions or TODO-only files
7. **Test locally** - Include at least basic verification steps
