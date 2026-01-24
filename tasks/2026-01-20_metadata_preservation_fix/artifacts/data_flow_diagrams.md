# Data Flow Diagrams: YouTube Search to Bulk Transcribe Metadata Preservation

## Current Problematic Data Flow

```mermaid
sequenceDiagram
    participant User
    participant YT as YouTube Search Tool
    participant API as YouTube Data API
    participant BT as Bulk Transcribe Tool
    participant DEAPI as DEAPI Service

    User->>YT: Search for videos
    YT->>API: search_youtube(query)
    API-->>YT: SearchResult with VideoSearchItem[]
    YT->>User: Display results with metadata

    User->>YT: Select and filter videos
    YT->>YT: Extract URLs only: urls = [item.video_url for item in selected]
    YT->>BT: st.session_state['transcript_urls'] = urls

    User->>BT: Navigate to Bulk Transcribe
    BT->>BT: Parse URLs into minimal ParsedSheet
    BT->>User: Show table with empty metadata fields

    User->>BT: Start transcription
    BT->>DEAPI: Process videos (no context/metadata)
    DEAPI-->>BT: Transcripts generated
    BT->>User: Results with generic video info
```

## Current Data Structure Flow

```mermaid
flowchart TD
    A[YouTube Data API] --> B[VideoSearchItem]
    B --> C{User Selection}
    C --> D[Extract URLs Only]
    D --> E[st.session_state['transcript_urls']]
    E --> F[Bulk Transcribe Input]
    F --> G[Parse URLs to ParsedSheet]
    G --> H[Normalized Rows with Empty Fields]
    H --> I[Transcription Processing]

    style D fill:#ffcccc,stroke:#ff0000,stroke-width:2px
    style H fill:#ffcccc,stroke:#ff0000,stroke-width:2px
```

## Proposed Solution Data Flow

```mermaid
sequenceDiagram
    participant User
    participant YT as YouTube Search Tool
    participant API as YouTube Data API
    participant BT as Bulk Transcribe Tool
    participant DEAPI as DEAPI Service

    User->>YT: Search for videos
    YT->>API: search_youtube(query)
    API-->>YT: SearchResult with VideoSearchItem[]
    YT->>User: Display results with metadata

    User->>YT: Select and filter videos
    YT->>YT: Preserve full metadata: metadata = selected_video_items
    YT->>BT: st.session_state['transcript_metadata'] = metadata
    YT->>BT: st.session_state['transcript_urls'] = urls (backward compatibility)

    User->>BT: Navigate to Bulk Transcribe
    BT->>BT: Check for rich metadata input
    BT->>BT: Convert VideoSearchItem[] to ParsedSheet with full metadata
    BT->>User: Show table with complete video details

    User->>BT: Start transcription
    BT->>DEAPI: Process videos with full context
    DEAPI-->>BT: Transcripts generated
    BT->>User: Results with rich video metadata
```

## Proposed Data Structure Flow

```mermaid
flowchart TD
    A[YouTube Data API] --> B[VideoSearchItem]
    B --> C{User Selection}
    C --> D[Preserve Full Metadata]
    D --> E[st.session_state['transcript_metadata']]
    D --> F[st.session_state['transcript_urls'] - Legacy]
    E --> G{Bulk Transcribe Input Handler}
    F --> G
    G --> H{Rich Metadata Available?}
    H -->|Yes| I[Convert to ParsedSheet with Metadata]
    H -->|No| J[Parse URLs to Minimal ParsedSheet]
    I --> K[Normalized Rows with Full Fields]
    J --> L[Normalized Rows with Empty Fields]
    K --> M[Transcription Processing with Context]
    L --> M

    style D fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style I fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style K fill:#ccffcc,stroke:#00aa00,stroke-width:2px
```

## Class Diagram: Current vs Proposed

```mermaid
classDiagram
    class VideoSearchItem {
        +video_id: str
        +title: str
        +description: str
        +channel_title: str
        +channel_id: str
        +published_at: str
        +thumbnail_url: str
        +thumbnail_high_url: str
        +video_url: str
        +raw_data: Dict[str, Any]
    }

    class ParsedSheet {
        +columns: List[str]
        +rows: List[Dict[str, str]]
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

    %% Current Problem: Lossy conversion
    VideoSearchItem ..|> URL String : "Only video_url extracted"

    %% Proposed Solution: Rich conversion
    VideoSearchItem --> ParsedSheet : "Full metadata mapping"

    ColumnMapping --> ParsedSheet : "Maps columns to fields"
```

