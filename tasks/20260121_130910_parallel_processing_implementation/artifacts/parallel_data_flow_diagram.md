# Parallel Data Flow Diagram

## High-Level Data Flow

```mermaid
flowchart TD
    subgraph "Input Processing"
        UI[User Input<br/>Video URLs + Config]
        CFG[Configuration<br/>max_concurrent=5<br/>rate_limit=300]
        VS[Video Source<br/>CSV/TSV/Text Input]
    end

    subgraph "Queue Management"
        QM[Queue Manager<br/>Distributes videos<br/>to threads]
        PB[Processing Batch<br/>List[VideoItem]]
    end

    subgraph "Parallel Execution Engine"
        TPE[ThreadPoolExecutor<br/>max_workers=5]
        RL[Rate Limiter<br/>Distributed 300 RPM]

        subgraph "Worker Threads"
            W1[Worker 1<br/>Thread-1]
            W2[Worker 2<br/>Thread-2]
            W3[Worker 3<br/>Thread-3]
            W4[Worker 4<br/>Thread-4]
            W5[Worker 5<br/>Thread-5]
        end
    end

    subgraph "Individual Processing Pipeline"
        MD[Metadata Fetch<br/>YouTube API]
        TR[Transcript Request<br/>deAPI Submit]
        POLL[Status Polling<br/>deAPI Check]
        DL[Download Results<br/>deAPI Fetch]
        SAVE[Save Files<br/>Markdown + JSON]
    end

    subgraph "Progress & State Management"
        PM[Progress Monitor<br/>Thread-safe updates]
        SM[Session Manager<br/>Persistence layer]
        DB[Session Database<br/>Manifest + State]
    end

    subgraph "Output & Results"
        LOG[Processing Logs<br/>Detailed status]
        FILES[Output Files<br/>Transcripts + Metadata]
        STATS[Statistics<br/>Success/Failure counts]
    end

    UI --> CFG
    VS --> QM
    CFG --> QM
    QM --> PB
    PB --> TPE

    TPE --> W1
    TPE --> W2
    TPE --> W3
    TPE --> W4
    TPE --> W5

    W1 --> RL
    W2 --> RL
    W3 --> RL
    W4 --> RL
    W5 --> RL

    RL --> MD
    MD --> TR
    TR --> POLL
    POLL --> DL
    DL --> SAVE

    W1 --> PM
    W2 --> PM
    W3 --> PM
    W4 --> PM
    W5 --> PM

    PM --> SM
    SM --> DB

    SAVE --> FILES
    PM --> LOG
    PM --> STATS

    style TPE fill:#e1f5fe
    style RL fill:#fff3e0
    style PM fill:#e8f5e8
```

## Thread-Level Data Flow

```mermaid
flowchart TD
    subgraph "Thread Lifecycle"
        START[Thread Starts<br/>Video assigned]
        RATE_CHECK[Rate Limit Check<br/>acquire_permission()]
        METADATA[Fetch Metadata<br/>YouTube API call]
        SUBMIT[Submit Transcript<br/>deAPI POST request]
        POLL_LOOP{Polling Loop<br/>5-15s intervals}
        DOWNLOAD[Download Result<br/>deAPI GET request]
        SAVE_LOCAL[Save Files<br/>Local filesystem]
        COMPLETE[Mark Complete<br/>Update progress]
    end

    subgraph "Rate Limiting"
        GLOBAL_LIMIT[Global Limit<br/>300 RPM]
        THREAD_ALLOCATION[Per-Thread Limit<br/>300/5 = 60 RPM]
        THREAD_COUNTER[Thread Counter<br/>Requests this minute]
        RESET_TIMER[Reset Timer<br/>Minute boundary]
    end

    subgraph "Progress Updates"
        THREAD_STATE[Thread State<br/>Current status]
        AGGREGATE_STATS[Aggregate Stats<br/>Total progress]
        UI_CALLBACKS[UI Callbacks<br/>Real-time updates]
        SESSION_PERSIST[Session Persistence<br/>Recovery support]
    end

    START --> RATE_CHECK
    RATE_CHECK --> METADATA
    METADATA --> SUBMIT
    SUBMIT --> POLL_LOOP

    POLL_LOOP -->|Job Complete| DOWNLOAD
    POLL_LOOP -->|Still Processing| POLL_LOOP
    POLL_LOOP -->|Job Failed| ERROR_HANDLER

    DOWNLOAD --> SAVE_LOCAL
    SAVE_LOCAL --> COMPLETE

    RATE_CHECK --> GLOBAL_LIMIT
    GLOBAL_LIMIT --> THREAD_ALLOCATION
    THREAD_ALLOCATION --> THREAD_COUNTER
    THREAD_COUNTER --> RESET_TIMER

    METADATA --> THREAD_STATE
    SUBMIT --> THREAD_STATE
    POLL_LOOP --> THREAD_STATE
    DOWNLOAD --> THREAD_STATE
    SAVE_LOCAL --> THREAD_STATE
    COMPLETE --> THREAD_STATE

    THREAD_STATE --> AGGREGATE_STATS
    AGGREGATE_STATS --> UI_CALLBACKS
    AGGREGATE_STATS --> SESSION_PERSIST

    ERROR_HANDLER --> THREAD_STATE
```

