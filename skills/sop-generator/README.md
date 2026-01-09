# SOP Generator

Generate Standard Operating Procedures (SOPs) from course content automatically.

## Overview

The SOP Generator skill transforms educational content, tutorials, and documentation into structured Standard Operating Procedures. SOPs are step-by-step instructions that document how to perform specific tasks, making them essential for:

- Training new team members
- Ensuring consistent process execution
- Compliance and audit documentation
- Knowledge preservation

## Features

- **Automatic Procedure Extraction** - Identifies procedural content using action verbs and step patterns
- **Standard SOP Format** - Outputs industry-standard SOP documents with purpose, scope, prerequisites, steps, and verification
- **Quick Reference Generation** - Creates condensed checklists for field use
- **Glossary Extraction** - Automatically identifies and collects term definitions
- **Multi-file Processing** - Aggregates procedures from all validated course files

## Output Structure

```
__ccg_SOP/
├── README.md           # Index of all procedures
├── quick_reference.md  # Condensed checklists
├── glossary.md         # Terms and definitions
└── procedures/
    ├── SOP-001_Setup_Environment.md
    ├── SOP-002_Configure_Database.md
    └── SOP-003_Deploy_Application.md
```

## SOP Document Format

Each generated SOP follows this structure:

1. **Header** - Document ID, source, generation date
2. **Purpose** - What the procedure accomplishes
3. **Scope** - Who should use it and when
4. **Prerequisites** - Required knowledge, tools, access
5. **Procedure** - Numbered steps with details
6. **Verification** - How to confirm success
7. **Troubleshooting** - Common issues and solutions
8. **Related Procedures** - Links to other SOPs

## How It Works

1. Scans validated files for procedural content
2. Identifies steps using:
   - Numbered sequences (1. 2. 3.)
   - Action verbs (click, select, configure, etc.)
   - Sequential markers (first, then, next, finally)
3. Groups steps into logical procedures
4. Generates formatted SOP documents
5. Creates index, quick reference, and glossary

## Requirements

- Python 3.8+
- No external dependencies (uses stdlib only)

## Limitations

- Requires at least 3 steps to form a procedure
- Works best with tutorial-style content
- May need manual review for accuracy
- Does not generate diagrams or flowcharts

## See Also

- [Usage Guide](Usage.md) - Activation phrases and examples
- [SKILL.md](SKILL.md) - Technical specification
