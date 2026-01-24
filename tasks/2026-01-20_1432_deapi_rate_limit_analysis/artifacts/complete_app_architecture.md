# Complete App Architecture - Bulk Transcribe Tool

## System Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web App<br/>pages/1_Bulk_Transcribe.py]
        SIDEBAR[Sidebar Config<br/>API Keys, Balance Display]
        PROGRESS[Progress Table<br/>Real-time Status Updates]
        LOGS[Session Logs<br/>Comprehensive Error Details]
    end

    subgraph "Application Logic Layer"
        CONTROLLER[Bulk Controller<br/>Main Processing Loop]
        VALIDATOR[Input Validator<br/>URL & Data Validation]
        SESSION[Session Manager<br/>State Persistence]
        ERROR_HANDLER[Error Handler<br/>Categorization & Display]
    end

    subgraph "Service Integration Layer"
        YT_SERVICE[YouTube Service<br/>Metadata & Captions]
        DEAPI_SERVICE[DEAPI Service<br/>AI Transcription]
        FALLBACK[Error Recovery<br/>Retry Logic & Fallbacks]
    end

    subgraph "Data Processing Layer"
        TRANSCRIPT_EXTRACTOR[Transcript Extractor<br/>src/bulk_transcribe/youtube_transcript.py]
        RESULT_PROCESSOR[Result Processor<br/>Success/Failure Handling]
        STATUS_TRACKER[Status Tracker<br/>Progress Counters]
    end

    subgraph "Data Storage Layer"
        SESSION_STATE[Session State<br/>In-Memory State]
        OUTPUT_FILES[Output Files<br/>JSON, Markdown, Logs]
        CACHE[Response Cache<br/>Temporary Data]
    end

    subgraph "External APIs"
        YOUTUBE_API[YouTube Data API v3]
        DEAPI_API[DEAPI Inference API<br/>https://api.deapi.ai]
    end

    UI --> CONTROLLER
    CONTROLLER --> VALIDATOR
    CONTROLLER --> SESSION
    CONTROLLER --> YT_SERVICE
    CONTROLLER --> DEAPI_SERVICE
    CONTROLLER --> ERROR_HANDLER
    YT_SERVICE --> YOUTUBE_API
    DEAPI_SERVICE --> DEAPI_API
    CONTROLLER --> TRANSCRIPT_EXTRACTOR
    TRANSCRIPT_EXTRACTOR --> RESULT_PROCESSOR
    RESULT_PROCESSOR --> STATUS_TRACKER
    CONTROLLER --> SESSION_STATE
    CONTROLLER --> OUTPUT_FILES
    CONTROLLER --> CACHE
    PROGRESS --> CONTROLLER
    LOGS --> CONTROLLER
    SIDEBAR --> CONTROLLER
```

## Error Message Flow Analysis

```mermaid
flowchart TD
    A[DEAPI API Call] --> B{HTTP Response}
    B -->|Success 200| C[Process Transcript]
    B -->|Error 4xx/5xx| D[Capture Raw Response]

    D --> E[Store in TranscriptResult]
    E --> F[Return to Controller]

    F --> G[Error Handler Processes]
    G --> H{Current Behavior<br/>Categorize Only}
    G --> I{Desired Behavior<br/>Show Raw + Categorized}

    H --> J[Display Categorized Message<br/>❌ "Rate limited"]
    I --> K[Display Raw Server Response<br/>✅ {"error": "RESOURCE_EXHAUSTED"}]

    J --> L[Progress Table]
    J --> M[Session Logs]
    J --> N[Sidebar Balance]
    J --> O[Console Output]

    K --> L
    K --> M
    K --> N
    K --> O
```

## Data Flow: Error Messages Through System

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Controller as Bulk Controller
    participant Extractor as Transcript Extractor
    participant DEAPI as DEAPI API
    participant Processor as Result Processor
    participant Display as Progress Display
    participant Logs as Session Logs

    User->>UI: Start transcription
    UI->>Controller: Process videos

    loop For each video
        Controller->>Extractor: get_youtube_transcript()
        Extractor->>DEAPI: API request
        DEAPI-->>Extractor: Error response (429)
    end

    Note over Extractor: Captures raw response:<br/>{"error": "RESOURCE_EXHAUSTED",<br/>"message": "Rate limit exceeded"}

    Extractor->>Extractor: Creates TranscriptResult with raw data
    Extractor-->>Controller: TranscriptResult

    Controller->>Processor: Process result
    Processor->>Processor: categorize_error() → "Rate limited - wait before retrying"

    Processor-->>Controller: Categorized error message
    Controller->>Display: Update progress table
    Controller->>Logs: Write session logs

    Note over Display: Currently shows: "Rate limited - wait before retrying"
    Note over Logs: Currently shows: "Rate limited - wait before retrying"

    Note over User: Wants to see: {"error": "RESOURCE_EXHAUSTED", "message": "Rate limit exceeded"}
```

## Component Interaction Details

### 1. Transcript Extractor (`src/bulk_transcribe/youtube_transcript.py`)

```mermaid
classDiagram
    class TranscriptResult {
        +success: bool
        +method: str
        +transcript_text: str?
        +error_message: str?
        +deapi_request_id: str?
        +raw_response_data: dict?      // NEW: Raw JSON response
        +raw_response_text: str?       // NEW: Raw response text
        +http_status_code: int?        // NEW: HTTP status code
    }

    class TranscriptExtractor {
        +get_youtube_transcript(url, api_key): TranscriptResult
        +try_youtube_captions(url): str?
        +try_deapi_transcription(url, api_key): TranscriptResult
        -_try_deapi_transcription_once(...): TranscriptResult
    }

    TranscriptExtractor --> TranscriptResult
```

### 2. Bulk Controller (`pages/1_Bulk_Transcribe.py`)

```mermaid
stateDiagram-v2
    [*] --> InputValidation
    InputValidation --> ProcessingVideos

    ProcessingVideos --> TranscriptExtraction
    TranscriptExtraction --> ResultProcessing

    ResultProcessing --> Success: Update counters, save files
    ResultProcessing --> ErrorHandling: Categorize error, update UI

    ErrorHandling --> ProgressUpdate: Update table with error
    ErrorHandling --> LogUpdate: Write to session logs

    ProgressUpdate --> NextVideo
    LogUpdate --> NextVideo
    Success --> NextVideo

    NextVideo --> ProcessingVideos: More videos
    NextVideo --> [*]: All done

    note right of ErrorHandling
        Current: categorize_error() → user-friendly message
        Desired: Show raw server response + categorization
    end note
```

### 3. UI Display Components

```mermaid
classDiagram
    class ProgressTable {
        +update_row(video_data): void
        +show_status_icon(): str
        +show_error_message(): str        // CURRENT: Categorized
        +show_raw_response(): str         // NEW: Raw server response
    }

    class SessionLogs {
        +write_log_entry(): void
        +format_error_details(): str      // CURRENT: Categorized
        +include_raw_response(): str      // NEW: Include raw data
    }

    class SidebarBalance {
        +check_balance(): dict
        +display_balance(): void
        +show_last_error(): str           // NEW: Show API errors
    }

    class ErrorCategorizer {
        +categorize_error(msg): tuple
        +get_raw_response(result): str    // NEW: Extract raw data
    }

    ProgressTable --> ErrorCategorizer
    SessionLogs --> ErrorCategorizer
    SidebarBalance --> ErrorCategorizer
```

## Error Display Locations (All Need Updates)

### 1. **Progress Table** (`pages/1_Bulk_Transcribe.py:635-640`)
```python
video_status.update({
    "Status": f"{status_icon} Failed",
    "Method": transcript_result.method,
    "Error": display_error,  # CURRENT: Categorized message
    "Time": f"{elapsed:.1f}s"
})
```

**Update needed**: Add raw response column or expandable details

### 2. **Session Logs** (`pages/1_Bulk_Transcribe.py:790-810`)
```python
log_lines = [
    f"Session: {session.session_id}",
    # ... other lines ...
    f"Retryable Failures: {rate_limited_count}",
    "",
    "=" * 80,
    "DETAILED STATUS LOG",
    "=" * 80,
]
```

**Update needed**: Include raw server responses in detailed log

### 3. **Console Output** (Terminal/debugging)
**Update needed**: Show raw responses in debug output

### 4. **Error Summary** (`pages/1_Bulk_Transcribe.py:755-760`)
```python
if rate_limited_count > 0:
    st.warning(f"⚠️ {rate_limited_count} videos hit rate limits. Wait 10-15 minutes and try again with just the failed videos.")
```

**Update needed**: Show which specific errors caused rate limiting

## Implementation Strategy

### Phase 1: Data Capture ✅
- [x] Modified `TranscriptResult` class to store raw responses
- [x] Updated all DEAPI function returns to include raw data
- [x] Added HTTP status codes and response text

### Phase 2: UI Updates (In Progress)
- [ ] Modify progress table to show raw responses
- [ ] Add expandable details for full response inspection
- [ ] Update session logs to include raw data
- [ ] Add raw response display in error summaries

### Phase 3: Error Enhancement
- [ ] Create hybrid display: "Rate limited (RESOURCE_EXHAUSTED)"
- [ ] Add "Show Raw Response" buttons/expanders
- [ ] Include request IDs and timestamps in logs
- [ ] Add error export functionality

## Key Technical Changes Required

### 1. Progress Table Enhancement
```python
# Add raw response column or expandable row
"Raw Response": transcript_result.raw_response_text or "N/A",
"Status Code": transcript_result.http_status_code or "N/A"
```

### 2. Session Log Enhancement
```python
# Include raw responses in detailed logs
for status in status_data:
    if "Failed" in status.get("Status", ""):
        log_lines.append(f"Raw Response: {status.get('raw_response', 'N/A')}")
```

### 3. Error Categorization Enhancement
```python
def categorize_error_with_raw(error_msg: str, transcript_result: TranscriptResult) -> dict:
    """Return both categorized message and raw response"""
    return {
        "categorized": categorize_error(error_msg),
        "raw_response": transcript_result.raw_response_text,
        "status_code": transcript_result.http_status_code,
        "request_id": transcript_result.deapi_request_id
    }
```

## Success Criteria

- [ ] **Progress Table**: Shows exact DEAPI server responses for all errors
- [ ] **Session Logs**: Include raw JSON responses in detailed error logs
- [ ] **Error Messages**: Display both user-friendly and exact server responses
- [ ] **Debugging**: Easy access to full API response details for troubleshooting
- [ ] **Transparency**: Users can see exactly what DEAPI servers are returning