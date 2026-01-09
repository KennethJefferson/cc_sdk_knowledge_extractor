---
name: file-router
description: Unified file identification and routing for CCKnowledgeExtractor pipeline. Detects file types via magic bytes with extension fallback, returns processor skill to invoke. Use FIRST when processing any unknown file. Handles databases (sqlite, access), PDFs, images (png, jpg, gif, bmp, tiff), HTML, archives (zip, rar, 7z, tar), Office docs (docx, pptx, xlsx), and plain text.
---

# File Router

Unified file type detection and processor routing.

## Quick Start

```bash
# Identify and route a single file
python scripts/file_router.py path/to/file

# JSON output for pipeline
python scripts/file_router.py path/to/file --json

# Batch process directory
python scripts/file_router.py --dir /path/to/folder --json

# List all supported types
python scripts/file_router.py --list-types
```

## Output

Human-readable:
```
File: document.pdf
Size: 2.1 MB

Type: pdf
Processor: pdf
Confidence: high (signature)
```

JSON (for pipeline):
```json
{
  "file_type": "pdf",
  "processor": "pdf",
  "confidence": "high",
  "detection_method": "signature",
  "metadata": {
    "path": "/path/to/document.pdf",
    "size_bytes": 2200000,
    "extension": ".pdf"
  }
}
```

## Routing Table

| Type | Processor Skill | Detection Method |
|------|-----------------|------------------|
| sqlite | db-extractor-sqlite | signature |
| access | db-identify | signature |
| pdf | pdf | signature |
| docx | docx | signature (PK zip + [Content_Types].xml) |
| pptx | pptx | signature (PK zip + [Content_Types].xml) |
| xlsx | xlsx-processor | signature (PK zip + [Content_Types].xml) |
| html | html2markdown | extension + content sniff |
| png/jpg/gif/bmp/tiff | image-ocr | signature |
| zip/rar/7z/tar | archive-extractor | signature |
| txt/md/csv/json/code | passthrough | extension |

## Detection Priority

1. Magic byte signature (high confidence)
2. OOXML container inspection for Office docs
3. Extension hint (low confidence)

## Pipeline Integration

Typical workflow:
```bash
# Step 1: Route the file
ROUTE=$(python file_router.py input.file --json)

# Step 2: Extract processor
PROCESSOR=$(echo "$ROUTE" | jq -r '.processor')

# Step 3: Invoke processor skill based on result
```

## CLI Reference

```
python scripts/file_router.py FILE [OPTIONS]
python scripts/file_router.py --dir DIRECTORY [OPTIONS]
python scripts/file_router.py --list-types

Arguments:
  FILE                  File to identify and route

Options:
  -j, --json            Output as JSON
  -d, --dir PATH        Process directory (returns list)
  -r, --recursive       Recursive directory scan
  -l, --list-types      Show supported file types
```
