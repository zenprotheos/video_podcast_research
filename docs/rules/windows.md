---
title: "Windows"
created: "2025-09-23T04:36:49.276Z"
type: "document"
purpose: "This document provides detailed information and guidance for understanding and working with the documented subject matter. It includes comprehensive explanations, examples, and practical instructions to support effective implementation and usage of the described concepts or processes."
status: "Active"
tags: ["voicescribeai"]
---




win_rule_version: 2025-09-22
sot: docs/rules/SOP_AGENT.md
---

# 🚀 Windows Command Execution Guide

## ⚡ URGENT: Cursor Stalls?
```bash
# ❌ AVOID: PowerShell commands cause Cursor stalls
# ✅ USE: MCP tools instead
delete_file(target_file="path/to/file")
list_dir(target_directory="path/to/dir")
grep(pattern="search", path="file.txt")
```

## 🎯 Decision Tree
```
Command → File ops? → Use MCP tools (delete_file, list_dir, grep)
         ↓
       Variables/loops? → Use TEMP SCRIPT
         ↓
       Long-running? → Use MCP tools or temp scripts
         ↓
       Unix-style? → Convert to MCP equivalents
         ↓
       Still needed? → Use temp script pattern
```

## ⚡ RECOMMENDED: MCP Tool Patterns

### ✅ File Operations (Use These Instead)
```bash
# Instead of: powershell.exe -Command "Remove-Item -Path 'file.txt'"
delete_file(target_file="file.txt")

# Instead of: powershell.exe -Command "Get-ChildItem -Path 'dir'"
list_dir(target_directory="dir")

# Instead of: powershell.exe -Command "Get-Content -Path 'file.txt' | Select-String 'pattern'"
grep(pattern="pattern", path="file.txt")
```

### 🧪 Network/API Testing (Use Python Scripts)
```python
# Instead of: curl http://localhost:5000/api/status | python -c "..."
# Create temp/network_test.py:
import requests
response = requests.get('http://localhost:5000/api/status')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 🔍 Environment Variable Checking (Use Python Scripts)
```python
# Instead of: powershell.exe -Command "echo $env:VARIABLE"
# Create temp/env_check.py:
import os
print(f"TEST_MODE: {os.environ.get('TEST_MODE')}")
print(f"DEV_FORCE_TEST_MODE: {os.environ.get('DEV_FORCE_TEST_MODE')}")
```

### ✅ Long-Running Processes (Use Python Temp Scripts)
```python
# Create temp Python script for complex operations (more reliable than PowerShell)
temp_script = "temp/operation.py"
with open(temp_script, 'w') as f:
    f.write("""
import requests
import os

print("Starting operation...")
# Your complex logic here
print("[[DONE:operation]]")
""")
# Execute with timeout protection
import subprocess
result = subprocess.run(['python', temp_script], timeout=30)
os.remove(temp_script)
```

### ⚠️ DEPRECATED: PowerShell Inline Commands
**These patterns cause Cursor stalls - use MCP tools or temp scripts instead**

```bash
# ❌ STALLS: powershell.exe -Command "Get-Date"
# ✅ WORKS: Use temp script or MCP equivalent

# ❌ STALLS: powershell.exe -Command "& { python -c 'print(1)' }"
# ✅ WORKS: Create temp .py file and execute

# ❌ STALLS: powershell.exe -Command "& { npm run build }"
# ❌ NEVER USE: npm run build during development - use npm run dev instead
# ✅ WORKS: Use temp script with proper error handling
```

## 🔧 Troubleshooting

### **If Still Stalls:**
1. **FIRST**: Switch to MCP tools for file operations
2. **SECOND**: Use temp scripts for complex operations
3. **THIRD**: Add sentinels and MCP buffer reset only as last resort

### **Common Fixes:**
- **File operations** → Use MCP tools: `delete_file`, `list_dir`, `grep`
- **Complex commands** → Use temp `.ps1` files in `temp\` directory
- **Variable interpolation** → Move to temp scripts
- **Long commands** → Break into temp scripts with proper error handling

## ✅ WORKING PATTERNS (Use These)

### ✅ MCP File Operations (RECOMMENDED)
```bash
# These work reliably without stalls:
delete_file(target_file="frontend/src/pages/topics")
list_dir(target_directory="frontend/src/app")
grep(pattern="import.*React", path="src/components")

