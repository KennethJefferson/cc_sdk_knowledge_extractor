# MySQL Extraction Guide

Best practices for extracting MySQL databases for LLM synthesis workflows.

## Connection String Format

```
mysql://[user[:password]@]host[:port]/database
```

### Examples

| Use Case | Connection String |
|----------|-------------------|
| Local dev | `mysql://root:password@localhost:3306/mydb` |
| Remote | `mysql://user:pass@db.example.com/production` |
| No password | `mysql://root@localhost/mydb` |
| Non-default port | `mysql://user:pass@localhost:3307/mydb` |

### Special Characters in Password

URL-encode special characters:
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`

Example: Password `p@ss:word` → `mysql://user:p%40ss%3Aword@host/db`

## Format Selection

### CSV
**Tokens:** Low (no structural overhead)
**Best when:**
- Processing with pandas/code before LLM
- Data will be summarized programmatically
- Need Excel/spreadsheet compatibility

### JSON
**Tokens:** Medium (keys repeated per row)
**Best when:**
- Data has nested structures
- Need type preservation (numbers vs strings)
- Will be processed programmatically

### Markdown
**Tokens:** Medium (table formatting)
**Best when:**
- Direct inclusion in LLM context
- Human review needed
- Data is tabular and readable

## MySQL-Specific Considerations

### Binary Data (BLOB)
Binary columns are replaced with `[BINARY:N bytes]` placeholder to keep exports readable.

### Character Encoding
Default charset is `utf8mb4` (full Unicode support including emoji). Override with `--charset`:
```bash
python db_extract.py mysql://... --charset latin1
```

### Large Tables
For tables with millions of rows:
1. Use `--max-rows` to limit markdown output
2. Consider extracting to CSV for programmatic summarization
3. Use `--tables` to extract only needed tables

### Connection Timeouts
For slow networks or large queries:
```bash
python db_extract.py mysql://... --timeout 60
```

## Token Optimization Tips

1. **Extract schema separately** (`--schema`) - describe structure once
2. **Filter tables** (`--tables`) - only extract what's needed
3. **Limit rows** (`--max-rows`) - sample data often sufficient
4. **Exclude large tables** (`--exclude`) - skip logs, audit trails

## Recommended Workflow

```bash
# Step 1: Extract with schema for context
python db_extract.py mysql://user:pass@host/db -f markdown --schema -o ./extracted

# Step 2: Review _schema.md to understand structure

# Step 3: Include relevant .md files in LLM context for synthesis
```

## Troubleshooting

### "Access denied"
Check username/password in connection string. Verify user has SELECT privileges.

### "Unknown database"
Verify database name exists. Check with `SHOW DATABASES`.

### "Connection refused"
- Check host and port
- Verify MySQL is running
- Check firewall rules
- Ensure skip-networking is not enabled

### "mysql-connector-python not found"
```bash
pip install mysql-connector-python
```
