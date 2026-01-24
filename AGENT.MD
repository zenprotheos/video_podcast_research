# AGENT.md

## Purpose
This document defines authoritative operating rules for Claude Code when working in this repository.  
All claims of work must correspond to real tool execution in the CLI.  
Reasoning alone does not count as completed work.

---

## Claude Code Tool Command Reference (Authoritative)

Claude Code may only claim a task is complete if one or more tools that modify the repository were actually invoked.

### Tool Semantics

| Tool | Purpose | Modifies Repo | Usage Rules |
|---|---|---|---|
| `read` | Load file contents into context | No | Must be used before modifying any existing file. Never assume file contents. |
| `search` | Locate files, symbols, or text | No | Use to discover where changes should occur before editing. |
| `write` | Create or fully overwrite a file | Yes | Use only for new files or intentional full rewrites. Avoid for incremental edits. |
| `update` / `edit` / `patch` | Modify part of an existing file | Yes | Preferred tool for fixes and refactors. Preserve unrelated code. |
| `run` | Execute shell commands | Conditional | Use for tests, builds, git commands, formatters. Does not modify files unless the command does. |
| Filesystem ops (`mkdir`, `mv`, `rm`) | Change file structure | Yes | Must be intentional, explained, and minimal. |

---

## Mandatory Tool Discipline Rules

1. Do not claim files were changed unless a `write`, `update`, or filesystem operation was executed.
2. Prefer `update` over `write` for existing files.
3. If no repository-modifying tool was used, explicitly state:  
   **“No files were modified.”**
4. Always `read` a file before editing it.
5. After any modifying action:
    - Run `git status`
    - Report which files changed

---

## Failure Handling

- If a change cannot be applied due to permissions, missing files, uncertainty, or errors:
    - Stop execution
    - Explain the blocker clearly
    - Do not simulate or claim success
- If a plan was produced but no tools were executed:
    - Treat the task as **not completed**

---

## Verification Expectations

- Keep diffs minimal and focused.
- Avoid unnecessary rewrites.
- Run tests or linters when relevant.
- Update documentation if behavior or interfaces changed.

---

## Communication Contract

When finishing a task, always report:

1. Tools used
2. Files modified (if any)
3. Whether changes are staged or unstaged

---

## Session Rules

- This file is authoritative for agent behavior in this repository.
- Changes to this file require restarting the Claude Code session to take effect.
