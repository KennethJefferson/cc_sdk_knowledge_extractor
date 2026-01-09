# SOP Generator - Usage Guide

## Activation Phrases

Use the `-ccg` argument with any of these values to activate the SOP Generator:

| Phrase | Command |
|--------|---------|
| `SOP` | `ccke -i ./courses -ccg SOP` |
| `sop` | `ccke -i ./courses -ccg sop` |
| `procedure` | `ccke -i ./courses -ccg procedure` |
| `procedures` | `ccke -i ./courses -ccg procedures` |
| `standard-operating-procedure` | `ccke -i ./courses -ccg standard-operating-procedure` |

## Basic Usage

```bash
# Generate SOPs from a course directory
bun run src/index.ts -i ./my-courses -ccg SOP

# With verbose output
bun run src/index.ts -i ./my-courses -ccg SOP -v

# Preview without generating (dry-run)
bun run src/index.ts -i ./my-courses -ccg SOP --dry-run
```

## Examples

### Example 1: Single Course

```bash
# Input structure
courses/
└── DevOps101/
    ├── lesson1.srt
    ├── lesson2.srt
    └── CODE/
        └── scripts/

# Command
bun run src/index.ts -i ./courses -ccg SOP

# Output
courses/DevOps101/CODE/__ccg_SOP/
├── README.md
├── quick_reference.md
├── glossary.md
└── procedures/
    ├── SOP-001_Install_Docker.md
    ├── SOP-002_Configure_Kubernetes.md
    └── SOP-003_Deploy_Container.md
```

### Example 2: Multiple Courses

```bash
# Input structure
training/
├── AWS-Fundamentals/
├── Azure-Basics/
└── GCP-Essentials/

# Command - processes all courses
bun run src/index.ts -i ./training -ccg procedures

# Each course gets its own __ccg_SOP directory
```

### Example 3: With Parallel Processing

```bash
# Use 4 workers for faster processing
bun run src/index.ts -i ./courses -ccg SOP -w 4
```

## Input Requirements

The SOP Generator works best with content that contains:

### Good Input Examples

```markdown
# Setting Up the Development Environment

1. Install Node.js from the official website
2. Open a terminal and verify installation with `node --version`
3. Create a new project directory
4. Initialize the project with `npm init`
5. Install dependencies using `npm install`
```

```markdown
## Deploying to Production

First, ensure all tests pass locally.
Then, commit your changes to the main branch.
Next, trigger the CI/CD pipeline.
Finally, verify the deployment in the staging environment.
```

```
Step 1: Open the configuration file
Step 2: Locate the database section
Step 3: Update the connection string
Step 4: Save and restart the service
```

### Action Verbs Recognized

The generator looks for these action verbs to identify steps:

| Category | Verbs |
|----------|-------|
| Navigation | click, select, open, close, navigate, go to |
| Input | enter, type, press, drag, drop |
| File Operations | create, delete, save, load, copy, paste |
| System | run, execute, install, configure, start, stop, restart |
| Development | build, compile, deploy, test, verify |
| Data | import, export, download, upload |
| Settings | enable, disable, check, uncheck, add, remove, update |
| Authentication | login, logout, connect, disconnect, authenticate |

## Output Files

### README.md

Main index with table of all procedures:

```markdown
# Standard Operating Procedures

| ID | Procedure | Steps | Source |
|----|-----------|-------|--------|
| SOP-001 | Install Docker | 5 | lesson1.srt |
| SOP-002 | Configure Network | 8 | lesson2.srt |
```

### quick_reference.md

Condensed checklists for field use:

```markdown
## Install Docker

- [ ] **Step 1:** Download Docker Desktop from docker.com
- [ ] **Step 2:** Run the installer
- [ ] **Step 3:** Restart your computer
- [ ] **Step 4:** Verify with `docker --version`
```

### procedures/SOP-XXX_*.md

Full SOP documents with:

- Document ID and metadata
- Purpose and scope
- Prerequisites
- Numbered steps with details
- Verification checklist
- Troubleshooting table

### glossary.md

Extracted terms and definitions:

```markdown
**Container**
: A lightweight, standalone package that includes everything needed to run software.

**Image**
: A read-only template used to create containers.
```

## Tips for Best Results

1. **Use structured content** - Numbered lists and clear headings produce better SOPs
2. **Include action verbs** - Start steps with verbs like "click", "run", "configure"
3. **Provide context** - Include prerequisites and expected outcomes
4. **Keep steps atomic** - Each step should be a single action
5. **Review output** - Auto-generated SOPs should be validated before production use

## Troubleshooting

### No procedures generated

- Ensure input files contain procedural content (steps, sequences)
- Check that files have at least 3 identifiable steps
- Use verbose mode (`-v`) to see processing details

### Missing steps

- The generator requires clear step indicators
- Add numbers or action verbs to step content
- Check for minimum content length (steps under 10 characters are skipped)

### Incorrect grouping

- SOPs are grouped by headings in the source
- Add clear section headings to improve grouping
- Review and manually reorganize if needed
