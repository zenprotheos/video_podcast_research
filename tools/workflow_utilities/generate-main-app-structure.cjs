#!/usr/bin/env node

/**
 * VoiceScribeAI Main Application Structure Generator
 *
 * Generates a concise tree of the runtime-critical backend and frontend
 * assets so AI agents always have an up-to-date view of the main app.
 */

const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const docsRoot = path.join(repoRoot, 'docs');
const defaultOutput = path.join(docsRoot, 'MAIN_APP_STRUCTURE.md');

const SECTION_DEFINITIONS = [
    {
        title: 'Backend (Flask API)',
        description:
            'Python backend responsible for ingestion, transcription, summarization, and knowledge management integrations.',
        items: [
            { path: 'app.py' },
            { path: 'main.py' },
            { path: 'routes.py' },
            { path: 'models.py' },
            { path: 'config' },
            { path: 'services' },
            { path: 'src' },
            { path: 'templates' },
            { path: 'static' },
            { path: 'prompts' },
            { path: 'database' },
            { path: 'migrations' }
        ]
    },
    {
        title: 'Frontend (Next.js Application)',
        description:
            'Next.js interface that communicates with the Flask backend. Includes runtime configuration and source directories.',
        items: [{ path: 'frontend' }]
    },
    {
        title: 'Runtime Tooling & Dependencies',
        description: 'Launch scripts and dependency manifests required for local development of the main app.',
        items: [
            { path: 'requirements.txt' },
            { path: 'pyproject.toml' },
            { path: 'uv.lock' },
            { path: 'start-app.bat' },
            { path: 'start-backend.bat' },
            { path: 'start-frontend.bat' },
            { path: 'start-smart-simple.bat' },
            { path: 'stop-services.bat' }
        ]
    }
];

const DEFAULT_EXCLUDED_DIRECTORIES = new Set([
    '.git',
    '.idea',
    '.vscode',
    '.cache',
    '.mypy_cache',
    '.pytest_cache',
    '__pycache__',
    'node_modules',
    '.next',
    '.turbo',
    '.vercel',
    'coverage',
    'dist',
    'build',
    'temp',
    'tasks',
    'test',
    'tests',
    '__tests__',
    '__snapshots__'
]);

const DEFAULT_EXCLUDED_FILES = new Set(['.DS_Store', 'Thumbs.db']);
const DEFAULT_FILE_PATTERNS = [/\.pyc$/i, /\.pyo$/i, /\.log$/i];

const PATH_RULES = {
    frontend: {
        excludeDirs: new Set(['node_modules', 'tests', '.next', '.turbo', '.vercel', 'coverage', 'cypress']),
        excludeFiles: new Set(['jest.config.js', 'vitest.config.ts', 'README.md', '.gitignore'])
    }
};

function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        output: defaultOutput,
        print: false
    };

    for (let i = 0; i < args.length; i += 1) {
        const arg = args[i];
        switch (arg) {
            case '--output':
            case '-o': {
                const next = args[i + 1];
                if (!next) {
                    throw new Error('Missing value for --output');
                }
                options.output = path.resolve(repoRoot, next);
                i += 1;
                break;
            }
            case '--print':
            case '--show':
                options.print = true;
                break;
            case '--help':
            case '-h':
                printHelp();
                process.exit(0);
                break;
            default:
                throw new Error(`Unknown option: ${arg}`);
        }
    }

    return options;
}

function printHelp() {
    console.log(`VoiceScribeAI main application structure generator\n\nUsage:\n  node tools/workflow_utilities/generate-main-app-structure.cjs [options]\n\nOptions:\n  -o, --output <path>  Write to a custom output path (default: docs/MAIN_APP_STRUCTURE.md)\n  --print, --show      Echo the generated document to stdout after writing\n  -h, --help           Show this help message\n`);
}

function shouldExclude(dirent, parentRelPath, rootKey) {
    const name = dirent.name;

    if (dirent.isDirectory()) {
        if (DEFAULT_EXCLUDED_DIRECTORIES.has(name)) {
            return true;
        }
    } else {
        if (DEFAULT_EXCLUDED_FILES.has(name)) {
            return true;
        }
        for (const pattern of DEFAULT_FILE_PATTERNS) {
            if (pattern.test(name)) {
                return true;
            }
        }
    }

    const rule = PATH_RULES[rootKey];
    if (rule) {
        if (dirent.isDirectory() && rule.excludeDirs && rule.excludeDirs.has(name)) {
            return true;
        }
        if (!dirent.isDirectory() && rule.excludeFiles && rule.excludeFiles.has(name)) {
            return true;
        }
    }

    return false;
}

