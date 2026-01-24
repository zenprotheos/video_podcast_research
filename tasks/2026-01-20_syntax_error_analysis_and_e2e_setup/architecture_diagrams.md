# Bulk Transcribe Application Architecture

## High-Level Component Diagram

```mermaid
graph TB
    subgraph "User Interface"
        A[Streamlit App<br/>app.py]
        B[Bulk Transcribe Page<br/>pages/1_Bulk_Transcribe.py]
        C[YouTube Search Page<br/>pages/2_YouTube_Search.py]
    end

    subgraph "Core Processing Engine"
        D[Session Manager<br/>session_manager.py]
        E[Sheet Ingest<br/>sheet_ingest.py]
        F[Video Filter<br/>video_filter.py]
        G[Direct Input<br/>direct_input.py]
    end

    subgraph "YouTube Integration"
        H[YouTube Search<br/>youtube_search.py]
        I[YouTube Metadata<br/>youtube_metadata.py]
        J[YouTube Transcript<br/>youtube_transcript.py]
    end

    subgraph "Output & Utils"
        K[Transcript Writer<br/>transcript_writer.py]
        L[Utils<br/>utils.py]
    end

    subgraph "Data Storage"
        M[Output Directory<br/>output/sessions/]
        N[JSON Metadata Files]
        O[Markdown Transcripts]
    end

    A --> B
    A --> C
    B --> D
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
    B --> J
    H --> I
    I --> J
    J --> K
    D --> M
    K --> N
    K --> O
    L -.-> B
    L -.-> D
    L -.-> K

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#e8f5e8
    style H fill:#fff3e0
    style M fill:#fce4ec
```

## Class Diagram - Core Components

```mermaid
classDiagram
    class SessionManager {
        +create_session() Session
        +get_session(session_id) Session
        +list_sessions() List[Session]
        +cleanup_old_sessions()
    }

    class BulkTranscribeProcessor {
        +process_videos(urls, filters) Dict
        +validate_urls(urls) List[str]
        +categorize_errors(error_msg) Tuple[str, str]
        -_process_single_video(video_data) Dict
    }

    class YouTubeMetadataFetcher {
        +fetch_metadata(url) YouTubeMetadata
        +extract_video_id(url) str
        +validate_url(url) bool
    }

    class YouTubeTranscriptFetcher {
        +get_transcript(video_id, api_key) TranscriptResult
        +_try_youtube_api(video_id) TranscriptResult
        +_try_fallback_methods(video_id) TranscriptResult
    }

    class TranscriptWriter {
        +write_transcript_markdown(path, data)
        +generate_filename(video_id, title, source) str
        +format_transcript_text(text) str
    }

    class VideoFilter {
        +apply_filters(videos, criteria) List[Video]
        +filter_by_duration(videos, min_duration) List[Video]
        +filter_by_keywords(videos, keywords) List[Video]
    }

    class SheetIngest {
        +read_excel(file_path) DataFrame
        +read_csv(file_path) DataFrame
        +validate_columns(df) bool
        +extract_urls(df) List[str]
    }

    SessionManager --> BulkTranscribeProcessor
    BulkTranscribeProcessor --> YouTubeMetadataFetcher
    BulkTranscribeProcessor --> YouTubeTranscriptFetcher
    BulkTranscribeProcessor --> TranscriptWriter
    BulkTranscribeProcessor --> VideoFilter
    BulkTranscribeProcessor --> SheetIngest

    note for BulkTranscribeProcessor "Main processing logic\nHandles error categorization\nManages status updates"
    note for YouTubeTranscriptFetcher "Multiple fallback methods\nAPI key management\nRate limiting handling"
```

## Sequence Diagram - YouTube Video Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant StreamlitUI
    participant BulkProcessor
    participant YouTubeAPI
    participant FileSystem

    User->>StreamlitUI: Upload CSV/Excel with URLs
    StreamlitUI->>BulkProcessor: process_videos(urls, filters)

    loop For each video URL
        BulkProcessor->>BulkProcessor: Validate URL format
        BulkProcessor->>YouTubeAPI: fetch_metadata(url)
        YouTubeAPI-->>BulkProcessor: metadata (title, duration, etc.)

        BulkProcessor->>YouTubeAPI: get_transcript(video_id)
        YouTubeAPI-->>BulkProcessor: transcript_result

        alt Success
            BulkProcessor->>FileSystem: write_transcript_markdown()
            BulkProcessor->>FileSystem: save_metadata_json()
            BulkProcessor-->>StreamlitUI: Success status
        else Error
            BulkProcessor-->>StreamlitUI: Error status with details
        end
    end

    BulkProcessor-->>StreamlitUI: Processing complete
    StreamlitUI-->>User: Display results table

    note over BulkProcessor,YouTubeAPI: Handles rate limits, API errors, fallbacks
    note over BulkProcessor,FileSystem: Creates session directories, saves outputs
