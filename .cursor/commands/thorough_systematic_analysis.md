---
title: "Thorough Systematic Analysis Command"
created: 2025-09-23
updated: 2025-09-23
type: tool
purpose: "Conducts comprehensive analysis of complex problems using systematic questioning, element mapping, and strategic solution planning to maximize success rates and eliminate errors."
status: Active
tags: ["cursor-command", "analysis", "problem-solving", "systematic-approach"]
---

GOAL: Execute thorough systematic analysis of any complex problem requiring optimal, secure, and reliable solutions through comprehensive questioning, element mapping, and strategic solution planning, extending task UML architecture docs and maintaining docs/specs alignment.

CONTEXT: extends MASTER_Architecture_UMLs_*.md in task directories; maintains docs/specs as source of truth.

RULES: MUST read and extend task UML architecture docs for complete accuracy; MUST reference docs/specs to prevent drift/duplication; MUST analyze all available data to avoid redundancies; MUST identify slight nuances as new information; MUST consider inputs/outputs/mapping across codebase; MUST provide concrete implementation steps; FORBID generic advice without specific evidence; FORBID solutions without verification; FORBID template-only outputs.

TASKS:
1) Read task UML architecture doc and docs/specs source of truth for contextual awareness
2) Generate comprehensive questions covering security, reliability, performance, and implementation concerns
3) Answer all questions inline using available data, codebase knowledge, UML docs, and safe assumptions
4) Identify all related elements: files, functions, variables, data flows, dependencies, and touch points
5) Map inputs/outputs and data transformations across the entire codebase with UML validation
6) Assess risks, failure points, and error scenarios for each identified element against UML specs
7) Design systematic testing strategy with unit tests, integration tests, and debug logging
8) Create iterative implementation plan with rollback mechanisms and validation checkpoints
9) Extend UML architecture doc with implementation details and update success criteria

OUTPUT CONTRACT:
1) Complete question-answer matrix covering all critical considerations with inline evidence-based responses
2) Comprehensive element inventory with file paths, function signatures, and dependency relationships
3) Input/output mapping diagram showing data flow across all affected components
4) Risk assessment report identifying failure points and mitigation strategies
5) Systematic testing plan with specific test cases and validation criteria
6) Step-by-step implementation roadmap with checkpoint requirements
7) Error handling specifications with logging levels and recovery procedures
8) Extended UML architecture documentation with implementation details and updated success criteria
9) docs/specs alignment verification report preventing drift and duplication

NEXT STEPS: Execute analysis immediately on current task; implement findings through todo_write tool; run frontmatter validation; execute systematic testing; deploy with monitoring.