## Session State Schema Evolution

```mermaid
stateDiagram-v2
    [*] --> Current: Simple URL transfer

    state Current as "Current Session State"
    state Proposed as "Proposed Session State"

    Current --> Proposed: Add metadata preservation

    state "st.session_state['transcript_urls']: List[str]" as CurrentURLs
    state "st.session_state['transcript_metadata']: List[VideoSearchItem]" as NewMetadata
    state "st.session_state['transcript_source']: str" as NewSource

    Current --> CurrentURLs
    Proposed --> CurrentURLs: Backward compatibility
    Proposed --> NewMetadata
    Proposed --> NewSource

    note right of Proposed
        Enhanced session state
        maintains backward compatibility
        while adding rich metadata
    end note
```

## Data Transformation Pipeline

```mermaid
flowchart LR
    subgraph "YouTube Search Tool"
        A[VideoSearchItem[]] --> B[User Selection]
        B --> C[Filter by criteria]
        C --> D[Extract for transfer]
    end

    subgraph "Data Transfer"
        D --> E[Serialize to session state]
        E --> F[st.session_state['transcript_metadata']]
        D --> G[Legacy URL extraction]
        G --> H[st.session_state['transcript_urls']]
    end

    subgraph "Bulk Transcribe Tool"
        F --> I[Deserialize from session state]
        H --> J[Legacy URL processing]
        I --> K[Convert to ParsedSheet format]
        J --> L[Convert to minimal ParsedSheet]
        K --> M[Column mapping with rich data]
        L --> N[Column mapping with empty fields]
    end

    subgraph "Processing Pipeline"
        M --> O[Normalized rows with metadata]
        N --> P[Normalized rows without metadata]
        O --> Q[Transcription with context]
        P --> Q
    end

    style F fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style K fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style M fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style O fill:#ccffcc,stroke:#00aa00,stroke-width:2px
```

## Error Handling Flow

```mermaid
flowchart TD
    A[Metadata Transfer Attempt] --> B{Metadata Available?}
    B -->|Yes| C[Validate Metadata Structure]
    B -->|No| D[Use Legacy URL Processing]

    C --> E{Metadata Valid?}
    E -->|Yes| F[Convert to ParsedSheet with Metadata]
    E -->|No| G[Log Warning + Use Legacy Processing]

    F --> H[Proceed with Rich Data]
    G --> D
    D --> I[Convert URLs to Minimal ParsedSheet]

    H --> J[Display Full Video Details]
    I --> K[Display Generic Video Info]

    J --> L[User sees complete context]
    K --> M[User sees basic URL info]

    style F fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style H fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style J fill:#ccffcc,stroke:#00aa00,stroke-width:2px
    style L fill:#ccffcc,stroke:#00aa00,stroke-width:2px
```

## Performance Impact Analysis

```mermaid
pie title Session State Size Impact
    "URLs only (current)" : 5
    "Rich metadata (proposed)" : 95
```

```mermaid
gantt
    title Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Analysis
        Architecture Analysis           :done,    analysis1, 2026-01-20, 2h
        UML Diagram Creation           :active,   analysis2, 2026-01-20, 2h
        Data Flow Documentation        :         analysis3, after analysis2, 1h

    section Design
        Solution Design                :         design1, after analysis3, 2h
        Session State Schema Design    :         design2, after design1, 1h
        Backward Compatibility Plan    :         design3, after design2, 1h

    section Implementation
        YouTube Search Tool Changes    :         impl1, after design3, 2h
        Bulk Transcribe Tool Changes   :         impl2, after impl1, 3h
        Metadata Serialization Logic   :         impl3, after impl2, 1h

    section Testing
        Unit Tests                     :         test1, after impl3, 1h
        Integration Tests              :         test2, after test1, 2h
        User Acceptance Tests          :         test3, after test2, 1h

    section Documentation
        Code Documentation Updates     :         docs1, after test3, 1h
        User Guide Updates             :         docs2, after docs1, 1h
        Task Archive                   :         docs3, after docs2, 0.5h
```