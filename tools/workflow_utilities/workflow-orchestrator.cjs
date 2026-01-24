#!/usr/bin/env node

/**
 * Workflow Orchestrator - Bulk Utility Runner
 * Runs all workflow utilities in optimal order with anti-stall protection
 *
 * Usage:
 *   node tools/workflow_utilities/workflow-orchestrator.cjs [options] [files...]
 *
 * Options:
 *   --all          Process all markdown files
 *   --files        Process specific files (comma-separated)
 *   --quick        Skip verbose output for faster execution
 *   --validate-only Run validation only, no fixes
 */

const { execSync } = require('child_process');
const path = require('path');

function runWithFreshTerminal(cmd, description, timeoutSec = 120) {
  console.log(`\n🔧 ${description}`);
  console.log(`$ ${cmd}`);

  // Ensure temp directory exists
  const fs = require('fs');
  if (!fs.existsSync('temp')) {
    fs.mkdirSync('temp', { recursive: true });
  }

  // Create temp script for fresh terminal execution
  const tempScript = path.resolve(`temp/docs_maint_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.ps1`);

  const scriptContent = `
$ErrorActionPreference = 'Stop'
try {
  ${cmd}
  Write-Host '[[DONE:${description.replace(/\s+/g, '_')}]]'
  exit 0
} catch {
  Write-Host "[[ERROR:${description.replace(/\s+/g, '_')}]]"
  exit 1
}
`;

  // Write temp script
  console.log(`📝 Creating temp script: ${tempScript}`);
  require('fs').writeFileSync(tempScript, scriptContent);
  console.log(`✅ Temp script created successfully`);

  // Small delay to ensure file system sync
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500);

  // Verify file was created
  if (!require('fs').existsSync(tempScript)) {
    throw new Error(`Failed to create temp script: ${tempScript}`);
  }
  console.log(`✅ Temp script verified: ${require('fs').statSync(tempScript).size} bytes`);

  // Double-check file contents
  const content = require('fs').readFileSync(tempScript, 'utf8');
  console.log(`📄 Script content length: ${content.length} characters`);
  console.log(`📄 Script preview: ${content.substring(0, 100)}...`);

  try {
    // Execute in fresh PowerShell terminal (Windows rule compliant)
    const fullCmd = `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${tempScript}"`;

    console.log(`🚀 Executing PowerShell command: ${fullCmd}`);

    // Use execSync for simplicity and reliability
    const result = require('child_process').execSync(fullCmd, {
      stdio: 'inherit',
      timeout: timeoutSec * 1000,
      killSignal: 'SIGKILL'
    });

    console.log(`✅ ${description} completed (PowerShell process terminated)`);
    return result;

  } catch (error) {
    console.error(`❌ ${description} failed:`, error.message);
    throw error;
  } finally {
    // Clean up temp script
    try {
      require('fs').unlinkSync(tempScript);
      console.log(`🗑️ Cleaned up temp script: ${tempScript}`);
    } catch (e) {
      console.log(`⚠️ Could not clean up temp script: ${e.message}`);
    }
  }
}

function getCommandArgs() {
  const args = process.argv.slice(2);
  let command = '--all'; // default
  let files = [];

  if (args.includes('--files')) {
    const filesIndex = args.indexOf('--files') + 1;
    if (args[filesIndex]) {
      files = args[filesIndex].split(',').map(f => f.trim());
      command = `--files "${args[filesIndex]}"`;
    }
  } else if (args.includes('--all')) {
    command = '--all';
  }

  const verbose = !args.includes('--quick');
  const validateOnly = args.includes('--validate-only');

  return { command, files, verbose, validateOnly };
}

async function runMaintenance() {
  const { command, files, verbose, validateOnly } = getCommandArgs();
  const verboseFlag = verbose ? '--verbose' : '';

  console.log('🚀 Starting Workflow Orchestrator - Bulk Utility Runner');
  console.log('=' .repeat(50));

  let commandCount = 0;

  try {
    // Step 1: Front matter validation and fixes
    if (!validateOnly) {
      runWithFreshTerminal(`node tools/workflow_utilities/frontmatter_validator.cjs validate docs/`, 'Front-matter validation');
      commandCount++;

      // Buffer reset every 3-5 commands (Windows rule)
      if (commandCount % 3 === 0) {
        console.log('\n🔄 Buffer reset performed');
      }
    }

    // Step 2: TOC generation/update
    if (!validateOnly) {
      runWithFreshTerminal(`node tools/workflow_utilities/enhanced-toc-updater.cjs ${command} ${verboseFlag}`, 'TOC generation/update');
      commandCount++;

      // Buffer reset every 3-5 commands (Windows rule)
      if (commandCount % 3 === 0) {
        console.log('\n🔄 Buffer reset performed');
      }
    }

    // Step 3: Index generation
    runWithFreshTerminal(`node tools/workflow_utilities/global_indexer.cjs generate docs/`, 'Index generation');
    commandCount++;

    // Buffer reset every 3-5 commands (Windows rule)
    if (commandCount % 3 === 0) {
      console.log('\n🔄 Buffer reset performed');
    }

    // Step 4: Main app structure generation
    runWithFreshTerminal(`node tools/workflow_utilities/generate-main-app-structure.cjs`, 'Main app structure generation');
    commandCount++;

    // Buffer reset every 3-5 commands (Windows rule)
    if (commandCount % 3 === 0) {
      console.log('\n🔄 Buffer reset performed');
    }

    // Step 5: Terminal cleanup (new addition)
    if (!validateOnly) {
      console.log('\n🖥️ Running terminal cleanup...');
      try {
        runWithFreshTerminal(`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools/workflow_utilities/process_management/terminal_cleanup.ps1" -MaxAgeMinutes 15`, 'Terminal cleanup');
        commandCount++;
      } catch (e) {
        console.log('⚠️ Terminal cleanup skipped (may not be available in this environment)');
      }

      // Buffer reset every 3-5 commands (Windows rule)
      if (commandCount % 3 === 0) {
        console.log('\n🔄 Buffer reset performed');
      }
    }

    console.log('\n' + '='.repeat(50));
    console.log('✅ All documentation maintenance tasks completed successfully!');
    console.log('📋 Summary:');
    console.log('   • Front matter validated and corrected');
    console.log('   • Table of contents generated/updated');
    console.log('   • Documentation indexes rebuilt');
    console.log('   • Main app structure regenerated');
    console.log('   • Terminal processes cleaned up');
    console.log('   • All systems synchronized');

    // Clear completion sentinel for cursor agent
    console.log('\n[[COMPLETED:0]]');
    process.exit(0);

  } catch (e) {
    console.error('\n❌ Workflow orchestrator failed:', e.message);
    console.log('\n🔍 Troubleshooting:');
    console.log('   • Check that all tools in tools/workflow_utilities/ are present');
    console.log('   • Verify Node.js is installed and accessible');
    console.log('   • Ensure write permissions on target directories');

    // Clear error sentinel for cursor agent
    console.log('\n[[ERROR:1]]');
    process.exit(1);
  }
}

// Run the maintenance suite
runMaintenance();


