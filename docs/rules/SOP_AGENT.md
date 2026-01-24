---
title: "SOP AGENT"
created: "2025-09-23T04:36:49.275Z"
type: "document"
purpose: "This document provides detailed information and guidance for understanding and working with the documented subject matter. It includes comprehensive explanations, examples, and practical instructions to support effective implementation and usage of the described concepts or processes."
status: "Active"
tags: ["voicescribeai"]
sop_version: "2025-09-23"
---





TITLE: AI DEV AGENT — IDE EXECUTION SOP (≤200 lines)

MISSION
- Ship working code with verifiable tests, diffs, and commits. No completion without proof.

PRINCIPLES
- Respect repo rules and stored instructions; keep edits small, test-backed, and reviewable.
- Interact with the environment (terminal/tests) now; never promise background work.
- Prefer minimal sufficient context from docs; expand only if blocked.
- All references MUST include explicit repo paths.
- **SPECS AS SOURCE OF TRUTH**: Always read docs/specs/INDEX.md first; specs drive all development decisions and must be updated when implementation changes affect architecture, data models, APIs, or user flows.
- **DEVELOPMENT WORKFLOW**: Use `start-smart-simple.bat` for one-click startup (backend + frontend). Reserve `npm run dev` for frontend-only debugging (run from `frontend/` directory). Production builds are handled through deployment processes only - focus on development efficiency during active development.
- Always use Context7 MCP tools for file operations, terminal management, and code analysis when developing with Next.js, React, TypeScript, Flask, Python, and Tailwind CSS.
- Use native Cursor Browser tool for frontend validation: viewing the app, taking screenshots, validating UI visuals, and interactive testing.

PATHS (repo-root relative)
- Indexer: tools/workflow_utilities/global_indexer.cjs
- Orchestrator: tools/workflow_utilities/workflow-orchestrator.cjs
- Date script: tools/workflow_utilities/date-current.ps1
- Main app structure map: docs/MAIN_APP_STRUCTURE.md (regenerate via `node tools/workflow_utilities/generate-main-app-structure.cjs`)
- Docs index: docs/INDEX.md
- Specs index: docs/specs/INDEX.md (MANDATORY READ - source of truth for all development)
- Roadmap: docs/development/development_roadmap_2025.md
- Immediate tasks: docs/development/immediate_development_tasks.md
- Tasks root: tasks/
- Workspace pattern: `tasks/${DATE}_${TaskName}/`
- Standard files (within workspace):
  - INDEX.md
  - `MASTER_Architecture_UMLs_${TaskName}.md`
  - `progress_tracker_${TaskName}.md`
  - `completion-summary_${TaskName}.md`
  - tests/unit_test.py
  - tests/master_end_to_end_test.py
  - `subtasks/NN_name/{INDEX.md,progress_tracker_*.md,tests/}`
  - `temp/{debug_*.log,temp_*.ps1,temp_*.py,scratch_*.md}`
  - modules/{core,api,ui,utils}/ (when needed)

ARCHITECTURE PATHS (hybrid backend/frontend)
- Backend (Flask/Python): /
  - Entry: main.py, routes.py
  - Services: services/
  - Storage: storage/
  - Tests: tests/
- Frontend (Next.js/React): frontend/
  - Entry: frontend/package.json, frontend/src/app/
  - Components: frontend/src/components/
  - Services: frontend/src/services/
  - Tests: frontend/tests/
  - Config: frontend/next.config.js, frontend/tailwind.config.js
- Root (Docs Tooling): / (root package.json for documentation maintenance, NOT app runtime)
  - **DEFAULT WORKFLOW**: Use `start-smart-simple.bat` for development (backend + frontend). For frontend-only debugging: `cd frontend && npm run dev`. Reserve production builds for deployment only.

TASK TYPE (choose ONE)
- BUG FIX → tests-first → minimal repro → fix → tests pass
- DEBUGGING → root cause → instrument → verify
- NEW FEATURE → brief design → implement → tests
- ANALYSIS/CONFIG/REFACTOR → read context → plan → safe change → validate

SEQUENCE (hard requirements)

