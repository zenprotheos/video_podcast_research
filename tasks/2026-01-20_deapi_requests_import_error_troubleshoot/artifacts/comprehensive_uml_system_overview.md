# Comprehensive UML System Diagrams - Bulk Transcribe Application

## 1. System Context Diagram

```mermaid
graph TB
    subgraph "External Systems & Services"
        YT[YouTube API<br/>Video Metadata & Captions]
        DEAPI[DEAPI Service<br/>Video Transcription]
        ST[Streamlit Cloud<br/>Web Interface Hosting]
    end

    subgraph "Bulk Transcribe Application System Boundary"
        BA[Bulk Transcribe<br/>Application]
    end

    subgraph "User Environment"
        U[User<br/>Browser]
        FS[File System<br/>Input/Output]
        ENV[Environment Variables<br/>API Keys, Config]
    end

    subgraph "Development Environment"
        IDE[Cursor IDE<br/>Code Editing]
        VCS[Git<br/>Version Control]
        PKG[Package Managers<br/>pip, conda]
    end

    U --> BA
    BA --> YT
    BA --> DEAPI
    BA --> FS
    BA --> ENV
    BA --> ST

    IDE --> BA
    VCS --> BA
    PKG --> BA

    style BA fill:#e1f5fe
    style U fill:#f3e5f5
    style IDE fill:#e8f5e8
```

## 2. System Architecture - Component View

```mermaid
graph TB
    subgraph "User Interface Layer"
        SA[Streamlit App<br/>app.py]
        BT[Bulk Transcribe Page<br/>pages/1_Bulk_Transcribe.py]
        YS[YouTube Search Page<br/>pages/2_YouTube_Search.py]
    end

    subgraph "Business Logic Layer"
        SI[Sheet Ingest Module<br/>src/bulk_transcribe/sheet_ingest.py]
        SM[Session Manager<br/>src/bulk_transcribe/session_manager.py]
        YT_TRAN[YouTube Transcript<br/>src/bulk_transcribe/youtube_transcript.py]
        YT_META[YouTube Metadata<br/>src/bulk_transcribe/youtube_metadata.py]
        YT_SEARCH[YouTube Search<br/>src/bulk_transcribe/youtube_search.py]
        TRAN_WR[Transcript Writer<br/>src/bulk_transcribe/transcript_writer.py]
    end

    subgraph "Data Access Layer"
        FS[File System<br/>CSV/TSV/JSON files]
        HTTP[HTTP Client<br/>requests library]
        YT_API[YouTube Data API v3]
        DEAPI_HTTP[DEAPI REST API]
    end

    subgraph "Infrastructure Layer"
        VENV[Virtual Environment<br/>.venv/]
        PKG_DEPS[Package Dependencies<br/>requirements.txt]
        CONF[Configuration<br/>.env, environment vars]
        LOG[Logging System<br/>session logs, output files]
    end

    SA --> BT
    SA --> YS
    BT --> SI
    BT --> SM
    BT --> YT_TRAN
    BT --> YT_META
    BT --> TRAN_WR

    YT_TRAN --> YT_API
    YT_TRAN --> DEAPI_HTTP
    YT_TRAN --> HTTP

    YT_SEARCH --> YT_API
    YT_SEARCH --> HTTP

    YT_META --> YT_API
    YT_META --> HTTP

    SI --> FS
    SM --> FS
    TRAN_WR --> FS
    LOG --> FS

    VENV --> PKG_DEPS
    CONF --> ENV_VARS[Environment Variables]
```

## 3. Process Execution Architecture

