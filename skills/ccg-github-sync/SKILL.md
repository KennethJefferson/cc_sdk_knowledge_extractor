# ccg-github-sync

Sync generated assets to GitHub repositories.

## Purpose

After content generation (Project, Exam, SOP, Summary), this skill creates a GitHub repository and pushes the generated files. Each asset gets its own public repository with a standardized naming convention.

## When to Use

- After any CCG generator completes successfully
- When `--github-sync=true` flag is set
- Works with all asset types: Project, Exam, SOP, Summary

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Git installed
- Run `gh auth status` to verify authentication

## Input

The skill expects:
1. `asset_path` - Path to the generated asset folder
2. `asset_type` - Type of asset (Project, Exam, SOP, Summary)
3. `discovery_json` - Path to discovery.json with metadata

## Repository Configuration

| Setting | Value |
|---------|-------|
| Naming | `ccg_{AssetType}_{SynthesizedName}` |
| Visibility | Public |
| Description | `"{Tech} {type} - {short description}"` |

## Workflow

1. Read discovery.json for metadata
2. Create .gitignore based on tech stack
3. Initialize git repository
4. Commit all files with "init commit"
5. Create GitHub repo or push to existing

## .gitignore Templates

Based on primary tech stack (references gh-repo skill templates):

| Tech | Template |
|------|----------|
| Rust | Cargo, target/, *.pdb |
| Python | __pycache__, venv/, *.pyc |
| JavaScript/TypeScript | node_modules/, dist/, .next/ |
| Go | bin/, *.exe, vendor/ |
| Java | target/, *.class, .gradle/ |
| C# | bin/, obj/, *.dll |

Falls back to universal template if tech not recognized.

## Output

Returns JSON:
```json
{
  "success": true,
  "repo_name": "ccg_Project_RustSoftwareDevelopment",
  "repo_url": "https://github.com/user/ccg_Project_RustSoftwareDevelopment",
  "action": "created"  // or "updated"
}
```

On failure:
```json
{
  "success": false,
  "error": "gh repo create failed: network timeout",
  "repo_name": "ccg_Project_RustSoftwareDevelopment"
}
```

## Error Handling

- Network failures: Return error, don't halt pipeline
- Repo exists: Push new commit to existing repo
- Auth expired: Return error with auth instructions
- Invalid tech: Use universal .gitignore

## CLI Usage

```bash
# Direct invocation (for testing)
python github_sync.py <asset_path> --type Project --discovery <path>

# Via CCKnowledgeExtractor
bun run src/index.ts -i ./courses -ccg Project --github-sync=true
```
