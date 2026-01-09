---
name: db-router
description: Route database files to appropriate extraction method based on identification from db-identify. Decides between DBeaver CLI (for supported formats) or db-extractor-* skills (for unsupported formats). Use AFTER db-identify to determine extraction workflow.
---

# Database Router

Route identified databases to the correct extraction method.

## Decision Flow

```
db-identify output
       │
       ▼
┌──────────────────┐
│ dbeaver_supported│
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    ▼         ▼
 DBeaver   db-extractor-*
   CLI        skill
```

## Quick Start

```bash
# Route from identification JSON (typical workflow)
python scripts/db_route.py --json '{"format": "sqlite", "dbeaver_supported": true}'

# Identify + route in one step
python scripts/db_route.py --file database.db

# View routing table
python scripts/db_route.py --list-routes
```

## Output

```
Format: sqlite
Decision: use_dbeaver
Method: dbeaver_cli

Instructions:
  • Use DBeaver CLI to export sqlite database
  • DBeaver supports this format natively
  • Fallback: db-extractor-sqlite (available)
```

## Routing Table

| Format | DBeaver | Extractor Skill | Status |
|--------|---------|-----------------|--------|
| sqlite | ✓ | db-extractor-sqlite | available |
| access | ✓ | db-extractor-access | planned |
| dbf | ✓ | db-extractor-dbf | planned |
| h2 | ✓ | db-extractor-h2 | planned |
| firebird | ✓ | db-extractor-firebird | planned |
| berkeleydb | ✗ | db-extractor-berkeleydb | planned |
| redis-rdb | ✗ | db-extractor-redis | planned |

## Decision Types

| Decision | Meaning | Action |
|----------|---------|--------|
| `use_dbeaver` | DBeaver CLI supported | Use DBeaver for extraction |
| `use_skill` | Skill available, DBeaver not | Use db-extractor-* skill |
| `skill_needed` | No DBeaver, skill not ready | Need to build extractor |
| `unknown_format` | Unidentified format | Manual investigation |

## CLI Reference

```
python scripts/db_route.py [OPTIONS]

Options:
  -f, --file PATH       Database file (runs db-identify first)
  -j, --json JSON       Identification JSON from db-identify
  --format FORMAT       Database format directly
  --dbeaver-supported   true/false
  --output-json         Output routing decision as JSON
  -l, --list-routes     Show routing table
```

## Agent Workflow

```bash
# Step 1: Identify
IDENT=$(python db-identify/scripts/db_identify.py course.db --json)

# Step 2: Route
python db-router/scripts/db_route.py --json "$IDENT"

# Step 3: Execute based on decision
# → use_dbeaver: run DBeaver CLI export
# → use_skill: run db-extractor-* script
# → skill_needed: create extractor skill
```
