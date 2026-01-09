#!/usr/bin/env python3
"""
MySQL Database Content Extractor

Extracts MySQL database tables to text-readable formats (CSV, JSON, Markdown)
for use in LLM-based content synthesis.

Primary use case: Course material databases -> readable text for synthesis

Usage:
    python db_extract.py mysql://user:pass@localhost:3306/mydb
    python db_extract.py mysql://user:pass@host/db -o ./output
    python db_extract.py mysql://user:pass@host/db -f json
    python db_extract.py mysql://user:pass@host/db -f markdown
    python db_extract.py mysql://user:pass@host/db --tables users,posts
    python db_extract.py mysql://user:pass@host/db --schema

Requires: pip install mysql-connector-python
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("ERROR: mysql-connector-python is required.", file=sys.stderr)
    print("Install with: pip install mysql-connector-python", file=sys.stderr)
    sys.exit(1)


# System databases to exclude from extraction
SYSTEM_DATABASES = {"mysql", "information_schema", "performance_schema", "sys"}


def parse_connection_string(uri: str) -> dict:
    """
    Parse MySQL connection string.

    Format: mysql://[user[:password]@]host[:port]/database

    Examples:
        mysql://root:password@localhost:3306/mydb
        mysql://root@localhost/mydb
        mysql://user:pass@db.example.com/production
    """
    if not uri.startswith("mysql://"):
        raise ValueError(f"Invalid connection string. Expected mysql://... got: {uri}")

    parsed = urlparse(uri)

    if not parsed.hostname:
        raise ValueError("Host is required in connection string")

    if not parsed.path or parsed.path == "/":
        raise ValueError("Database name is required in connection string")

    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username) if parsed.username else "root",
        "password": unquote(parsed.password) if parsed.password else "",
        "database": parsed.path.lstrip("/"),
    }


def get_connection(connection_string: str, charset: str = "utf8mb4", timeout: int = 30):
    """Create MySQL database connection."""
    config = parse_connection_string(connection_string)

    conn = mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset=charset,
        connection_timeout=timeout,
        use_pure=True,  # Pure Python implementation for compatibility
    )

    return conn


def get_tables(conn) -> list[str]:
    """Get list of all user tables in database (excludes system tables)."""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_schema(conn, table: str) -> list[dict]:
    """Get column info for a table from INFORMATION_SCHEMA."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """, (table,))

    schema = []
    for row in cursor.fetchall():
        schema.append({
            "name": row[0],
            "type": row[1],
            "nullable": row[2] == "YES",
            "primary_key": row[3] == "PRI",
            "auto_increment": "auto_increment" in (row[4] or "").lower(),
        })

    cursor.close()
    return schema


def get_row_count(conn, table: str) -> int:
    """Get row count for a table."""
    cursor = conn.cursor()
    # Use backticks for table names with special characters
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def get_table_info(conn, table: str) -> dict:
    """Get additional table metadata (engine, charset, etc.)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ENGINE, TABLE_COLLATION
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
    """, (table,))
    row = cursor.fetchone()
    cursor.close()

    if row:
        return {"engine": row[0], "collation": row[1]}
    return {}


def export_to_csv(conn, table: str, output_dir: Path) -> Path:
    """Export table to CSV file."""
    output_file = output_dir / f"{table}.csv"

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table}`")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            # Handle bytes/BLOB data
            processed_row = []
            for cell in row:
                if isinstance(cell, bytes):
                    processed_row.append(f"[BINARY:{len(cell)} bytes]")
                else:
                    processed_row.append(cell)
            writer.writerow(processed_row)

    return output_file


def export_to_json(conn, table: str, output_dir: Path) -> Path:
    """Export table to JSON file."""
    output_file = output_dir / f"{table}.json"

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table}`")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    data = []
    for row in rows:
        record = {}
        for col, cell in zip(columns, row):
            if isinstance(cell, bytes):
                record[col] = f"[BINARY:{len(cell)} bytes]"
            else:
                record[col] = cell
        data.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    return output_file


def export_to_markdown(conn, table: str, output_dir: Path, max_rows: int = 100) -> Path:
    """Export table to Markdown file with table format."""
    output_file = output_dir / f"{table}.md"

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `{table}`")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    total_rows = len(rows)
    display_rows = rows[:max_rows]

    lines = [f"# {table}", ""]

    # Add row count info
    lines.append(f"**Rows:** {total_rows}")
    if total_rows > max_rows:
        lines.append(f"*(showing first {max_rows} rows)*")
    lines.append("")

    # Create markdown table
    if columns and display_rows:
        # Header
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

        # Rows
        for row in display_rows:
            cells = []
            for cell in row:
                if isinstance(cell, bytes):
                    cells.append(f"[BINARY:{len(cell)}B]")
                else:
                    # Escape pipes and truncate long content
                    cell_str = str(cell).replace("|", "\\|").replace("\n", " ")[:100]
                    cells.append(cell_str)
            lines.append("| " + " | ".join(cells) + " |")
    else:
        lines.append("*Empty table*")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_file


