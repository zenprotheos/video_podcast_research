#!/usr/bin/env node

/**
 * Enhanced TOC Updater (VoiceScribeAI)
 * - Regenerates existing TOCs to match current content
 * - Adds TOCs to files that don't have them
 * - Maintains standard TOC format with maintenance comments
 * - Supports selective file processing
 * - Safe backup and preview modes
 */

const fs = require('fs');
const path = require('path');

class EnhancedTOCUpdater {
  constructor(options = {}) {
    this.dryRun = options.dryRun || false;
    this.verbose = options.verbose || false;
    this.forceRegenerate = options.forceRegenerate || false;
    this.baseDir = options.baseDir || 'docs';
    
    // Standard markers
    this.TOC_MARKER = '## 📋 Table of Contents';
    this.TOC_MAINTENANCE_START = '🤖 **AI TIP: TABLE OF CONTENTS MAINTENANCE**';
    this.TOC_MAINTENANCE_END = '- **Update TOC immediately after making structural changes to this document**';
    this.FRONTMATTER_START = '---';
    this.FRONTMATTER_END = '---';
  }

  async processFromArgs() {
    const args = process.argv.slice(2);
    let filesToProcess = [];

    if (args.includes('--help')) {
      this.showHelp();
      return;
    }

    // Parse options
    this.dryRun = args.includes('--dry-run');
    this.verbose = args.includes('--verbose');
    this.forceRegenerate = args.includes('--force-regenerate');

    // Determine files to process
    if (args.includes('--all')) {
      filesToProcess = await this.getAllMarkdownFiles();
    } else if (args.includes('--files')) {
      const filesArg = args[args.indexOf('--files') + 1];
      if (filesArg) {
        filesToProcess = filesArg.split(',').map(f => f.trim());
      }
    } else if (args.includes('--pattern')) {
      const pattern = args[args.indexOf('--pattern') + 1];
      if (pattern) {
        console.log('Pattern matching not yet implemented (glob dependency removed)');
        filesToProcess = [];
      }
    } else {
      filesToProcess = await this.findFilesNeedingTOCUpdate();
    }

    if (filesToProcess.length === 0) {
      console.log('No files to process.');
      return;
    }

    console.log(`\n📋 Enhanced TOC Updater`);
    console.log(`Mode: ${this.dryRun ? 'DRY RUN' : 'LIVE UPDATE'}`);
    console.log(`Files to process: ${filesToProcess.length}`);
    console.log(`Force regenerate: ${this.forceRegenerate ? 'Yes' : 'No'}`);
    console.log(`─────────────────────────────────────────\n`);

    let processed = 0;
    let errors = 0;

    for (const filePath of filesToProcess) {
      try {
        const result = await this.processFile(filePath);
        if (result.changed) {
          processed++;
        }
        
        if (this.verbose || result.changed) {
          console.log(`${result.changed ? '✅' : '⏭️'} ${filePath}: ${result.message}`);
        }
      } catch (error) {
        errors++;
        console.error(`❌ ${filePath}: ${error.message}`);
      }
    }

    console.log(`\n📊 Summary:`);
    console.log(`  Files processed: ${processed}`);
    console.log(`  Errors: ${errors}`);
    console.log(`  Mode: ${this.dryRun ? 'DRY RUN (no changes made)' : 'CHANGES APPLIED'}`);

    // Completion sentinel for cursor agent
    console.log(`\n[[COMPLETED:${errors > 0 ? 1 : 0}]]`);
  }