# For directory creation/checking:
# Use MCP tools to check first, then create via temp script if needed
```

### ✅ Temp Script Pattern (For Complex Operations)
```powershell
# ALWAYS use temp scripts for any complex operations
$tempScript = "temp\cleanup_topics.ps1"
@"
# Complex logic here - no Cursor stalls
if (Test-Path 'frontend/src/pages/topics') {
    Remove-Item -Path 'frontend/src/pages/topics' -Recurse -Force
    Write-Host 'Old topics directory removed'
} else {
    Write-Host 'Old topics directory already removed'
}
Write-Host '[[DONE:cleanup-old-topics]]'
"@ | Set-Content -Path $tempScript
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempScript
Remove-Item $tempScript -Force
```

### ✅ MCP Buffer Reset (When Needed)
```bash
# Use this sparingly - prefer MCP tools over PowerShell
grep pattern="version" path="package.json" output_mode="content" head_limit="1"
```

## ⚠️ DEPRECATED PATTERNS (Cause Stalls)

## ❌ AVOID These Patterns (Cause Cursor Stalls)
- **Complex PowerShell inline commands**: `powershell.exe -Command "try { ... } catch { ... }"`
- Script blocks with variables: `& { $var = Get-Date; Write-Host $var }` ❌ STALLS
- Multiple statements with variables: `$a = 1; $b = 2; Write-Host "$a + $b"` ❌ STALLS
- Network operations: `Invoke-WebRequest` in inline commands ❌ STALLS
- External processes: `npx`, `python` calls in inline commands ❌ STALLS
- Complex escaping: nested quotes/semicolons in -Command parameter ❌ STALLS
- **PIPED COMMANDS**: `curl ... | python -c "..."` (causes parsing stalls)
- **JSON PARSING**: `| ConvertFrom-Json` in inline commands ❌ STALLS
- **Environment Variables**: `$env:VARIABLE` in inline commands ❌ STALLS
- **PowerShell temp scripts**: Even `.ps1` files with network operations stall ❌ STALLS

## ✅ WORKING PATTERNS (Updated 2025-09-22)
- **Simple PowerShell**: `powershell.exe -Command "Get-Date"` ✅ WORKS
- **Multiple simple statements**: `Write-Host 'test'; Get-Location` ✅ WORKS
- **MCP tools**: `list_dir`, `read_file`, `grep`, `delete_file` ✅ WORKS
- **Echo commands**: `echo "message"` ✅ WORKS
- **Python temp scripts**: `.py` files for complex operations ✅ WORKS

## ✅ RECOMMENDED: Core Practices
- **File operations**: Use MCP tools (`delete_file`, `list_dir`, `grep`)
- **Complex operations**: Use temp scripts in `temp\` directory
- **Buffer reset**: Use MCP tools like `grep` for buffer state reset
- **Temp files**: Create in `temp\` folder, always cleanup after use
- **Timeouts**: Default 30s for simple ops, use temp scripts for longer operations

## ✅ Post-Run Checklist
* MCP tools used for file operations • Temp scripts created in `temp\` • Temp files removed • No PowerShell inline commands used

---

## 📋 Table of Contents

- [⚡ URGENT: Cursor Stalls?](#-urgent-cursor-stalls)
- [🎯 Decision Tree](#-decision-tree)
- [⚡ RECOMMENDED: MCP Tool Patterns](#-recommended-mcp-tool-patterns)
  - [✅ File Operations (Use These Instead)](#-file-operations-use-these-instead)
  - [🧪 Network/API Testing (Use Python Scripts)](#-networkapi-testing-use-python-scripts)
  - [🔍 Environment Variable Checking (Use Python Scripts)](#-environment-variable-checking-use-python-scripts)
  - [✅ Long-Running Processes (Use Python Temp Scripts)](#-long-running-processes-use-python-temp-scripts)
  - [⚠️ DEPRECATED: PowerShell Inline Commands](#-deprecated-powershell-inline-commands)
- [🔧 Troubleshooting](#-troubleshooting)
  - [**If Still Stalls:**](#if-still-stalls)
  - [**Common Fixes:**](#common-fixes)
- [✅ WORKING PATTERNS (Use These)](#-working-patterns-use-these)
  - [✅ MCP File Operations (RECOMMENDED)](#-mcp-file-operations-recommended)
  - [✅ Temp Script Pattern (For Complex Operations)](#-temp-script-pattern-for-complex-operations)
  - [✅ MCP Buffer Reset (When Needed)](#-mcp-buffer-reset-when-needed)
- [⚠️ DEPRECATED PATTERNS (Cause Stalls)](#-deprecated-patterns-cause-stalls)
- [❌ AVOID These Patterns (Cause Cursor Stalls)](#-avoid-these-patterns-cause-cursor-stalls)
- [✅ WORKING PATTERNS (Updated 2025-09-22)](#-working-patterns-updated-2025-09-22)
- [✅ RECOMMENDED: Core Practices](#-recommended-core-practices)
- [✅ Post-Run Checklist](#-post-run-checklist)
- [📚 LESSON LEARNED: Cursor Command Stall Analysis (2025-09-22)](#-lesson-learned-cursor-command-stall-analysis-2025-09-22)
  - [Testing Results: Command Structure Impact on Stalls](#testing-results-command-structure-impact-on-stalls)
  - [Updated Command Complexity Decision Tree:](#updated-command-complexity-decision-tree)
  - [Recent Issue: TEST_MODE Configuration Drift Debug (2025-09-17)](#recent-issue-test_mode-configuration-drift-debug-2025-09-17)
  - [What Failed:](#what-failed)
  - [What Worked:](#what-worked)
  - [Prevention Strategy:](#prevention-strategy)
  - [Command Complexity Decision Tree:](#command-complexity-decision-tree)
  - [🚨 Command Failure Recovery:](#-command-failure-recovery)
  - [📋 Pre-Command Assessment Checklist](#-pre-command-assessment-checklist)
- [📋 QUICK REFERENCE](#-quick-reference)
  - [For File Operations:](#for-file-operations)
  - [For Complex Operations:](#for-complex-operations)
  - [For Buffer Reset:](#for-buffer-reset)

🤖 **AI TIP: TABLE OF CONTENTS MAINTENANCE**
- **TOC is automatically maintained by: `node tools/workflow_utilities/enhanced-toc-updater.cjs`**
- **For manual updates: Run the workflow orchestrator with: `node tools/workflow_utilities/workflow-orchestrator.cjs`**
- **This TOC was auto-generated and will be updated automatically on structural changes**
- **Update TOC immediately after making structural changes to this document**


## 📚 LESSON LEARNED: Cursor Command Stall Analysis (2025-09-22)

### Testing Results: Command Structure Impact on Stalls

**Testing performed on the original failing command:**
```powershell
powershell.exe -ExecutionPolicy Bypass -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:9222/json/version' -TimeoutSec 5; Write-Host 'MCP server running: YES'; $response.Content } catch { Write-Host 'MCP server running: NO'; Write-Host 'Starting MCP server...'; npx @agentdeskai/browser-tools-server@latest }"
```

**Results:**
- ❌ **STALLS**: Complex PowerShell with variables, network calls, and external processes
- ❌ **STALLS**: Even temp script execution with network operations stalls
- ✅ **WORKS**: Simple PowerShell commands: `Get-Date`, `Write-Host 'test'`
- ✅ **WORKS**: Multiple statements without variables: `Write-Host 'test'; Get-Location`
- ✅ **WORKS**: MCP tools: `list_dir`, `read_file`, `grep`, `delete_file`
- ✅ **WORKS**: Simple echo commands: `echo "message"`

### Updated Command Complexity Decision Tree:
```
Need to run a command?
├── File operation? → Use MCP tools (list_dir, grep, read_file) ✅ WORKS
├── Network/API call? → Use temp .py script (not temp .ps1) ❌ STALLS
├── Environment check? → Use Python script in temp/ ✅ WORKS
├── Simple output? → Use echo or simple PowerShell ✅ WORKS
├── Complex logic? → Use temp .py script (avoid temp .ps1) ❌ STALLS
├── Multiple simple statements? → Use PowerShell without variables ✅ WORKS
└── Still complex? → Use MCP tools or Python temp scripts ✅ WORKS
```

### Recent Issue: TEST_MODE Configuration Drift Debug (2025-09-17)
- **Problem:** PowerShell inline commands caused Cursor stalls during backend status checking
- **Root Cause:** Complex command structure with JSON parsing and variable interpolation
- **Impact:** Commands would hang, requiring manual Ctrl+Enter intervention

### What Failed:
```bash
# ❌ These caused stalls:
curl http://localhost:5000/api/system/status | python -c "import json, sys; print(json.load(sys.stdin))"
powershell.exe -Command "& { $env:VARIABLE; Get-Date }"
```

### What Worked:
```powershell
# ✅ Temp script pattern:
$tempScript = "temp/check_backend_status.ps1"
@"
# Clean PowerShell logic
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/system/status"
    $data = $response.Content | ConvertFrom-Json
    Write-Host "test_mode: $($data.test_mode)"
} catch {
    Write-Host "Backend not accessible: $($_.Exception.Message)"
}
"@ | Set-Content -Path $tempScript
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempScript
Remove-Item $tempScript -Force
```

### Prevention Strategy:
1. **Assess Complexity First:** Use decision tree before writing any command
2. **Use Approved Patterns:** Reference this guide's recommended patterns
3. **Test Incrementally:** Start with simple commands, build complexity gradually
4. **Have Fallbacks:** Know MCP tool alternatives for each operation type

### Command Complexity Decision Tree:
```
Need to run a command?
├── File operation? → Use MCP tools (list_dir, grep, read_file)
├── Network/API call? → Use Python script in temp/
├── Environment check? → Use Python script in temp/
├── Complex logic? → Use temp .ps1 or .py script
├── Multiple steps? → Break into temp script
└── Still complex? → Reassess - is this really needed?
```

### 🚨 Command Failure Recovery:
**If Command Stalls:**
1. **IMMEDIATE:** Press Ctrl+Enter to recover Cursor
2. **PREVENTION:** Switch to temp script pattern immediately
3. **FALLBACK:** Use MCP tools for file operations
4. **DEBUG:** Check this guide for approved patterns

**Remember:** Any PowerShell inline command with variables, pipes, or complex logic WILL cause stalls. Use temp scripts instead.

### 📋 Pre-Command Assessment Checklist
**Use this BEFORE running ANY command:**

- [ ] **File Operation?** → Use MCP tools (`list_dir`, `grep`, `read_file`)
- [ ] **Network/API Call?** → Use Python script in `temp/`
- [ ] **Environment Check?** → Use Python script in `temp/`
- [ ] **Contains Variables?** → Use temp script
- [ ] **Contains Pipes?** → Use temp script (e.g., `| python -c`)
- [ ] **JSON Parsing?** → Use temp script
- [ ] **Multiple Steps?** → Break into temp script
- [ ] **Longer than 30s?** → Use temp script
- [ ] **Still unsure?** → Default to temp script pattern

**If ANY box is checked → Use temp script, NOT inline command**

---

## 📋 QUICK REFERENCE

### For File Operations:
```bash
# ✅ GOOD: Use MCP tools
delete_file(target_file="path/to/file")
list_dir(target_directory="path/to/dir")
grep(pattern="search", path="file")
```

### For Complex Operations:
```powershell
# ✅ GOOD: Use temp scripts
$tempScript = "temp\your_operation.ps1"
@"
# Your complex PowerShell code here
Write-Host "[[DONE:operation]]"
"@ | Set-Content -Path $tempScript
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempScript
Remove-Item $tempScript -Force
```

### For Buffer Reset:
```bash
# ✅ GOOD: Use MCP tools
grep pattern="version" path="package.json" output_mode="content" head_limit="1"
```
