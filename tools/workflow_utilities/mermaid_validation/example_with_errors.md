---
title: "Example With Errors"
created: "2025-09-23T04:36:49.598Z"
type: "document"
purpose: "This document provides detailed information and guidance for understanding and working with the documented subject matter. It includes comprehensive explanations, examples, and practical instructions to support effective implementation and usage of the described concepts or processes."
status: "Active"
tags: ["voicescribeai"]
---




# Example Markdown with Mermaid Errors

This file contains intentional Mermaid syntax errors to demonstrate the validation tool.

## Working Diagram (No Errors)

```mermaid
graph TD
    A["Start"] --> B["Process"]
    B --> C["End"]
```

## Diagram with HTML Tags (Error)

```mermaid
graph TD
    A[Start<br/>Process] --> B[End<br/>Result]
```

## Diagram with Unquoted Special Characters (Warning)

```mermaid
graph TD
    A[File/Path] --> B[Data/Info]
```

## Diagram with Wrong Orientation (Warning)

```mermaid
graph LR
    A[Left] --> B[Right]
```

## Diagram with Nested Quotes (Error)

```mermaid
graph TD
    A["Start "with quotes" here"] --> B["End "also with quotes" here"]
```

## Complex Class Syntax (Warning)

```mermaid
classDiagram
    A ||--|| B : relationship
```

## Diamond Shape Syntax Error (Error)

```mermaid
graph TD
    A[Start] --> B{Jinja2 Parser Encounters {% include %}}
    B --> C[Resolve Include Path]
```

## Mixed Valid/Invalid Content

Regular markdown content here...

```mermaid
graph TD
    A["Valid<br/>Label"] --> B[Invalid/Path]
```

End of example file.


