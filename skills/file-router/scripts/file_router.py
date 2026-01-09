#!/usr/bin/env python3
"""
File Router - Unified file identification and routing.

Usage:
    python file_router.py FILE [OPTIONS]
    python file_router.py --dir DIRECTORY [OPTIONS]
    python file_router.py --list-types
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Optional

# Magic byte signatures: (offset, bytes, file_type, processor)
SIGNATURES = [
    # Databases
    (0, b"SQLite format 3\x00", "sqlite", "db-extractor-sqlite"),
    (0, b"\x00\x01\x00\x00Standard Jet DB", "access", "db-identify"),
    (0, b"\x00\x01\x00\x00Standard ACE DB", "access", "db-identify"),

    # PDF
    (0, b"%PDF-", "pdf", "pdf"),

    # Images
    (0, b"\x89PNG\r\n\x1a\n", "png", "image-ocr"),
    (0, b"\xff\xd8\xff", "jpeg", "image-ocr"),
    (0, b"GIF87a", "gif", "image-ocr"),
    (0, b"GIF89a", "gif", "image-ocr"),
    (0, b"BM", "bmp", "image-ocr"),
    (0, b"II\x2a\x00", "tiff", "image-ocr"),  # Little-endian TIFF
    (0, b"MM\x00\x2a", "tiff", "image-ocr"),  # Big-endian TIFF

    # Archives
    (0, b"PK\x03\x04", "zip", None),  # Could be zip or OOXML - needs deeper inspection
    (0, b"Rar!\x1a\x07\x00", "rar", "archive-extractor"),
    (0, b"Rar!\x1a\x07\x01\x00", "rar5", "archive-extractor"),
    (0, b"7z\xbc\xaf\x27\x1c", "7z", "archive-extractor"),
    (0, b"\x1f\x8b", "gzip", "archive-extractor"),
    (257, b"ustar", "tar", "archive-extractor"),  # tar magic at offset 257
]

# OOXML detection for Office docs (all start with PK zip signature)
OOXML_TYPES = {
    "word/document.xml": ("docx", "docx"),
    "ppt/presentation.xml": ("pptx", "pptx"),
    "xl/workbook.xml": ("xlsx", "xlsx-processor"),
}

# Extension fallback mapping
EXTENSION_MAP = {
    # Documents
    ".pdf": ("pdf", "pdf"),
    ".docx": ("docx", "docx"),
    ".doc": ("doc", "docx"),
    ".pptx": ("pptx", "pptx"),
    ".ppt": ("ppt", "pptx"),
    ".xlsx": ("xlsx", "xlsx-processor"),
    ".xls": ("xls", "xlsx-processor"),

    # Databases
    ".db": ("sqlite", "db-extractor-sqlite"),
    ".sqlite": ("sqlite", "db-extractor-sqlite"),
    ".sqlite3": ("sqlite", "db-extractor-sqlite"),
    ".mdb": ("access", "db-identify"),
    ".accdb": ("access", "db-identify"),

    # HTML
    ".html": ("html", "html2markdown"),
    ".htm": ("html", "html2markdown"),
    ".xhtml": ("html", "html2markdown"),

    # Images
    ".png": ("png", "image-ocr"),
    ".jpg": ("jpeg", "image-ocr"),
    ".jpeg": ("jpeg", "image-ocr"),
    ".gif": ("gif", "image-ocr"),
    ".bmp": ("bmp", "image-ocr"),
    ".tiff": ("tiff", "image-ocr"),
    ".tif": ("tiff", "image-ocr"),

    # Archives
    ".zip": ("zip", "archive-extractor"),
    ".rar": ("rar", "archive-extractor"),
    ".7z": ("7z", "archive-extractor"),
    ".tar": ("tar", "archive-extractor"),
    ".gz": ("gzip", "archive-extractor"),
    ".tgz": ("tar.gz", "archive-extractor"),
    ".tar.gz": ("tar.gz", "archive-extractor"),
    ".tar.bz2": ("tar.bz2", "archive-extractor"),

    # Text/Code (passthrough)
    ".txt": ("text", "passthrough"),
    ".md": ("markdown", "passthrough"),
    ".csv": ("csv", "passthrough"),
    ".json": ("json", "passthrough"),
    ".xml": ("xml", "passthrough"),
    ".yaml": ("yaml", "passthrough"),
    ".yml": ("yaml", "passthrough"),
    ".srt": ("srt", "passthrough"),
    ".vtt": ("vtt", "passthrough"),

    # Source code (passthrough)
    ".ts": ("typescript", "passthrough"),
    ".tsx": ("typescript", "passthrough"),
    ".js": ("javascript", "passthrough"),
    ".jsx": ("javascript", "passthrough"),
    ".py": ("python", "passthrough"),
    ".java": ("java", "passthrough"),
    ".c": ("c", "passthrough"),
    ".cpp": ("cpp", "passthrough"),
    ".h": ("c-header", "passthrough"),
    ".hpp": ("cpp-header", "passthrough"),
    ".cs": ("csharp", "passthrough"),
    ".go": ("go", "passthrough"),
    ".rs": ("rust", "passthrough"),
    ".rb": ("ruby", "passthrough"),
    ".php": ("php", "passthrough"),
    ".swift": ("swift", "passthrough"),
    ".kt": ("kotlin", "passthrough"),
    ".sql": ("sql", "passthrough"),
    ".sh": ("shell", "passthrough"),
    ".bash": ("shell", "passthrough"),
    ".ps1": ("powershell", "passthrough"),
    ".bat": ("batch", "passthrough"),
    ".cmd": ("batch", "passthrough"),

    # Video (skip)
    ".mp4": ("video", "skip"),
    ".mkv": ("video", "skip"),
    ".avi": ("video", "skip"),
    ".mov": ("video", "skip"),
    ".wmv": ("video", "skip"),
    ".flv": ("video", "skip"),
    ".webm": ("video", "skip"),

    # Audio (skip)
    ".mp3": ("audio", "skip"),
    ".wav": ("audio", "skip"),
    ".flac": ("audio", "skip"),
    ".aac": ("audio", "skip"),
    ".ogg": ("audio", "skip"),
    ".wma": ("audio", "skip"),
    ".m4a": ("audio", "skip"),
}


def read_header(filepath: str, size: int = 512) -> bytes:
    """Read file header for signature detection."""
    with open(filepath, "rb") as f:
        return f.read(size)


def detect_ooxml_type(filepath: str) -> Optional[tuple]:
    """Detect Office XML document type by inspecting zip contents."""
    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            names = zf.namelist()
            for marker, (file_type, processor) in OOXML_TYPES.items():
                if marker in names:
                    return (file_type, processor)
    except (zipfile.BadZipFile, IOError):
        pass
    return None


def detect_by_signature(header: bytes, filepath: str) -> Optional[dict]:
    """Detect file type by magic bytes."""
    for offset, magic, file_type, processor in SIGNATURES:
        if len(header) >= offset + len(magic):
            if header[offset : offset + len(magic)] == magic:
                # Special handling for PK signature (could be zip or OOXML)
                if file_type == "zip":
                    ooxml = detect_ooxml_type(filepath)
                    if ooxml:
                        return {
                            "file_type": ooxml[0],
                            "processor": ooxml[1],
                            "detection_method": "signature",
                            "confidence": "high",
                        }
                    # Regular zip file
                    return {
                        "file_type": "zip",
                        "processor": "archive-extractor",
                        "detection_method": "signature",
                        "confidence": "high",
                    }
                return {
                    "file_type": file_type,
                    "processor": processor,
                    "detection_method": "signature",
                    "confidence": "high",
                }
    return None


def detect_by_extension(filepath: str) -> Optional[dict]:
    """Fallback detection by file extension."""
    path = Path(filepath)
    ext = path.suffix.lower()

    # Handle compound extensions
    name_lower = path.name.lower()
    for compound in [".tar.gz", ".tar.bz2", ".tar.xz"]:
        if name_lower.endswith(compound):
            ext = compound
            break

    if ext in EXTENSION_MAP:
        file_type, processor = EXTENSION_MAP[ext]
        return {
            "file_type": file_type,
            "processor": processor,
            "detection_method": "extension",
            "confidence": "low",
        }
    return None


def route_file(filepath: str) -> dict:
    """Identify file type and determine processor."""
    path = Path(filepath)

    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    if not path.is_file():
        return {"error": f"Not a file: {filepath}"}

    stat = path.stat()
    metadata = {
        "path": str(path.absolute()),
        "name": path.name,
        "size_bytes": stat.st_size,
        "extension": path.suffix.lower(),
    }

    # Try signature detection
    try:
        header = read_header(filepath)
        result = detect_by_signature(header, filepath)
    except Exception as e:
        return {"error": str(e), "metadata": metadata}

    # Fallback to extension
    if not result:
        result = detect_by_extension(filepath)

    # Unknown type
    if not result:
        return {
            "file_type": "unknown",
            "processor": None,
            "detection_method": "none",
            "confidence": "none",
            "metadata": metadata,
        }

    result["metadata"] = metadata
    return result


def process_directory(dirpath: str, recursive: bool = False) -> list:
    """Process all files in a directory."""
    results = []
    path = Path(dirpath)

    if not path.exists() or not path.is_dir():
        return [{"error": f"Invalid directory: {dirpath}"}]

    glob_pattern = "**/*" if recursive else "*"
    for file_path in path.glob(glob_pattern):
        if file_path.is_file():
            results.append(route_file(str(file_path)))

    return results


def list_supported_types() -> dict:
    """List all supported file types and their processors."""
    types = {}

    # From signatures
    for _, _, file_type, processor in SIGNATURES:
        if file_type not in types and processor:
            types[file_type] = {"processor": processor, "detection": "signature"}

    # From extensions
    for ext, (file_type, processor) in EXTENSION_MAP.items():
        if file_type not in types:
            types[file_type] = {"processor": processor, "detection": "extension"}

    return types


def format_human_readable(result: dict) -> str:
    """Format result for human consumption."""
    if "error" in result:
        return f"Error: {result['error']}"

    metadata = result.get("metadata", {})
    size_bytes = metadata.get("size_bytes", 0)
    size_str = (
        f"{size_bytes / 1024 / 1024:.1f} MB"
        if size_bytes > 1024 * 1024
        else f"{size_bytes / 1024:.1f} KB"
        if size_bytes > 1024
        else f"{size_bytes} B"
    )

    lines = [
        f"File: {metadata.get('name', 'unknown')}",
        f"Size: {size_str}",
        "",
        f"Type: {result.get('file_type', 'unknown')}",
        f"Processor: {result.get('processor', 'none')}",
        f"Confidence: {result.get('confidence', 'none')} ({result.get('detection_method', 'none')})",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="File Router - Unified file identification and routing"
    )
    parser.add_argument("file", nargs="?", help="File to identify and route")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument("-d", "--dir", help="Process directory")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursive directory scan"
    )
    parser.add_argument(
        "-l", "--list-types", action="store_true", help="Show supported file types"
    )

    args = parser.parse_args()

    # List types mode
    if args.list_types:
        types = list_supported_types()
        if args.json:
            print(json.dumps(types, indent=2))
        else:
            print("Supported File Types:\n")
            for file_type, info in sorted(types.items()):
                print(
                    f"  {file_type:15} -> {info['processor']:20} ({info['detection']})"
                )
        return 0

    # Directory mode
    if args.dir:
        results = process_directory(args.dir, args.recursive)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                print(format_human_readable(result))
                print("-" * 40)
        return 0

    # Single file mode
    if not args.file:
        parser.print_help()
        return 1

    result = route_file(args.file)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human_readable(result))

    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
