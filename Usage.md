# Usage Guide

## Command Line Interface

```
ccke -i <input> -ccg <type> [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `-i, --input <dir>` | Root directory containing course folders |
| `-ccg, --ClaudeCodeGenerated <type>` | Content type to generate |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `-sw, --scanningworkers <n>` | 1 | Number of parallel scanning workers |
| `-w, --workers <n>` | 1 | Number of parallel processing workers |
| `-o, --output <dir>` | (auto) | Override output directory |
| `-v, --verbose` | false | Enable verbose/debug output |
| `--dry-run` | false | Preview processing without making changes |
| `--init-config` | - | Generate sample .cckrc.json config file |

### Content Types

| Type | Aliases | Description |
|------|---------|-------------|
| Exam | exam, quiz | Generate quiz with multiple choice, short answer, T/F |
| Summary | summary, docs, documentation | Generate README, glossary, study guide |

## Examples

### Basic Usage

```bash
# Process all courses in a directory, generate exams
bun run src/index.ts -i ./courses -ccg Exam

# Generate documentation summaries
bun run src/index.ts -i ./courses -ccg Summary
```

### Parallel Processing

```bash
# Use 4 workers for faster processing
bun run src/index.ts -i ./courses -ccg Exam -w 4

# Use 2 scanning workers and 4 processing workers
bun run src/index.ts -i ./courses -ccg Exam -sw 2 -w 4
```

### Preview Mode

```bash
# See what would be processed without making changes
bun run src/index.ts -i ./courses -ccg Exam --dry-run

# Dry-run with verbose output for debugging
bun run src/index.ts -i ./courses -ccg Exam --dry-run -v
```

### Configuration

```bash
# Generate a sample config file in current directory
bun run src/index.ts --init-config

# Generate config in a specific directory
bun run src/index.ts --init-config -i ./my-project
```

## Configuration File

Create a `.cckrc.json` file in your project root or input directory:

```json
{
  "defaults": {
    "scanningWorkers": 2,
    "workers": 4,
    "verbose": false,
    "contentType": "Exam"
  },
  "exclude": [
    "node_modules",
    ".git",
    "*.log"
  ],
  "output": {
    "validatedDir": "__cc_validated_files",
    "generatedPrefix": "__ccg_"
  }
}
```

### Config File Search Order

1. `.cckrc.json`
2. `.cckrc`
3. `ccke.config.json`

The tool searches from the input directory upward to the filesystem root.

## Input Directory Structure

The tool expects a directory containing one or more course folders:

```
courses/                    # Input directory (-i)
├── Course1/               # Each subfolder is a course
│   ├── lesson1.srt
│   ├── lesson2.srt
│   └── CODE/
│       ├── project1/
│       └── resources/
├── Course2/
│   ├── transcript.srt
│   └── CODE/
│       └── examples/
└── Course3/
    └── ...
```

### Warning: Running Inside a Course

If you run the tool from inside a course folder (where .srt files exist in the root), you'll see a warning:

```
WARNING: Found .srt files in input root. You may be inside a course folder.
For multi-mode processing, run from the parent directory containing course folders.
```

## Output Structure

For each course, the tool creates:

```
<course>/CODE/
├── __cc_validated_files/           # Extracted text content
│   ├── lesson1.srt                 # Text files copied as-is
│   ├── project1_main.cpp           # Nested files flattened
│   └── resources_notes.md
├── __ccg_<ContentType>/            # Generated content
│   ├── quiz.md                     # (for Exam)
│   ├── answer_key.md
│   └── README.md                   # (for Summary)
└── error_YYYYMMDD_HHMMSS.log       # Error/warning log
```

## Processing Pipeline

1. **Course Discovery** - Scan input for course folders
2. **File Scanning** - Recursively find all processable files
3. **File Routing** - Determine processor for each file type
4. **Processing** - Extract text content via skills
5. **Content Generation** - Generate quiz/summary from validated files

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - all files processed |
| 1 | Error - validation failed or processing errors occurred |

## Troubleshooting

### No courses found

Ensure your input directory contains subdirectories with course content. The tool treats each immediate subdirectory as a separate course.

### Skill errors

Check that Python is installed and accessible. Some skills require additional dependencies:
- `image-ocr`: Tesseract OCR, Pillow
- `archive-extractor`: 7-Zip
- `html2markdown`: Pandoc

### Permission errors

Ensure write access to the course CODE directories where output will be created.