## State Management Flow

```mermaid
stateDiagram-v2
    [*] --> SessionInitialization

    SessionInitialization --> ParallelConfigLoad: Load user config
    ParallelConfigLoad --> ThreadPoolCreation: Create ThreadPoolExecutor
    ThreadPoolCreation --> RateLimiterInit: Initialize distributed rate limiter
    RateLimiterInit --> ProgressMonitorInit: Initialize progress monitor

    ProgressMonitorInit --> VideoBatchLoad: Load video batch
    VideoBatchLoad --> TaskDistribution: Distribute to threads

    TaskDistribution --> ThreadProcessing: Individual threads process
    ThreadProcessing --> ProgressUpdate: Update thread progress
    ProgressUpdate --> AggregateCalculation: Calculate overall progress

    AggregateCalculation --> SessionPersistence: Save to session state
    SessionPersistence --> UIUpdate: Update Streamlit UI

    ThreadProcessing --> CompletionCheck: Check if all done
    CompletionCheck --> MoreTasks: More videos to process
    CompletionCheck --> BatchComplete: All videos processed

    MoreTasks --> TaskDistribution
    BatchComplete --> FinalAggregation: Aggregate final results
    FinalAggregation --> SessionFinalSave: Save final session state
    SessionFinalSave --> CleanupResources: Clean up threads
    CleanupResources --> [*]

    note right of ParallelConfigLoad
        max_concurrent: 5
        rate_limit_rpm: 300
        thread_timeout: 300s
    end note

    note right of ThreadProcessing
        Each thread processes one video
        Rate limited independently
        Progress updated continuously
    end note
```

## Error Handling Data Flow

```mermaid
flowchart TD
    subgraph "Error Sources"
        RATE_ERROR[Rate Limit Error<br/>429 Too Many Requests]
        NETWORK_ERROR[Network Error<br/>Connection/Timeout]
        API_ERROR[API Error<br/>Invalid request/Server error]
        SYSTEM_ERROR[System Error<br/>Thread crash/Disk full]
    end

    subgraph "Error Classification"
        CLASSIFIER[Error Classifier<br/>Categorize by type]
        RETRY_LOGIC[Retry Logic<br/>Exponential backoff]
        FAILURE_MARKER[Failure Marker<br/>Mark video as failed]
    end

    subgraph "Recovery Mechanisms"
        RATE_WAIT[Rate Limit Wait<br/>Wait for reset]
        RETRY_ATTEMPT[Retry Attempt<br/>With backoff]
        SKIP_VIDEO[Skip Video<br/>Continue batch]
    end

    subgraph "Impact Isolation"
        THREAD_ISOLATION[Thread Isolation<br/>One thread failure<br/>doesn't affect others]
        PROGRESS_CONTINUATION[Progress Continuation<br/>Batch continues]
        RESOURCE_CLEANUP[Resource Cleanup<br/>Clean thread state]
    end

    subgraph "Reporting & Logging"
        ERROR_LOGGING[Error Logging<br/>Detailed error records]
        PROGRESS_UPDATE[Progress Update<br/>Failure status]
        USER_NOTIFICATION[User Notification<br/>Error summary]
    end

    RATE_ERROR --> CLASSIFIER
    NETWORK_ERROR --> CLASSIFIER
    API_ERROR --> CLASSIFIER
    SYSTEM_ERROR --> CLASSIFIER

    CLASSIFIER --> RETRY_LOGIC
    RETRY_LOGIC --> RETRY_ATTEMPT
    RETRY_LOGIC --> FAILURE_MARKER

    RETRY_ATTEMPT --> RATE_WAIT
    RETRY_ATTEMPT --> SKIP_VIDEO

    FAILURE_MARKER --> THREAD_ISOLATION
    RATE_WAIT --> THREAD_ISOLATION
    SKIP_VIDEO --> THREAD_ISOLATION

    THREAD_ISOLATION --> PROGRESS_CONTINUATION
    PROGRESS_CONTINUATION --> RESOURCE_CLEANUP

    RESOURCE_CLEANUP --> ERROR_LOGGING
    ERROR_LOGGING --> PROGRESS_UPDATE
    PROGRESS_UPDATE --> USER_NOTIFICATION

    style RATE_ERROR fill:#ffebee
    style NETWORK_ERROR fill:#ffebee
    style API_ERROR fill:#ffebee
    style SYSTEM_ERROR fill:#ffebee

    style THREAD_ISOLATION fill:#e8f5e8
    style USER_NOTIFICATION fill:#e1f5fe
```

