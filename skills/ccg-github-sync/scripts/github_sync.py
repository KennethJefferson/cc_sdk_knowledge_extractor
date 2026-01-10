#!/usr/bin/env python3
"""
GitHub Sync for CCG Generated Assets

Syncs generated content (Projects, Exams, SOPs, Summaries) to GitHub repositories.
Each asset gets its own public repo with standardized naming: ccg_{Type}_{Name}
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


# .gitignore templates by tech stack
GITIGNORE_TEMPLATES = {
    "rust": """# Rust
/target/
**/*.rs.bk
Cargo.lock
*.pdb

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
""",

    "python": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/
venv/
.venv/
env/
.env/
*.egg
.mypy_cache/
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
""",

    "javascript": """# Node.js / JavaScript / TypeScript
node_modules/
dist/
build/
.next/
.nuxt/
.output/
*.tsbuildinfo
.cache/
coverage/
.env
.env.local
.env.*.local
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
""",

    "typescript": """# Node.js / JavaScript / TypeScript
node_modules/
dist/
build/
.next/
.nuxt/
.output/
*.tsbuildinfo
.cache/
coverage/
.env
.env.local
.env.*.local
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
""",

    "go": """# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
bin/
/build/
*.test
*.out
coverage.html
vendor/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
""",

    "java": """# Java
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
target/
build/
out/
.gradle/
!gradle-wrapper.jar

# IDE
.idea/
*.iws
*.iml
*.ipr
.vscode/

# OS
.DS_Store
Thumbs.db
""",

    "csharp": """# .NET / C#
bin/
obj/
.vs/
*.user
*.suo
*.cache
*.dll
*.exe
*.pdb
*.nupkg
packages/
artifacts/

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db
""",

    "universal": """# Universal .gitignore

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Editor/IDE
.idea/
.vscode/
*.swp
*.swo
*~
*.sublime-project
*.sublime-workspace

# Environment and secrets
.env
.env.local
.env.*.local
*.pem
*.key
secrets.json

# Logs
logs/
*.log

# Temporary files
tmp/
temp/
*.tmp
*.temp
*.bak
*.backup
"""
}

# Tech name normalization
TECH_ALIASES = {
    "node": "javascript",
    "nodejs": "javascript",
    "js": "javascript",
    "ts": "typescript",
    "react": "javascript",
    "vue": "javascript",
    "angular": "javascript",
    "next": "javascript",
    "nuxt": "javascript",
    "c#": "csharp",
    ".net": "csharp",
    "dotnet": "csharp",
    "golang": "go",
}


class GitHubSync:
    """Sync generated assets to GitHub."""

    def __init__(self, asset_path: str, asset_type: str, discovery_path: Optional[str] = None,
                 verbose: bool = False):
        self.asset_path = Path(asset_path)
        self.asset_type = asset_type
        self.discovery_path = Path(discovery_path) if discovery_path else None
        self.verbose = verbose
        self.metadata: Dict[str, Any] = {}

    def _log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"       {message}", file=sys.stderr)

    def _run_command(self, cmd: list, cwd: Optional[Path] = None) -> tuple[bool, str]:
        """Run a shell command and return (success, output)."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.asset_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def _load_metadata(self) -> bool:
        """Load metadata from discovery.json."""
        if self.discovery_path and self.discovery_path.exists():
            try:
                with open(self.discovery_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Get first project's metadata (or course-level if no projects)
                if data.get('projects') and len(data['projects']) > 0:
                    proj = data['projects'][0]
                    self.metadata = {
                        'synthesized_name': proj.get('synthesized_name', ''),
                        'name': proj.get('name', ''),
                        'description': proj.get('description', ''),
                        'tech_stack': proj.get('tech_stack', []),
                        'primary_tech': proj['tech_stack'][0] if proj.get('tech_stack') else '',
                    }
                else:
                    # No projects - use course name from path
                    course_name = self._extract_course_name(data.get('course_path', ''))
                    self.metadata = {
                        'synthesized_name': self._synthesize_name(course_name),
                        'name': course_name,
                        'description': f'{course_name} - Course materials',
                        'tech_stack': [],
                        'primary_tech': '',
                    }
                return True
            except Exception as e:
                self._log(f"Warning: Could not load discovery.json: {e}")

        # Fallback to folder name
        folder_name = self.asset_path.name
        self.metadata = {
            'synthesized_name': folder_name,
            'name': folder_name.replace('_', ' ').replace('-', ' '),
            'description': f'{folder_name} - Generated content',
            'tech_stack': [],
            'primary_tech': '',
        }
        return True

    def _extract_course_name(self, course_path: str) -> str:
        """Extract course name from path."""
        if not course_path:
            return "Course"
        path = Path(course_path)
        # Go up to find course folder (above __cc_validated_files or CODE)
        for parent in [path] + list(path.parents):
            if parent.name not in ('__cc_validated_files', 'CODE', '__ccg_Project', '__ccg_Exam', '__ccg_SOP', '__ccg_Summary'):
                name = parent.name
                # Clean up the name
                name = re.sub(r'[^\w\s-]', ' ', name)
                name = ' '.join(name.split())
                if len(name) > 3:
                    return name
        return "Course"

    def _synthesize_name(self, name: str) -> str:
        """Create synthesized name from course/project name."""
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        words = clean.split()[:4]
        return ''.join(w.title() for w in words)

    def _get_repo_name(self) -> str:
        """Generate repository name."""
        synth_name = self.metadata.get('synthesized_name', 'Unknown')
        # Remove any existing Project_ prefix to avoid duplication
        synth_name = re.sub(r'^Project_', '', synth_name)
        return f"ccg_{self.asset_type}_{synth_name}"

    def _get_description(self) -> str:
        """Generate repository description."""
        tech = self.metadata.get('primary_tech', '')
        desc = self.metadata.get('description', '')

        # Shorten description if needed
        if len(desc) > 100:
            desc = desc[:97] + '...'

        if tech:
            return f"{tech} {self.asset_type.lower()} - {desc}"
        else:
            return f"{self.asset_type} - {desc}"

    def _get_gitignore_template(self) -> str:
        """Get appropriate .gitignore template for tech stack."""
        tech_stack = self.metadata.get('tech_stack', [])

        for tech in tech_stack:
            tech_lower = tech.lower()
            # Check aliases first
            if tech_lower in TECH_ALIASES:
                tech_lower = TECH_ALIASES[tech_lower]
            # Check if we have a template
            if tech_lower in GITIGNORE_TEMPLATES:
                return GITIGNORE_TEMPLATES[tech_lower]

        # Fallback to universal
        return GITIGNORE_TEMPLATES['universal']

    def _create_gitignore(self) -> bool:
        """Create .gitignore file."""
        gitignore_path = self.asset_path / '.gitignore'
        template = self._get_gitignore_template()

        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(template)
            tech = self.metadata.get('primary_tech', 'universal')
            self._log(f"> .gitignore created ({tech})")
            return True
        except Exception as e:
            self._log(f"x .gitignore creation failed: {e}")
            return False

    def _git_init(self) -> bool:
        """Initialize git repository."""
        git_dir = self.asset_path / '.git'
        if git_dir.exists():
            self._log("> git already initialized")
            return True

        success, output = self._run_command(['git', 'init'])
        if success:
            self._log("> git init")
        else:
            self._log(f"x git init failed: {output}")
        return success

    def _git_add_commit(self) -> bool:
        """Add all files and commit."""
        # Add all files
        success, output = self._run_command(['git', 'add', '.'])
        if not success:
            self._log(f"x git add failed: {output}")
            return False

        # Check if there are changes to commit
        success, output = self._run_command(['git', 'status', '--porcelain'])
        if not output.strip():
            self._log("> nothing to commit")
            return True

        # Commit
        success, output = self._run_command(['git', 'commit', '-m', 'init commit'])
        if success:
            self._log('> git commit "init commit"')
        else:
            # Check if it's just "nothing to commit"
            if 'nothing to commit' in output:
                self._log("> nothing to commit")
                return True
            self._log(f"x git commit failed: {output}")
        return success

    def _check_repo_exists(self, repo_name: str) -> bool:
        """Check if repo already exists on GitHub."""
        success, output = self._run_command(['gh', 'repo', 'view', repo_name], cwd=Path.cwd())
        return success

    def _create_github_repo(self, repo_name: str, description: str) -> tuple[bool, str]:
        """Create new GitHub repo and push."""
        cmd = [
            'gh', 'repo', 'create', repo_name,
            '--public',
            '--source', '.',
            '--push',
            '--description', description
        ]

        success, output = self._run_command(cmd)
        if success:
            self._log("> gh repo create (new repo)")
            # Extract URL from output
            url_match = re.search(r'https://github\.com/[^\s]+', output)
            url = url_match.group(0) if url_match else f"https://github.com/{repo_name}"
            return True, url
        else:
            self._log(f"x gh repo create failed: {output}")
            return False, output

    def _push_to_existing(self, repo_name: str) -> tuple[bool, str]:
        """Push to existing GitHub repo."""
        # Get current user
        success, username = self._run_command(['gh', 'api', 'user', '-q', '.login'], cwd=Path.cwd())
        if not success:
            return False, "Could not get GitHub username"
        username = username.strip()

        remote_url = f"https://github.com/{username}/{repo_name}.git"

        # Check if remote exists
        success, output = self._run_command(['git', 'remote', 'get-url', 'origin'])
        if not success:
            # Add remote
            success, output = self._run_command(['git', 'remote', 'add', 'origin', remote_url])
            if not success:
                return False, f"Could not add remote: {output}"

        # Push
        success, output = self._run_command(['git', 'push', '-u', 'origin', 'main'])
        if not success:
            # Try master branch
            success, output = self._run_command(['git', 'push', '-u', 'origin', 'master'])

        if success:
            self._log("> git push (updated existing)")
            return True, f"https://github.com/{username}/{repo_name}"
        else:
            self._log(f"x git push failed: {output}")
            return False, output

    def sync(self) -> Dict[str, Any]:
        """Perform the full sync operation."""
        print(f"[SYNC] Starting sync for {self.asset_path.name}", file=sys.stderr)

        # Load metadata
        self._load_metadata()

        repo_name = self._get_repo_name()
        description = self._get_description()

        # Create .gitignore
        if not self._create_gitignore():
            return {
                'success': False,
                'error': 'Failed to create .gitignore',
                'repo_name': repo_name
            }

        # Git init
        if not self._git_init():
            return {
                'success': False,
                'error': 'Failed to initialize git',
                'repo_name': repo_name
            }

        # Git add and commit
        if not self._git_add_commit():
            return {
                'success': False,
                'error': 'Failed to commit files',
                'repo_name': repo_name
            }

        # Check if repo exists and create/push accordingly
        if self._check_repo_exists(repo_name):
            success, result = self._push_to_existing(repo_name)
            action = 'updated'
        else:
            success, result = self._create_github_repo(repo_name, description)
            action = 'created'

        if success:
            print(f"       -> {result}", file=sys.stderr)
            return {
                'success': True,
                'repo_name': repo_name,
                'repo_url': result,
                'action': action
            }
        else:
            return {
                'success': False,
                'error': result,
                'repo_name': repo_name
            }


def main():
    parser = argparse.ArgumentParser(
        description='Sync generated assets to GitHub'
    )
    parser.add_argument(
        'asset_path',
        help='Path to the generated asset folder'
    )
    parser.add_argument(
        '--type', '-t',
        required=True,
        choices=['Project', 'Exam', 'SOP', 'Summary'],
        help='Type of asset being synced'
    )
    parser.add_argument(
        '--discovery', '-d',
        help='Path to discovery.json with metadata'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )

    args = parser.parse_args()

    syncer = GitHubSync(
        asset_path=args.asset_path,
        asset_type=args.type,
        discovery_path=args.discovery,
        verbose=args.verbose or args.json  # Always verbose when JSON output
    )

    result = syncer.sync()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"Synced: {result['repo_url']}")
        else:
            print(f"Failed: {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
