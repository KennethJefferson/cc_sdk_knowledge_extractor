# Project Maker - Usage Guide

## Activation Phrases

Use the `-ccg` argument with any of these values to activate the Project Maker:

| Phrase | Command | Description |
|--------|---------|-------------|
| `Project` | `ccke -i ./courses -ccg Project` | Primary activation |
| `project` | `ccke -i ./courses -ccg project` | Lowercase variant |
| `Projects` | `ccke -i ./courses -ccg Projects` | Plural variant |
| `make` | `ccke -i ./courses -ccg make` | Short form |
| `synthesize` | `ccke -i ./courses -ccg synthesize` | Descriptive form |
| `build-project` | `ccke -i ./courses -ccg build-project` | Explicit form |

## Basic Usage

### Generate Projects from a Course

```bash
ccke -i ./my-courses -ccg Project
```

This will:
1. Scan all validated files in each course's `CODE/__cc_validated_files/`
2. Discover projects from the content
3. Generate complete project implementations
4. Output to `CODE/__ccg_Project/`

### Preview Mode (Dry Run)

```bash
ccke -i ./my-courses -ccg Project --dry-run
```

Preview what would be generated without creating files.

### Verbose Output

```bash
ccke -i ./my-courses -ccg Project -v
```

See detailed progress and discovery information.

### Process Specific Course

```bash
ccke -i "./courses/Rust Course" -ccg Project
```

Process only the specified course directory.

### Parallel Processing

```bash
ccke -i ./my-courses -ccg Project -w 4
```

Use 4 workers for faster file processing (before generation).

## Output Structure

### Discovery Manifest

`__ccg_Project/discovery.json`:

```json
{
  "course_path": "/path/to/course/CODE/__cc_validated_files",
  "discovered_at": "2026-01-09T22:00:00Z",
  "version": "1.0",
  "source_files": {
    "transcripts": 21,
    "documentation": 3,
    "code_samples": 7,
    "extracted": 2
  },
  "projects": [
    {
      "id": "proj_001",
      "name": "Property Manager",
      "synthesized_name": "Project_RustPropertyManager",
      "description": "A Rust GUI application for managing properties",
      "tech_stack": ["Rust", "Iced", "SQLite"],
      "complexity": "intermediate",
      "status": "generated",
      "files_created": 8
    }
  ],
  "total_projects": 1,
  "successful": 1,
  "failed": 0
}
```

### Generation Log

`__ccg_Project/generation.log`:

```
[22:00:00] Starting Project Maker...
[22:00:00] Step 1: Scanning source files...
[22:00:01] Found 33 source files
[22:00:01] Step 2: Analyzing content...
[22:00:02] Discovered 1 project(s)
[22:00:02] Step 3: Generating projects...
[22:00:02]   Generating: Project_RustPropertyManager
[22:00:03]     Status: generated, Files: 8
[22:00:03] Step 4: Writing manifest...
```

### Generated Project

`__ccg_Project/Project_RustPropertyManager/`:

```
Project_RustPropertyManager/
├── README.md           # Project overview
├── USAGE.md            # Usage guide
├── CHANGELOG.md        # Version history
├── CLAUDE.md           # AI instructions
├── .gitignore          # Rust ignores
├── Cargo.toml          # Dependencies
└── src/
    ├── main.rs         # Main application
    └── lib.rs          # Library modules
```

## Working with Generated Projects

### Rust Projects

```bash
cd __ccg_Project/Project_RustPropertyManager

# Build
cargo build

# Run
cargo run

# Test
cargo test
```

### Node.js/TypeScript Projects

```bash
cd __ccg_Project/Project_ReactDashboard

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Python Projects

```bash
cd __ccg_Project/Project_FastAPIBackend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Understanding Project Names

Project names follow the pattern: `Project_<Tech><Feature>`

Examples:
- `Project_RustPropertyManager` - Rust app for property management
- `Project_ReactJobPortal` - React-based job portal
- `Project_FastAPIDashboard` - FastAPI backend dashboard
- `Project_TypeScriptCLI` - TypeScript command-line tool

## Complexity Levels

| Level | What to Expect |
|-------|----------------|
| **Beginner** | Single module, basic CRUD, minimal dependencies |
| **Intermediate** | Multiple modules, state management, API integration |
| **Advanced** | Complex architecture, auth systems, real-time features |

## Tech Stack Detection

Project Maker detects technologies from:

1. **File Extensions**: `.rs` → Rust, `.ts` → TypeScript
2. **Import Statements**: `use iced::*` → Iced framework
3. **Code Patterns**: `fn main()` → Rust, `async def` → Python async
4. **Text Mentions**: "we'll use React" → React framework

## Troubleshooting

### No Projects Discovered

If "No projects discovered in content" appears:

1. **Check content type** - Ensure transcripts contain hands-on coding content
2. **Verify file types** - Should have `.srt`, `.md`, or code files
3. **Look for indicators** - Content should mention building/creating projects

### Missing Dependencies

If generated project won't build:

1. **Check config file** - Verify dependencies in package.json/Cargo.toml
2. **Update versions** - Some dependency versions may need updating
3. **Add missing** - Review imports and add any missing packages

### Incomplete Code

If code has TODOs or placeholders:

1. **Review source content** - Original content may have been high-level
2. **Add implementations** - Fill in business logic based on requirements
3. **Check CLAUDE.md** - Use it to guide Claude for enhancements

## Examples

### Full Workflow Example

```bash
# 1. First, process course files
ccke -i ./courses/rust-gui-course -ccg Summary -w 4

# 2. Then generate projects
ccke -i ./courses/rust-gui-course -ccg Project

# 3. Check output
ls ./courses/rust-gui-course/CODE/__ccg_Project/

# 4. Build the project
cd ./courses/rust-gui-course/CODE/__ccg_Project/Project_RustPropertyManager
cargo build && cargo run
```

### Multiple Courses

```bash
# Process all courses in a directory
ccke -i ./all-my-courses -ccg Project -w 4 -v
```

### Integration with Other Skills

```bash
# Generate summary first (for reference)
ccke -i ./course -ccg Summary

# Generate quiz (for testing knowledge)
ccke -i ./course -ccg Exam

# Then generate projects (for hands-on practice)
ccke -i ./course -ccg Project
```

## Best Practices

1. **Process transcripts first** - Run file extraction before project generation
2. **Use verbose mode** - Track what's being discovered and generated
3. **Review discovery.json** - Understand what was detected before diving into code
4. **Enhance generated code** - Generated projects are starting points
5. **Add tests** - Expand on the basic test structure provided
6. **Update documentation** - Customize README and USAGE for your needs

## See Also

- [README.md](README.md) - Feature overview
- [SKILL.md](SKILL.md) - Technical specification
