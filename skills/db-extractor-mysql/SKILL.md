---
name: db-extractor-mysql
description: Extract MySQL database content to text-readable formats (CSV, JSON, Markdown) for LLM processing and content synthesis. Use when working with MySQL databases that need to be converted to text formats for analysis, synthesis, or inclusion in LLM context windows. Routed from db-router skill.
---

# MySQL Database Extractor

Extract MySQL database tables to text-readable formats for LLM-based content synthesis.

## Quick Start

```bash
# Extract all tables to CSV (default)
python scripts/db_extract.py mysql://user:password@localhost:3306/mydb

# Extract to JSON
python scripts/db_extract.py mysql://user:password@localhost/mydb -f json

# Extract to Markdown (best for LLM context)
python scripts/db_extract.py mysql://root:secret@localhost/course_db -f markdown

# All formats with schema documentation
python scripts/db_extract.py mysql://user:pass@host/db -f all --schema -o ./output
```

## Connection String Format

```
mysql://[user[:password]@]host[:port]/database
```

**Examples:**
- `mysql://root:password@localhost:3306/mydb` - Full format
- `mysql://root@localhost/mydb` - No password (prompts or uses empty)
- `mysql://user:pass@db.example.com/production` - Remote host

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
python scripts/db_extract.py mysql://root:pass@localhost/course_db -f markdown --schema -o ./course_content
```

### Selective Table Extraction
```bash
# Only specific tables
python scripts/db_extract.py mysql://user:pass@host/db --tables users,posts,comments

# Exclude system tables
python scripts/db_extract.py mysql://user:pass@host/db --exclude migrations,logs
```

### Large Database Handling
```bash
# Limit markdown rows for large tables
python scripts/db_extract.py mysql://user:pass@host/db -f markdown --max-rows 50
```

## CLI Reference

```
python scripts/db_extract.py CONNECTION [OPTIONS]

Arguments:
  CONNECTION            MySQL connection string: mysql://user:pass@host:port/database

Options:
  -o, --output DIR      Output directory (default: ./extracted)
  -f, --format FORMAT   csv|json|markdown|all (default: csv)
  --tables TABLES       Comma-separated table list
  --exclude TABLES      Tables to skip
  --schema              Include _schema.md documentation
  --max-rows N          Row limit for markdown (default: 100)
  --charset CHARSET     Character set (default: utf8mb4)
  --timeout SECONDS     Connection timeout (default: 30)
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

- Python 3.8+
- mysql-connector-python

```bash
pip install mysql-connector-python
```

## Filtered System Databases

The following are automatically excluded from extraction:
- `mysql`
- `information_schema`
- `performance_schema`
- `sys`
