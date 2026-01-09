#!/usr/bin/env python3
"""
Batch convert HTML files to Markdown using pandoc.

Usage:
    python html2markdown.py /path/to/directory [options]

Options:
    --output-dir DIR    Output directory (default: in-place)
    --flatten           Flatten output to single directory
    --wrap MODE         Line wrap mode: none, auto, preserve (default: none)
    --format FMT        Output format: markdown, gfm, commonmark (default: markdown)
    --exclude PATTERN   Glob pattern to exclude (can be used multiple times)
    --strip-elements    Strip script, style, nav, footer, header before conversion
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_html_files(root_dir: Path, exclude_patterns: list[str] = None) -> list[Path]:
    """Recursively find all HTML files in directory."""
    exclude_patterns = exclude_patterns or []
    html_files = []
    
    for html_file in root_dir.rglob("*.html"):
        # Check exclusion patterns
        excluded = False
        for pattern in exclude_patterns:
            if html_file.match(pattern):
                excluded = True
                break
        
        if not excluded:
            html_files.append(html_file)
    
    # Also check for .htm files
    for htm_file in root_dir.rglob("*.htm"):
        excluded = False
        for pattern in exclude_patterns:
            if htm_file.match(pattern):
                excluded = True
                break
        
        if not excluded:
            html_files.append(htm_file)
    
    return sorted(html_files)


def strip_unwanted_elements(html_content: str) -> str:
    """Remove script, style, nav, footer, header elements from HTML."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
            tag.decompose()
        
        return str(soup)
    except ImportError:
        print("Warning: BeautifulSoup not installed. Skipping element stripping.", file=sys.stderr)
        return html_content


def convert_html_to_markdown(
    html_file: Path,
    output_file: Path,
    wrap_mode: str = "none",
    output_format: str = "markdown",
    strip_elements: bool = False
) -> bool:
    """Convert a single HTML file to Markdown using pandoc."""
    
    try:
        # Build pandoc command
        cmd = [
            "pandoc",
            "-f", "html",
            "-t", output_format,
            f"--wrap={wrap_mode}",
        ]
        
        if strip_elements:
            # Read, strip, and pipe to pandoc
            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            
            html_content = strip_unwanted_elements(html_content)
            
            cmd.extend(["-o", str(output_file)])
            
            result = subprocess.run(
                cmd,
                input=html_content,
                capture_output=True,
                text=True
            )
        else:
            # Direct file conversion
            cmd.extend([str(html_file), "-o", str(output_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error converting {html_file}: {result.stderr}", file=sys.stderr)
            return False
        
        return True
        
    except Exception as e:
        print(f"Error converting {html_file}: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert HTML files to Markdown using pandoc"
    )
    parser.add_argument("directory", type=Path, help="Root directory to scan")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--flatten", action="store_true", help="Flatten to single directory")
    parser.add_argument("--wrap", choices=["none", "auto", "preserve"], default="none")
    parser.add_argument("--format", choices=["markdown", "gfm", "commonmark"], default="markdown")
    parser.add_argument("--exclude", action="append", default=[], help="Patterns to exclude")
    parser.add_argument("--strip-elements", action="store_true", 
                       help="Strip script, style, nav, footer, header elements")
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        sys.exit(1)
    
    # Check pandoc is installed
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: pandoc is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)
    
    html_files = find_html_files(args.directory, args.exclude)
    
    if not html_files:
        print("No HTML files found.")
        sys.exit(0)
    
    print(f"Found {len(html_files)} HTML file(s)")
    
    success_count = 0
    fail_count = 0
    
    for html_file in html_files:
        # Determine output path
        if args.output_dir:
            if args.flatten:
                # Flatten: all files in output dir with unique names
                output_file = args.output_dir / f"{html_file.stem}.md"
                # Handle name collisions
                counter = 1
                while output_file.exists():
                    output_file = args.output_dir / f"{html_file.stem}_{counter}.md"
                    counter += 1
            else:
                # Preserve directory structure
                relative_path = html_file.relative_to(args.directory)
                output_file = args.output_dir / relative_path.with_suffix('.md')
        else:
            # In-place: same directory as source
            output_file = html_file.with_suffix('.md')
        
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Converting: {html_file} -> {output_file}")
        
        if convert_html_to_markdown(
            html_file, output_file, args.wrap, args.format, args.strip_elements
        ):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\nComplete: {success_count} succeeded, {fail_count} failed")
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
