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

# Windows command execution (WSL-first)

## Current rules
- Primary shell is WSL (bash).
- File operations use MCP tools (no shell-based file edits/copy/move/delete).
- Any command needing variables/loops/JSON parsing/network calls runs as a script file (prefer `.py`, otherwise `.sh`).
- PowerShell is used only for Windows-only utilities (for example, running existing `.ps1` scripts).
- Temp scripts must print a sentinel before exit: `[[COMPLETED:<code>]]`.

## Current patterns

### File operations (MCP)
```bash
delete_file(target_file="path/to/file")
list_dir(target_directory="path/to/dir")
grep(pattern="pattern", path="path/to/file_or_dir")
```

### Windows-only scripts from WSL
```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "tools/workflow_utilities/date-current.ps1" timestamp
```