```mermaid
graph TB
    subgraph "Entry Point"
        RAP[run_app.ps1<br/>PowerShell Script]
    end

    subgraph "Environment Setup"
        VENV_CHECK[Check Virtual Env<br/>Exists]
        PATH_ISO[PATH Isolation<br/>Virtual Env First]
        ENV_VARS[Set Environment<br/>Variables]
    end

    subgraph "Python Process Launch"
        PY_LAUNCH[Launch Python<br/>.venv\Scripts\python.exe]
        ST_IMPORT[Import Streamlit<br/>streamlit module]
        ST_CMD[Execute streamlit.cmd<br/>Batch File]
    end

    subgraph "Streamlit Runtime"
        ST_SERVER[Streamlit Server<br/>Web Server Process]
        ST_RUNNER[Script Runner<br/>Thread/Process]
        ST_SESSION[Session State<br/>User Interaction Data]
    end

    subgraph "Application Execution"
        APP_LOAD[Load app.py<br/>Main Application]
        PAGE_LOAD[Load Page<br/>User Navigation]
        UI_RENDER[Render UI<br/>Streamlit Components]
    end

    subgraph "Transcription Process"
        URL_PROC[Process URLs<br/>From Input]
        META_FETCH[Fetch Metadata<br/>YouTube API]
        CAPTIONS_TRY[Try Captions<br/>youtube_transcript_api]
        DEAPI_CALL[DEAPI Transcription<br/>HTTP Request]
        FILE_WRITE[Write Output<br/>Markdown Files]
    end

    RAP --> VENV_CHECK
    VENV_CHECK --> PATH_ISO
    PATH_ISO --> ENV_VARS
    ENV_VARS --> PY_LAUNCH
    PY_LAUNCH --> ST_IMPORT
    ST_IMPORT --> ST_CMD
    ST_CMD --> ST_SERVER
    ST_SERVER --> ST_RUNNER
    ST_RUNNER --> APP_LOAD
    APP_LOAD --> PAGE_LOAD
    PAGE_LOAD --> UI_RENDER
    UI_RENDER --> URL_PROC
    URL_PROC --> META_FETCH
    META_FETCH --> CAPTIONS_TRY
    CAPTIONS_TRY --> DEAPI_CALL
    DEAPI_CALL --> FILE_WRITE
```

## 4. Component Relationship Diagram (Modules)

```mermaid
graph TD
    subgraph "Main Application"
        APP[app.py]
    end

    subgraph "Page Components"
        BT_PAGE[1_Bulk_Transcribe.py]
        YS_PAGE[2_YouTube_Search.py]
    end

    subgraph "Core Modules"
        SHEET_ING[sheet_ingest.py<br/>CSV/TSV parsing]
        SESS_MGR[session_manager.py<br/>Session handling]
        YT_TRANS[youtube_transcript.py<br/>Transcription logic]
        YT_META[youtube_metadata.py<br/>Video metadata]
        YT_SEARCH[youtube_search.py<br/>Video search]
        TRANS_WR[transcript_writer.py<br/>File output]
    end

    subgraph "Utility Modules"
        UTILS[utils.py<br/>Helper functions]
    end

    subgraph "External Dependencies"
        YT_API_LIB[youtube_transcript_api<br/>Caption extraction]
        REQUESTS[requests<br/>HTTP client]
        PANDAS[pandas<br/>Data processing]
        STREAMLIT[streamlit<br/>Web framework]
        DOTENV[python-dotenv<br/>Environment config]
        GOOGLE_API[google-api-python-client<br/>YouTube API]
    end

    APP --> BT_PAGE
    APP --> YS_PAGE

    BT_PAGE --> SHEET_ING
    BT_PAGE --> SESS_MGR
    BT_PAGE --> YT_TRANS
    BT_PAGE --> YT_META
    BT_PAGE --> TRANS_WR

    YS_PAGE --> YT_SEARCH
    YS_PAGE --> SHEET_ING

    YT_TRANS --> YT_API_LIB
    YT_TRANS --> REQUESTS

    YT_META --> REQUESTS
    YT_META --> GOOGLE_API

    YT_SEARCH --> REQUESTS
    YT_SEARCH --> GOOGLE_API

    SHEET_ING --> PANDAS
    TRANS_WR --> UTILS

    BT_PAGE --> STREAMLIT
    YS_PAGE --> STREAMLIT
    APP --> DOTENV
```

