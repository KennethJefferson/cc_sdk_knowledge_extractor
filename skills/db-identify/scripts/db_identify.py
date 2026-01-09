#!/usr/bin/env python3
"""
Database Format Identifier

Identifies database file formats by scanning magic bytes/signatures.
Pure identification only - no routing decisions.

Usage:
    python db_identify.py database.file
    python db_identify.py database.file --json
    python db_identify.py --list-formats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Database signatures: (offset, magic_bytes, format_name, version_info)
SIGNATURES = [
    # SQLite
    (0, b"SQLite format 3\x00", "sqlite", "3.x"),
    
    # Microsoft Access
    (0, b"\x00\x01\x00\x00Standard Jet DB", "access", "2000/2003 (Jet)"),
    (0, b"\x00\x01\x00\x00Standard ACE DB", "access", "2007+ (ACE)"),
    
    # dBase / DBF family
    (0, b"\x03", "dbf", "dBase III"),
    (0, b"\x83", "dbf", "dBase III + memo"),
    (0, b"\x8b", "dbf", "dBase IV + memo"),
    (0, b"\xf5", "dbf", "FoxPro"),
    (0, b"\x30", "dbf", "Visual FoxPro"),
    (0, b"\x31", "dbf", "Visual FoxPro + autoincrement"),
    
    # H2 Database (Java)
    (0, b"-- H2 0.5/B", "h2", "0.5"),
    
    # Firebird / InterBase
    (0, b"\x01\x00\x00\x00", "firebird", "unknown"),
    
    # Berkeley DB
    (12, b"\x00\x05\x31\x62", "berkeleydb", "unknown"),
    (12, b"\x62\x31\x05\x00", "berkeleydb", "unknown (LE)"),
    
    # Apache Derby
    (0, b"\x00\x00\x04\x00", "derby", "unknown"),
    
    # Redis RDB
    (0, b"REDIS", "redis-rdb", "unknown"),
]

# Extension hints when signature detection fails
EXTENSION_HINTS = {
    ".db": ("sqlite", "Could be SQLite or other formats"),
    ".sqlite": ("sqlite", "Likely SQLite"),
    ".sqlite3": ("sqlite", "Likely SQLite 3.x"),
    ".mdb": ("access", "Microsoft Access 2003 or earlier"),
    ".accdb": ("access", "Microsoft Access 2007+"),
    ".dbf": ("dbf", "dBase/FoxPro/Clipper"),
    ".fdb": ("firebird", "Firebird database"),
    ".gdb": ("firebird", "Firebird/InterBase database"),
    ".h2.db": ("h2", "H2 Database"),
    ".kdbx": ("keepass", "KeePass database (encrypted)"),
    ".realm": ("realm", "Realm mobile database"),
    ".rdb": ("redis-rdb", "Redis database dump"),
}

# DBeaver CLI compatibility
DBEAVER_SUPPORTED = {
    "sqlite": True,
    "mysql": True,  # Server-based, uses connection strings not files
    "access": True,
    "dbf": True,
    "h2": True,
    "firebird": True,
    "derby": True,
    "berkeleydb": False,
    "redis-rdb": False,
    "keepass": False,
    "realm": False,
}


def read_file_header(filepath: str, size: int = 64) -> bytes:
    """Read the first N bytes of a file."""
    with open(filepath, "rb") as f:
        return f.read(size)


def detect_by_signature(header: bytes) -> Optional[dict]:
    """Detect database format by magic bytes signature."""
    for offset, magic, fmt, version in SIGNATURES:
        if len(header) >= offset + len(magic):
            if header[offset:offset + len(magic)] == magic:
                return {
                    "format": fmt,
                    "version": version,
                    "detection_method": "signature",
                    "confidence": "high",
                }
    return None


def detect_by_extension(filepath: str) -> Optional[dict]:
    """Guess format by file extension (lower confidence)."""
    path = Path(filepath)
    name_lower = path.name.lower()
    
    for ext, (fmt, note) in EXTENSION_HINTS.items():
        if name_lower.endswith(ext):
            return {
                "format": fmt,
                "version": "unknown",
                "detection_method": "extension",
                "confidence": "low",
                "note": note,
            }
    return None


def format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def identify(filepath: str) -> dict:
    """
    Identify database file format.
    
    Returns dict with:
        - format: Database format name (or "unknown")
        - version: Version if detectable
        - detection_method: "signature" or "extension"
        - confidence: "high", "low", or "none"
        - dbeaver_supported: Whether DBeaver CLI can handle this format
        - file_info: Size, path info
    """
    path = Path(filepath)
    
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    
    if not path.is_file():
        return {"error": f"Not a file: {filepath}"}
    
    # Get file info
    stat = path.stat()
    file_info = {
        "path": str(path.absolute()),
        "name": path.name,
        "size_bytes": stat.st_size,
        "size_human": format_size(stat.st_size),
    }
    
    # Try signature detection first
    try:
        header = read_file_header(filepath)
        result = detect_by_signature(header)
    except PermissionError:
        return {"error": f"Permission denied: {filepath}", "file_info": file_info}
    except Exception as e:
        return {"error": f"Could not read file: {e}", "file_info": file_info}
    
    # Fall back to extension detection
    if not result:
        result = detect_by_extension(filepath)
    
    # Unknown format
    if not result:
        return {
            "format": "unknown",
            "version": None,
            "detection_method": "none",
            "confidence": "none",
            "dbeaver_supported": None,
            "file_info": file_info,
        }
    
    # Add file info and DBeaver support
    result["file_info"] = file_info
    result["dbeaver_supported"] = DBEAVER_SUPPORTED.get(result["format"])
    
    return result


def list_supported_formats() -> dict:
    """List all detectable database formats."""
    formats = {}
    for _, _, fmt, version in SIGNATURES:
        if fmt not in formats:
            formats[fmt] = {
                "versions": [],
                "dbeaver_supported": DBEAVER_SUPPORTED.get(fmt),
            }
        if version not in formats[fmt]["versions"]:
            formats[fmt]["versions"].append(version)
    return formats


def main():
    parser = argparse.ArgumentParser(
        description="Identify database file format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db_identify.py course.db
  python db_identify.py course.db --json
  python db_identify.py --list-formats
        """
    )
    
    parser.add_argument("database", nargs="?", help="Database file to identify")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--list-formats", "-l", action="store_true", help="List detectable formats")
    
    args = parser.parse_args()
    
    if args.list_formats:
        formats = list_supported_formats()
        if args.json:
            print(json.dumps(formats, indent=2))
        else:
            print("Detectable database formats:\n")
            for fmt, info in formats.items():
                dbeaver = "✓" if info["dbeaver_supported"] else "✗"
                print(f"  {fmt}")
                print(f"    Versions: {', '.join(info['versions'])}")
                print(f"    DBeaver supported: {dbeaver}")
                print()
        return
    
    if not args.database:
        parser.print_help()
        sys.exit(1)
    
    result = identify(args.database)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        print(f"File: {result['file_info']['name']}")
        print(f"Size: {result['file_info']['size_human']}")
        print()
        
        if result["format"] == "unknown":
            print("Format: Unknown")
            print("Could not identify database format.")
            sys.exit(1)
        
        print(f"Format: {result['format']}")
        print(f"Version: {result['version']}")
        print(f"Confidence: {result['confidence']} ({result['detection_method']} detection)")
        
        if result["dbeaver_supported"] is not None:
            dbeaver = "Yes" if result["dbeaver_supported"] else "No"
            print(f"DBeaver supported: {dbeaver}")


if __name__ == "__main__":
    main()
