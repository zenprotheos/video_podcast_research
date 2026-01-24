---
title: "README"
created: "2025-09-23T04:36:49.600Z"
type: "guide"
purpose: "Essential project documentation providing comprehensive information about system capabilities, setup instructions, usage guidelines, and important considerations for effective implementation and operation of the VoiceScribeAI application."
status: "Active"
tags: ["voicescribeai"]
---




# Mermaid Diagram Validation Tool

This tool validates Mermaid diagrams in markdown files against the syntax rules documented in `.cursor/rules/mermaid-rule.mdc`.

## Purpose

Automatically detect common Mermaid syntax errors before they cause diagram rendering failures, saving time and reducing frustration during documentation creation.

## Features

- **Comprehensive Validation**: Checks for all documented syntax errors
- **Flexible Scanning**: Works on single directories or entire project trees
- **Clear Reporting**: Detailed error messages with line numbers and fixes
- **Severity Levels**: Distinguishes between errors and warnings
- **Fast Execution**: Efficient pattern matching for large codebases

## Usage

### Basic Usage
```powershell
# Validate current directory
.\validate_mermaid.ps1

# Validate specific directory
.\validate_mermaid.ps1 -Path "tasks/my_task"

# Validate recursively
.\validate_mermaid.ps1 -Path "." -Recurse
```

### PowerShell Examples
```powershell
# Validate a task workspace
.\validate_mermaid.ps1 -Path "tasks/2025-08-25_MyTask"

# Validate entire project
.\validate_mermaid.ps1 -Path "." -Recurse

# Validate specific subdirectory
.\validate_mermaid.ps1 -Path "docs/architecture" -Recurse
```

## What It Checks

Based on `.cursor/rules/mermaid-rule.mdc`:

### 🚨 Critical Errors (Must Fix)
- HTML tags in node labels (`<br/>`, `<b>`, `<i>`)
- Nested quotes in labels
- Unquoted special characters
- Diamond shape syntax errors (nested braces, unclosed diamonds)

### ⚠️ Warnings (Should Fix)
- Horizontal orientation (`graph LR`) in vertical documents
- Complex class diagram syntax
- Suboptimal patterns

## Output Format

```
Mermaid Diagram Validation
==========================
Scanning: tasks/my_task
Recursive: False

Checking: tasks/my_task/architecture.md
[Error] tasks/my_task/architecture.md:15
  Pattern: <br/>
  Issue: HTML <br/> tags found - replace with | for line breaks
  Line: AR[AgentRunner<br/>4 modules]

[Warning] tasks/my_task/architecture.md:23
  Pattern: graph LR
  Issue: Horizontal orientation (LR) found - use TD for vertical docs
  Line: graph LR

Validation Summary
==================
Files checked: 5
Files with issues: 2

❌ Issues found. Please fix the reported syntax errors.
Reference: .cursor/rules/mermaid-rule.mdc for detailed rules.
```

## Integration with Workflow

### Pre-Commit Hook
Add to your git hooks to catch errors before committing:

```bash
# .git/hooks/pre-commit
#!/bin/bash
powershell.exe -ExecutionPolicy Bypass -File tools/mermaid_validation/validate_mermaid.ps1 -Path "." -Recurse
if [ $? -ne 0 ]; then
    echo "Mermaid validation failed. Please fix syntax errors."
    exit 1
fi
```

### CI/CD Integration
```yaml
# .github/workflows/validate.yml
- name: Validate Mermaid Diagrams
  run: powershell.exe -ExecutionPolicy Bypass -File tools/mermaid_validation/validate_mermaid.ps1 -Path "." -Recurse
```

### Task Workspace Validation
```powershell
# In your coding task workflow
.\validate_mermaid.ps1 -Path "tasks/current_task"
```

## Error Reference

| Error Pattern | Fix |
|---------------|-----|
| `<br/>` | Replace with `\|` |
| `graph LR` | Use `graph TD` |
| `A[File/Path]` | Use `A["File/Path"]` |
| Nested quotes | Remove inner quotes |
| Complex class syntax | Use `--> label` |
| `{Check {nested} braces}` | `{Check nested braces}` |
| `{Unclosed diamond` | `{Unclosed diamond}` |

## File Detection

The tool automatically detects Mermaid diagrams by looking for:
- ````mermaid` code blocks
- `graph TD/LR` declarations
- `flowchart TD/LR` declarations

Only processes markdown files (`.md` extension) containing these patterns.

## Performance

- **Fast**: Uses efficient regex pattern matching
- **Memory Efficient**: Processes files line-by-line
- **Scalable**: Handles large codebases with thousands of files

## Troubleshooting

### No Files Found
- Ensure you're in the correct directory
- Check that markdown files exist with `.md` extension
- Verify Mermaid diagrams are present in the files

### False Positives
- Some complex diagram syntax might trigger warnings
- Review the specific error before fixing
- Check `.cursor/rules/mermaid-rule.mdc` for latest rules

### Permission Errors
- Run PowerShell as administrator if needed
- Ensure read access to target directories
- Check file permissions on markdown files

## Contributing

When new Mermaid syntax errors are discovered:
1. Document the error pattern in `.cursor/rules/mermaid-rule.mdc`
2. Add the pattern to this validation script
3. Test with known good/bad examples
4. Update this README with the new error type

## Related Files

- `.cursor/rules/mermaid-rule.mdc` - Complete syntax rules
- `snippets/progress_tracker_template.md` - Diagram creation workflow
- `.cursor/rules/coding-tasks.mdc` - Overall task execution rules