## 5. Data Flow Diagram

```mermaid
graph TD
    subgraph "Input Sources"
        CSV_FILE[CSV/TSV Files<br/>User uploaded]
        TXT_FILE[Text Input<br/>Direct paste]
        JSON_FILE[JSON Files<br/>Pre-populated]
        ENV_VARS[Environment Variables<br/>API Keys]
    end

    subgraph "Data Processing Pipeline"
        PARSE_SHEET[Parse Spreadsheet<br/>sheet_ingest.py]
        NORMALIZE_ROWS[Normalize Data<br/>Standard format]
        VALIDATE_ROWS[Validate URLs<br/>Format checking]
        CREATE_SESSION[Create Session<br/>session_manager.py]
    end

    subgraph "YouTube Processing"
        EXTRACT_VID_ID[Extract Video IDs<br/>URL parsing]
        FETCH_METADATA[Fetch Metadata<br/>YouTube API calls]
        TRY_CAPTIONS[Try Captions<br/>youtube_transcript_api]
        CALL_DEAPI[Call DEAPI<br/>HTTP requests]
    end

    subgraph "Output Generation"
        CREATE_TRANSCRIPT[Create Transcript<br/>Text processing]
        GENERATE_FILENAME[Generate Filename<br/>Slug logic]
        WRITE_MARKDOWN[Write Markdown<br/>transcript_writer.py]
        SAVE_METADATA[Save Metadata<br/>JSON files]
    end

    subgraph "Storage Layer"
        SESSION_DIR[Session Directory<br/>output/sessions/]
        LOG_FILES[Session Logs<br/>Progress tracking]
        TRANSCRIPT_FILES[Transcript Files<br/>.md files]
        METADATA_FILES[Metadata Files<br/>.json files]
    end

    CSV_FILE --> PARSE_SHEET
    TXT_FILE --> PARSE_SHEET
    JSON_FILE --> PARSE_SHEET

    PARSE_SHEET --> NORMALIZE_ROWS
    NORMALIZE_ROWS --> VALIDATE_ROWS
    VALIDATE_ROWS --> CREATE_SESSION

    CREATE_SESSION --> EXTRACT_VID_ID
    EXTRACT_VID_ID --> FETCH_METADATA
    FETCH_METADATA --> TRY_CAPTIONS
    TRY_CAPTIONS --> CALL_DEAPI

    CALL_DEAPI --> CREATE_TRANSCRIPT
    CREATE_TRANSCRIPT --> GENERATE_FILENAME
    GENERATE_FILENAME --> WRITE_MARKDOWN
    FETCH_METADATA --> SAVE_METADATA

    WRITE_MARKDOWN --> TRANSCRIPT_FILES
    SAVE_METADATA --> METADATA_FILES
    CREATE_SESSION --> LOG_FILES
    LOG_FILES --> SESSION_DIR
    TRANSCRIPT_FILES --> SESSION_DIR
    METADATA_FILES --> SESSION_DIR

    ENV_VARS --> CALL_DEAPI
    ENV_VARS --> FETCH_METADATA
```

## 6. Environment Context Diagram

