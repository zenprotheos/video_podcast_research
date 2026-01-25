# AGENT.md

## Purpose
This document defines repository-specific verification and reporting conventions for Claude Code.
Core operating rules are defined in `.cursor\rules\00-core.mdc` and are authoritative for this repository.

---

## Core Operating Framework

**Primary Rules Source:** `.cursor\rules\00-core.mdc`

All work MUST follow these core rules:
- Task-centric organization: meaningful work belongs to task workspaces under `tasks\`
- No ad-hoc work in repo root
- Specs in `docs\specs\` are the source of truth
- Never use emojis in code
- Python development guardrails: syntax validation, indentation checks, import standards

**Key Required Paths (repo-root relative):**
- Tasks root: `tasks\`
- Specs: `docs\specs\`
- Standards: `docs/standards/`
- Task resume: `docs/task_resume/`

**Standard Task Structure:**
- `INDEX.md`
- `progress_tracker_${TaskName}.md`
- `specs_impact_assessment.md`
- `tests\` (unit/e2e)
- `temp\`
- `artifacts\`

---

## Repository-Specific Conventions

These conventions supplement the core rules with repo-specific expectations.

### Verification After Modifications

After any `Write`, `Edit`, or filesystem operation:
- Run `git status`
- Report which files changed

### Communication Contract

When finishing a task, always report:
1. Tools used
2. Files modified (if any)
3. Whether changes are staged or unstaged

### Accountability Standard

- Claims of completed work must correspond to actual tool execution
- Reasoning alone does not count as completed work
- If no repository-modifying tool was used, explicitly state: **"No files were modified."**

### Failure Handling

- If a change cannot be applied due to permissions, missing files, uncertainty, or errors:
    - Stop execution
    - Explain the blocker clearly
    - Do not simulate or claim success
- If a plan was produced but no tools were executed:
    - Treat the task as **not completed**

---

## Session Rules

- This file and `.cursor\rules\00-core.mdc` are authoritative for agent behavior in this repository.
- Changes to AGENT.md require restarting the Claude Code session to take effect.
- Changes to 00-core.mdc apply immediately upon reload.
