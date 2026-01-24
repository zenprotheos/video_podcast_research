# System Architecture Overview - Bulk Transcribe Tool

## High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web Interface<br/>pages/1_Bulk_Transcribe.py]
        CONFIG[Configuration Management<br/>API Keys, Settings]
    end

    subgraph "Application Logic Layer"
        CONTROLLER[Bulk Processing Controller<br/>Main Processing Loop]
        VALIDATOR[Input Validator<br/>URL Validation, Deduplication]
        STATUS[Status Manager<br/>Progress Tracking, Counters]
    end

    subgraph "Service Integration Layer"
        YT[YOUTUBE API<br/>Metadata Extraction]
        DEAPI[DEAPI Service<br/>Video Transcription]
        FALLBACK[Fallback Mechanisms<br/>Error Recovery]
    end

    subgraph "Data Layer"
        CACHE[Local Cache<br/>Session State, Results]
        OUTPUT[Output Management<br/>JSON, Text Files]
        LOGS[Logging System<br/>Error Tracking]
    end

    subgraph "External Services"
        YT_API[YouTube Data API v3]
        DEAPI_API[DEAPI Inference API]
    end

    UI --> CONTROLLER
    CONTROLLER --> VALIDATOR
    CONTROLLER --> STATUS
    CONTROLLER --> YT
    CONTROLLER --> DEAPI
    CONTROLLER --> FALLBACK
    YT --> YT_API
    DEAPI --> DEAPI_API
    CONTROLLER --> CACHE
    CONTROLLER --> OUTPUT
    CONTROLLER --> LOGS
    CONFIG --> UI
    CONFIG --> DEAPI
```

## Current Issues Mapping

```mermaid
graph LR
    subgraph "Critical Issues"
        A[NameError: rate_limited_count<br/>Variable not initialized]
        B[False Rate Limit Detection<br/>Incorrect error classification]
        C[Missing Balance Checking<br/>No proactive quota monitoring]
    end

    subgraph "Root Causes"
        D[Session State Incomplete<br/>Missing counter variables]
        E[String Matching Logic<br/>Overly broad error detection]
        F[No API Status Endpoints<br/>Reactive instead of proactive]
    end

    subgraph "Impact Areas"
        G[Application Startup<br/>Complete failure]
        H[User Experience<br/>Misleading error messages]
        I[API Usage<br/>Inefficient resource usage]
    end

    A --> D
    B --> E
    C --> F
    D --> G
    E --> H
    F --> I
```

## Data Flow Diagram

```mermaid
flowchart TD
    START([User Uploads CSV/URLs]) --> VALIDATE{Validate Input}
    VALIDATE -->|Valid| PROCESS[Process Each Video]
    VALIDATE -->|Invalid| ERROR1[Show Validation Errors]

    PROCESS --> EXTRACT[Extract YouTube Metadata]
    EXTRACT --> ATTEMPT1{YouTube Captions<br/>Available?}

    ATTEMPT1 -->|Yes| SUCCESS1[Success Counter +1<br/>Save Transcript]
    ATTEMPT1 -->|No| ATTEMPT2[Try DEAPI Transcription]

    ATTEMPT2 --> DEAPI_CHECK{Check API Balance<br/>Rate Limits?}
    DEAPI_CHECK -->|Rate Limited| RATE_LIMIT[Rate Limit Counter +1<br/>Mark as Retryable]
    DEAPI_CHECK -->|Credits OK| DEAPI_CALL[Call DEAPI API]

    DEAPI_CALL --> POLL_STATUS[Poll for Completion]
    POLL_STATUS --> RESULT{Result Status}

    RESULT -->|Success| SUCCESS2[Success Counter +1<br/>Save Transcript]
    RESULT -->|Error| ERROR_ANALYZE[Analyze Error Type]

    ERROR_ANALYZE -->|Rate Limit| RATE_LIMIT
    ERROR_ANALYZE -->|Other Error| FAILED[Failed Counter +1<br/>Mark as Permanent]

    SUCCESS1 --> NEXT{Next Video?}
    SUCCESS2 --> NEXT
    RATE_LIMIT --> NEXT
    FAILED --> NEXT

    NEXT -->|Yes| PROCESS
    NEXT -->|No| REPORT[Generate Final Report]

    REPORT --> DISPLAY[Display Results to User<br/>Show Counters & Recommendations]

    ERROR1 --> DISPLAY
```

## Error Handling Flow

```mermaid
stateDiagram-v2
    [*] --> ProcessingVideo

    ProcessingVideo --> YouTubeCaptions : Try YouTube first
    YouTubeCaptions --> Success : Captions found
    YouTubeCaptions --> DEAPITranscription : No captions

    DEAPITranscription --> CheckBalance : Before API call
    CheckBalance --> RateLimited : Insufficient credits
    CheckBalance --> APICall : Credits available

    APICall --> Polling : Request submitted
    Polling --> Success : Transcription complete
    Polling --> APIError : Request failed

    APIError --> AnalyzeError : Parse error response
    AnalyzeError --> RateLimited : 429/Rate limit error
    AnalyzeError --> InsufficientCredits : 402/Payment required
    AnalyzeError --> NetworkError : Connection/server error
    AnalyzeError --> OtherError : Unknown error type

    RateLimited --> RetryableFailure
    InsufficientCredits --> PermanentFailure
    NetworkError --> RetryableFailure
    OtherError --> PermanentFailure

    Success --> [*]
    RetryableFailure --> [*]
    PermanentFailure --> [*]
```

## Counter Management Issues

```mermaid
classDiagram
    class SessionState {
        +is_running: bool
        +should_stop: bool
        +processed_count: int
        +success_count: int
        +failed_count: int
        -rate_limited_count: int  // MISSING!
        +status_history: List
    }

    class CounterLogic {
        +increment_success()
        +increment_failed()
        +increment_rate_limited()  // NOT IMPLEMENTED!
        +get_totals()
    }

    class ErrorDetector {
        +detect_rate_limit(error_msg): bool
        +categorize_error(error_msg): ErrorType
    }

    class DisplayManager {
        +show_counters()
        +show_recommendations()
        +generate_report()
    }

    SessionState --> CounterLogic
    CounterLogic --> ErrorDetector
    DisplayManager --> SessionState

    note for rate_limited_count "Variable exists in UI code\nbut never initialized or incremented"
    note for increment_rate_limited "Method exists conceptually\nbut not implemented in code"
```

## DEAPI Integration Issues

```mermaid
sequenceDiagram
    participant UI as Bulk Transcribe UI
    participant DEAPI as DEAPI Service
    participant Balance as Balance Checker
    participant Status as Status Poller

    Note over UI,Status: Current Issues:
    UI->>DEAPI: Submit transcription request
    DEAPI-->>UI: Request ID

    UI->>Status: Poll for completion
    Status-->>UI: Status response

    Note over UI: No balance checking before requests

    UI->>UI: Parse error messages with string matching
    Note over UI: "rate limit" or "429" detection is unreliable

    Note over Balance: Balance checking not implemented
    Note over Status: No proactive rate limit monitoring
```