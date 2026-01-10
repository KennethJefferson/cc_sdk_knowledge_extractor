#!/usr/bin/env python3
"""
Project Maker - Transform validated course content into complete, working projects.

Usage:
    python project_maker.py <input_dir> -o <output_dir> [--json]

This is the crown jewel of CCKnowledgeExtractor. It synthesizes ALL validated
file assets into production-ready project implementations.
"""

import argparse
import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SourceFile:
    """Represents a source file from validated files."""
    path: Path
    name: str
    extension: str
    content: str
    file_type: str  # transcript, documentation, code, extracted
    char_count: int

@dataclass
class ProjectCandidate:
    """A candidate project discovered from content."""
    id: str
    name: str
    synthesized_name: str
    description: str
    source_files: List[str]
    tech_stack: List[str]
    complexity: str  # beginner, intermediate, advanced
    features: List[str]
    code_snippets: List[Dict[str, str]]

@dataclass
class GeneratedFile:
    """A file generated for a project."""
    path: str
    content: str
    file_type: str  # source, config, doc, test

@dataclass
class Project:
    """A fully generated project."""
    id: str
    name: str
    synthesized_name: str
    description: str
    source_files: List[str]
    tech_stack: List[str]
    complexity: str
    status: str  # generated, failed, partial
    output_path: str
    files_created: int
    generated_at: Optional[str]
    error: Optional[str] = None


# =============================================================================
# Content Parsers
# =============================================================================

class SRTParser:
    """Parse SRT subtitle files."""

    @staticmethod
    def parse(content: str) -> str:
        """Extract plain text from SRT content."""
        lines = []
        current_text = []

        for line in content.split('\n'):
            line = line.strip()

            # Skip sequence numbers
            if line.isdigit():
                if current_text:
                    lines.append(' '.join(current_text))
                    current_text = []
                continue

            # Skip timestamps
            if '-->' in line:
                continue

            # Skip empty lines
            if not line:
                if current_text:
                    lines.append(' '.join(current_text))
                    current_text = []
                continue

            # Collect text
            current_text.append(line)

        if current_text:
            lines.append(' '.join(current_text))

        return '\n'.join(lines)