```mermaid
graph TD
    subgraph "System Level"
        WINDOWS_OS[Windows OS<br/>Base system]
        POWERSHELL_ENV[PowerShell Process<br/>Script execution]
        SYSTEM_PATH[System PATH<br/>C:\Python312\Scripts\]
    end

    subgraph "Virtual Environment Context"
        VENV_DIR[.venv Directory<br/>Isolated Python env]
        VENV_PYTHON[.venv\Scripts\python.exe<br/>Virtual Python]
        VENV_PACKAGES[.venv\Lib\site-packages\<br/>Installed packages]
        VENV_SCRIPTS[.venv\Scripts\<br/>Executable scripts]
    end

    subgraph "Process Execution Contexts"
        PS_PROC[PowerShell Process<br/>run_app.ps1 execution]
        PY_PARENT[Parent Python Process<br/>Streamlit launcher]
        PY_CHILD[Child Python Process<br/>Streamlit server]
        PY_THREAD[Python Threads<br/>Streamlit runners]
    end

    subgraph "Streamlit Runtime Context"
        ST_WEB_SERVER[Streamlit Web Server<br/>HTTP endpoint]
        ST_SCRIPT_RUNNER[Script Runner Thread<br/>Code execution]
        ST_SESSION_MGR[Session Manager<br/>State management]
        ST_FILE_WATCHER[File Watcher<br/>Hot reload]
    end

    subgraph "Module Execution Context"
        IMPORT_CONTEXT[Import Context<br/>Module loading]
        FUNCTION_CONTEXT[Function Execution<br/>DEAPI calls]
        HTTP_CONTEXT[HTTP Request Context<br/>API communication]
        FILE_CONTEXT[File I/O Context<br/>Output writing]
    end

    WINDOWS_OS --> POWERSHELL_ENV
    POWERSHELL_ENV --> SYSTEM_PATH
    SYSTEM_PATH --> PS_PROC

    VENV_DIR --> VENV_PYTHON
    VENV_DIR --> VENV_PACKAGES
    VENV_DIR --> VENV_SCRIPTS

    PS_PROC --> PY_PARENT
    PY_PARENT --> PY_CHILD
    PY_CHILD --> PY_THREAD

    PY_THREAD --> ST_WEB_SERVER
    PY_THREAD --> ST_SCRIPT_RUNNER
    PY_THREAD --> ST_SESSION_MGR
    PY_THREAD --> ST_FILE_WATCHER

    ST_SCRIPT_RUNNER --> IMPORT_CONTEXT
    ST_SCRIPT_RUNNER --> FUNCTION_CONTEXT
    ST_SCRIPT_RUNNER --> HTTP_CONTEXT
    ST_SCRIPT_RUNNER --> FILE_CONTEXT

    VENV_PYTHON --> PY_PARENT
    VENV_PACKAGES --> IMPORT_CONTEXT
```

## 7. Error Propagation Diagram

```mermaid
graph TD
    subgraph "Entry Points"
        PS_SCRIPT_FAIL[run_app.ps1 Failure<br/>Virtual env not found]
        PY_LAUNCH_FAIL[Python Launch Failure<br/>Executable not found]
        IMPORT_FAIL[Import Failure<br/>Module not found]
    end

    subgraph "Streamlit Layer Errors"
        ST_START_FAIL[Streamlit Start Failure<br/>Port binding, config]
        ST_EXEC_FAIL[Script Execution Failure<br/>Syntax errors, runtime]
        ST_RENDER_FAIL[UI Render Failure<br/>Component errors]
    end

    subgraph "Application Layer Errors"
        FILE_PARSE_FAIL[File Parsing Failure<br/>Invalid CSV/TSV]
        URL_VALID_FAIL[URL Validation Failure<br/>Malformed URLs]
        API_KEY_FAIL[API Key Missing<br/>DEAPI_API_KEY not set]
    end

    subgraph "YouTube Processing Errors"
        YT_API_FAIL[YouTube API Failure<br/>Quota, auth, network]
        CAPTION_FAIL[Caption Extraction Failure<br/>No captions available]
        VID_PRIVATE[Video Privacy Failure<br/>Private/deleted videos]
    end

    subgraph "DEAPI Layer Errors"
        REQUESTS_IMPORT_FAIL[requests Import Failure<br/>Module resolution]
        HTTP_CONN_FAIL[HTTP Connection Failure<br/>Network, timeout]
        API_AUTH_FAIL[API Authentication Failure<br/>Invalid API key]
        API_QUOTA_FAIL[API Quota Failure<br/>Rate limits, credits]
    end

    subgraph "Output Layer Errors"
        FILE_WRITE_FAIL[File Write Failure<br/>Permissions, disk space]
        DIR_CREATE_FAIL[Directory Creation Failure<br/>Path issues]
        ENCODE_FAIL[Encoding Failure<br/>Unicode issues]
    end

    subgraph "User Experience"
        UI_ERROR_DISPLAY[UI Error Display<br/>Streamlit error messages]
        LOG_ERROR_WRITE[Log Error Writing<br/>Session log files]
        PARTIAL_SUCCESS[Partial Success<br/>Some URLs work, some fail]
    end

    PS_SCRIPT_FAIL --> UI_ERROR_DISPLAY
    PY_LAUNCH_FAIL --> UI_ERROR_DISPLAY
    IMPORT_FAIL --> LOG_ERROR_WRITE

    ST_START_FAIL --> UI_ERROR_DISPLAY
    ST_EXEC_FAIL --> UI_ERROR_DISPLAY
    ST_RENDER_FAIL --> UI_ERROR_DISPLAY

    FILE_PARSE_FAIL --> UI_ERROR_DISPLAY
    URL_VALID_FAIL --> UI_ERROR_DISPLAY
    API_KEY_FAIL --> UI_ERROR_DISPLAY

    YT_API_FAIL --> LOG_ERROR_WRITE
    CAPTION_FAIL --> DEAPI Layer Errors
    VID_PRIVATE --> LOG_ERROR_WRITE

    REQUESTS_IMPORT_FAIL --> LOG_ERROR_WRITE
    HTTP_CONN_FAIL --> LOG_ERROR_WRITE
    API_AUTH_FAIL --> LOG_ERROR_WRITE
    API_QUOTA_FAIL --> LOG_ERROR_WRITE

    FILE_WRITE_FAIL --> LOG_ERROR_WRITE
    DIR_CREATE_FAIL --> LOG_ERROR_WRITE
    ENCODE_FAIL --> LOG_ERROR_WRITE

    LOG_ERROR_WRITE --> PARTIAL_SUCCESS
```