```

## Data Flow Diagram

```mermaid
flowchart TD
    A[Input Sources] --> B{Input Type}
    B -->|CSV/Excel| C[Sheet Ingest]
    B -->|Direct URLs| D[Direct Input Parser]
    B -->|YouTube Search| E[YouTube Search API]

    C --> F[DataFrame]
    D --> F
    E --> F

    F --> G[Video Filter Engine]
    G --> H[Filtered Video List]

    H --> I{Batch Processor}
    I --> J[YouTube Metadata Fetcher]
    I --> K[YouTube Transcript Fetcher]

    J --> L[Metadata JSON]
    K --> M[Transcript Markdown]

    L --> N[Output Directory Structure]
    M --> N

    N --> O[Session Manifest]
    O --> P[Streamlit Results Display]

    Q[Error Handler] -.-> I
    Q -.-> P

    style A fill:#bbdefb
    style N fill:#c8e6c9
    style P fill:#fff9c4
```

## Error Handling Flow

```mermaid
stateDiagram-v2
    [*] --> ProcessingVideo

    ProcessingVideo --> FetchMetadata : Valid URL
    ProcessingVideo --> InvalidURLError : Invalid URL

    FetchMetadata --> FetchTranscript : Metadata OK
    FetchMetadata --> MetadataError : API Error/Network Issue

    FetchTranscript --> WriteFiles : Transcript OK
    FetchTranscript --> TranscriptError : API/Rate Limit/Quota

    WriteFiles --> Success : Files written
    WriteFiles --> FileSystemError : Disk/IO Error

    InvalidURLError --> ErrorLogged
    MetadataError --> ErrorLogged
    TranscriptError --> ErrorLogged
    FileSystemError --> ErrorLogged

    ErrorLogged --> [*] : Continue to next video
    Success --> [*] : Video complete

    note right of ErrorLogged : Error categorization:\nRate limit, quota, timeout, etc.
    note right of Success : Update progress counters
```

## Testing Strategy Overview

```mermaid
mindmap
  root((Testing Strategy))
    Unit Tests
      Core Functions
        URL Validation
        Error Categorization
        Filename Generation
      YouTube Integration
        Metadata Fetching
        Transcript Retrieval
        API Error Handling
      Data Processing
        CSV/Excel Parsing
        Video Filtering
        Session Management
    Integration Tests
      End-to-End Workflows
        Single Video Processing
        Batch Processing
        Error Scenarios
      API Integration
        YouTube API Calls
        Rate Limiting
        Fallback Methods
    E2E Tests
      Streamlit UI
        File Upload
        Progress Display
        Results Table
        Error Messages
      Full Workflows
        Complete Processing Pipeline
        Session Management
        Output Validation
```

## Deployment & CI/CD Architecture

```mermaid
graph LR
    subgraph "Development"
        A[Local Environment]
        B[Git Repository]
        C[Tests Suite]
    end

    subgraph "CI/CD Pipeline"
        D[GitHub Actions]
        E[Syntax Validation]
        F[Unit Tests]
        G[Integration Tests]
        H[Build Artifact]
    end

    subgraph "Production"
        I[Streamlit Cloud]
        J[Environment Variables]
        K[Log Monitoring]
    end

    A --> B
    B --> D
    D --> E
    D --> F
    D --> G
    G --> H
    H --> I
    J -.-> I
    I -.-> K

    style A fill:#e3f2fd
    style D fill:#f3e5f5
    style I fill:#e8f5e8
```

## Security Considerations

```mermaid
graph TD
    subgraph "Input Validation"
        A[URL Sanitization]
        B[File Type Checking]
        C[Data Size Limits]
    end

    subgraph "API Security"
        D[API Key Management]
        E[Rate Limiting]
        F[Error Message Sanitization]
    end

    subgraph "Output Security"
        G[File Path Sanitization]
        H[Directory Traversal Prevention]
        I[Content Validation]
    end

    subgraph "Monitoring"
        J[Error Logging]
        K[Usage Tracking]
        L[Performance Metrics]
    end

    A --> D
    B --> D
    C --> D
    D --> G
    E --> J
    F --> J
    G --> I
    I --> L
    J --> K

    style D fill:#ffebee
    style J fill:#fff3e0
```