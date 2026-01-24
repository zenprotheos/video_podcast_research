---
title: "README"
created: "2025-09-23T04:36:49.601Z"
type: "guide"
purpose: "Essential project documentation providing comprehensive information about system capabilities, setup instructions, usage guidelines, and important considerations for effective implementation and operation of the VoiceScribeAI application."
status: "Active"
tags: ["voicescribeai"]
---




# Workflow Utilities

This directory contains automated tools for workflow enhancement, documentation maintenance, and system utilities in the OneShot system.

## Quick Start

**For most cases, use the workflow orchestrator:**
```bash
node tools/workflow_utilities/workflow-orchestrator.cjs --all
```

**For specific needs, use individual tools:**
```bash
# TOC only
node tools/workflow_utilities/enhanced-toc-updater.cjs --files "document.md"

# Front matter validation only
node tools/workflow_utilities/frontmatter_validator.cjs validate docs/

# Index generation only
node tools/workflow_utilities/global_indexer.cjs generate docs/

# Date utility for task naming
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 taskFolder
```

## AI Agent Usage Guidelines

### When to Use Comprehensive Maintenance
- ✅ **After task completion** - Run full maintenance on entire docs
- ✅ **Before git commits** - Ensure all docs are up to date
- ✅ **After major structural changes** - When multiple files need updates
- ✅ **End-of-session cleanup** - Comprehensive validation and fixes

### When to Use Individual Tools
- 🎯 **Single file TOC update** - `enhanced-toc-updater.cjs --files "file.md"`
- 🎯 **Front matter validation only** - `frontmatter_validator.cjs validate docs/`
- 🎯 **Quick index check** - `global_indexer.cjs check docs/`
- 🎯 **Performance-critical scenarios** - When you only need one specific maintenance task

### Completion Signals
All tools now include clear completion sentinels:
- `[[COMPLETED:0]]` - Success
- `[[COMPLETED:1]]` - Success with warnings/errors
- `[[ERROR:1]]` - Failure

This helps cursor agents reliably detect when scripts have finished executing.

## Tools Overview

### Core Maintenance Tools

#### `workflow-orchestrator.cjs` ⭐ **RECOMMENDED**
- **Purpose**: Bulk utility runner with anti-stall protection
- **Usage**: `node tools/workflow_utilities/workflow-orchestrator.cjs --all` (comprehensive) or individual options
- **Features**:
  - Runs all maintenance tools in optimal order
  - Clear completion sentinels for cursor agents
  - Validate-only mode for checking without changes
  - Progress tracking and error handling

#### `enhanced-toc-updater.cjs`
- **Purpose**: Updates and maintains table of contents across documentation
- **Usage**: `node enhanced-toc-updater.cjs [directory]`
- **Features**: Intelligent TOC generation with cross-references

#### `frontmatter_validator.cjs`
- **Purpose**: Validates front-matter in markdown files
- **Usage**: `node frontmatter_validator.cjs validate [directory]`
- **Features**:
  - Required field validation (title, created, type, purpose, status, tags)
  - Type validation against allowed values
  - Purpose description quality checks

#### `global_indexer.cjs`
- **Purpose**: Generates hierarchical indexes for documentation
- **Usage**: `node tools/workflow_utilities/global_indexer.cjs generate [directory]`
- **Features**:
  - Change detection and caching
  - Hierarchical index generation
  - Auto-generated navigation

#### `generate-main-app-structure.cjs`
- **Purpose**: Produces an up-to-date map of the runtime-ready backend and frontend assets.
- **Usage**: `node tools/workflow_utilities/generate-main-app-structure.cjs`
- **Features**:
  - Groups backend, frontend, and tooling paths into clearly separated sections
  - Filters out documentation, tests, and development-only artifacts
  - Overwrites `docs/MAIN_APP_STRUCTURE.md` with timestamps for agent awareness

#### `indentation_checker.py`
- **Purpose**: Comprehensive Python indentation and syntax validation
- **Usage**: `python tools/workflow_utilities/indentation_checker.py file.py`
- **Features**:
  - py_compile syntax checking (catches IndentationError, SyntaxError)
  - AST parsing validation (deep syntax analysis)
  - Import testing (module-level validation)
  - Pattern analysis (indentation consistency checks)
  - Control flow analysis (missing indentation detection)
  - Detailed error reporting with line numbers

#### `demonstrate_indentation_checks.py`
- **Purpose**: Demonstration and testing of programmatic indentation checking methods
- **Usage**: `python tools/workflow_utilities/demonstrate_indentation_checks.py`
- **Features**:
  - Shows all available indentation checking methods
  - Demonstrates proper usage patterns
  - Provides validation examples
  - Includes troubleshooting recommendations

#### `date-current.ps1`
- **Purpose**: Generates current date/timestamp for task workspaces and documentation
- **Usage**:
  ```bash
  # Date only (default)
  powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 taskFolder

  # Date and time timestamp
  powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 timestamp
  ```
- **Features**:
  - ISO 8601 timestamp generation
  - Task workspace naming support
  - Filename-friendly timestamp format (YYYYMMDD_HHMMSS)
  - Windows-compatible date formatting

### Python Development Tools

#### Indentation Checking Tools
Essential tools for preventing Python syntax errors and IndentationErrors:

**When to Use:**
- ✅ **Before commits** - Mandatory validation phase per core rules
- ✅ **After structural changes** - Loops, conditionals, try/except blocks
- ✅ **During debugging** - When encountering runtime syntax errors
- ✅ **Code reviews** - Automated syntax validation