class ContentAnalyzer:
    """Analyze content to identify projects and extract information."""

    # Project name extraction patterns (ordered by reliability)
    # These patterns look for explicit project names, not conversational text
    PROJECT_NAME_PATTERNS = [
        # CLI initialization commands (most reliable)
        r"cargo\s+new\s+([a-z][a-z0-9_-]+)",
        r"npm\s+(?:init|create)\s+([a-z][a-z0-9_-]+)",
        r"npx\s+create-\w+-app\s+([a-z][a-z0-9_-]+)",
        r"django-admin\s+startproject\s+([a-z][a-z0-9_]+)",
        r"rails\s+new\s+([a-z][a-z0-9_-]+)",
        r"dotnet\s+new\s+\w+\s+-n\s+([A-Za-z][A-Za-z0-9_]+)",

        # Explicit project naming
        r"project\s*(?:named?|called?)\s*[\"']?([A-Z][A-Za-z0-9_\s]+?)[\"']?(?:\.|,|!|\s|$)",
        r"(?:the|our|this)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\s+(?:project|application|app|system)",

        # Title-case application names (2-4 words)
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+(?:Application|App|System|Manager|Portal|Dashboard)\b",
    ]

    # Patterns that indicate project boundaries (for multi-project courses)
    PROJECT_BOUNDARY_PATTERNS = [
        r"project\s*[#]?\s*(\d+)\s*[:\-]",
        r"(?:first|second|third|next)\s+project",
        r"new\s+project\s*[:\-]",
    ]

    # Framework/language detection
    TECH_PATTERNS = {
        # Languages
        'Rust': [r'\brust\b', r'\.rs\b', r'\bcargo\b', r'\bfn\s+\w+', r'\blet\s+mut\b'],
        'Python': [r'\bpython\b', r'\.py\b', r'\bdef\s+\w+', r'\bimport\s+\w+', r'\bpip\b'],
        'JavaScript': [r'\bjavascript\b', r'\.js\b', r'\bconst\s+\w+\s*=', r'\bfunction\b', r'\bnpm\b'],
        'TypeScript': [r'\btypescript\b', r'\.ts\b', r'\binterface\s+\w+', r':\s*string\b', r':\s*number\b'],
        'Go': [r'\bgolang\b', r'\bgo\b', r'\.go\b', r'\bfunc\s+\w+', r'\bpackage\s+\w+'],
        'Java': [r'\bjava\b', r'\.java\b', r'\bpublic\s+class\b', r'\bprivate\s+\w+\b'],
        'C#': [r'\bc#\b', r'\bcsharp\b', r'\.cs\b', r'\bnamespace\s+\w+', r'\busing\s+System\b'],
        'C++': [r'\bc\+\+\b', r'\.cpp\b', r'\.hpp\b', r'#include\s*<', r'\bstd::\b'],

        # Frontend frameworks
        'React': [r'\breact\b', r'\buseState\b', r'\buseEffect\b', r'\bJSX\b', r'<\w+\s*/?>'],
        'Vue': [r'\bvue\b', r'\bv-bind\b', r'\bv-model\b', r'<template>'],
        'Angular': [r'\bangular\b', r'@Component', r'@Injectable', r'\bngModule\b'],
        'Svelte': [r'\bsvelte\b', r'\$:\s*\w+', r'<script>'],

        # Backend frameworks
        'Express': [r'\bexpress\b', r'app\.get\(', r'app\.post\(', r'req,\s*res'],
        'FastAPI': [r'\bfastapi\b', r'@app\.get', r'@app\.post', r'\bUvicorn\b'],
        'Django': [r'\bdjango\b', r'from django', r'\bmodels\.Model\b'],
        'Flask': [r'\bflask\b', r'@app\.route', r'from flask'],

        # GUI frameworks
        'Iced': [r'\biced\b', r'\bApplication\b.*\bMessage\b', r'Command::none'],
        'Tauri': [r'\btauri\b', r'#\[tauri::command\]'],
        'Electron': [r'\belectron\b', r'BrowserWindow', r'ipcMain'],

        # Databases
        'SQLite': [r'\bsqlite\b', r'\.sqlite\b', r'\.db\b', r'CREATE TABLE'],
        'PostgreSQL': [r'\bpostgres\b', r'\bpostgresql\b', r'\bpg\b'],
        'MongoDB': [r'\bmongodb\b', r'\bmongo\b', r'mongoose'],
        'MySQL': [r'\bmysql\b', r'mariadb'],

        # Tools
        'Docker': [r'\bdocker\b', r'Dockerfile', r'docker-compose'],
        'Git': [r'\bgit\b', r'\.gitignore', r'git clone'],
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        'advanced': [
            r'\bmicroservice', r'\boauth\b', r'\bjwt\b', r'\bwebsocket\b',
            r'\breal-?time\b', r'\bdistributed\b', r'\bscalable\b',
            r'\bkubernetes\b', r'\bci/cd\b', r'\bload balanc',
        ],
        'intermediate': [
            r'\bauthenticat', r'\bauthoriz', r'\bapi\b', r'\bcrud\b',
            r'\bstate management\b', r'\bdatabase\b', r'\borm\b',
            r'\brouting\b', r'\bmiddleware\b', r'\bvalidat',
        ],
        'beginner': [
            r'\bhello world\b', r'\bbasic\b', r'\bsimple\b', r'\bintro',
            r'\bgetting started\b', r'\bfirst\s+\w+\b', r'\btutorial\b',
        ]
    }

    def __init__(self):
        self.detected_tech = set()
        self.detected_features = []
        self.code_blocks = []

    def analyze(self, content: str, filename: str = "") -> Dict[str, Any]:
        """Analyze content for project information."""
        content_lower = content.lower()

        # Detect tech stack
        tech_stack = self._detect_tech_stack(content, content_lower)

        # Detect complexity
        complexity = self._detect_complexity(content_lower)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(content)

        # Detect project names/features
        projects = self._detect_projects(content, content_lower)

        # Extract features mentioned
        features = self._extract_features(content_lower)

        return {
            'tech_stack': list(tech_stack),
            'complexity': complexity,
            'code_blocks': code_blocks,
            'projects': projects,
            'features': features,
            'source': filename,
        }

    def _detect_tech_stack(self, content: str, content_lower: str) -> set:
        """Detect technologies mentioned in content."""
        detected = set()

        for tech, patterns in self.TECH_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower if pattern.startswith(r'\b') else content, re.IGNORECASE):
                    detected.add(tech)
                    break

        return detected

    def _detect_complexity(self, content_lower: str) -> str:
        """Assess complexity level of content."""
        scores = {'advanced': 0, 'intermediate': 0, 'beginner': 0}

        for level, patterns in self.COMPLEXITY_INDICATORS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower))
                scores[level] += matches

        # Determine level based on scores
        if scores['advanced'] >= 3:
            return 'advanced'
        elif scores['intermediate'] >= 3 or scores['advanced'] >= 1:
            return 'intermediate'
        else:
            return 'beginner'

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content."""
        blocks = []

        # Markdown code blocks
        pattern = r'```(\w*)\n(.*?)```'
        for match in re.finditer(pattern, content, re.DOTALL):
            blocks.append({
                'language': match.group(1) or 'unknown',
                'code': match.group(2).strip(),
            })

        # Indented code (4+ spaces or tab)
        lines = content.split('\n')
        current_block = []
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                current_block.append(line)
            elif current_block:
                code = '\n'.join(current_block)
                if len(code) > 50:  # Meaningful code block
                    blocks.append({'language': 'unknown', 'code': code})
                current_block = []

        return blocks

    def _detect_projects(self, content: str, content_lower: str) -> List[Dict[str, str]]:
        """Detect explicit project names in content."""
        projects = []
        seen_names = set()

        # Common words that are NOT project names
        stopwords = {
            'the', 'this', 'our', 'a', 'an', 'we', 'i', 'you', 'it', 'is', 'are',
            'and', 'or', 'but', 'for', 'to', 'in', 'on', 'at', 'by', 'from',
            'new', 'my', 'your', 'app', 'application', 'project', 'system',
            'file', 'data', 'code', 'src', 'lib', 'main', 'test', 'build',
            'run', 'start', 'stop', 'create', 'make', 'add', 'get', 'set',
            'property', 'value', 'name', 'type', 'function', 'class', 'struct',
        }

        # First, try CLI command patterns (most reliable) - patterns 0-5
        for pattern in self.PROJECT_NAME_PATTERNS[:6]:
            for match in re.finditer(pattern, content_lower):
                name = match.group(1).strip()
                # Must be at least 4 chars and not a stopword
                if name and len(name) >= 4 and name.lower() not in stopwords and name.lower() not in seen_names:
                    # Convert snake_case/kebab-case to Title Case
                    clean_name = name.replace('_', ' ').replace('-', ' ').title()
                    seen_names.add(name.lower())
                    projects.append({
                        'name': clean_name,
                        'context': content[max(0, match.start()-50):match.end()+50],
                        'source': 'cli_command',
                        'confidence': 'high',
                    })

        # Then try explicit naming patterns (on original content for case sensitivity)
        for pattern in self.PROJECT_NAME_PATTERNS[6:]:
            for match in re.finditer(pattern, content):
                name = match.group(1).strip()
                # Filter out stopwords and short names
                if name.lower() in stopwords or len(name) < 4:
                    continue
                if name and len(name) <= 50 and name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    projects.append({
                        'name': name,
                        'context': content[max(0, match.start()-50):match.end()+50],
                        'source': 'explicit_name',
                        'confidence': 'medium',
                    })

        return projects

    def _extract_features(self, content_lower: str) -> List[str]:
        """Extract feature mentions from content."""
        feature_patterns = [
            (r'\b(?:add|implement|create|build)\s+(?:a\s+)?(\w+\s+\w+)\s+(?:feature|functionality)', 1),
            (r'\b(\w+)\s+(?:component|module|service|handler|controller)', 1),
            (r'(?:user|data|file|image|api|database)\s+(\w+)', 0),
        ]

        features = set()
        for pattern, group in feature_patterns:
            for match in re.finditer(pattern, content_lower):
                feature = match.group(group).strip()
                if len(feature) > 3 and len(feature) < 50:
                    features.add(feature)

        return list(features)[:20]  # Limit to top 20


# =============================================================================
# Project Generator
# =============================================================================

class ProjectGenerator:
    """Generate project files from analyzed content."""

    # Language-specific templates
    TEMPLATES = {
        'Rust': {
            'config': 'Cargo.toml',
            'main': 'src/main.rs',
            'lib': 'src/lib.rs',
            'gitignore': '/target\nCargo.lock\n*.swp\n*.swo\n.idea/\n.vscode/\n',
        },
        'Python': {
            'config': 'requirements.txt',
            'main': 'main.py',
            'init': '__init__.py',
            'gitignore': '__pycache__/\n*.py[cod]\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n',
        },
        'JavaScript': {
            'config': 'package.json',
            'main': 'src/index.js',
            'gitignore': 'node_modules/\n.env\ndist/\nbuild/\n*.log\n.DS_Store\n',
        },
        'TypeScript': {
            'config': 'package.json',
            'main': 'src/index.ts',
            'tsconfig': 'tsconfig.json',
            'gitignore': 'node_modules/\n.env\ndist/\nbuild/\n*.log\n.DS_Store\n',
        },
    }

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.generated_files: List[GeneratedFile] = []

    def generate_project(self, candidate: ProjectCandidate, all_content: str) -> Project:
        """Generate a complete project from a candidate."""
        project_dir = self.output_dir / candidate.synthesized_name
        project_dir.mkdir(parents=True, exist_ok=True)

        files_created = 0

        try:
            # Determine primary language
            primary_lang = self._get_primary_language(candidate.tech_stack)

            # Generate configuration files
            files_created += self._generate_config(project_dir, candidate, primary_lang)

            # Generate source files
            files_created += self._generate_sources(project_dir, candidate, primary_lang, all_content)

            # Generate documentation
            files_created += self._generate_docs(project_dir, candidate)

            # Generate .gitignore
            files_created += self._generate_gitignore(project_dir, primary_lang)

            return Project(
                id=candidate.id,
                name=candidate.name,
                synthesized_name=candidate.synthesized_name,
                description=candidate.description,
                source_files=candidate.source_files,
                tech_stack=candidate.tech_stack,
                complexity=candidate.complexity,
                status='generated',
                output_path=str(project_dir.relative_to(self.output_dir.parent)),
                files_created=files_created,
                generated_at=datetime.now().isoformat(),
            )

        except Exception as e:
            return Project(
                id=candidate.id,
                name=candidate.name,
                synthesized_name=candidate.synthesized_name,
                description=candidate.description,
                source_files=candidate.source_files,
                tech_stack=candidate.tech_stack,
                complexity=candidate.complexity,
                status='failed',
                output_path=str(project_dir.relative_to(self.output_dir.parent)),
                files_created=files_created,
                generated_at=datetime.now().isoformat(),
                error=str(e),
            )

    def _get_primary_language(self, tech_stack: List[str]) -> str:
        """Determine the primary programming language."""
        priority = ['Rust', 'TypeScript', 'Python', 'JavaScript', 'Go', 'Java', 'C#', 'C++']
        for lang in priority:
            if lang in tech_stack:
                return lang
        return 'JavaScript'  # Default

    def _generate_config(self, project_dir: Path, candidate: ProjectCandidate, lang: str) -> int:
        """Generate configuration files."""
        count = 0

        if lang == 'Rust':
            cargo_toml = f'''[package]
name = "{candidate.synthesized_name.lower().replace("project_", "").replace("_", "-")}"
version = "0.1.0"
edition = "2021"
description = "{candidate.description}"

[dependencies]
'''
            # Add common Rust dependencies based on tech stack
            if 'Iced' in candidate.tech_stack:
                cargo_toml += 'iced = "0.12"\n'
            if 'SQLite' in candidate.tech_stack:
                cargo_toml += 'rusqlite = { version = "0.31", features = ["bundled"] }\n'
            cargo_toml += 'serde = { version = "1.0", features = ["derive"] }\nserde_json = "1.0"\n'

            (project_dir / 'Cargo.toml').write_text(cargo_toml, encoding='utf-8')
            count += 1

        elif lang in ['JavaScript', 'TypeScript']:
            package_json = {
                'name': candidate.synthesized_name.lower().replace('project_', '').replace('_', '-'),
                'version': '0.1.0',
                'description': candidate.description,
                'main': 'src/index.ts' if lang == 'TypeScript' else 'src/index.js',
                'scripts': {
                    'start': 'node dist/index.js' if lang == 'TypeScript' else 'node src/index.js',
                    'build': 'tsc' if lang == 'TypeScript' else 'echo "No build step"',
                    'dev': 'ts-node src/index.ts' if lang == 'TypeScript' else 'node src/index.js',
                    'test': 'jest',
                },
                'dependencies': {},
                'devDependencies': {},
            }

            if lang == 'TypeScript':
                package_json['devDependencies']['typescript'] = '^5.0.0'
                package_json['devDependencies']['@types/node'] = '^20.0.0'
                package_json['devDependencies']['ts-node'] = '^10.9.0'

            if 'React' in candidate.tech_stack:
                package_json['dependencies']['react'] = '^18.2.0'
                package_json['dependencies']['react-dom'] = '^18.2.0'

            if 'Express' in candidate.tech_stack:
                package_json['dependencies']['express'] = '^4.18.0'

            (project_dir / 'package.json').write_text(
                json.dumps(package_json, indent=2), encoding='utf-8'
            )
            count += 1

            if lang == 'TypeScript':
                tsconfig = {
                    'compilerOptions': {
                        'target': 'ES2022',
                        'module': 'commonjs',
                        'lib': ['ES2022'],
                        'outDir': './dist',
                        'rootDir': './src',
                        'strict': True,
                        'esModuleInterop': True,
                        'skipLibCheck': True,
                        'forceConsistentCasingInFileNames': True,
                    },
                    'include': ['src/**/*'],
                    'exclude': ['node_modules', 'dist'],
                }
                (project_dir / 'tsconfig.json').write_text(
                    json.dumps(tsconfig, indent=2), encoding='utf-8'
                )
                count += 1

        elif lang == 'Python':
            requirements = []
            if 'FastAPI' in candidate.tech_stack:
                requirements.extend(['fastapi>=0.100.0', 'uvicorn>=0.23.0'])
            if 'Flask' in candidate.tech_stack:
                requirements.append('flask>=3.0.0')
            if 'Django' in candidate.tech_stack:
                requirements.append('django>=5.0.0')
            if 'SQLite' in candidate.tech_stack or any('database' in f.lower() for f in candidate.features):
                requirements.append('sqlalchemy>=2.0.0')

            requirements.extend(['python-dotenv>=1.0.0', 'pydantic>=2.0.0'])

            (project_dir / 'requirements.txt').write_text(
                '\n'.join(requirements), encoding='utf-8'
            )
            count += 1

        return count

    def _generate_sources(self, project_dir: Path, candidate: ProjectCandidate,
                          lang: str, all_content: str) -> int:
        """Generate source code files."""
        count = 0
        src_dir = project_dir / 'src'
        src_dir.mkdir(exist_ok=True)

        if lang == 'Rust':
            # Generate main.rs with extracted code or template
            main_content = self._generate_rust_main(candidate, all_content)
            (src_dir / 'main.rs').write_text(main_content, encoding='utf-8')
            count += 1

            # Generate lib.rs if multiple modules
            if candidate.complexity != 'beginner':
                lib_content = self._generate_rust_lib(candidate)
                (src_dir / 'lib.rs').write_text(lib_content, encoding='utf-8')
                count += 1

        elif lang in ['JavaScript', 'TypeScript']:
            ext = 'ts' if lang == 'TypeScript' else 'js'

            # Generate main entry point
            main_content = self._generate_js_main(candidate, lang, all_content)
            (src_dir / f'index.{ext}').write_text(main_content, encoding='utf-8')
            count += 1

            # Generate additional modules based on features
            if candidate.complexity != 'beginner':
                for feature in candidate.features[:5]:
                    module_name = re.sub(r'[^a-z0-9]', '', feature.lower())
                    if module_name:
                        module_content = self._generate_js_module(feature, lang)
                        (src_dir / f'{module_name}.{ext}').write_text(module_content, encoding='utf-8')
                        count += 1

        elif lang == 'Python':
            # Generate main module
            main_content = self._generate_python_main(candidate, all_content)
            (src_dir / '__init__.py').write_text('', encoding='utf-8')
            (project_dir / 'main.py').write_text(main_content, encoding='utf-8')
            count += 2

            # Generate additional modules
            if candidate.complexity != 'beginner':
                for feature in candidate.features[:5]:
                    module_name = re.sub(r'[^a-z0-9_]', '_', feature.lower())
                    if module_name:
                        module_content = self._generate_python_module(feature)
                        (src_dir / f'{module_name}.py').write_text(module_content, encoding='utf-8')
                        count += 1

        return count

    def _generate_rust_main(self, candidate: ProjectCandidate, all_content: str) -> str:
        """Generate Rust main.rs content."""
        # Extract any Rust code from the content
        rust_blocks = []
        for block in candidate.code_snippets:
            if block.get('language', '').lower() in ['rust', 'rs', '']:
                rust_blocks.append(block['code'])

        # If we have code blocks, try to construct main.rs
        if rust_blocks:
            # Look for fn main or create one
            combined = '\n\n'.join(rust_blocks)
            if 'fn main' not in combined:
                combined = f'''//! {candidate.description}
//!
//! Generated from course content by CCKnowledgeExtractor

{combined}

fn main() {{
    println!("{candidate.name} - Starting application...");
    // TODO: Initialize and run the application
}}
'''
            return combined

        # Generate template based on tech stack
        has_iced = 'Iced' in candidate.tech_stack
        has_sqlite = 'SQLite' in candidate.tech_stack

        if has_iced:
            return f'''//! {candidate.description}
//!
//! A GUI application built with Iced framework.
//! Generated from course content by CCKnowledgeExtractor

use iced::{{Application, Command, Element, Settings, Theme}};
use iced::widget::{{button, column, container, text, text_input}};

pub fn main() -> iced::Result {{
    {candidate.synthesized_name.replace("Project_", "")}::run(Settings::default())
}}

#[derive(Default)]
struct {candidate.synthesized_name.replace("Project_", "")} {{
    // Application state
    input_value: String,
    items: Vec<String>,
}}

#[derive(Debug, Clone)]
enum Message {{
    InputChanged(String),
    AddItem,
    RemoveItem(usize),
}}

impl Application for {candidate.synthesized_name.replace("Project_", "")} {{
    type Executor = iced::executor::Default;
    type Message = Message;
    type Theme = Theme;
    type Flags = ();

    fn new(_flags: ()) -> (Self, Command<Message>) {{
        (Self::default(), Command::none())
    }}

    fn title(&self) -> String {{
        String::from("{candidate.name}")
    }}

    fn update(&mut self, message: Message) -> Command<Message> {{
        match message {{
            Message::InputChanged(value) => {{
                self.input_value = value;
            }}
            Message::AddItem => {{
                if !self.input_value.is_empty() {{
                    self.items.push(self.input_value.clone());
                    self.input_value.clear();
                }}
            }}
            Message::RemoveItem(index) => {{
                if index < self.items.len() {{
                    self.items.remove(index);
                }}
            }}
        }}
        Command::none()
    }}

    fn view(&self) -> Element<Message> {{
        let input = text_input("Enter item...", &self.input_value)
            .on_input(Message::InputChanged)
            .padding(10);

        let add_button = button("Add").on_press(Message::AddItem);

        let items: Element<_> = column(
            self.items
                .iter()
                .enumerate()
                .map(|(i, item)| {{
                    text(item).into()
                }})
                .collect(),
        )
        .spacing(5)
        .into();

        container(
            column![input, add_button, items].spacing(20).padding(20),
        )
        .into()
    }}
}}
'''
        elif has_sqlite:
            return f'''//! {candidate.description}
//!
//! A database-driven application with SQLite.
//! Generated from course content by CCKnowledgeExtractor

use rusqlite::{{Connection, Result}};
use serde::{{Deserialize, Serialize}};

#[derive(Debug, Serialize, Deserialize)]
struct Item {{
    id: i64,
    name: String,
    description: Option<String>,
    created_at: String,
}}

struct Database {{
    conn: Connection,
}}

impl Database {{
    fn new(path: &str) -> Result<Self> {{
        let conn = Connection::open(path)?;
        conn.execute(
            "CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        Ok(Self {{ conn }})
    }}

    fn add_item(&self, name: &str, description: Option<&str>) -> Result<i64> {{
        self.conn.execute(
            "INSERT INTO items (name, description) VALUES (?1, ?2)",
            [name, description.unwrap_or("")],
        )?;
        Ok(self.conn.last_insert_rowid())
    }}

    fn get_all_items(&self) -> Result<Vec<Item>> {{
        let mut stmt = self.conn.prepare("SELECT id, name, description, created_at FROM items")?;
        let items = stmt.query_map([], |row| {{
            Ok(Item {{
                id: row.get(0)?,
                name: row.get(1)?,
                description: row.get(2)?,
                created_at: row.get(3)?,
            }})
        }})?;
        items.collect()
    }}
}}

fn main() -> Result<()> {{
    println!("{candidate.name} - Initializing...");

    let db = Database::new("{candidate.synthesized_name.lower()}.db")?;

    // Example usage
    let id = db.add_item("Sample Item", Some("A sample item for demonstration"))?;
    println!("Added item with ID: {{}}", id);

    let items = db.get_all_items()?;
    for item in items {{
        println!("{{:?}}", item);
    }}

    Ok(())
}}
'''
        else:
            return f'''//! {candidate.description}
//!
//! Generated from course content by CCKnowledgeExtractor

use std::io;

fn main() {{
    println!("=== {candidate.name} ===");
    println!();

    // TODO: Implement main application logic
    // Features to implement:
{chr(10).join(f'    // - {f}' for f in candidate.features[:10])}

    println!("Application started successfully!");
}}
'''

    def _generate_rust_lib(self, candidate: ProjectCandidate) -> str:
        """Generate Rust lib.rs content."""
        modules = []
        for feature in candidate.features[:5]:
            mod_name = re.sub(r'[^a-z0-9_]', '_', feature.lower())
            if mod_name:
                modules.append(f'pub mod {mod_name};')

        return f'''//! {candidate.name} Library
//!
//! {candidate.description}

{chr(10).join(modules) if modules else '// Add modules here'}

/// Application configuration
pub struct Config {{
    pub debug: bool,
    pub database_url: Option<String>,
}}

impl Default for Config {{
    fn default() -> Self {{
        Self {{
            debug: false,
            database_url: None,
        }}
    }}
}}
'''

    def _generate_js_main(self, candidate: ProjectCandidate, lang: str, all_content: str) -> str:
        """Generate JavaScript/TypeScript main entry point."""
        is_ts = lang == 'TypeScript'

        # Check for React
        if 'React' in candidate.tech_stack:
            return f'''{"// " + candidate.description}
// Generated from course content by CCKnowledgeExtractor

import React from 'react';
import ReactDOM from 'react-dom/client';

{"interface AppProps {}" if is_ts else ""}

const App{":" if is_ts else ""} {"React.FC<AppProps>" if is_ts else "= ()"} {"=>" if not is_ts else ""} {{
  return (
    <div className="app">
      <h1>{candidate.name}</h1>
      <p>{candidate.description}</p>
      {{/* TODO: Implement main application */}}
    </div>
  );
}};

const root = ReactDOM.createRoot(
  document.getElementById('root'){"!" if is_ts else ""}
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''

        # Check for Express
        if 'Express' in candidate.tech_stack:
            return f'''{"// " + candidate.description}
// Generated from course content by CCKnowledgeExtractor

{"import express, { Request, Response } from 'express';" if is_ts else "const express = require('express');"}

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req{": Request" if is_ts else ""}, res{": Response" if is_ts else ""}) => {{
  res.json({{
    name: '{candidate.name}',
    description: '{candidate.description}',
    status: 'running'
  }});
}});

// TODO: Add routes for features:
{chr(10).join(f'// - {f}' for f in candidate.features[:10])}

app.listen(PORT, () => {{
  console.log(`{candidate.name} running on port ${{PORT}}`);
}});
'''

        # Default
        return f'''{"// " + candidate.description}
// Generated from course content by CCKnowledgeExtractor

{"export " if is_ts else ""}function main(){":" if is_ts else ""} {"void" if is_ts else ""} {{
  console.log('=== {candidate.name} ===');
  console.log();

  // TODO: Implement main application logic
  // Features to implement:
{chr(10).join(f'  // - {f}' for f in candidate.features[:10])}

  console.log('Application initialized!');
}}

main();
'''

    def _generate_js_module(self, feature: str, lang: str) -> str:
        """Generate a JavaScript/TypeScript module."""
        is_ts = lang == 'TypeScript'
        class_name = ''.join(word.title() for word in feature.split())

        return f'''// {feature} module
// Generated from course content by CCKnowledgeExtractor

{"export " if is_ts else ""}class {class_name} {{
  {"private data: any[];" if is_ts else ""}

  constructor() {{
    {"this.data = [];" if is_ts else "this.data = [];"}
  }}

  {"public " if is_ts else ""}process(input{": any" if is_ts else ""}){": any" if is_ts else ""} {{
    // TODO: Implement {feature} processing
    console.log(`Processing {feature}:`, input);
    return input;
  }}
}}

{"export default " + class_name + ";" if not is_ts else ""}
'''

    def _generate_python_main(self, candidate: ProjectCandidate, all_content: str) -> str:
        """Generate Python main module."""
        # Check for FastAPI
        if 'FastAPI' in candidate.tech_stack:
            return f'''"""
{candidate.description}