function sortDirents(a, b) {
    if (a.isDirectory() && !b.isDirectory()) return -1;
    if (!a.isDirectory() && b.isDirectory()) return 1;
    return a.name.localeCompare(b.name, 'en', { sensitivity: 'base', numeric: true });
}

function buildTreeLines(relativePath, rootKey, indentLevel = 0) {
    const absolutePath = path.join(repoRoot, relativePath);
    const stats = fs.lstatSync(absolutePath);
    const segments = relativePath.split(/\\|\//);
    const name = segments[segments.length - 1];
    const indent = '  '.repeat(indentLevel);
    const displayName = stats.isDirectory() ? `${name}/` : name;
    const lines = [`${indent}${displayName}`];

    if (stats.isDirectory()) {
        const entries = fs.readdirSync(absolutePath, { withFileTypes: true })
            .filter((dirent) => !shouldExclude(dirent, relativePath, rootKey))
            .sort(sortDirents);

        for (const entry of entries) {
            const childRel = `${relativePath}/${entry.name}`.replace(/\\/g, '/');
            lines.push(...buildTreeLines(childRel, rootKey, indentLevel + 1));
        }
    }

    return lines;
}

function ensureDocsDirectory() {
    if (!fs.existsSync(docsRoot)) {
        fs.mkdirSync(docsRoot, { recursive: true });
    }
}

function generateDocument(sections) {
    const now = new Date().toISOString();
    const header = [
        '# VoiceScribeAI — Main Application Structure',
        '',
        `_Generated automatically on ${now} by \`tools/workflow_utilities/generate-main-app-structure.cjs\`._`,
        '',
        'This map lists only the runtime-critical backend and frontend resources.',
        'Documentation, tasks, archived assets, and auxiliary tooling are intentionally excluded.',
        'All paths are relative to the repository root.',
        ''
    ];

    const missingItems = [];
    const body = [];

    for (const section of sections) {
        body.push(`## ${section.title}`);
        if (section.description) {
            body.push('', section.description, '');
        } else {
            body.push('');
        }

        const treeLines = [];
        for (const item of section.items) {
            const normalized = item.path.replace(/\\/g, '/');
            const absolute = path.join(repoRoot, normalized);
            if (!fs.existsSync(absolute)) {
                missingItems.push(normalized);
                continue;
            }

            const rootKey = item.rootKey || normalized.split('/')[0];
            const lines = buildTreeLines(normalized, rootKey, 0);
            if (lines.length) {
                treeLines.push(...lines);
            }
        }

        if (treeLines.length) {
            body.push('```', ...treeLines, '```', '');
        } else {
            body.push('_No entries found._', '');
        }
    }

    if (missingItems.length) {
        body.push('## Missing Paths', '', 'The following configured paths were not found when the structure was generated:', '');
        for (const missing of missingItems) {
            body.push(`- ${missing}`);
        }
        body.push('');
    }

    body.push('## Regeneration', '', '```bash', 'node tools/workflow_utilities/generate-main-app-structure.cjs', '```', '');

    return header.concat(body).join('\n');
}

function main() {
    let options;
    try {
        options = parseArgs();
    } catch (error) {
        console.error(`❌ ${error.message}`);
        console.log('\n[[ERROR:1]]');
        process.exit(1);
    }

    try {
        ensureDocsDirectory();
        const content = generateDocument(SECTION_DEFINITIONS);
        fs.writeFileSync(options.output, content, 'utf8');

        console.log(`✅ Main app structure written to ${path.relative(repoRoot, options.output).replace(/\\/g, '/')}`);
        if (options.print) {
            console.log('\n' + content);
        }
        console.log('\n[[COMPLETED:0]]');
    } catch (error) {
        console.error(`❌ Failed to generate structure: ${error.message}`);
        console.log('\n[[ERROR:1]]');
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    SECTION_DEFINITIONS,
    buildTreeLines,
    generateDocument
};