**Usage Examples:**
```bash
# Quick syntax check (core rules requirement)
python -m py_compile pages/1_Bulk_Transcribe.py

# Comprehensive analysis
python tools/workflow_utilities/indentation_checker.py pages/1_Bulk_Transcribe.py

# Demonstration of all methods
python tools/workflow_utilities/demonstrate_indentation_checks.py
```

**Integration with Core Rules:**
These tools implement the **MANDATORY VALIDATION PHASE** required by `.cursor/rules/00-core.mdc`:
- All Python files must pass syntax validation before task completion
- Validation results must be documented in progress trackers
- Tasks cannot be marked complete with syntax errors

## Directory Structure

```
tools/workflow_utilities/
├── README.md                           # This documentation file
├── date-current.ps1                   # Date utility for timestamp generation
├── indentation_checker.py             # Comprehensive Python indentation validation
├── demonstrate_indentation_checks.py  # Demonstration of indentation checking methods
├── enhanced-toc-updater.cjs          # Table of contents management and updates
├── frontmatter_validator.cjs         # Front-matter validation for markdown files
├── global_indexer.cjs                # Hierarchical index generation for documentation
├── generate-main-app-structure.cjs   # Main app structure snapshot for agents
├── workflow-orchestrator.cjs         # Bulk utility runner with anti-stall protection
├── mermaid_validation/               # Mermaid diagram validation tools
│   ├── README.md                     # Mermaid validation documentation
│   ├── example_with_errors.md        # Example file with validation errors
│   ├── validate_mermaid.bat          # Batch script for mermaid validation
│   └── validate_mermaid.ps1          # PowerShell script for mermaid validation
└── process_management/               # Windows process management utilities
    ├── auto_cleanup.ps1              # Automatic cleanup of hanging processes
    ├── emergency_cleanup.ps1         # Emergency process cleanup
    ├── manual_cleanup.bat            # Manual process cleanup script
    ├── process_monitor.ps1           # Process monitoring and management
    └── PYTHON_PROCESS_FIX_README.md  # Python process troubleshooting guide
```

## Integration Points

### Recommended Workflow (Simple)
```bash
# One command handles everything
node tools/workflow_utilities/workflow-orchestrator.cjs --all
# Look for [[COMPLETED:0]] to confirm completion
```

### Advanced Workflow (Granular Control)
1. **Validation**: `node tools/workflow_utilities/frontmatter_validator.cjs validate docs/`
2. **TOC Updates**: `node tools/workflow_utilities/enhanced-toc-updater.cjs --all --verbose`
3. **Indexing**: `node tools/workflow_utilities/global_indexer.cjs generate docs/`

### CI/CD Integration
All tools include completion sentinels for reliable automation:
- Scripts exit with proper codes (0=success, 1=error)
- Clear `[[COMPLETED:X]]` or `[[ERROR:X]]` messages
- No hanging - cursor agents can reliably detect completion

## Global Rules Integration

Update the following global rules to reference the new paths:

- `.cursor/rules/cursor-windows-rule.mdc` - Update tool paths
- `.cursor/rules/coding-tasks.mdc` - Update maintenance workflow references
- Any scripts that reference these tools directly

## Usage in Workflows

### Automated Validation Pipeline
```bash
# Validate all documentation
node tools/workflow_utilities/frontmatter_validator.cjs validate docs/

# Generate indexes
node tools/workflow_utilities/global_indexer.cjs generate docs/

# Update TOCs
node tools/workflow_utilities/enhanced-toc-updater.cjs docs/

# Get current date for task naming
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 taskFolder

# Get timestamp for filename sorting (YYYYMMDD_HHMMSS)
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 timestamp
```

### CI/CD Integration
These tools can be integrated into CI/CD pipelines for automated documentation quality checks.

## Specialized Tool Directories

### Mermaid Validation Tools (`mermaid_validation/`)
Tools for validating Mermaid diagrams in documentation:
- **validate_mermaid.bat**: Batch script for Windows command line validation
- **validate_mermaid.ps1**: PowerShell script with enhanced error reporting
- **example_with_errors.md**: Sample file demonstrating common Mermaid syntax issues
- **README.md**: Comprehensive guide for Mermaid validation and troubleshooting

**Usage**:
```bash
# Windows Batch
tools/workflow_utilities/mermaid_validation/validate_mermaid.bat "diagram.md"

# PowerShell
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/mermaid_validation/validate_mermaid.ps1 -File "diagram.md"
```

### Process Management Tools (`process_management/`)
Windows-specific utilities for managing hanging processes and cleanup:
- **process_monitor.ps1**: Real-time process monitoring and management
- **auto_cleanup.ps1**: Automatic cleanup of common hanging processes
- **emergency_cleanup.ps1**: Force cleanup for critical process hangs
- **manual_cleanup.bat**: Manual process termination script
- **PYTHON_PROCESS_FIX_README.md**: Troubleshooting guide for Python process issues

**Usage**:
```bash
# Monitor processes
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/process_management/process_monitor.ps1

# Emergency cleanup
powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/process_management/emergency_cleanup.ps1
```

## Contributing

When adding new maintenance tools to this directory:

1. Follow the existing naming convention
2. Update this README with the new tool's purpose and usage
3. Ensure proper error handling and logging
4. Test integration with existing tools
5. Update global rules if necessary
