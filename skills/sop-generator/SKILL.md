# SOP Generator Skill

Generate Standard Operating Procedures (SOPs) from course content and validated files.

## Purpose

Transforms extracted course content into structured, actionable Standard Operating Procedures. SOPs are step-by-step instructions that document how to perform specific tasks or processes, commonly used in professional, technical, and educational contexts.

## Activation

This skill is invoked via the `-ccg` CLI argument:

```bash
ccke -i ./courses -ccg SOP
ccke -i ./courses -ccg sop
ccke -i ./courses -ccg procedure
ccke -i ./courses -ccg procedures
```

## Input

- Directory containing validated text files (`__cc_validated_files/`)
- Supports: .txt, .md, .srt, .vtt, code files

## Output

Creates `__ccg_SOP/` directory containing:

| File | Description |
|------|-------------|
| `README.md` | Overview of all procedures with navigation |
| `procedures/` | Individual SOP files organized by topic |
| `quick_reference.md` | Condensed checklist version of all procedures |
| `glossary.md` | Terms and definitions used in procedures |

## SOP Format

Each generated SOP follows a standard format:

```markdown
# SOP: [Procedure Title]

## Purpose
Brief description of what this procedure accomplishes.

## Scope
Who should use this procedure and when.

## Prerequisites
- Required knowledge
- Required tools/access
- Required materials

## Procedure

### Step 1: [Action]
Detailed instructions...

**Expected Result:** What should happen

### Step 2: [Action]
...

## Verification
How to confirm the procedure was completed successfully.

## Troubleshooting
Common issues and solutions.

## Related Procedures
Links to related SOPs.
```

## Configuration

The script accepts:
- Input directory (positional)
- `-o, --output` - Output directory
- `--json` - JSON output mode
- `--min-steps` - Minimum steps to form a procedure (default: 3)
- `--max-depth` - Maximum nesting depth (default: 3)

## Dependencies

- Python 3.8+
- No external packages required (stdlib only)
