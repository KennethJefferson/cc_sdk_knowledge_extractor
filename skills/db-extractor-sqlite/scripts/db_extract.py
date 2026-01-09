#!/usr/bin/env python3
"""
Database Content Extractor

Extracts database tables to text-readable formats (CSV, JSON, Markdown)
for use in LLM-based content synthesis.

Primary use case: Course material databases → readable text for synthesis

Usage:
    python db_extract.py database.db                    # Extract all to CSV
    python db_extract.py database.db -o ./output        # Specify output dir
    python db_extract.py database.db -f json            # Output as JSON
    python db_extract.py database.db -f markdown        # Output as Markdown tables
    python db_extract.py database.db --tables users,posts  # Specific tables only
    python db_extract.py database.db --schema           # Include schema info
"""

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional


def get_connection(db_path: str):
    """Create database connection. Supports SQLite and basic URI formats."""
    path = Path(db_path)
    
    # Handle SQLite URI format
    if db_path.startswith("sqlite:///"):
        db_path = db_path[10:]
        path = Path(db_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def get_tables(conn) -> list[str]:
    """Get list of all tables in database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def get_schema(conn, table: str) -> list[dict]:
    """Get column info for a table."""
    cursor = conn.execute(f"PRAGMA table_info('{table}')")
    return [
        {
            "name": row[1],
            "type": row[2],
            "nullable": not row[3],
            "primary_key": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]


def get_row_count(conn, table: str) -> int:
    """Get row count for a table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM '{table}'")
    return cursor.fetchone()[0]


def export_to_csv(conn, table: str, output_dir: Path) -> Path:
    """Export table to CSV file."""
    output_file = output_dir / f"{table}.csv"
    
    cursor = conn.execute(f"SELECT * FROM '{table}'")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    return output_file


def export_to_json(conn, table: str, output_dir: Path) -> Path:
    """Export table to JSON file."""
    output_file = output_dir / f"{table}.json"
    
    cursor = conn.execute(f"SELECT * FROM '{table}'")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    data = [dict(zip(columns, row)) for row in rows]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    
    return output_file


def export_to_markdown(conn, table: str, output_dir: Path, max_rows: int = 100) -> Path:
    """Export table to Markdown file with table format."""
    output_file = output_dir / f"{table}.md"
    
    cursor = conn.execute(f"SELECT * FROM '{table}'")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
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
            cells = [str(cell).replace("|", "\\|").replace("\n", " ")[:100] for cell in row]
            lines.append("| " + " | ".join(cells) + " |")
    else:
        lines.append("*Empty table*")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return output_file


def export_schema_info(conn, tables: list[str], output_dir: Path) -> Path:
    """Export database schema as Markdown documentation."""
    output_file = output_dir / "_schema.md"
    
    lines = ["# Database Schema", ""]
    
    for table in tables:
        schema = get_schema(conn, table)
        row_count = get_row_count(conn, table)
        
        lines.append(f"## {table}")
        lines.append(f"**Rows:** {row_count}")
        lines.append("")
        lines.append("| Column | Type | Nullable | Primary Key |")
        lines.append("| --- | --- | --- | --- |")
        
        for col in schema:
            pk = "✓" if col["primary_key"] else ""
            nullable = "✓" if col["nullable"] else ""
            lines.append(f"| {col['name']} | {col['type']} | {nullable} | {pk} |")
        
        lines.append("")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Extract database content to text-readable formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all tables to CSV (default)
  python db_extract.py course.db

  # Extract to JSON format
  python db_extract.py course.db -f json

  # Extract to Markdown tables (good for LLM context)
  python db_extract.py course.db -f markdown

  # Extract specific tables only
  python db_extract.py course.db --tables lessons,quizzes

  # Include schema documentation
  python db_extract.py course.db --schema

  # All formats at once
  python db_extract.py course.db -f all --schema
        """
    )
    
    parser.add_argument("database", help="Path to SQLite database file")
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
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress progress output")
    
    args = parser.parse_args()
    
    def log(msg):
        if not args.quiet:
            print(msg)
    
    try:
        # Connect to database
        log(f"Opening: {args.database}")
        conn = get_connection(args.database)
        
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
            log(f"  Schema → {schema_file}")
        
        conn.close()
        log(f"\nExtracted to: {output_dir}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except sqlite3.Error as e:
        print(f"DATABASE ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
