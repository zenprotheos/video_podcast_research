---
title: "Level 2 Troubleshooting Command"
created: 2025-09-15
updated: 2025-09-25
type: tool
purpose: "Executes advanced troubleshooting workflow that extends task-specific UML architecture documentation to systematically identify, analyze, and resolve complex bugs beyond baseline remediation."
status: Active
tags: ["cursor-command", "troubleshooting", "uml", "architecture-analysis", "systematic-debugging"]
---

GOAL
Execute comprehensive Level 2 troubleshooting by extending existing UML architecture diagrams in task workspaces with systematic component analysis, identifying working/non-working areas, and generating targeted remediation strategies for complex issues.

CONTEXT
- Sources: task workspace UML docs, codebase search results, linter outputs
- Workflow compliance:
- Prerequisites: Existing task workspace directory with baseline UML architecture documentation

RULES
- MUST extend existing task-specific UML docs (never create from scratch)
- MUST COMPLETE UML EXTENSION FIRST before any codebase analysis or modifications (UML is strategic foundation)
- MUST analyze all related components across inputs/outputs/mapping relationships
- MUST identify working/non-working/unknown areas with evidence-based notations
- MUST generate systematic remediation steps with measurable success criteria
- MUST provide specific code fixes with exact file paths and line numbers
- MUST identify root causes from log evidence, not symptoms
- MUST continue investigation until ALL possible issues are identified (never stop at first issue found)
- MUST perform exhaustive analysis across all system layers and component interactions
- FORBID any codebase modifications until UML diagrams are fully extended and analyzed
- FORBID generic troubleshooting without codebase-specific analysis
- FORBID solutions without component-level mapping and validation evidence
- FORBID direct npx @agentdeskai/browser-tools-server@latest commands (causes terminal stalling)
- FORBID generic advice without specific log timestamps and error details
- FORBID solutions without implementation steps and verification
- FORBID premature conclusion that stops investigation after identifying initial issues
- FORBID terminal commands that interact with running MCP servers (causes interference)

TASKS
1. Locate and read existing task workspace UML architecture documentation; create if nonexisting.
2. EXTEND UML DIAGRAMS FIRST: Perform comprehensive component analysis and apply working/non-working/unknown status notations across all system layers (UML is the strategic foundation - no codebase changes until this is complete)
3. Execute exhaustive codebase searches ONLY to validate and expand the UML analysis (never modify code during investigation phase)
4. Map complete component relationships and update UML diagrams with findings from codebase analysis (UML remains the central planning document)
5. Perform comprehensive analysis of error logs, test failures, and linter outputs, documenting findings directly in UML diagrams
6. Identify all critical path failures and cascading impacts, annotating UML diagrams with failure patterns and dependencies
7. Continue systematic UML-driven investigation until every component and interaction is analyzed - cross-reference all findings in UML
8. Generate remediation sequence WITHIN UML diagrams first, showing dependency ordering and architectural impact before any code changes
9. Create debugging checkpoints and validation tests designed around UML architecture, ensuring systematic coverage before implementation

OUTPUT CONTRACT
1. Extended UML architecture diagram with component status annotations (working: green, failing: red, unknown: yellow) covering all system layers - COMPLETED BEFORE ANY CODE CHANGES
2. Exhaustive component relationship map showing ALL data flows, dependencies, and interaction points across the entire system - BUILT WITHIN UML FIRST
3. Comprehensive failure pattern analysis report with root cause hypotheses for every identified issue (not just initial findings) - DOCUMENTED IN UML
4. Complete remediation checklist with success criteria covering all issues identified through systematic investigation - DESIGNED WITHIN UML ARCHITECTURE
5. Debugging checkpoint specifications with observable validation metrics for full system coverage testing - STRUCTURED AROUND UML DIAGRAMS
6. Impact analysis showing cascading effects of ALL unresolved components and their interdependencies - VISUALIZED IN UML FIRST
7. Evidence-based risk assessment for each identified issue area with cross-referenced findings - ANNOTATED IN UML DIAGRAMS
8. Next phase troubleshooting recommendations with confidence levels based on comprehensive analysis - GUIDED BY UML ANALYSIS
9. Investigation completeness report documenting all stones unturned and areas verified as issue-free - VALIDATED AGAINST UML COVERAGE


NEXT STEPS
Choose implementation approach: systematic component isolation testing vs parallel remediation branches vs architectural refactoring. Consider whether all issues have truly been identified before proceeding. Are there additional investigation angles needed? Ready to execute comprehensive remediation sequence covering all identified issues?