## 8. Class Hierarchy Diagram

```mermaid
classDiagram
    class AppConfig {
        +output_root: str
        +deapi_api_key_present: bool
    }

    class ParsedSheet {
        +columns: List[str]
        +rows: List[Dict]
        +row_count: int
    }

    class ColumnMapping {
        +source_type: str
        +youtube_url: str
        +mp3_url: str
        +title: str
        +description: str
        +episode_url: str
    }

    class SessionConfig {
        +output_root: str
    }

    class SessionManager {
        +config: SessionConfig
        +create_session(): Session
        +write_items_csv(path, rows)
        +write_manifest(path, data)
        +read_manifest(path): Dict
    }

    class TranscriptResult {
        +success: bool
        +method: str
        +transcript_text: Optional[str]
        +error_message: Optional[str]
        +deapi_request_id: Optional[str]
    }

    AppConfig ||--o ParsedSheet
    ParsedSheet ||--o ColumnMapping
    SessionConfig ||--o SessionManager
    SessionManager --> Session

    note for TranscriptResult "Result of transcription attempts\nContains success status, method used,\nand either transcript text or error message"
```

## 9. Module Dependency Diagram

```mermaid
graph TD
    subgraph "Entry Points"
        APP_PY[app.py<br/>Main entry]
        RUN_PS1[run_app.ps1<br/>Launcher script]
    end

    subgraph "Core Application"
        BT_PAGE[pages/1_Bulk_Transcribe.py<br/>Main UI]
        YS_PAGE[pages/2_YouTube_Search.py<br/>Search UI]
    end

    subgraph "Business Logic"
        SHEET_ING[src/bulk_transcribe/sheet_ingest.py<br/>Data parsing]
        SESS_MGR[src/bulk_transcribe/session_manager.py<br/>Session mgmt]
        YT_TRANS[src/bulk_transcribe/youtube_transcript.py<br/>Transcription]
        YT_META[src/bulk_transcribe/youtube_metadata.py<br/>Metadata]
        YT_SEARCH[src/bulk_transcribe/youtube_search.py<br/>Search]
        TRANS_WR[src/bulk_transcribe/transcript_writer.py<br/>Output]
        UTILS[src/bulk_transcribe/utils.py<br/>Utilities]
    end

    subgraph "External Libraries"
        STREAMLIT[streamlit<br/>Web framework]
        PANDAS[pandas<br/>Data processing]
        REQUESTS[requests<br/>HTTP client]
        YT_TRANSCRIPT_API[youtube_transcript_api<br/>Caption extraction]
        GOOGLE_API[google-api-python-client<br/>YouTube API]
        DOTENV[python-dotenv<br/>Config]
        OPENPYXL[openpyxl<br/>Excel support]
    end

    subgraph "Standard Library"
        OS[os<br/>File system]
        JSON[json<br/>Data format]
        DATETIME[datetime<br/>Time handling]
        PATHLIB[pathlib<br/>Path handling]
        SUBPROCESS[subprocess<br/>Process execution]
        THREADING[threading<br/>Concurrency]
    end

    RUN_PS1 --> APP_PY
    APP_PY --> BT_PAGE
    APP_PY --> YS_PAGE

    BT_PAGE --> SHEET_ING
    BT_PAGE --> SESS_MGR
    BT_PAGE --> YT_TRANS
    BT_PAGE --> YT_META
    BT_PAGE --> TRANS_WR

    YS_PAGE --> YT_SEARCH
    YS_PAGE --> SHEET_ING

    YT_TRANS --> YT_TRANSCRIPT_API
    YT_TRANS --> REQUESTS

    YT_META --> REQUESTS
    YT_META --> GOOGLE_API

    YT_SEARCH --> REQUESTS
    YT_SEARCH --> GOOGLE_API

    SHEET_ING --> PANDAS
    SHEET_ING --> OPENPYXL

    TRANS_WR --> UTILS

    APP_PY --> DOTENV
    APP_PY --> STREAMLIT
    BT_PAGE --> STREAMLIT
    YS_PAGE --> STREAMLIT

    YT_TRANS --> OS
    YT_TRANS --> JSON
    YT_TRANS --> DATETIME
    YT_TRANS --> SUBPROCESS
    YT_TRANS --> THREADING

    SESS_MGR --> OS
    SESS_MGR --> JSON
    SESS_MGR --> DATETIME

    TRANS_WR --> OS
    TRANS_WR --> PATHLIB
```

