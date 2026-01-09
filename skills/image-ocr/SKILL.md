---
name: image-ocr
description: Extract text from images using pytesseract OCR. Handles PNG, JPG, JPEG, GIF, BMP, TIFF formats. Use when processing image files that may contain text, diagrams with labels, screenshots, or scanned documents. Returns extracted text content.
---

# Image OCR

Extract text from images using Tesseract OCR.

## Prerequisites

- **Tesseract OCR** must be installed:
  ```bash
  # Windows (via chocolatey)
  choco install tesseract

  # Or download from: https://github.com/UB-Mannheim/tesseract/wiki

  # Verify
  tesseract --version
  ```

- **Python packages**:
  ```bash
  pip install pytesseract Pillow
  ```

## Quick Start

```bash
# Extract text from single image
python scripts/image_ocr.py image.png

# Output to file
python scripts/image_ocr.py image.png -o output.txt

# JSON output with confidence
python scripts/image_ocr.py image.png --json

# Batch process directory
python scripts/image_ocr.py --dir /path/to/images -o ./extracted

# Specify language
python scripts/image_ocr.py image.png --lang eng+fra
```

## Output

Human-readable:
```
File: screenshot.png
Characters extracted: 1523
Confidence: 87.5%

[Extracted text appears here...]
```

JSON:
```json
{
  "source": "screenshot.png",
  "text": "Extracted text content...",
  "char_count": 1523,
  "confidence": 87.5,
  "language": "eng"
}
```

## Supported Formats

| Format | Extensions |
|--------|------------|
| PNG | .png |
| JPEG | .jpg, .jpeg |
| GIF | .gif |
| BMP | .bmp |
| TIFF | .tiff, .tif |

## CLI Reference

```
python scripts/image_ocr.py IMAGE [OPTIONS]

Arguments:
  IMAGE                 Image file to process

Options:
  -o, --output PATH     Output file (default: stdout)
  -d, --dir PATH        Process directory of images
  -j, --json            Output as JSON
  -l, --lang LANG       Tesseract language code (default: eng)
  --dpi DPI             Image DPI for processing (default: 300)
  --psm MODE            Page segmentation mode (default: 3)
  -q, --quiet           Suppress progress output
```

## Integration Notes

Called by file-router when image files are detected. Output text can be passed to quiz-generator or stored in `__cc_validated_files/`.