def export_schema_info(conn, tables: list[str], output_dir: Path) -> Path:
    """Export database schema as Markdown documentation."""
    output_file = output_dir / "_schema.md"

    # Get database name
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    cursor.close()

    lines = [f"# Database Schema: {db_name}", ""]

    for table in tables:
        schema = get_schema(conn, table)
        row_count = get_row_count(conn, table)
        table_info = get_table_info(conn, table)

        lines.append(f"## {table}")
        lines.append(f"**Rows:** {row_count}")
        if table_info.get("engine"):
            lines.append(f"**Engine:** {table_info['engine']}")
        lines.append("")
        lines.append("| Column | Type | Nullable | Primary Key | Auto-Inc |")
        lines.append("| --- | --- | --- | --- | --- |")

        for col in schema:
            pk = "✓" if col["primary_key"] else ""
            nullable = "✓" if col["nullable"] else ""
            auto_inc = "✓" if col["auto_increment"] else ""
            lines.append(f"| {col['name']} | {col['type']} | {nullable} | {pk} | {auto_inc} |")

        lines.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Extract MySQL database content to text-readable formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all tables to CSV (default)
  python db_extract.py mysql://user:pass@localhost:3306/mydb

  # Extract to JSON format
  python db_extract.py mysql://user:pass@localhost/mydb -f json

  # Extract to Markdown tables (good for LLM context)
  python db_extract.py mysql://user:pass@localhost/mydb -f markdown

  # Extract specific tables only
  python db_extract.py mysql://user:pass@localhost/mydb --tables lessons,quizzes

  # Include schema documentation
  python db_extract.py mysql://user:pass@localhost/mydb --schema

  # All formats at once
  python db_extract.py mysql://user:pass@localhost/mydb -f all --schema
        """
    )

    parser.add_argument("connection",
                        help="MySQL connection string: mysql://user:pass@host:port/database")
    parser.add_argument("-o", "--output", default="./extracted",
                        help="Output directory (default: ./extracted)")
    parser.add_argument("-f", "--format",
                        choices=["csv", "json", "markdown", "all"],
                        default="csv",
                        help="Output format (default: csv)")
    parser.add_argument("--tables",
                        help="Comma-separated list of tables (default: all)")
    parser.add_argument("--exclude",
                        help="Comma-separated list of tables to exclude")
    parser.add_argument("--schema", action="store_true",
                        help="Also export schema documentation")
    parser.add_argument("--max-rows", type=int, default=100,
                        help="Max rows for markdown format (default: 100)")
    parser.add_argument("--charset", default="utf8mb4",
                        help="Character set (default: utf8mb4)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Connection timeout in seconds (default: 30)")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress progress output")

    args = parser.parse_args()

    def log(msg):
        if not args.quiet:
            print(msg)

    try:
        # Connect to database
        log(f"Connecting: {args.connection.split('@')[0].split(':')[0]}://***@{args.connection.split('@')[-1]}")
        conn = get_connection(args.connection, charset=args.charset, timeout=args.timeout)

        # Get tables
        all_tables = get_tables(conn)

        if args.tables:
            tables = [t.strip() for t in args.tables.split(",")]
            tables = [t for t in tables if t in all_tables]
        else:
            tables = all_tables

        if args.exclude:
            exclude = [t.strip() for t in args.exclude.split(",")]
            tables = [t for t in tables if t not in exclude]

        if not tables:
            print("No tables found to export", file=sys.stderr)
            sys.exit(1)

        log(f"Found {len(tables)} tables: {', '.join(tables)}")

        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine formats to export
        formats = ["csv", "json", "markdown"] if args.format == "all" else [args.format]

        # Export each table
        for table in tables:
            row_count = get_row_count(conn, table)
            log(f"  {table} ({row_count} rows)")

            for fmt in formats:
                if fmt == "csv":
                    subdir = output_dir / "csv" if len(formats) > 1 else output_dir
                    subdir.mkdir(exist_ok=True)
                    export_to_csv(conn, table, subdir)
                elif fmt == "json":
                    subdir = output_dir / "json" if len(formats) > 1 else output_dir
                    subdir.mkdir(exist_ok=True)
                    export_to_json(conn, table, subdir)
                elif fmt == "markdown":
                    subdir = output_dir / "markdown" if len(formats) > 1 else output_dir
                    subdir.mkdir(exist_ok=True)
                    export_to_markdown(conn, table, subdir, args.max_rows)

        # Export schema if requested
        if args.schema:
            schema_file = export_schema_info(conn, tables, output_dir)
            log(f"  Schema -> {schema_file}")

        conn.close()
        log(f"\nExtracted to: {output_dir}")

    except ValueError as e:
        print(f"CONNECTION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except MySQLError as e:
        print(f"DATABASE ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