## 10. State Transition Diagram (Transcription Process)

```mermaid
stateDiagram-v2
    [*] --> URL_Received: User provides YouTube URLs

    URL_Received --> Validation_Pending: URLs parsed from input
    Validation_Pending --> URL_Valid: Format validation passes
    Validation_Pending --> URL_Invalid: Invalid format

    URL_Valid --> Session_Created: Session directory created
    Session_Created --> Metadata_Fetch_Pending: Ready to process

    Metadata_Fetch_Pending --> Metadata_Fetching: YouTube API call
    Metadata_Fetching --> Metadata_Success: Metadata retrieved
    Metadata_Fetching --> Metadata_Failed: API error/quota

    Metadata_Success --> Caption_Attempt_Pending: Video info available

    Caption_Attempt_Pending --> Caption_Fetching: youtube_transcript_api call
    Caption_Fetching --> Caption_Success: Captions found
    Caption_Fetching --> Caption_Not_Available: No captions/private video

    Caption_Success --> Transcript_Complete: Use caption text
    Caption_Not_Available --> DEAPI_Attempt_Pending: Fallback to DEAPI

    DEAPI_Attempt_Pending --> DEAPI_Requesting: HTTP POST to DEAPI
    DEAPI_Requesting --> DEAPI_Polling: Check transcription status
    DEAPI_Polling --> DEAPI_Complete: Transcription finished
    DEAPI_Polling --> DEAPI_Failed: API error/rate limit

    DEAPI_Complete --> Transcript_Complete: Use DEAPI text
    DEAPI_Failed --> Transcription_Failed: All methods exhausted

    URL_Invalid --> Transcription_Failed: Invalid input
    Metadata_Failed --> Transcription_Failed: Cannot proceed

    Transcript_Complete --> Output_Writing: Generate markdown
    Output_Writing --> Session_Complete: Files written

    Transcription_Failed --> Session_Complete: Error logged
    Session_Complete --> [*]: Ready for next batch

    note right of DEAPI_Requesting : This is where "requests import error" occurs
    note right of Caption_Not_Available : Triggers DEAPI fallback
    note right of DEAPI_Failed : Rate limits, auth errors, etc.
```

