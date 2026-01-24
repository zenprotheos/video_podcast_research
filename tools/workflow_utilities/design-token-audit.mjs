import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, extname, join, normalize, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const repoRoot = resolve(__dirname, '..', '..');

const DEFAULT_INCLUDE_ROOTS = [
  join(repoRoot, 'frontend', 'src'),
  join(repoRoot, 'frontend', 'tests'),
];

const IGNORED_DIRECTORIES = new Set([
  'node_modules',
  '.next',
  '.turbo',
  'coverage',
  '.git',
  'dist',
  'build',
  'out',
  '.cache',
  '.idea',
]);

const IGNORED_FILES = new Set([
  // Theme tokens live here and may use raw values by design.
  normalize(join(repoRoot, 'frontend', 'src', 'app', 'globals.css')),
]);

const SUPPORTED_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.css', '.scss', '.sass']);

const TAILWIND_COLOR_PATTERN = /\b(?:[a-z-]+:)*(?:bg|text|border|ring|outline|fill|stroke|shadow)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(?:50|100|200|300|400|500|600|700|800|900)\b/g;
const DIRECT_COLOR_PATTERN = /(#[0-9a-fA-F]{3,8})|(rgba?\([^)]*\))|(hsla?\([^)]*\))|\b(white|black|silver|gray|grey|red|orange|yellow|lime|green|teal|cyan|blue|indigo|purple|violet|magenta|pink|gold|brown|maroon|navy)\b/gi;

const HEADER = '\n🎨 VoiceScribeAI Design Token Audit\n';

function walkFiles(startDir, collected = []) {
  const entries = readdirSync(startDir);
  for (const entry of entries) {
    const fullPath = join(startDir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      if (IGNORED_DIRECTORIES.has(entry)) continue;
      walkFiles(fullPath, collected);
    } else if (stats.isFile()) {
      const ext = extname(entry);
      if (!SUPPORTED_EXTENSIONS.has(ext)) continue;
      collected.push(fullPath);
    }
  }
  return collected;
}

function analyzeFile(filePath) {
  if (IGNORED_FILES.has(normalize(filePath))) {
    return [];
  }

  const content = readFileSync(filePath, 'utf8');
  const lines = content.split(/\r?\n/);
  const relativePath = relative(repoRoot, filePath);

  const violations = [];

  lines.forEach((line, index) => {
    const lineNumber = index + 1;

    const tailwindMatches = line.match(TAILWIND_COLOR_PATTERN) || [];
    tailwindMatches.forEach((match) => {
      violations.push({
        type: 'tailwind-color',
        file: relativePath,
        line: lineNumber,
        token: match,
        excerpt: line.trim().slice(0, 180),
        message: `Replace '${match}' with a CSS variable from the design token system (var(--color-*))).`,
      });
    });

    const sanitizedForDirectColors = line
      .replace(/var\([^)]*\)/g, ' ')
      .replace(TAILWIND_COLOR_PATTERN, ' ');

    const directColorMatches = sanitizedForDirectColors.match(DIRECT_COLOR_PATTERN) || [];
    directColorMatches.forEach((match) => {
      const normalized = match.trim();
      if (normalized.length === 0) return;
      // Ignore 'transparent' since it is often required for accessibility focus rings.
      if (/^transparent$/i.test(normalized)) return;
      violations.push({
        type: 'direct-color',
        file: relativePath,
        line: lineNumber,
        token: normalized,
        excerpt: line.trim().slice(0, 180),
        message: `Replace '${normalized}' with the matching design token (var(--color-*))).`,
      });
    });
  });

  return violations;
}

function main() {
  console.log(HEADER);
  const roots = DEFAULT_INCLUDE_ROOTS.filter((dir) => statSync(dir, { throwIfNoEntry: false }));
  if (roots.length === 0) {
    console.error('⚠️  No target directories found to scan.');
    process.exitCode = 1;
    return;
  }

  const allFiles = roots.flatMap((dir) => walkFiles(dir));
  const violations = allFiles.flatMap(analyzeFile);

  if (violations.length === 0) {
    console.log('✅ Design token audit passed — no non-token colors detected.');
    return;
  }

  console.error('❌ Design token audit failed — detected non-token colors.');
  const summary = violations.reduce((acc, violation) => {
    acc[violation.type] = (acc[violation.type] || 0) + 1;
    return acc;
  }, {});
  const grouped = new Map();
  for (const violation of violations) {
    const key = violation.file;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(violation);
  }

  for (const [file, fileViolations] of grouped.entries()) {
    console.error(`\n  • ${file}`);
    fileViolations.forEach((violation) => {
      console.error(
        `    - line ${violation.line}: ${violation.message}\n      ${violation.excerpt}`
      );
    });
  }

  console.error(`\nTotals: ${JSON.stringify(summary)} (Total: ${violations.length})`);
  process.exitCode = 1;
}

main();
