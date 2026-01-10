# GitHub Sync for Generated Assets

Design document for auto-syncing generated content to GitHub.

## Overview

Add ability to automatically create GitHub repositories for each generated asset (Projects, Exams, SOPs, Summaries) after generation completes.

## CLI Interface

### Flags

```bash
-ccg <types>              # Comma-separated generator types (Exam,Project,SOP,Summary,all)
--github-sync=true|false  # Sync each generated asset to GitHub (default: false)
```

### Examples

```bash
# Single generator, no sync
bun run src/index.ts -i ./courses -ccg Project

# Multiple generators, no sync
bun run src/index.ts -i ./courses -ccg Exam,Project,SOP

# Multiple generators with sync
bun run src/index.ts -i ./courses -ccg Exam,Project,SOP --github-sync=true

# All generators with sync
bun run src/index.ts -i ./courses -ccg all --github-sync=true
```

### Execution Order

Process each generator type sequentially per course:
```
Course A: Exam -> sync -> Project -> sync -> SOP -> sync
Course B: Exam -> sync -> Project -> sync -> SOP -> sync
```

## GitHub Repository Configuration

| Setting | Value |
|---------|-------|
| Naming pattern | `ccg_{AssetType}_{SynthesizedName}` |
| Visibility | Always public |
| Description | `"{Tech} {type} - {short description}"` |
| Owner | Authenticated user via `gh` CLI |

### Examples

- `ccg_Project_RustSoftwareDevelopmentBuilding`
- `ccg_Exam_RustSoftwareDevelopmentBuilding`
- `ccg_SOP_RustSoftwareDevelopmentBuilding`

Description example: `"Rust project - Property management system with Iced GUI"`

## Sync Flow

### Per Asset

1. Generate asset files to `__ccg_{Type}/{SynthesizedName}/`
2. Create `.gitignore` (always, based on tech stack)
3. If `--github-sync=true`:
   - `git init` (if not already a repo)
   - `git add .`
   - `git commit -m "init commit"`
   - Check if repo exists on GitHub:
     - If NO: `gh repo create ccg_{Type}_{Name} --public --source . --push`
     - If YES: `git remote add origin ... && git push`
4. On failure:
   - Log warning with error details
   - Continue to next asset
   - Add to failure summary

### Console Output

**Success:**
```
[SYNC] ccg_Project_RustSoftwareDevelopment
       > .gitignore created (Rust)
       > git init
       > git commit "init commit"
       > gh repo create (new repo)
       -> https://github.com/KennethJefferson/ccg_Project_RustSoftwareDevelopment
```

**Failure:**
```
[SYNC] ccg_Exam_RustSoftwareDevelopment
       > .gitignore created (Rust)
       > git init
       > git commit "init commit"
       x gh repo create failed: network timeout
       -> Skipping sync, local files preserved
```

### End-of-Run Summary

```
==================================================
GitHub Sync Summary
==================================================
  Synced:  3
  Failed:  1

  > ccg_Project_RustSoftwareDevelopment
  > ccg_SOP_RustSoftwareDevelopment
  > ccg_Summary_RustSoftwareDevelopment
  x ccg_Exam_RustSoftwareDevelopment (network timeout)
==================================================
```

### Sync Results File

Write `__ccg_sync_results.json` in course folder:
```json
{
  "synced_at": "2026-01-10T12:00:00Z",
  "total": 4,
  "successful": 3,
  "failed": 1,
  "results": [
    {
      "asset_type": "Project",
      "repo_name": "ccg_Project_RustSoftwareDevelopment",
      "status": "success",
      "url": "https://github.com/KennethJefferson/ccg_Project_RustSoftwareDevelopment"
    },
    {
      "asset_type": "Exam",
      "repo_name": "ccg_Exam_RustSoftwareDevelopment",
      "status": "failed",
      "error": "network timeout"
    }
  ]
}
```

## Handling Conceptual Courses

Some courses are theoretical with no discoverable projects.

**Behavior:**
- No projects discovered = valid outcome
- Empty `projects` array in discovery.json
- Other asset types (Exam, SOP, Summary) still generated and synced
- Use course folder name for `{SynthesizedName}` when no project exists

**discovery.json:**
```json
{
  "course_path": "...",
  "projects": [],
  "total_projects": 0,
  "no_project_reason": "No hands-on coding projects identified - course appears conceptual/theoretical"
}
```

## Implementation

### New Skill: ccg-github-sync

```
skills/
  ccg-github-sync/
    SKILL.md           # References gh-repo, defines CCG workflow
    scripts/
      github_sync.py   # Handles naming, description, invokes git/gh
```

### Skill Responsibilities

**github_sync.py:**
1. Read discovery.json for metadata (tech_stack, synthesized_name, description)
2. Determine .gitignore template from tech_stack (reference gh-repo templates)
3. Construct repo name: `ccg_{Type}_{SynthesizedName}`
4. Construct description: `"{Tech} {type} - {description}"`
5. Run git commands: init, add, commit
6. Run gh commands: repo create or push to existing
7. Return success/failure status

### Integration Points

| Component | File | Changes |
|-----------|------|---------|
| CLI parsing | `src/cli/args.ts` | Parse `-ccg` as array, add `--github-sync` flag |
| Config type | `src/types/index.ts` | Add `githubSync: boolean` and `generators: string[]` |
| Constants | `src/core/constants.ts` | Add `all` shorthand mapping |
| Orchestration | `src/core/app.ts` | Loop through generators, invoke sync after each |
| Skill invocation | `src/skills/skill-invoker.ts` | Call ccg-github-sync after generator completes |

### Composing with gh-repo Skill

The `ccg-github-sync` skill references `gh-repo` for:
- .gitignore templates (by tech stack)
- `gh repo create` command syntax
- Git initialization workflow

This avoids duplicating knowledge and keeps skills composable.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Network failure | Log warning, continue, include in summary |
| Auth expired | Log warning, continue, include in summary |
| Repo name collision | Push new commit to existing repo |
| Invalid tech stack | Use universal .gitignore template |
| No projects found | Skip Project generation, continue with other types |

## Future Considerations

- Private repo option (currently always public)
- Organization target (currently always personal)
- Custom description templates
- Batch sync mode (sync all at end instead of per-asset)