## 11. Sequence Diagram - Complete Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant BT as BulkTranscribe Page
    participant SI as SheetIngest
    participant SM as SessionManager
    participant YT as YouTubeTranscript
    participant YM as YouTubeMetadata
    participant TW as TranscriptWriter
    participant FS as File System
    participant YT_API as YouTube API
    participant DEAPI as DEAPI Service

    U->>UI: Upload CSV/enter URLs
    UI->>BT: Submit for processing
    BT->>SI: Parse input data
    SI->>BT: Return ParsedSheet
    BT->>SM: Create session
    SM->>FS: Create session directory
    SM->>BT: Return Session

    loop For each URL
        BT->>YT: get_youtube_transcript(url, api_key)
        YT->>YM: fetch_youtube_metadata(url)
        YM->>YT_API: GET video metadata
        YT_API->>YM: Return metadata
        YM->>YT: Return metadata

        YT->>YT: try_youtube_captions(url)
        Note over YT: Try youtube_transcript_api

        alt Captions available
            YT->>BT: Return TranscriptResult (success)
        else No captions
            YT->>YT: try_deapi_transcription(url, api_key)
            Note over YT: Import requests (PROBLEMATIC)

            YT->>DEAPI: POST transcription request
            DEAPI->>YT: Return request_id

            loop Poll for completion
                YT->>DEAPI: GET status
                DEAPI->>YT: Return status
            end

            YT->>DEAPI: GET result
            DEAPI->>YT: Return transcript text
            YT->>BT: Return TranscriptResult (success)
        end

        BT->>TW: write_transcript_markdown(...)
        TW->>FS: Write .md file
        TW->>FS: Write .json metadata

        BT->>SM: Update manifest
        SM->>FS: Write manifest file
    end

    BT->>UI: Display results
    UI->>U: Show completion status
```

## 12. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_WS[Development Workspace<br/>Local machine]
        CURSOR_IDE[Cursor IDE<br/>Code editing]
        GIT_REPO[Git Repository<br/>Version control]
    end

    subgraph "Local Runtime Environment"
        POWERSHELL[PowerShell<br/>Script execution]
        VENV[Virtual Environment<br/>.venv/]
        PYTHON_EXE[Python Executable<br/>python.exe]
        STREAMLIT_CMD[Streamlit Command<br/>streamlit.cmd]
    end

    subgraph "Application Runtime"
        ST_WEB[Streamlit Web Server<br/>localhost:8501]
        ST_SESSION[Session State<br/>In-memory]
        FILE_WATCH[File Watcher<br/>Hot reload]
    end

    subgraph "External Dependencies"
        YT_API_SVC[YouTube Data API<br/>Google Cloud]
        DEAPI_SVC[DEAPI Service<br/>deapi.ai]
    end

    subgraph "Data Storage"
        LOCAL_FS[Local File System<br/>output/sessions/]
        LOG_FILES[Log Files<br/>.txt files]
        MD_FILES[Transcript Files<br/>.md files]
        JSON_FILES[Metadata Files<br/>.json files]
    end

    DEV_WS --> CURSOR_IDE
    CURSOR_IDE --> GIT_REPO

    DEV_WS --> POWERSHELL
    POWERSHELL --> VENV
    VENV --> PYTHON_EXE
    PYTHON_EXE --> STREAMLIT_CMD

    STREAMLIT_CMD --> ST_WEB
    ST_WEB --> ST_SESSION
    ST_WEB --> FILE_WATCH

    ST_WEB --> YT_API_SVC
    ST_WEB --> DEAPI_SVC

    ST_WEB --> LOCAL_FS
    LOCAL_FS --> LOG_FILES
    LOCAL_FS --> MD_FILES
    LOCAL_FS --> JSON_FILES
```

