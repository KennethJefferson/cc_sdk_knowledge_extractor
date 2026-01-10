#!/usr/bin/env python3
"""
PPTX Text Extractor - Extract text content from PowerPoint presentations.

Usage:
    python extract_text.py INPUT.pptx [-o OUTPUT.md] [--json]
"""

import argparse
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


# OOXML namespaces
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}


def extract_text_from_xml(xml_content: bytes) -> list[str]:
    """Extract all text elements from an XML slide."""
    texts = []
    try:
        root = ET.fromstring(xml_content)
        # Find all text elements (a:t tags)
        for text_elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
            if text_elem.text:
                texts.append(text_elem.text)
    except ET.ParseError:
        pass
    return texts


def extract_from_pptx(pptx_path: str) -> dict:
    """Extract all text from a PPTX file."""
    path = Path(pptx_path)

    if not path.exists():
        return {"error": f"File not found: {pptx_path}"}

    if path.suffix.lower() not in ['.pptx', '.ppt']:
        return {"error": f"Not a PowerPoint file: {path.suffix}"}

    try:
        slides = []
        notes = []

        with zipfile.ZipFile(pptx_path, 'r') as zf:
            # Get list of all files in the archive
            file_list = zf.namelist()

            # Extract slide content
            slide_files = sorted([f for f in file_list if f.startswith('ppt/slides/slide') and f.endswith('.xml')])

            for i, slide_file in enumerate(slide_files, 1):
                try:
                    xml_content = zf.read(slide_file)
                    texts = extract_text_from_xml(xml_content)
                    if texts:
                        slides.append({
                            "slide_number": i,
                            "content": texts
                        })
                except Exception:
                    continue

            # Extract notes
            notes_files = sorted([f for f in file_list if f.startswith('ppt/notesSlides/') and f.endswith('.xml')])

            for notes_file in notes_files:
                try:
                    xml_content = zf.read(notes_file)
                    texts = extract_text_from_xml(xml_content)
                    if texts:
                        # Filter out slide number placeholders
                        filtered = [t for t in texts if not t.isdigit() and len(t) > 1]
                        if filtered:
                            notes.extend(filtered)
                except Exception:
                    continue

        # Combine all text
        all_text = []
        for slide in slides:
            all_text.extend(slide["content"])
        all_text.extend(notes)

        return {
            "source": str(path.absolute()),
            "slide_count": len(slides),
            "slides": slides,
            "notes": notes,
            "text": "\n".join(all_text),
            "char_count": sum(len(t) for t in all_text),
        }

    except zipfile.BadZipFile:
        return {"error": f"Invalid or corrupted PPTX file: {pptx_path}"}
    except Exception as e:
        return {"error": str(e), "source": str(path.absolute())}


def format_as_markdown(result: dict) -> str:
    """Format extracted content as Markdown."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [f"# {Path(result.get('source', 'Presentation')).stem}", ""]

    for slide in result.get("slides", []):
        lines.append(f"## Slide {slide['slide_number']}")
        lines.append("")
        for text in slide["content"]:
            lines.append(text)
        lines.append("")

    if result.get("notes"):
        lines.append("## Speaker Notes")
        lines.append("")
        for note in result["notes"]:
            lines.append(note)
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PowerPoint presentations"
    )
    parser.add_argument("input", help="Input PPTX file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = extract_from_pptx(args.input)

    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_as_markdown(result)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        # Always write plain text content to file for downstream processing
        text_content = result.get("text", "")
        Path(args.output).write_text(text_content, encoding="utf-8")
        # Print JSON status for the invoker
        if args.json:
            print(json.dumps({"success": True, "output": args.output, "char_count": len(text_content)}))
        else:
            print(f"Wrote {len(text_content)} characters to {args.output}")
    else:
        print(output)

    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
