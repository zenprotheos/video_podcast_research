# Proposed URL Input Flow - UML Strategy

## Improved User Interaction Flow

```mermaid
flowchart TD
    A[User opens Bulk Transcribe page] --> B[User sees URL input section]
    B --> C[User types/pastes URLs]

    C --> D{User chooses input method}

    D -->|Types ctrl+enter| E[URLs parsed and validated]
    D -->|Clicks 'Submit URLs' button| E

    E --> F[Column mapping section appears]
    F --> G[User maps columns]
    G --> H[User clicks 'Start session']
    H --> I[Processing begins]

    style D fill:#d4edda
```

## Proposed UI Layout

```mermaid
graph TD
    subgraph "URL Input Section"
        TA[Textarea<br/>st.text_area<br/>placeholder: URLs...]
        BT[Visible Button<br/>st.button<br/>label: 'Submit URLs'<br/>type: primary]
        KB[Optional Keyboard<br/>ctrl+enter<br/>shortcut still works]
    end

    TA --> BT
    TA --> KB
    BT --> P[URL Parsing Logic]
    KB -.-> P

    style BT fill:#d4edda,stroke:#28a745,stroke-width:2px
    style TA fill:#e1f5fe
    style KB fill:#fff3cd,stroke:#856404,stroke-dasharray: 5 5
```

## Benefits of Proposed Design

1. **Visible Action**: Clear button indicates how to proceed
2. **Better UX**: Meets user expectations for interactive elements
3. **Accessibility**: Multiple interaction methods (click + keyboard)
4. **Progressive Enhancement**: Button enhances, doesn't replace keyboard shortcut
5. **Clear Intent**: Button text clearly communicates the action

## Proposed Code Structure

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

    class InputTriggers {
        +on_button_click()
        +on_keyboard_enter()
        +validate_and_proceed()
    }

    StreamlitApp --> InputTriggers : multiple triggers
    InputTriggers --> URLInput : unified processing
    URLInput --> ParsedSheet : creates

    class ParsedSheet {
        +columns: List
        +rows: List
        +row_count: int
    }

    note for InputTriggers : New: Unified trigger handling\nButton + Keyboard shortcuts\nConsistent validation flow
```

## Implementation Strategy

### Layout Options

**Option A: Vertical Stack**
```
[Textarea]
[Submit URLs Button]
```

**Option B: Horizontal Layout**
```
[Textarea] [Button]
```

**Option C: Button Below with Help Text**
```
[Textarea]
[Submit URLs Button]
[Help: or press ctrl+enter]
```

### Recommended Approach: Option A
- Clean, simple layout
- Button clearly associated with textarea
- Maintains existing help text in textarea
- Progressive enhancement (button adds clarity, doesn't replace functionality)

## Event Handling Strategy

```mermaid
stateDiagram-v2
    [*] --> InputSection
    InputSection --> WaitingForInput

    WaitingForInput --> ButtonClicked : User clicks button
    WaitingForInput --> KeyboardEnter : User presses ctrl+enter

    ButtonClicked --> ValidateAndProceed
    KeyboardEnter --> ValidateAndProceed

    ValidateAndProceed --> ShowColumnMapping : Valid URLs
    ValidateAndProceed --> ShowErrors : Invalid URLs
    ShowErrors --> WaitingForInput : User fixes input

    ShowColumnMapping --> [*] : Continue to processing
```

## Error Handling

- **Empty Input**: Show warning, keep button enabled
- **Invalid URLs**: Show validation errors, allow retry
- **Network Issues**: Handle gracefully, show appropriate messages
- **Both Triggers**: Same error handling for button and keyboard input