Generated from course content by CCKnowledgeExtractor
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="{candidate.name}",
    description="{candidate.description}",
    version="0.1.0"
)


class Item(BaseModel):
    """Item model."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None


# In-memory storage
items: List[Item] = []


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"name": "{candidate.name}", "status": "running"}}


@app.get("/items", response_model=List[Item])
async def get_items():
    """Get all items."""
    return items


@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item."""
    item.id = len(items) + 1
    items.append(item)
    return item


# TODO: Implement additional features:
{chr(10).join(f'# - {f}' for f in candidate.features[:10])}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        # Check for Flask
        if 'Flask' in candidate.tech_stack:
            return f'''"""
{candidate.description}

Generated from course content by CCKnowledgeExtractor
"""

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    """Root endpoint."""
    return jsonify({{
        "name": "{candidate.name}",
        "status": "running"
    }})


# TODO: Implement features:
{chr(10).join(f'# - {f}' for f in candidate.features[:10])}


if __name__ == "__main__":
    app.run(debug=True, port=5000)
'''

        # Default
        return f'''"""
{candidate.description}

Generated from course content by CCKnowledgeExtractor
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Item:
    """Item data class."""
    id: int
    name: str
    description: Optional[str] = None


class {candidate.synthesized_name.replace("Project_", "")}:
    """Main application class."""

    def __init__(self):
        self.items: List[Item] = []

    def run(self):
        """Run the application."""
        print(f"=== {candidate.name} ===")
        print()

        # TODO: Implement main logic
        # Features:
{chr(10).join(f'        # - {f}' for f in candidate.features[:10])}

        print("Application running!")


def main():
    """Entry point."""
    app = {candidate.synthesized_name.replace("Project_", "")}()
    app.run()


if __name__ == "__main__":
    main()
'''

    def _generate_python_module(self, feature: str) -> str:
        """Generate a Python module."""
        class_name = ''.join(word.title() for word in feature.split())

        return f'''"""
{feature} module.

Generated from course content by CCKnowledgeExtractor
"""

from typing import Any, List, Optional


class {class_name}:
    """Handle {feature} operations."""

    def __init__(self):
        self.data: List[Any] = []

    def process(self, input_data: Any) -> Any:
        """Process {feature} data."""
        # TODO: Implement {feature} processing
        print(f"Processing {feature}: {{input_data}}")
        return input_data


def create_{feature.lower().replace(" ", "_")}() -> {class_name}:
    """Factory function to create {class_name}."""
    return {class_name}()
'''

    def _generate_docs(self, project_dir: Path, candidate: ProjectCandidate) -> int:
        """Generate documentation files."""
        count = 0

        # README.md
        readme = f'''# {candidate.name}

{candidate.description}

## Features

{chr(10).join(f'- {f.title()}' for f in candidate.features[:15]) if candidate.features else '- Core functionality'}

## Tech Stack

{chr(10).join(f'- {tech}' for tech in candidate.tech_stack)}

## Prerequisites

- {self._get_prerequisites(candidate.tech_stack)}

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {candidate.synthesized_name}

# Install dependencies
{self._get_install_command(candidate.tech_stack)}
```

## Usage

```bash
{self._get_run_command(candidate.tech_stack)}
```

## Project Structure

```
{candidate.synthesized_name}/
├── README.md
├── USAGE.md
├── CHANGELOG.md
├── CLAUDE.md
{self._get_structure(candidate.tech_stack)}
```

## Complexity

**Level**: {candidate.complexity.title()}

## Source Files

This project was synthesized from the following course content:

{chr(10).join(f'- {f}' for f in candidate.source_files[:20])}

---

*Generated by CCKnowledgeExtractor Project Maker*
'''
        (project_dir / 'README.md').write_text(readme, encoding='utf-8')
        count += 1

        # USAGE.md
        usage = f'''# {candidate.name} - Usage Guide

## Getting Started

### Quick Start

1. Install dependencies
2. Configure environment (if needed)
3. Run the application

### Detailed Setup

{self._get_detailed_setup(candidate.tech_stack)}

## Configuration

Environment variables:

```env
# Add configuration here
DEBUG=false
```

## Examples

### Basic Usage

```bash
{self._get_run_command(candidate.tech_stack)}
```

### API Endpoints (if applicable)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Root endpoint |
| GET | /items | List all items |
| POST | /items | Create new item |

## Features Guide

{chr(10).join(f'### {f.title()}{chr(10)}{chr(10)}TODO: Document {f}{chr(10)}' for f in candidate.features[:10])}

## Troubleshooting

### Common Issues

1. **Dependencies not installed**
   - Run: `{self._get_install_command(candidate.tech_stack)}`

2. **Port already in use**
   - Change the port in configuration

---

*Generated by CCKnowledgeExtractor Project Maker*
'''
        (project_dir / 'USAGE.md').write_text(usage, encoding='utf-8')
        count += 1

        # CHANGELOG.md
        changelog = f'''# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - {datetime.now().strftime("%Y-%m-%d")}

### Added

- Initial project structure
- Core implementation from course content
{chr(10).join(f'- {f.title()} feature' for f in candidate.features[:10])}
- Documentation (README, USAGE, CHANGELOG, CLAUDE.md)

### Notes

- Synthesized from {len(candidate.source_files)} source files
- Complexity level: {candidate.complexity}
- Tech stack: {", ".join(candidate.tech_stack)}

---

*Generated by CCKnowledgeExtractor Project Maker*
'''
        (project_dir / 'CHANGELOG.md').write_text(changelog, encoding='utf-8')
        count += 1

        # CLAUDE.md
        claude_md = f'''# CLAUDE.md - Project Instructions for Claude

## Project Overview

**{candidate.name}** - {candidate.description}

This project was automatically synthesized from course content by CCKnowledgeExtractor.

## Tech Stack

{chr(10).join(f'- **{tech}**' for tech in candidate.tech_stack)}

## Project Structure

```
{candidate.synthesized_name}/
{self._get_structure(candidate.tech_stack)}
```

## Key Patterns

- Follow {candidate.tech_stack[0] if candidate.tech_stack else 'standard'} conventions
- Use type safety where applicable
- Handle errors explicitly
- Document public APIs

## Build & Run

```bash
# Install dependencies
{self._get_install_command(candidate.tech_stack)}

# Run the application
{self._get_run_command(candidate.tech_stack)}
```

## Common Modifications

### Adding a New Feature

1. Create new module in `src/`
2. Implement core logic
3. Add exports to main module
4. Update tests
5. Document in README

### Modifying Existing Features

1. Locate feature in `src/`
2. Make changes
3. Update tests
4. Update documentation

## Source Files

This project was generated from:

{chr(10).join(f'- `{f}`' for f in candidate.source_files[:15])}

## Complexity: {candidate.complexity.title()}

---

*Generated by CCKnowledgeExtractor Project Maker*
'''
        (project_dir / 'CLAUDE.md').write_text(claude_md, encoding='utf-8')
        count += 1

        return count

    def _generate_gitignore(self, project_dir: Path, lang: str) -> int:
        """Generate .gitignore file."""
        templates = self.TEMPLATES.get(lang, self.TEMPLATES['JavaScript'])
        gitignore = templates.get('gitignore', 'node_modules/\n.env\n')
        (project_dir / '.gitignore').write_text(gitignore, encoding='utf-8')
        return 1

    def _get_prerequisites(self, tech_stack: List[str]) -> str:
        """Get prerequisites based on tech stack."""
        prereqs = []
        if 'Rust' in tech_stack:
            prereqs.append('Rust 1.70+ (https://rustup.rs)')
        if any(t in tech_stack for t in ['JavaScript', 'TypeScript', 'React', 'Express']):
            prereqs.append('Node.js 18+ (https://nodejs.org)')
        if any(t in tech_stack for t in ['Python', 'FastAPI', 'Flask', 'Django']):
            prereqs.append('Python 3.10+ (https://python.org)')
        return '\n- '.join(prereqs) if prereqs else 'See documentation'

    def _get_install_command(self, tech_stack: List[str]) -> str:
        """Get install command based on tech stack."""
        if 'Rust' in tech_stack:
            return 'cargo build'
        if any(t in tech_stack for t in ['JavaScript', 'TypeScript', 'React', 'Express']):
            return 'npm install'
        if any(t in tech_stack for t in ['Python', 'FastAPI', 'Flask', 'Django']):
            return 'pip install -r requirements.txt'
        return 'See documentation'

    def _get_run_command(self, tech_stack: List[str]) -> str:
        """Get run command based on tech stack."""
        if 'Rust' in tech_stack:
            return 'cargo run'
        if any(t in tech_stack for t in ['JavaScript', 'TypeScript', 'React', 'Express']):
            return 'npm start'
        if any(t in tech_stack for t in ['Python', 'FastAPI', 'Flask', 'Django']):
            return 'python main.py'
        return 'See documentation'

    def _get_structure(self, tech_stack: List[str]) -> str:
        """Get project structure based on tech stack."""
        if 'Rust' in tech_stack:
            return '''├── Cargo.toml
├── src/
│   ├── main.rs
│   └── lib.rs'''
        if any(t in tech_stack for t in ['TypeScript']):
            return '''├── package.json
├── tsconfig.json
├── src/
│   └── index.ts'''
        if any(t in tech_stack for t in ['JavaScript', 'React', 'Express']):
            return '''├── package.json
├── src/
│   └── index.js'''
        if any(t in tech_stack for t in ['Python', 'FastAPI', 'Flask']):
            return '''├── requirements.txt
├── main.py
├── src/
│   └── __init__.py'''
        return '''├── src/
│   └── ...'''

    def _get_detailed_setup(self, tech_stack: List[str]) -> str:
        """Get detailed setup instructions."""
        if 'Rust' in tech_stack:
            return '''1. Install Rust via rustup: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
2. Clone the repository
3. Run `cargo build` to compile
4. Run `cargo run` to execute'''
        if any(t in tech_stack for t in ['JavaScript', 'TypeScript']):
            return '''1. Install Node.js 18+
2. Clone the repository
3. Run `npm install`
4. Run `npm start`'''
        if any(t in tech_stack for t in ['Python']):
            return '''1. Install Python 3.10+
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Unix) or `venv\\Scripts\\activate` (Windows)
4. Install: `pip install -r requirements.txt`
5. Run: `python main.py`'''
        return 'See prerequisites and run commands above.'