  async getAllMarkdownFiles() {
    // Simple recursive file finder (no glob dependency)
    const result = [];
    function walk(dir) {
      const files = fs.readdirSync(dir);
      for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
          walk(fullPath);
        } else if (file.endsWith('.md')) {
          result.push(fullPath);
        }
      }
    }
    walk(this.baseDir);
    return result;
  }

  async findFilesNeedingTOCUpdate() {
    const allFiles = await this.getAllMarkdownFiles();
    const needsUpdate = [];

    for (const filePath of allFiles) {
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const analysis = this.analyzeTOCStatus(content);
        if (analysis.needsUpdate) needsUpdate.push(filePath);
      } catch (_) {
        // ignore read errors
      }
    }
    return needsUpdate;
  }

  analyzeTOCStatus(content) {
    const lines = content.split('\n');
    const headings = this.extractHeadings(content);
    const tocIndex = lines.findIndex(line => line.includes(this.TOC_MARKER));
    const hasTOC = tocIndex !== -1;
    let needsUpdate = false;

    if (!hasTOC) {
      needsUpdate = headings.length > 0;
    } else if (this.forceRegenerate) {
      needsUpdate = true;
    } else {
      const currentTOC = this.extractCurrentTOC(content);
      const expectedTOC = this.generateTOCLines(headings);
      needsUpdate = !this.tocMatches(currentTOC, expectedTOC);
    }

    return { hasTOC, headingCount: headings.length, needsUpdate };
  }

  extractHeadings(content) {
    const lines = content.split('\n');
    const headings = [];
    for (const line of lines) {
      if (line.match(/^#{2,4}\s+/)) {
        const level = (line.match(/^#+/) || [''])[0].length;
        const title = line.replace(/^#+\s*/, '').trim();
        if (title.includes('Table of Contents') || title.includes('AI TIP:') || title.includes('🤖')) continue;
        headings.push({ level, title });
      }
    }
    return headings;
  }

  extractCurrentTOC(content) {
    const lines = content.split('\n');
    const tocStart = lines.findIndex(line => line.includes(this.TOC_MARKER));
    if (tocStart === -1) return [];
    const tocLines = [];
    let i = tocStart + 1;
    while (i < lines.length && lines[i].trim() === '') i++;
    while (i < lines.length) {
      const line = lines[i];
      if (line.includes(this.TOC_MAINTENANCE_START) || 
          line.match(/^#{1,4}\s+/) ||
          (!line.trim().startsWith('-') && line.trim() !== '')) break;
      if (line.trim().startsWith('-')) tocLines.push(line);
      i++;
    }
    return tocLines;
  }

  generateTOCLines(headings) {
    const tocLines = [];
    for (const heading of headings) {
      const anchor = heading.title.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
      const indent = '  '.repeat(heading.level - 2);
      tocLines.push(`${indent}- [${heading.title}](#${anchor})`);
    }
    return tocLines;
  }

  tocMatches(currentTOC, expectedTOC) {
    if (currentTOC.length !== expectedTOC.length) return false;
    for (let i = 0; i < currentTOC.length; i++) {
      if (currentTOC[i].trim() !== expectedTOC[i].trim()) return false;
    }
    return true;
  }

  async processFile(filePath) {
    if (!fs.existsSync(filePath)) throw new Error('File not found');
    const originalContent = fs.readFileSync(filePath, 'utf8');
    const analysis = this.analyzeTOCStatus(originalContent);
    if (!analysis.needsUpdate) return { changed: false, message: 'TOC is up to date' };
    if (analysis.headingCount === 0) return { changed: false, message: 'No headings found, skipping TOC' };
    const newContent = this.updateTOC(originalContent);
    if (newContent === originalContent) return { changed: false, message: 'No changes needed' };
    if (!this.dryRun) fs.writeFileSync(filePath, newContent);
    const action = analysis.hasTOC ? 'Updated' : 'Added';
    return { changed: true, message: `${action} TOC (${analysis.headingCount} headings)` };
  }

  updateTOC(content) {
    const lines = content.split('\n');
    const headings = this.extractHeadings(content);
    if (headings.length === 0) return content;

    const tocStartIndex = lines.findIndex(line => line.includes(this.TOC_MARKER));
    let tocEndIndex = -1;
    if (tocStartIndex !== -1) {
      for (let i = tocStartIndex + 1; i < lines.length; i++) {
        if (lines[i].includes(this.TOC_MAINTENANCE_END)) { tocEndIndex = i; break; }
        else if (lines[i].match(/^#{1,4}\s+/) && !lines[i].includes('🤖')) { tocEndIndex = i - 1; break; }
      }
      if (tocEndIndex === -1) tocEndIndex = tocStartIndex;
    }

    let insertIndex = 0;
    let inFrontMatter = false;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line === this.FRONTMATTER_START) {
        if (inFrontMatter) { insertIndex = i + 1; break; }
        else { inFrontMatter = true; }
      }
    }

    const tocLines = this.generateTOCLines(headings);
    const newTOCSection = [
      '',
      this.TOC_MARKER,
      '',
      ...tocLines,
      '',
      this.TOC_MAINTENANCE_START,
      '- **TOC is automatically maintained by: `node tools/workflow_utilities/enhanced-toc-updater.cjs`**',
      '- **For manual updates: Run the workflow orchestrator with: `node tools/workflow_utilities/workflow-orchestrator.cjs`**',
      '- **This TOC was auto-generated and will be updated automatically on structural changes**',
      this.TOC_MAINTENANCE_END,
      ''
    ];

    let newLines;
    if (tocStartIndex !== -1) {
      newLines = [
        ...lines.slice(0, tocStartIndex),
        ...newTOCSection,
        ...lines.slice(tocEndIndex + 1)
      ];
    } else {
      newLines = [
        ...lines.slice(0, insertIndex),
        ...newTOCSection,
        ...lines.slice(insertIndex)
      ];
    }
    return newLines.join('\n');
  }

  showHelp() {
    console.log(`
Enhanced TOC Updater (VoiceScribeAI)

Usage:
  node tools/workflow_utilities/enhanced-toc-updater.cjs [options]

Options:
  --all                     Process all .md files in docs/
  --files "file1,file2"     Process specific files (comma-separated)
  --pattern "docs/specs/*"  Process files matching glob pattern
  --dry-run                 Preview changes without applying them
  --verbose                 Show detailed output
  --force-regenerate        Force TOC regeneration even if current
  --help                    Show this help message
`);
  }
}

if (require.main === module) {
  const updater = new EnhancedTOCUpdater();
  updater.processFromArgs().catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
}

module.exports = EnhancedTOCUpdater;


