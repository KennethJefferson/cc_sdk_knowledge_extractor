---
name: db-extractor-sqlite
description: Extract SQLite database content to text-readable formats (CSV, JSON, Markdown) for LLM processing and content synthesis. Use when working with SQLite databases (.db, .sqlite, .sqlite3) from course materials, datasets, or applications that need to be converted to text formats for analysis, synthesis, or inclusion in LLM context windows. Routed from db-router skill.
---

# Database Content Extractor

Extract SQLite database tables to text-readable formats for LLM-based content synthesis.

## Quick Start

```bash
# Extract all tables to CSV (default)
python scripts/db_extract.py course.db

# Extract to JSON
python scripts/db_extract.py course.db -f json

# Extract to Markdown (best for LLM context)
python scripts/db_extract.py course.db -f markdown

# All formats with schema documentation
python scripts/db_extract.py course.db -f all --schema -o ./output
```

## Output Formats

| Format | Best For | File Extension |
|--------|----------|----------------|
| CSV | Data analysis, spreadsheets, pandas | `.csv` |
| JSON | Structured processing, APIs | `.json` |
| Markdown | LLM context, human reading | `.md` |

## Common Workflows

### Course Material Extraction
```bash
# Extract course DB with schema docs for context
python scripts/db_extract.py course.db -f markdown --schema -o ./course_content
```

### Selective Table Extraction
```bash
# Only specific tables
python scripts/db_extract.py app.db --tables users,posts,comments

# Exclude system tables
python scripts/db_extract.py app.db --exclude sqlite_sequence,migrations
```

### Large Database Handling
```bash
# Limit markdown rows for large tables (keeps files manageable)
python scripts/db_extract.py large.db -f markdown --max-rows 50
```

## CLI Reference

```
python scripts/db_extract.py DATABASE [OPTIONS]

Arguments:
  DATABASE              Path to SQLite database file

Options:
  -o, --output DIR      Output directory (default: ./extracted)
  -f, --format FORMAT   csv|json|markdown|all (default: csv)
  --tables TABLES       Comma-separated table list
  --exclude TABLES      Tables to skip
  --schema              Include _schema.md documentation
  --max-rows N          Row limit for markdown (default: 100)
  -q, --quiet           Suppress progress output
```

## Output Structure

```
output/
├── _schema.md          # Schema documentation (if --schema)
├── csv/                # (if format=all)
│   ├── table1.csv
│   └── table2.csv
├── json/
│   └── ...
└── markdown/
    └── ...
```

Single format outputs files directly to output directory without subdirectories.

## Dependencies

- Python 3.8+ (sqlite3 is built-in)
- No external packages required
