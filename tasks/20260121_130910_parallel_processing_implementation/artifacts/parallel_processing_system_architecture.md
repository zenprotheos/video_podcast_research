# Parallel Processing System Architecture

## UI-Compatible System Context Diagram

```mermaid
graph TB
    subgraph "User Interface (PRESERVE THIS - CRITICAL)"
        UI[Streamlit UI<br/>❌ BROKEN in previous attempt]
        PST[Processing Status Table<br/>MUST WORK - Shows all videos]
        GP[Global Progress<br/>MUST WORK - Overall completion]
        CV[Current Video Info<br/>MUST WORK - What's processing now]
        CFG[Parallel Config<br/>OFF by default - Conservative]
    end

    subgraph "Incremental Parallel Layer (Add Gradually)"
        TM[Task Manager<br/>UI-Compatible wrapper]
        QM[Queue Manager<br/>Preserves existing data flow]
        SM[Session Manager<br/>Enhanced carefully]
    end

    subgraph "Parallel Execution (Start Simple)"
        TPE[ThreadPoolExecutor<br/>max_workers=2 initially]
        RL[Rate Limiter<br/>UI-compatible design]
        PM[Progress Monitor<br/>Integrates with existing UI]
    end

    subgraph "Individual Video Processing (Start with 2)"
        VP1[Video Processor 1]
        VP2[Video Processor 2]
    end

    subgraph "External Services"
        YT[YouTube API<br/>Metadata Fetching]
        DEAPI[deAPI Service<br/>Video Transcription<br/>300 RPM Limit]
    end

    UI --> CFG
    CFG --> TM
    TM --> QM
    QM --> TPE
    TPE --> RL
    RL --> PM
    PM --> UI

    PST -.-> UI
    GP -.-> UI
    CV -.-> UI

    TPE --> VP1
    TPE --> VP2

    VP1 --> YT
    VP1 --> DEAPI
    VP2 --> YT
    VP2 --> DEAPI

    style UI fill:#ffebee
    style PST fill:#ffebee
    style GP fill:#ffebee
    style CV fill:#ffebee
    style TPE fill:#e1f5fe
    style RL fill:#fff3e0
    style PM fill:#e8f5e8
```

## Class Diagram: Core Components

```mermaid
classDiagram
    class ProcessingConfig {
        +max_concurrent: int
        +rate_limit_buffer: float
        +thread_timeout: int
        +enable_parallel: bool
    }

    class ParallelProcessor {
        -config: ProcessingConfig
        -executor: ThreadPoolExecutor
        -rate_limiter: RateLimiter
        -progress_monitor: ProgressMonitor
        +process_batch(videos: List[VideoItem]): ProcessingResults
        -submit_video_task(video: VideoItem): Future
        -collect_results(futures: List[Future]): List[Result]
    }

    class RateLimiter {
        -rpm_limit: int
        -requests_this_minute: int
        -last_reset: datetime
        +acquire(): bool
        +wait_if_needed(): void
        -reset_if_minute_elapsed(): void
    }

    class ProgressMonitor {
        -total_videos: int
        -completed_count: int
        -failed_count: int
        -active_threads: Dict[int, VideoStatus]
        +update_progress(thread_id: int, status: VideoStatus): void
        +get_aggregate_progress(): ProgressSummary
        +get_thread_status(thread_id: int): VideoStatus
    }

    class VideoProcessor {
        -video_item: VideoItem
        -deapi_key: str
        +process(): ProcessingResult
        -fetch_metadata(): VideoMetadata
        -request_transcript(): TranscriptResult
        -save_results(): bool
    }

    class SessionManager {
        -session_dir: str
        -manifest: Dict
        +update_parallel_progress(thread_updates: Dict): void
        +persist_thread_state(thread_states: Dict): void
        +resume_parallel_processing(): ProcessingState
    }

    ParallelProcessor --> ProcessingConfig
    ParallelProcessor --> RateLimiter
    ParallelProcessor --> ProgressMonitor
    ParallelProcessor --> SessionManager
    ParallelProcessor ..> VideoProcessor : creates

    ProgressMonitor --> VideoProcessor
    RateLimiter --> VideoProcessor
    SessionManager --> ProgressMonitor
```

## Sequence Diagram: Parallel Processing Workflow

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant PP as ParallelProcessor
    participant TPE as ThreadPoolExecutor
    participant RL as RateLimiter
    participant VP as VideoProcessor
    participant YT as YouTube API
    participant DEAPI as deAPI Service
    participant PM as ProgressMonitor

    UI->>PP: process_batch(videos, config)
    PP->>PP: initialize ThreadPoolExecutor(max_workers=5)
    PP->>PM: initialize progress tracking

    loop for each video in batch
        PP->>TPE: submit(video_task)
        TPE->>VP: process_video(video)
        VP->>RL: acquire() - rate limit check
        RL-->>VP: permission granted
        VP->>YT: fetch_metadata()
        YT-->>VP: metadata response
        VP->>PM: update_progress(thread_id, "metadata_fetched")
        PM-->>UI: real-time progress update

        VP->>DEAPI: request_transcript()
        DEAPI-->>VP: transcript job submitted
        VP->>PM: update_progress(thread_id, "transcribing")

        loop poll for completion
            VP->>DEAPI: check_status(job_id)
            DEAPI-->>VP: status response
            alt job completed
                VP->>VP: download transcript
                VP->>VP: save markdown file
                VP->>PM: update_progress(thread_id, "completed")
            else job still processing
                VP->>PM: update_progress(thread_id, "waiting")
            end
        end

        VP-->>TPE: processing result
    end

    TPE-->>PP: all futures completed
    PP->>PM: get_final_progress()
    PM-->>PP: final statistics
    PP-->>UI: ProcessingResults(success_count, failed_count, etc.)