## 13. Security Architecture

```mermaid
graph TB
    subgraph "Authentication & Authorization"
        API_KEYS[API Keys<br/>DEAPI_API_KEY, YOUTUBE_API_KEY]
        ENV_VARS[Environment Variables<br/>Secure storage]
        NO_HARD_CODED[No Hard-coded Secrets<br/>External configuration]
    end

    subgraph "Data Protection"
        HTTPS_ONLY[HTTPS Only<br/>Secure API calls]
        NO_PERSIST_SECRETS[No Persistent Secrets<br/>Runtime only]
        FILE_SANITIZE[File Path Sanitization<br/>Prevent directory traversal]
    end

    subgraph "Access Control"
        LOCAL_ONLY[Local Access Only<br/>No remote access]
        FILE_SYSTEM_ISO[File System Isolation<br/>Controlled directories]
        NETWORK_RESTRICT[Network Restrictions<br/>API-only access]
    end

    subgraph "Error Handling"
        NO_SECRET_LEAK[No Secret Leakage<br/>Error sanitization]
        LOG_SANITIZE[Log Sanitization<br/>No sensitive data]
        GRACEFUL_FAILURE[Graceful Failure<br/>No system crashes]
    end

    API_KEYS --> ENV_VARS
    ENV_VARS --> NO_HARD_CODED

    HTTPS_ONLY --> NETWORK_RESTRICT
    NO_PERSIST_SECRETS --> LOCAL_ONLY

    FILE_SANITIZE --> FILE_SYSTEM_ISO
    LOG_SANITIZE --> NO_SECRET_LEAK
    GRACEFUL_FAILURE --> ERROR_HANDLING[Error Boundaries]
```

## 14. Performance Architecture

```mermaid
graph TD
    subgraph "Concurrency Model"
        SINGLE_THREADED[Single-threaded<br/>Sequential processing]
        RATE_LIMITING[Rate Limiting<br/>API quota management]
        BATCH_PROCESSING[Batch Processing<br/>Multiple URLs]
    end

    subgraph "Resource Management"
        MEMORY_USAGE[Memory Usage<br/>DataFrame processing]
        DISK_IO[Disk I/O<br/>File writing]
        NETWORK_IO[Network I/O<br/>API calls]
    end

    subgraph "Optimization Points"
        CACHING[Response Caching<br/>API result storage]
        ASYNC_OPERATIONS[Async Operations<br/>Non-blocking calls]
        CONNECTION_POOLING[Connection Pooling<br/>HTTP reuse]
    end

    subgraph "Bottlenecks"
        API_RATE_LIMITS[API Rate Limits<br/>YouTube/DEAPI quotas]
        NETWORK_LATENCY[Network Latency<br/>HTTP round trips]
        FILE_IO_LATENCY[File I/O Latency<br/>Disk operations]
    end

    SINGLE_THREADED --> RATE_LIMITING
    RATE_LIMITING --> API_RATE_LIMITS

    MEMORY_USAGE --> RESOURCE_CONSTRAINTS[Resource Constraints]
    DISK_IO --> FILE_IO_LATENCY
    NETWORK_IO --> NETWORK_LATENCY

    CACHING --> PERFORMANCE_IMPROVEMENT[Performance Improvement]
    ASYNC_OPERATIONS --> CONCURRENCY_IMPROVEMENT[Concurrency Improvement]
    CONNECTION_POOLING --> NETWORK_EFFICIENCY[Network Efficiency]
```

These comprehensive UML diagrams provide a complete view of the Bulk Transcribe application architecture, showing all components, their relationships, data flows, error paths, and execution contexts. This should help identify any remaining issues with the DEAPI import error that weren't addressed by the previous fix attempts.