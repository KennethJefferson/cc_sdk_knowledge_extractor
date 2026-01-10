# CLAUDE.md - Project Instructions for Claude

## Project Overview

CCKnowledgeExtractor is a Bun/TypeScript CLI application that extracts course content (transcripts, documents, code, databases, images) and generates new educational content (quizzes, exams, summaries, SOPs, projects) using Python skills.

## Tech Stack

- **Runtime**: Bun (not Node.js)
- **Language**: TypeScript (strict mode)
- **CLI Framework**: Commander.js
- **Skills**: Python scripts invoked via subprocess
- **Dependencies**: See package.json

## Project Structure

```
src/
  index.ts          # CLI entry point
  cli/args.ts       # Argument parsing and validation
  core/
    app.ts          # Main orchestrator
    config.ts       # Config file loading (.cckrc.json)
    constants.ts    # File extensions, skill mappings
  queue/
    async-queue.ts  # Bun-native async queue
    worker-pool.ts  # Parallel worker management
  scanner/
    course-detector.ts  # Course structure detection
    scanner.ts          # File scanning
  routing/
    file-router.ts      # Extension-based routing
    skill-registry.ts   # Available skills
  processors/
    file-processor.ts   # File processing dispatcher
  skills/
    skill-invoker.ts    # Python script invocation
  output/
    output-manager.ts   # Output directory management
  logging/
    logger.ts           # Console logging
    error-logger.ts     # File-based error logging
    spinner.ts          # Progress display
  types/
    index.ts            # All TypeScript interfaces

skills/               # Python skill implementations
  file-router/        # File type detection
  image-ocr/          # Image text extraction
  archive-extractor/  # Archive unpacking
  quiz-generator/     # Quiz/exam generation
  summary-generator/  # Documentation generation
  sop-generator/      # Standard Operating Procedures
  project-maker/      # Project synthesis from transcripts
  ccg-github-sync/    # GitHub repo creation and sync
  pdf/, docx/, pptx/  # Document processing
  db-*/               # Database extraction
```

## Key Patterns

### Adding a New Content Generator

1. Create skill directory: `skills/<name>/`
2. Add `SKILL.md` with description
3. Create `scripts/<name>_generate.py` with:
   - Accept input directory as first arg
   - Accept `-o <output>` for output directory
   - Accept `--json` flag for JSON output
   - Return `{"success": true}` or `{"error": "message"}`
4. Register in `src/core/constants.ts` under `GENERATOR_SKILLS`
5. Add script mapping in `src/skills/skill-invoker.ts`

### Adding a New File Processor

1. Create skill in `skills/<name>/`
2. Add extension mapping in `src/core/constants.ts` under `EXTENSION_TO_SKILL`
3. Add output format in `SKILL_OUTPUT_FORMATS`

## Commands

```bash
# Run the CLI with single generator
bun run src/index.ts -i <input> -ccg <type>

# Run with multiple generators
bun run src/index.ts -i <input> -ccg Exam,Project,SOP

# Run all generators
bun run src/index.ts -i <input> -ccg all

# With GitHub sync (auto-creates repos for generated assets)
bun run src/index.ts -i <input> -ccg Project --github-sync=true

# Development with watch
bun run dev -- -i ./test-courses -ccg Exam --dry-run

# Generate sample config
bun run src/index.ts --init-config
```

## Testing

Test courses go in `test-courses/` (gitignored). Each subdirectory is treated as a separate course.

## Code Style

- Use explicit types, avoid `any`
- Handle errors explicitly with typed error objects
- Prefer async/await over raw promises
- Use the existing logger, not console.log directly
- Keep functions small and focused

## Important Files

- `src/core/app.ts` - Main processing loop
- `src/types/index.ts` - All interfaces (read this first)
- `src/core/constants.ts` - Configuration constants
- `src/skills/skill-invoker.ts` - How Python skills are called
