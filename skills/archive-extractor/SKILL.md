---
name: archive-extractor
description: Extract archive files using 7z CLI. Handles ZIP, RAR, 7z, TAR, TAR.GZ, TAR.BZ2 formats. Extracts to subfolder named after archive. Returns list of extracted files for further processing by file-router. Use when processing compressed archives containing course materials or mixed file types.
---

# Archive Extractor

Extract archives using 7-Zip CLI.

## Prerequisites

- **7-Zip** must be installed and in PATH:
  ```bash
  # Windows - typically installed at:
  # C:\Program Files\7-Zip\7z.exe

  # Verify
  7z --help
  ```

## Quick Start

```bash
# Extract archive to subfolder (archive-name/)
python scripts/archive_extract.py archive.zip

# Extract to specific location
python scripts/archive_extract.py archive.rar -o ./extracted

# JSON output with file list
python scripts/archive_extract.py course.7z --json

# Extract with password
python scripts/archive_extract.py protected.zip --password secret
```

## Output

Human-readable:
```
Archive: course_materials.zip
Extracting to: ./course_materials/

Extracted 15 files:
  course_materials/lesson1.pdf
  course_materials/lesson2.docx
  course_materials/images/diagram.png
  ...
```

JSON:
```json
{
  "source": "course_materials.zip",
  "destination": "./course_materials",
  "file_count": 15,
  "files": [
    {"path": "course_materials/lesson1.pdf", "size": 102400},
    {"path": "course_materials/lesson2.docx", "size": 51200}
  ],
  "status": "success"
}
```

## Supported Formats

| Format | Extensions | Notes |
|--------|------------|-------|
| ZIP | .zip | Standard zip archives |
| RAR | .rar | RAR4 and RAR5 |
| 7-Zip | .7z | High compression |
| TAR | .tar | Tape archive |
| GZIP | .tar.gz, .tgz | Gzipped tar |
| BZIP2 | .tar.bz2 | Bzipped tar |

## CLI Reference

```
python scripts/archive_extract.py ARCHIVE [OPTIONS]

Arguments:
  ARCHIVE               Archive file to extract

Options:
  -o, --output DIR      Output directory (default: archive name as folder)
  -j, --json            Output as JSON with file list
  -p, --password PWD    Archive password
  --flat                Don't create subfolder, extract directly
  --overwrite           Overwrite existing files
  -q, --quiet           Suppress progress output
```

## Pipeline Integration

After extraction, pass file list to file-router for recursive processing:

```bash
# Extract and get file list
FILES=$(python archive_extract.py course.zip --json | jq -r '.files[].path')

# Route each extracted file
for f in $FILES; do
    python file_router.py "$f" --json
done
```

## Extraction Behavior

- **Default**: Creates subfolder named after archive (without extension)
  - `course.zip` extracts to `./course/`
- **With --flat**: Extracts to current directory or specified output
- **Nested archives**: Not automatically extracted (process returned file list)
