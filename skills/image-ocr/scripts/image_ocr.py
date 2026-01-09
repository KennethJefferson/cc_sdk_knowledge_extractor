#!/usr/bin/env python3
"""
Image OCR - Extract text from images using pytesseract.

Usage:
    python image_ocr.py IMAGE [OPTIONS]
    python image_ocr.py --dir DIRECTORY [OPTIONS]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print(
        "ERROR: Missing dependencies. Install with: pip install pytesseract Pillow",
        file=sys.stderr,
    )
    sys.exit(1)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"}


def extract_text(
    image_path: str, lang: str = "eng", dpi: int = 300, psm: int = 3
) -> dict:
    """Extract text from image using Tesseract OCR."""
    path = Path(image_path)

    if not path.exists():
        return {"error": f"File not found: {image_path}"}

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {"error": f"Unsupported image format: {path.suffix}"}

    try:
        img = Image.open(image_path)

        # Configure tesseract
        config = f"--dpi {dpi} --psm {psm}"

        # Get OCR data with confidence
        try:
            data = pytesseract.image_to_data(
                img, lang=lang, config=config, output_type=pytesseract.Output.DICT
            )

            # Calculate average confidence (excluding empty entries)
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        except Exception:
            avg_confidence = 0

        # Extract text
        text = pytesseract.image_to_string(img, lang=lang, config=config)

        return {
            "source": str(path.absolute()),
            "text": text.strip(),
            "char_count": len(text.strip()),
            "confidence": round(avg_confidence, 1),
            "language": lang,
        }
    except pytesseract.TesseractNotFoundError:
        return {
            "error": "Tesseract not found. Please install Tesseract OCR and ensure it's in PATH.",
            "source": str(path.absolute()),
        }
    except Exception as e:
        return {"error": str(e), "source": str(path.absolute())}


def process_directory(
    dir_path: str,
    output_dir: Optional[str],
    lang: str,
    dpi: int,
    psm: int,
    quiet: bool,
) -> list:
    """Process all images in directory."""
    results = []
    dir_path_obj = Path(dir_path)

    if not dir_path_obj.exists() or not dir_path_obj.is_dir():
        return [{"error": f"Invalid directory: {dir_path}"}]

    for ext in SUPPORTED_EXTENSIONS:
        for img_file in dir_path_obj.rglob(f"*{ext}"):
            if not quiet:
                print(f"Processing: {img_file}", file=sys.stderr)

            result = extract_text(str(img_file), lang, dpi, psm)
            results.append(result)

            if output_dir and "text" in result and result["text"]:
                out_path = Path(output_dir) / f"{img_file.stem}.txt"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(result["text"], encoding="utf-8")

    return results


def format_human_readable(result: dict) -> str:
    """Format result for human consumption."""
    if "error" in result:
        return f"Error: {result['error']}"

    lines = [
        f"File: {Path(result.get('source', 'unknown')).name}",
        f"Characters extracted: {result.get('char_count', 0)}",
        f"Confidence: {result.get('confidence', 0)}%",
        "",
        result.get("text", ""),
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Image OCR - Extract text from images using pytesseract"
    )
    parser.add_argument("image", nargs="?", help="Image file to process")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("-d", "--dir", help="Process directory of images")
    parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "-l", "--lang", default="eng", help="Tesseract language code (default: eng)"
    )
    parser.add_argument(
        "--dpi", type=int, default=300, help="Image DPI for processing (default: 300)"
    )
    parser.add_argument(
        "--psm", type=int, default=3, help="Page segmentation mode (default: 3)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress progress output"
    )

    args = parser.parse_args()

    # Directory mode
    if args.dir:
        results = process_directory(
            args.dir, args.output, args.lang, args.dpi, args.psm, args.quiet
        )
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                print(format_human_readable(result))
                print("-" * 40)
        return 0

    # Single file mode
    if not args.image:
        parser.print_help()
        return 1

    result = extract_text(args.image, args.lang, args.dpi, args.psm)

    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = format_human_readable(result)

    if args.output:
        Path(args.output).write_text(
            result.get("text", "") if not args.json else output, encoding="utf-8"
        )
    else:
        print(output)

    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
