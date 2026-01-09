---
name: db-identify
description: Identify database file formats by scanning magic bytes and file signatures. Use FIRST when encountering any unknown database file. Returns format type, version, confidence level, and DBeaver CLI compatibility. Pure identification only - for routing decisions, pass results to db-router.
---

# Database Identifier

Identify database file formats via signature detection.

## Quick Start

```bash
# Identify a database file
python scripts/db_identify.py unknown.db

# JSON output for piping to db-router
python scripts/db_identify.py unknown.db --json

# List all detectable formats
python scripts/db_identify.py --list-formats
```

## Output

Human-readable:
```
File: course.db
Size: 12.0 KB

Format: sqlite
Version: 3.x
Confidence: high (signature detection)
DBeaver supported: Yes
```

JSON (for routing):
```json
{
  "format": "sqlite",
  "version": "3.x",
  "detection_method": "signature",
  "confidence": "high",
  "dbeaver_supported": true,
  "file_info": {
    "name": "course.db",
    "size_bytes": 12288,
    "size_human": "12.0 KB"
  }
}
```

## Detection Methods

| Method | Confidence | How |
|--------|------------|-----|
| Signature | High | Magic bytes at file start |
| Extension | Low | File extension hint |
| None | None | Unrecognized format |

## Supported Formats

| Format | DBeaver CLI | Notes |
|--------|-------------|-------|
| sqlite | ✓ | Most common for course materials |
| access | ✓ | .mdb, .accdb |
| dbf | ✓ | dBase, FoxPro |
| h2 | ✓ | Java H2 database |
| firebird | ✓ | .fdb, .gdb |
| berkeleydb | ✗ | Needs custom extractor |
| redis-rdb | ✗ | Needs custom extractor |

## CLI Reference

```
python scripts/db_identify.py DATABASE [OPTIONS]

Arguments:
  DATABASE              Database file to identify

Options:
  -j, --json            Output as JSON
  -l, --list-formats    List all detectable formats
```

## Typical Workflow

```bash
# 1. Identify format
python db_identify.py mystery.db --json > /tmp/db_info.json

# 2. Pass to router for extraction decision
# (handled by db-router skill)
```
