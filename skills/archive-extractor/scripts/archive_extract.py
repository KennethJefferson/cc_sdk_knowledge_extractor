#!/usr/bin/env python3
"""
Archive Extractor - Extract archives using 7z CLI.

Usage:
    python archive_extract.py ARCHIVE [OPTIONS]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

SUPPORTED_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"}


def find_7z() -> str:
    """Find 7z executable."""
    # Try common Windows locations
    common_paths = [
        "7z",
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]

    for path in common_paths:
        try:
            result = subprocess.run(
                [path, "--help"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0:
                return path
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        "7z not found. Install 7-Zip and ensure it's in PATH or at default location."
    )


def extract_archive(
    archive_path: str,
    output_dir: Optional[str] = None,
    password: Optional[str] = None,
    flat: bool = False,
    overwrite: bool = False,
    quiet: bool = False,
) -> dict:
    """Extract archive using 7z."""
    path = Path(archive_path)

    if not path.exists():
        return {"error": f"Archive not found: {archive_path}"}

    # Determine output directory
    if output_dir:
        dest = Path(output_dir)
    elif flat:
        dest = path.parent
    else:
        # Create subfolder from archive name (handle compound extensions)
        stem = path.stem
        if stem.endswith(".tar"):
            stem = stem[:-4]
        dest = path.parent / stem

    dest.mkdir(parents=True, exist_ok=True)

    # Find 7z
    try:
        sevenzip = find_7z()
    except FileNotFoundError as e:
        return {"error": str(e)}

    # Build 7z command
    cmd = [sevenzip, "x", str(path), f"-o{dest}"]

    if password:
        cmd.append(f"-p{password}")

    if overwrite:
        cmd.append("-aoa")  # Overwrite all
    else:
        cmd.append("-aos")  # Skip existing

    cmd.append("-y")  # Assume yes

    if not quiet:
        print(f"Extracting: {path.name} -> {dest}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        if result.returncode != 0:
            # Check for common errors
            stderr = result.stderr.lower()
            if "wrong password" in stderr or "encrypted" in stderr:
                return {
                    "error": "Archive is password protected. Use --password flag.",
                    "source": str(path.absolute()),
                }
            return {
                "error": f"Extraction failed: {result.stderr.strip()}",
                "source": str(path.absolute()),
            }

        # List extracted files
        extracted_files = []
        for file_path in dest.rglob("*"):
            if file_path.is_file():
                extracted_files.append(
                    {
                        "path": str(file_path),
                        "relative_path": str(file_path.relative_to(dest)),
                        "size": file_path.stat().st_size,
                    }
                )

        return {
            "source": str(path.absolute()),
            "destination": str(dest.absolute()),
            "file_count": len(extracted_files),
            "files": extracted_files,
            "status": "success",
        }

    except Exception as e:
        return {"error": str(e), "source": str(path.absolute())}


def format_human_readable(result: dict) -> str:
    """Format result for human consumption."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [
        f"Archive: {Path(result.get('source', 'unknown')).name}",
        f"Extracting to: {result.get('destination', 'unknown')}",
        "",
        f"Extracted {result.get('file_count', 0)} files:",
    ]

    files = result.get("files", [])
    for f in files[:20]:  # Show first 20 files
        size = f.get("size", 0)
        size_str = (
            f"{size / 1024:.1f} KB"
            if size > 1024
            else f"{size} B"
        )
        lines.append(f"  {f.get('relative_path', 'unknown')} ({size_str})")

    if len(files) > 20:
        lines.append(f"  ... and {len(files) - 20} more files")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Archive Extractor - Extract archives using 7z CLI"
    )
    parser.add_argument("archive", nargs="?", help="Archive file to extract")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument("-p", "--password", help="Archive password")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Don't create subfolder, extract directly",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress progress output"
    )

    args = parser.parse_args()

    if not args.archive:
        parser.print_help()
        return 1

    result = extract_archive(
        args.archive,
        output_dir=args.output,
        password=args.password,
        flat=args.flat,
        overwrite=args.overwrite,
        quiet=args.quiet,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human_readable(result))

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