0) PRECHECKS (paths explicit)
  0.1 Frontmatter Validation (MANDATORY - blocks all development)
    Run: node tools/workflow_utilities/frontmatter_validator.cjs validate .
    Block if any .md files lack proper frontmatter or have invalid content
    Fix all issues immediately - no development until compliant
  0.2 Index
    if missing: node tools/workflow_utilities/global_indexer.cjs generate docs/
    then READ: docs/INDEX.md (full)
  0.3 SPECS VALIDATION (MANDATORY - source of truth)
    READ: docs/specs/INDEX.md (full) - understand current architecture/specs baseline
    Identify relevant spec files from docs/specs/INDEX.md based on task type
    READ: Top 3-5 most relevant spec files (system-architecture.md, data-models.md, api-specifications.md, ui-architecture.md, user-flows.md)
    Block if specs are outdated or conflicting with task requirements
  0.4 Project context (read heads)
    if exists: docs/development/development_roadmap_2025.md (first ~80 lines)
    if exists: docs/development/immediate_development_tasks.md (first ~80 lines)
  0.5 Task-aware doc selection
    - Score docs from docs/INDEX.md (dir/type/status/recency/text-match)
    - Log selected list BEFORE reading bodies (Top-K full; next K skim headings)
    - Validate all selections against specs baseline from step 0.3

1) WORKSPACE (scaffold; explicit pathing)
  - DATE = (PowerShell) `powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 taskFolder`
  - TASK_DIR = `tasks/${DATE}_${TaskName}`
  - Create: `cmd.exe /c "mkdir ${TASK_DIR}\tests && echo [[DONE:mkdir]]"`
  - Generate task index: `node tools/workflow_utilities/global_indexer.cjs generate "${TASK_DIR}"`
  - Validate: `${TASK_DIR}/INDEX.md` exists and not placeholder

2) ARCHITECTURE (only what helps)
  - Create: `${TASK_DIR}/MASTER_Architecture_UMLs_${TaskName}.md`
  - Include: interactions, data flow, deps, plain-language summary -- MERMAID DIAGRAMS (read specs: `docs\rules\mermaid.md`)

2.5) PROGRESS TRACKER
  - Create: `${TASK_DIR}/progress_tracker_${TaskName}.md` (from `snippets/progress_tracker_template.md` if present)

3) TESTS — UNIT/COMPONENT
  - BUG FIX: write failing test first at ${TASK_DIR}/tests/unit_test.py
  - Others: add/adjust covering tests before E2E
  - Run (example):
    - Windows: python "${TASK_DIR}\tests\unit_test.py"
    - POSIX:   python "${TASK_DIR}/tests/unit_test.py"
  - Block if nonzero exit

4) IMPLEMENTATION
  - Edit minimal set of files; keep imports valid; document "reason → edit → effect"
  - Update error messages/types/logs alongside code
  - **SPECS IMPACT ASSESSMENT**: Evaluate if changes affect specs (architecture, data models, APIs, user flows)
  - Document any spec deviations in ${TASK_DIR}/specs_impact_assessment.md
  - Flag any required spec updates for post-implementation phase

5) MASTER E2E
  - Create: ${TASK_DIR}/tests/master_end_to_end_test.py
  - **THEME VALIDATION**: For UI/UX/visual design changes, use native Cursor Browser tools (taking full page screenshots, interactive testing, visual validation) to validate BOTH LIGHT AND DARK THEMES for proper functionality and visual consistency
  - Run until exit code 0

5.5) SPECS UPDATE (MANDATORY if implementation affects specs)
  - Review ${TASK_DIR}/specs_impact_assessment.md
  - Update relevant spec files in docs/specs/ if changes affect:
    - system-architecture.md (architecture changes)
    - data-models.md (data structure changes)
    - api-specifications.md (API contract changes)
    - ui-architecture.md (UI/UX changes)
    - user-flows.md (user interaction changes)
  - Regenerate docs/specs/INDEX.md if any specs were updated
  - Block completion if specs updates are required but not completed

6) FRONTMATTER COMPLIANCE (MANDATORY)
  - Run: node tools/workflow_utilities/frontmatter_validator.cjs validate .
  - Fix any new frontmatter issues introduced during development
  - Block completion if frontmatter compliance fails

7) DOCS MAINTENANCE (explicit path)
  - node tools/workflow_utilities/workflow-orchestrator.cjs --all (includes frontmatter validation, TOC updates, index generation, main app structure regeneration, and terminal cleanup)
  - Block on failure; show logs

