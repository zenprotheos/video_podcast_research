# Current URL Input Flow - UML Strategy

## Current User Interaction Flow

```mermaid
flowchart TD
    A[User opens Bulk Transcribe page] --> B[User sees URL input textarea]
    B --> C[User types/pastes URLs]
    C --> D{User presses ctrl+enter?}

    D -->|No| C
    D -->|Yes| E[URLs parsed and validated]
    E --> F[Column mapping section appears]
    F --> G[User maps columns]
    G --> H[User clicks 'Start session']
    H --> I[Processing begins]

    style D fill:#ffcccc
```

## Current UI Layout

```mermaid
graph TD
    subgraph "URL Input Section"
        TA[Textarea<br/>st.text_area<br/>placeholder: URLs...]
        KB[Invisible Trigger<br/>ctrl+enter<br/>keyboard shortcut]
    end

    TA --> KB
    KB -.->|"Triggers parsing"| P[URL Parsing Logic]

    style KB fill:#ffcccc,stroke:#ff0000,stroke-width:2px
    style TA fill:#e1f5fe
```

## Problems with Current Design

1. **Hidden Functionality**: ctrl+enter is not visually indicated
2. **Poor Discoverability**: Users may not know how to submit
3. **Accessibility Issues**: Keyboard-only interaction may not be clear
4. **User Expectations**: Modern UIs typically have visible action buttons

## Current Code Structure

```mermaid
classDiagram
    class StreamlitApp {
        +text_area()
        +button()
        +columns()
    }

    class URLInput {
        +parse_urls()
        +validate_urls()
        +create_parsed_sheet()
    }

    StreamlitApp --> URLInput : triggers
    URLInput --> ParsedSheet : creates

    class ParsedSheet {
        +columns: List
        +rows: List
        +row_count: int
    }

    note for StreamlitApp : Current: Only text_area\nNo visible submit button\nctrl+enter = hidden trigger
```