## Memory and Resource Management

```mermaid
graph LR
    subgraph "Memory Allocation"
        MAIN[Main Process<br/>256MB base]
        THREADS[Thread Pool<br/>128MB × 5 = 640MB]
        BUFFERS[Network Buffers<br/>64MB × 5 = 320MB]
        CACHE[Response Cache<br/>128MB shared]
    end

    subgraph "Resource Limits"
        CPU_LIMIT[CPU Limit<br/>80% max utilization]
        MEMORY_LIMIT[Memory Limit<br/>1.5GB total limit]
        NETWORK_LIMIT[Network Limit<br/>300 RPM API calls]
        DISK_LIMIT[Disk I/O Limit<br/>Concurrent file writes]
    end

    subgraph "Monitoring & Cleanup"
        MEMORY_MONITOR[Memory Monitor<br/>Per-thread usage]
        THREAD_MONITOR[Thread Monitor<br/>Active thread count]
        RESOURCE_CLEANER[Resource Cleaner<br/>Automatic cleanup]
        LEAK_DETECTOR[Leak Detector<br/>Resource leak detection]
    end

    MAIN --> CPU_LIMIT
    THREADS --> MEMORY_LIMIT
    BUFFERS --> NETWORK_LIMIT
    CACHE --> DISK_LIMIT

    CPU_LIMIT --> MEMORY_MONITOR
    MEMORY_LIMIT --> THREAD_MONITOR
    NETWORK_LIMIT --> RESOURCE_CLEANER
    DISK_LIMIT --> LEAK_DETECTOR

    MEMORY_MONITOR --> RESOURCE_CLEANER
    THREAD_MONITOR --> RESOURCE_CLEANER
    RESOURCE_CLEANER --> LEAK_DETECTOR

    style MAIN fill:#e3f2fd
    style THREADS fill:#fff3e0
    style BUFFERS fill:#e8f5e8
    style CACHE fill:#f3e5f5
```

## Configuration Data Flow

```mermaid
flowchart TD
    subgraph "User Configuration"
        CONCURRENCY_SLIDER[Concurrency Slider<br/>1-10, default=5]
        PARALLEL_TOGGLE[Parallel Toggle<br/>Enable/Disable]
        ADVANCED_SETTINGS[Advanced Settings<br/>Rate limits, timeouts]
    end

    subgraph "Configuration Validation"
        RANGE_VALIDATOR[Range Validator<br/>1 ≤ concurrency ≤ 10]
        RESOURCE_CHECKER[Resource Checker<br/>Available memory/CPU]
        RATE_CALCULATOR[Rate Calculator<br/>Effective RPM limits]
        COMPATIBILITY_CHECKER[Compatibility Checker<br/>Premium account required]
    end

    subgraph "Configuration Application"
        THREAD_POOL_CONFIG[ThreadPool Config<br/>max_workers setting]
        RATE_LIMITER_CONFIG[RateLimiter Config<br/>RPM distribution]
        PROGRESS_CONFIG[Progress Config<br/>Update intervals]
        TIMEOUT_CONFIG[Timeout Config<br/>Thread timeouts]
    end

    subgraph "Runtime Application"
        EXECUTOR_CREATION[Executor Creation<br/>ThreadPoolExecutor init]
        LIMITER_INIT[Limiter Init<br/>DistributedRateLimiter init]
        MONITOR_INIT[Monitor Init<br/>ProgressMonitor init]
        SESSION_INIT[Session Init<br/>State persistence setup]
    end

    CONCURRENCY_SLIDER --> RANGE_VALIDATOR
    PARALLEL_TOGGLE --> COMPATIBILITY_CHECKER
    ADVANCED_SETTINGS --> RATE_CALCULATOR

    RANGE_VALIDATOR --> RESOURCE_CHECKER
    RESOURCE_CHECKER --> RATE_CALCULATOR
    RATE_CALCULATOR --> COMPATIBILITY_CHECKER

    COMPATIBILITY_CHECKER --> THREAD_POOL_CONFIG
    RANGE_VALIDATOR --> RATE_LIMITER_CONFIG
    RESOURCE_CHECKER --> PROGRESS_CONFIG
    RATE_CALCULATOR --> TIMEOUT_CONFIG

    THREAD_POOL_CONFIG --> EXECUTOR_CREATION
    RATE_LIMITER_CONFIG --> LIMITER_INIT
    PROGRESS_CONFIG --> MONITOR_INIT
    TIMEOUT_CONFIG --> SESSION_INIT

    style CONCURRENCY_SLIDER fill:#e1f5fe
    style EXECUTOR_CREATION fill:#e8f5e8
```