8) GIT (explicit)
  - **PRE-COMMIT SPECS VALIDATION**: Verify all required specs updates from step 5.5 are completed
  - Confirm docs/specs/INDEX.md is up-to-date if any specs were modified
  - **PRE-COMMIT FRONTMATTER VALIDATION**: Verify frontmatter compliance from step 6
  - Stage (PowerShell guard):
    $job = Start-Job -ScriptBlock { git add -A }; Wait-Job $job -Timeout 30 | Out-Null; Receive-Job $job; Remove-Job $job
  - Commit:
    [TASK] ${TaskName}: One-line outcome
    Changes: (file paths)
    Specs Impact: (any specs updated - list files)
    Frontmatter: All .md files compliant
    Testing: unit/e2e/integration status
    Generated: (powershell.exe -ExecutionPolicy Bypass -File tools/workflow_utilities/date-current.ps1 iso)
  - Push: git push origin HEAD

9) COMPLETION SUMMARY (explicit paths)
  - Write `${TASK_DIR}/completion-summary_${TaskName}.md`:
    - What done, lessons, alternatives, improvements
    - Specs Impact Assessment: Changes made to specs files and rationale
    - Frontmatter Compliance: Confirmation all .md files have proper frontmatter
    - Categorized clickable file list (Documentation, Tests, Indexes, Artifacts) with full repo paths
    - Evidence summary (see EVIDENCE)
    - **MANDATORY NEXT STEPS**: Include 2-6 concrete next actions with repo paths (see OUTPUT CHECKLIST)
    - **SPECS VALIDATION CONFIRMATION**: Confirm all specs updates are complete and docs/specs/INDEX.md is current
    - **FRONTMATTER VALIDATION CONFIRMATION**: Confirm all .md files have proper frontmatter with 20+ word purposes

9.4) USER REVIEW INITIATION (Per-Task)
  - For the specific completed task entry in `${TASK_DIR}/progress_tracker_${TaskName}.md`:
    - Set per-task review to Ready for Review
    - Generate a User Testing Guide via `.cursor/commands/create_user_testing_guide.md` using:
      - task_workspace_path: `${TASK_DIR}/`
      - completed_features: copy from that entry's "Completed" list
    - Save guide at: `${TASK_DIR}/user-testing/YYYYMMDD-HHMM_UTG_[SubtaskSlug].md` (concise, unique)
    - Link the guide under that task entry and add to Artifacts

10) USER REVIEW & APPROVAL
  - On explicit OK: set per-task review to User Approved (record timestamp)
  - On feedback: revert per-task review to In Progress (no separate "Changes Requested" state)
  - If the user continues without requesting changes: mark the prior Ready for Review item as User Approved (implicit)

EVIDENCE (must show BEFORE “complete”)
- Files exist + non-empty:
  - Windows: `dir ${TASK_DIR}\path && type ${TASK_DIR}\path | more`
  - POSIX:   `ls -la ${TASK_DIR}/path && head -20 ${TASK_DIR}/path`
- Import sanity:
  - python -c "from <module.path> import <Symbol>; print('Import OK')"
- DB models (if any): quick import/query prints
- Tests: show commands + last lines; exit code == 0

DELIVERABLE FORMAT (always output)
- Plan (≤8 bullets)
- Diff/Edits Summary (file → key changes)
- Run Commands (unit, e2e, orchestrator, git) with full paths
- Artifacts (clickable repo paths)
- Evidence block (as above)
- Open Issues / Assumptions

CONTEXT SELECTION (deterministic)
- **MANDATORY SPECS FIRST**: Always read docs/specs/INDEX.md and relevant spec files BEFORE any other documentation
- Use Top-K full reads + K skims from docs/INDEX.md; expand one doc at a time if blocked
- Priority dirs by task:
  - BUG/DEBUG/REFACTOR: specs/, implementation/, development/
  - FEATURE/CONFIG: specs/, development/, product_planning/
  - ANALYSIS: specs/, product_planning/, development/, global_docs/
- Type priority (high→low): specs/system-architecture,data-models,api-specifications,ui-architecture,user-flows → planning → analysis → document → index
- **SPECS VALIDATION**: All context selections must be validated against current specs baseline

TERMINAL / OS SAFETY
- Prefer `cmd.exe /c "mkdir path && echo [[DONE:mkdir]]"` for Windows
- Keep all temp under `${TASK_DIR}/temp/`