# =============================================================================
# Main Orchestrator
# =============================================================================

class ProjectMaker:
    """Main orchestrator for project discovery and generation."""

    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.source_files: List[SourceFile] = []
        self.projects: List[Project] = []
        self.log: List[str] = []

    def run(self) -> Dict[str, Any]:
        """Execute the complete project making workflow."""
        self._log("Starting Project Maker...")

        # Step 1: Scan and load all source files
        self._log("Step 1: Scanning source files...")
        self._scan_sources()

        if not self.source_files:
            return self._create_result(success=False, error="No source files found")

        self._log(f"Found {len(self.source_files)} source files")

        # Step 2: Analyze content and discover projects
        self._log("Step 2: Analyzing content...")
        candidates = self._discover_projects()

        if not candidates:
            return self._create_result(
                success=True,
                error="No projects discovered in content",
                has_projects=False
            )

        self._log(f"Discovered {len(candidates)} project(s)")

        # Step 3: Generate projects
        self._log("Step 3: Generating projects...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        generator = ProjectGenerator(self.output_dir)
        all_content = '\n\n'.join(sf.content for sf in self.source_files)

        for candidate in candidates:
            self._log(f"  Generating: {candidate.synthesized_name}")
            project = generator.generate_project(candidate, all_content)
            self.projects.append(project)
            self._log(f"    Status: {project.status}, Files: {project.files_created}")

        # Step 4: Write discovery manifest
        self._log("Step 4: Writing manifest...")
        self._write_manifest()

        # Step 5: Write generation log
        self._write_log()

        return self._create_result(success=True, has_projects=True)

    def _log(self, message: str):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")

    def _scan_sources(self):
        """Scan input directory for all source files."""
        if not self.input_dir.exists():
            return

        # File type mappings
        type_map = {
            '.srt': 'transcript', '.vtt': 'transcript',
            '.md': 'documentation', '.txt': 'documentation',
            '.py': 'code', '.js': 'code', '.ts': 'code', '.rs': 'code',
            '.go': 'code', '.java': 'code', '.cs': 'code', '.cpp': 'code',
            '.c': 'code', '.h': 'code', '.hpp': 'code', '.rb': 'code',
            '.php': 'code', '.swift': 'code', '.kt': 'code',
        }

        for file_path in self.input_dir.rglob('*'):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            file_type = type_map.get(ext, 'extracted')

            # Skip binary files
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.exe']:
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Parse SRT files
                if ext in ['.srt', '.vtt']:
                    content = SRTParser.parse(content)

                if content.strip():
                    self.source_files.append(SourceFile(
                        path=file_path,
                        name=file_path.name,
                        extension=ext,
                        content=content,
                        file_type=file_type,
                        char_count=len(content),
                    ))
            except Exception as e:
                self._log(f"Warning: Could not read {file_path.name}: {e}")

    def _discover_projects(self) -> List[ProjectCandidate]:
        """Discover projects from analyzed content."""
        analyzer = ContentAnalyzer()

        # Aggregate analysis results
        all_tech = set()
        all_features = set()
        cli_projects = []  # Projects from CLI commands (high confidence)
        all_code = []
        complexity_votes = {'beginner': 0, 'intermediate': 0, 'advanced': 0}

        for sf in self.source_files:
            result = analyzer.analyze(sf.content, sf.name)
            all_tech.update(result['tech_stack'])
            all_features.update(result['features'])
            # Only keep high-confidence projects from CLI commands
            for proj in result['projects']:
                if proj.get('confidence') == 'high':
                    cli_projects.append(proj)
            all_code.extend(result['code_blocks'])
            complexity_votes[result['complexity']] += 1

        # Determine primary tech from file extensions (most reliable)
        primary_tech = self._determine_primary_tech(all_tech)

        # Determine overall complexity
        complexity = max(complexity_votes, key=complexity_votes.get)

        # Extract project name from course folder path
        course_name = self._extract_course_name()

        # Strategy: Create ONE comprehensive project per course
        # Only split if we found multiple distinct CLI-created projects
        if len(cli_projects) > 1:
            # Multiple distinct projects found via CLI commands
            self._log(f"  Found {len(cli_projects)} distinct projects via CLI commands")
            return self._create_multiple_candidates(
                cli_projects, primary_tech, all_tech, all_features, all_code, complexity
            )
        else:
            # Single comprehensive project from all content
            project_name = cli_projects[0]['name'] if cli_projects else course_name
            return [self._create_single_candidate(
                project_name, primary_tech, all_tech, all_features, all_code, complexity
            )]

    def _determine_primary_tech(self, all_tech: set) -> str:
        """Determine primary technology, prioritizing by file extensions."""
        # Priority order - languages that define the project type
        priority = ['Rust', 'Go', 'TypeScript', 'Python', 'JavaScript', 'Java', 'C#', 'C++']

        # Count code files by extension
        ext_counts = defaultdict(int)
        for sf in self.source_files:
            if sf.file_type == 'code':
                ext_counts[sf.extension] += 1

        # Map extensions to languages
        ext_to_lang = {
            '.rs': 'Rust', '.go': 'Go', '.ts': 'TypeScript', '.tsx': 'TypeScript',
            '.py': 'Python', '.js': 'JavaScript', '.jsx': 'JavaScript',
            '.java': 'Java', '.cs': 'C#', '.cpp': 'C++', '.c': 'C++'
        }

        # Find most common code file extension
        if ext_counts:
            most_common_ext = max(ext_counts, key=ext_counts.get)
            if most_common_ext in ext_to_lang:
                return ext_to_lang[most_common_ext]

        # Fall back to priority order from detected tech
        for lang in priority:
            if lang in all_tech:
                return lang

        return list(all_tech)[0] if all_tech else ''

    def _extract_course_name(self) -> str:
        """Extract a clean project name from the course folder path."""
        # Go up from __cc_validated_files to get the course name
        course_path = self.input_dir
        if course_path.name == '__cc_validated_files':
            course_path = course_path.parent  # CODE folder
        if course_path.name == 'CODE':
            course_path = course_path.parent  # Course folder

        course_name = course_path.name

        # Clean up the name
        # Remove common prefixes/suffixes
        for pattern in [r'^\d+\s*[-_.]\s*', r'\s*[-_]\s*\d+$', r'\s*\(.*\)$']:
            course_name = re.sub(pattern, '', course_name)

        # Extract key words (skip common words)
        skip_words = {'with', 'and', 'the', 'a', 'an', 'for', 'to', 'in', 'on', 'of', 'from', 'by'}
        words = []
        for word in re.findall(r'[A-Za-z]+', course_name):
            if word.lower() not in skip_words and len(word) > 1:
                words.append(word.title())

        if len(words) >= 2:
            # Take up to 4 meaningful words
            return ' '.join(words[:4])
        elif words:
            return words[0]
        else:
            return "Course Project"

    def _create_single_candidate(self, name: str, primary_tech: str, all_tech: set,
                                  all_features: set, all_code: list, complexity: str) -> ProjectCandidate:
        """Create a single comprehensive project candidate."""
        # Generate synthesized name
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        words = [w for w in clean_name.split() if w.lower() != primary_tech.lower()][:3]
        synth_name = f"Project_{primary_tech}{''.join(w.title() for w in words)}"
        synth_name = synth_name[:50]

        return ProjectCandidate(
            id="proj_001",
            name=name,
            synthesized_name=synth_name,
            description=f"{name} - A {complexity} level {primary_tech or 'programming'} project",
            source_files=[sf.name for sf in self.source_files],
            tech_stack=self._order_tech_stack(primary_tech, all_tech),
            complexity=complexity,
            features=list(all_features)[:20],
            code_snippets=all_code[:10],
        )

    def _create_multiple_candidates(self, cli_projects: list, primary_tech: str, all_tech: set,
                                     all_features: set, all_code: list, complexity: str) -> List[ProjectCandidate]:
        """Create multiple project candidates from CLI-discovered projects."""
        candidates = []
        seen_names = set()

        for i, proj in enumerate(cli_projects[:3]):  # Limit to 3 projects
            name = proj['name']
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
            words = [w for w in clean_name.split() if w.lower() != primary_tech.lower()][:3]
            synth_name = f"Project_{primary_tech}{''.join(w.title() for w in words)}"
            synth_name = synth_name[:50]

            candidates.append(ProjectCandidate(
                id=f"proj_{i+1:03d}",
                name=name,
                synthesized_name=synth_name,
                description=f"{name} - A {complexity} level {primary_tech or 'programming'} project",
                source_files=[sf.name for sf in self.source_files],
                tech_stack=self._order_tech_stack(primary_tech, all_tech),
                complexity=complexity,
                features=list(all_features)[:20],
                code_snippets=all_code[:10],
            ))

        return candidates

    def _order_tech_stack(self, primary_tech: str, all_tech: set) -> List[str]:
        """Order tech stack with primary tech first."""
        ordered = []
        if primary_tech:
            ordered.append(primary_tech)
        for tech in sorted(all_tech):
            if tech != primary_tech:
                ordered.append(tech)
        return ordered

    def _write_manifest(self):
        """Write discovery.json manifest."""
        manifest = {
            'course_path': str(self.input_dir),
            'discovered_at': datetime.now().isoformat(),
            'version': '1.0',
            'source_files': {
                'transcripts': sum(1 for sf in self.source_files if sf.file_type == 'transcript'),
                'documentation': sum(1 for sf in self.source_files if sf.file_type == 'documentation'),
                'code_samples': sum(1 for sf in self.source_files if sf.file_type == 'code'),
                'extracted': sum(1 for sf in self.source_files if sf.file_type == 'extracted'),
            },
            'projects': [asdict(p) for p in self.projects],
            'total_projects': len(self.projects),
            'successful': sum(1 for p in self.projects if p.status == 'generated'),
            'failed': sum(1 for p in self.projects if p.status == 'failed'),
        }

        (self.output_dir / 'discovery.json').write_text(
            json.dumps(manifest, indent=2), encoding='utf-8'
        )

    def _write_log(self):
        """Write generation.log."""
        (self.output_dir / 'generation.log').write_text(
            '\n'.join(self.log), encoding='utf-8'
        )

    def _create_result(self, success: bool, error: Optional[str] = None,
                       has_projects: bool = False) -> Dict[str, Any]:
        """Create result dictionary."""
        return {
            'success': success,
            'error': error,
            'has_projects': has_projects,
            'projects_generated': len([p for p in self.projects if p.status == 'generated']),
            'projects_failed': len([p for p in self.projects if p.status == 'failed']),
            'output_path': str(self.output_dir),
            'projects': [
                {
                    'name': p.synthesized_name,
                    'status': p.status,
                    'files_created': p.files_created,
                    'path': p.output_path,
                }
                for p in self.projects
            ],
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Project Maker - Transform course content into working projects'
    )
    parser.add_argument('input_dir', help='Input directory with validated files')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('--json', action='store_true', help='Output JSON result')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)

    try:
        maker = ProjectMaker(input_dir, output_dir)
        result = maker.run()

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['success'] and result['has_projects']:
                print(f"\nProject Maker Complete!")
                print(f"="*50)
                print(f"  Projects generated: {result['projects_generated']}")
                print(f"  Projects failed:    {result['projects_failed']}")
                print(f"  Output:             {result['output_path']}")
                print()
                for proj in result['projects']:
                    status_icon = "✓" if proj['status'] == 'generated' else "✗"
                    print(f"  {status_icon} {proj['name']}")
                    print(f"    Files: {proj['files_created']}")
                    print(f"    Path:  {proj['path']}")
                print()
            elif result['success']:
                print(f"\nNo projects discovered in content.")
                print(f"The source files may not contain hands-on project content.")
            else:
                print(f"\nError: {result.get('error', 'Unknown error')}")
                sys.exit(1)

    except Exception as e:
        if args.json:
            print(json.dumps({'success': False, 'error': str(e)}))
        else:
            print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