```

## Activity Diagram: Individual Video Processing

```mermaid
stateDiagram-v2
    [*] --> InitializeVideoProcessor
    InitializeVideoProcessor --> CheckRateLimit

    CheckRateLimit --> RateLimitExceeded: rate limit hit
    RateLimitExceeded --> WaitForRateLimitReset
    WaitForRateLimitReset --> CheckRateLimit

    CheckRateLimit --> RateLimitOK: within limits
    RateLimitOK --> FetchMetadata

    FetchMetadata --> MetadataSuccess: metadata retrieved
    MetadataSuccess --> SubmitTranscriptRequest

    FetchMetadata --> MetadataFailed: API error/timeout
    MetadataFailed --> MarkVideoFailed

    SubmitTranscriptRequest --> TranscriptJobSubmitted: job ID received
    TranscriptJobSubmitted --> PollForCompletion

    PollForCompletion --> JobCompleted: transcript ready
    JobCompleted --> DownloadTranscript
    DownloadTranscript --> SaveMarkdownFile
    SaveMarkdownFile --> MarkVideoSuccess

    PollForCompletion --> JobStillProcessing: wait longer
    JobStillProcessing --> PollForCompletion

    PollForCompletion --> JobFailed: permanent failure
    JobFailed --> MarkVideoFailed

    SubmitTranscriptRequest --> SubmitFailed: API error
    SubmitFailed --> MarkVideoFailed

    MarkVideoSuccess --> [*]
    MarkVideoFailed --> [*]

    note right of CheckRateLimit
        Rate Limiter ensures
        < 300 RPM across
        all threads
    end note

    note right of PollForCompletion
        Async processing:
        5-15 second polls
        up to 10 minutes timeout
    end note
```

## Deployment Diagram: Resource Allocation

```mermaid
graph TB
    subgraph "Streamlit Server Process"
        ST[Streamlit App<br/>PID: 1234<br/>Memory: 256MB]

        subgraph "Main Thread"
            MT[Main UI Thread<br/>Config Management<br/>Session State]
        end

        subgraph "ThreadPoolExecutor (max_workers=5)"
            T1[Thread-1<br/>Video Processor 1<br/>Memory: 128MB]
            T2[Thread-2<br/>Video Processor 2<br/>Memory: 128MB]
            T3[Thread-3<br/>Video Processor 3<br/>Memory: 128MB]
            T4[Thread-4<br/>Video Processor 4<br/>Memory: 128MB]
            T5[Thread-5<br/>Video Processor 5<br/>Memory: 128MB]
        end
    end

    subgraph "Rate Limiting (Shared)"
        RL[RateLimiter<br/>300 RPM Tracker<br/>Thread-safe counters]
    end

    subgraph "Progress Monitoring (Shared)"
        PM[ProgressMonitor<br/>Real-time updates<br/>Thread-safe state]
    end

    subgraph "Session Storage"
        SD[Session Directory<br/>Output files<br/>Manifest updates]
    end

    MT --> T1
    MT --> T2
    MT --> T3
    MT --> T4
    MT --> T5

    T1 --> RL
    T2 --> RL
    T3 --> RL
    T4 --> RL
    T5 --> RL

    T1 --> PM
    T2 --> PM
    T3 --> PM
    T4 --> PM
    T5 --> PM

    T1 --> SD
    T2 --> SD
    T3 --> SD
    T4 --> SD
    T5 --> SD

    ST -.-> RL
    ST -.-> PM

    style ST fill:#e3f2fd
    style MT fill:#f3e5f5
    style RL fill:#fff3e0
    style PM fill:#e8f5e8
```

## Component Interaction Flow

```mermaid
flowchart TD
    A[User Sets Concurrency = 5] --> B[ParallelProcessor.init()]
    B --> C[ThreadPoolExecutor(max_workers=5)]
    C --> D[RateLimiter.init(300 RPM)]
    D --> E[ProgressMonitor.init()]

    F[Video Batch Submitted] --> G[Queue Manager]
    G --> H{For each video}
    H --> I[Submit to ThreadPool]
    I --> J[Thread acquires rate limit]
    J --> K[Process video metadata]
    K --> L[Submit transcript request]
    L --> M[Poll for completion]

    M --> N{Status check}
    N -->|Completed| O[Download & save]
    N -->|Processing| P[Wait & retry]
    N -->|Failed| Q[Mark failed]

    O --> R[Update progress]
    Q --> R
    P --> M

    R --> S[Thread completes]
    S --> T[Aggregate results]
    T --> U[Return to UI]

    style A fill:#e1f5fe
    style F fill:#fff3e0
    style U fill:#e8f5e8
```