SERVICE MANAGEMENT (organized startup)
- **PORT 3000 MANAGEMENT**: Always check if localhost:3000 is active before starting frontend services. If port 3000 is active, assume the app is already launched and use the existing instance instead of creating a new one. Port 3000 is ALWAYS reserved for the app.
- **PRIMARY COMMAND**: Use `start-smart-simple.bat` for one-click startup (backend + frontend with conflict detection)
- **RESTART COMMAND**: Use `restart-services.bat` for seamless service restart (stops all → starts all → opens browser)
- **STOP COMMAND**: Use `stop-services.bat` to gracefully shut down all services
- **FRONTEND-ONLY**: For Next.js debugging, run `cd frontend && npm run dev` (from frontend/ directory only)
- **WINDOWS NOTE**: Direct `npm run dev` may stall due to console buffering - use startup scripts for reliability
- For detailed status: Run `start-smart-simple.bat status`
- Individual control: tools/workflow_utilities/service_manager.ps1 (start-frontend, start-backend, stop-frontend, stop-backend, status, stop-all)
- Organized scripts: tools/workflow_utilities/startup/ (start-backend.bat, start-frontend.bat, stop-services.bat)
- Port conflict detection: Automatic checking of ports 3000 (frontend) and 5000 (backend)
- Use -Force flag to override port conflicts when necessary

SUBTASKS (if needed)
- Create ${TASK_DIR}/subtasks/NN_name/{INDEX.md,progress_tracker_*.md,tests/}
- Each subtask must pass Steps 3→5 before merge back

GOVERNANCE / LIMITS
- If ambiguous, pick safe default; document in "Open Issues"
- Do not proceed if tests or orchestrator fail
- **SPECS COMPLIANCE**: Block if specs are outdated, conflicting, or not updated when required
- **FRONTMATTER COMPLIANCE**: Block if any .md files lack proper frontmatter or have invalid content
- Never mark complete without Steps 3–9 satisfied AND specs/frontmatter validation confirmed
- **SPECS WORKFLOW**: Tasks complete in workspaces → User confirms working → Git commit → Specs validation/update → Source of truth maintained
- **FRONTMATTER WORKFLOW**: All .md files must have proper frontmatter with 20+ word purposes before any development task

OUTPUT CHECKLIST (agent must include verbatim)
- [ ] Task Type selected
- [ ] FRONTMATTER VALIDATION: All .md files have proper frontmatter with 20+ word purposes
- [ ] SPECS READ: docs/specs/INDEX.md and relevant spec files
- [ ] Plan (≤8 bullets)
- [ ] Files to touch (repo paths)
- [ ] New/changed tests (paths)
- [ ] Specs Impact Assessment documented
- [ ] Commands (unit/e2e/orchestrator/git) with full paths
- [ ] Evidence (files/imports/tests)
- [ ] Artifacts (clickable repo paths)
- [ ] Per-task review set: Ready for Review → User Approved if applicable
- [ ] User Testing Guide created at `${TASK_DIR}/user-testing/YYYYMMDD-HHMM_UTG_[SubtaskSlug].md` and linked
- [ ] If user continued without changes, previous item marked User Approved (implicit)
- [ ] SPECS UPDATES: Any required spec file updates completed
- [ ] FRONTMATTER COMPLIANCE: All .md files compliant (confirmed via validator)
- [ ] Open Issues/Assumptions
- [ ] NEXT STEPS PROMPT (MANDATORY):
  - [ ] Display "Outstanding SOP items not completed" (derive from checklist ☑/☐)
  - [ ] Propose 2–6 concrete next actions with repo paths, e.g.:
    - [ ] Finish remaining SOP items for current task (list paths)
    - [ ] Validate and update specs in docs/specs/ if development changes affected architecture/data/APIs
    - [ ] Tackle highest-priority item from docs/development/immediate_development_tasks.md
    - [ ] Advance roadmap milestone from docs/development/development_roadmap_2025.md
    - [ ] Open follow-up refactor/tests hardening in ${TASK_DIR}/subtasks/
    - [ ] Update documentation reflecting changes: subtasks, progress trackers, codebase docs (docs/)
    - [ ] Create resumable session prompt: full instructions + context + file paths + references for new chat
  - [ ] Ask explicitly: "What would you like me to do next?" and wait for selection

AFTER COMPLETION — NEXT STEPS PROMPT REFERENCE
- See OUTPUT CHECKLIST above for detailed requirements
- This section ensures NEXT STEPS are prioritized in the completion workflow
- Always include before marking any task as complete

END OF SOP
