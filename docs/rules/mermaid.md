---
title: "Mermaid"
created: "2025-09-23T04:36:49.273Z"
type: "document"
purpose: "This document provides detailed information and guidance for understanding and working with the documented subject matter. It includes comprehensive explanations, examples, and practical instructions to support effective implementation and usage of the described concepts or processes."
status: "Active"
tags: ["voicescribeai"]
---






## 📋 Table of Contents

- [Defaults](#defaults)
- [Sequence Diagrams](#sequence-diagrams)
- [Common Parse Errors & Fixes](#common-parse-errors-fixes)
- [COMMON SYNTAX ERRORS](#common-syntax-errors)
- [Template Snippets](#template-snippets)
- [Update Protocol](#update-protocol)

🤖 **AI TIP: TABLE OF CONTENTS MAINTENANCE**
- **TOC is automatically maintained by: `node tools/workflow_utilities/enhanced-toc-updater.cjs`**
- **For manual updates: Run the workflow orchestrator with: `node tools/workflow_utilities/workflow-orchestrator.cjs`**
- **This TOC was auto-generated and will be updated automatically on structural changes**
- **Update TOC immediately after making structural changes to this document**



# Mermaid Diagrams — Canonical Syntax Rules

## Defaults
- Orientation: `flowchart TD` / `graph TD`.
- Labels: no HTML; use pipes for newlines inside quotes, e.g., `A["Line1|Line2"]`.
- Edges: `-->` (arrow), `--o` (assoc), `--|>` (inherit), `--*` (compose).

## Sequence Diagrams
- Declare participants first.
- Use `Note over` blocks sparingly; keep to ASCII.

## Common Parse Errors & Fixes
- **HTML in label** → remove `<br/>`, use pipes inside quotes.
- **Unescaped parens/brackets** → quote the label: `A["text()"]`.
- **Dangling edges** → ensure both node ids defined once.
- **Conflicting styles** → avoid classDef unless necessary.
- **PowerShell property access** → always use `$_` prefix: `Where-Object { $_.Property }`, not `{ .Property }`.

## COMMON SYNTAX ERRORS
- **Forward slashes in labels** → quote labels containing `/`: `A["/path/"]` not `A[/path/]`.
- **Parentheses in labels** → quote labels containing `(` or `)`: `A["text (note)"]` not `A[text (note)]`.
- **Arrows/symbols in labels** → quote labels containing `→`, `←`, `⇒`: `A["A → B"]` not `A[A → B]`.
- **File paths in labels** → quote labels containing paths: `A["frontend/src/file.tsx"]` not `A[frontend/src/file.tsx]`.
- **Nested brackets in labels** → avoid nested brackets; use quotes: `A["text[id]more"]` not `A[text[id]more]`.
- **Mixed special chars** → quote any label with `/`, `(`, `)`, `[`, `]`, `→`, `←`: `A["/path/[id] (note) → file"]`.

## Template Snippets
- **Flowchart**
  ```mermaid
  flowchart TD
    A["Start"] --> B["Do thing"]
    B --> C{Decision?}
    C -- Yes --> D["Path 1"]
    C -- No  --> E["Path 2"]
  ```
- **Sequence**
  ```mermaid
  sequenceDiagram
    participant U as User
    participant S as System
    U->>S: Action
    S-->>U: Result
  ```

## Update Protocol
- When adding a new error→solution pair, append to this file and bump `mermaid_rule_version`.
