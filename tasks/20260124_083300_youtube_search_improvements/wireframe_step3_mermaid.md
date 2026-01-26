# Mermaid Diagrams: Step 3 Layout Structure

## Component Hierarchy

```mermaid
graph TD
    A[Step 3: Planned Query Results] --> B[Run Summary Section]
    A --> C[Query Navigation Section]
    A --> D[Status Strip Section]
    A --> E[Results Table Section]
    A --> F[Pagination & Controls Section]
    
    B --> B1[Total Queries Card]
    B --> B2[Completed Card]
    B --> B3[Total Results Card]
    B --> B4[Deduplicated Card]
    B --> B5[Status Breakdown]
    B --> B6[Last Updated]
    
    C --> C1[All Results Tab]
    C --> C2[Query 1 Tab]
    C --> C3[Query 2 Tab]
    C --> C4[Query N Tab]
    C --> C5[More Queries Dropdown]
    
    D --> D1[Query Name]
    D --> D2[Status Badge]
    D --> D3[Results Count]
    D --> D4[Pages Count]
    D --> D5[Error/Warning Messages]
    D --> D6[Retry Button]
    
    E --> E1[Selection Controls]
    E --> E2[Table Header]
    E --> E3[Table Rows]
    E --> E4[Scroll Container]
    
    E2 --> E2A[Checkbox Column]
    E2 --> E2B[Thumbnail Column]
    E2 --> E2C[Title Column]
    E2 --> E2D[Channel Column]
    E2 --> E2E[Date Column]
    E2 --> E2F[Duration Column]
    E2 --> E2G[Views Column]
    E2 --> E2H[Query Source Column - All Results Only]
    
    F --> F1[Pagination Controls]
    F --> F2[Export Actions]
    F --> F3[Bulk Actions]
    F --> F4[Cap Warning]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e8f5e9
    style D fill:#f3e5f5
    style E fill:#fff9c4
    style F fill:#e0f2f1
```

## User Flow: Tab Navigation

```mermaid
flowchart LR
    Start[User Arrives at Step 3] --> Default[All Results Tab Active]
    
    Default --> ViewAll[View Deduplicated Results<br/>98 videos from 4 queries]
    
    ViewAll --> ClickTab1[Click Query 1 Tab]
    ViewAll --> ClickTab2[Click Query 2 Tab]
    ViewAll --> ClickTabN[Click Query N Tab]
    
    ClickTab1 --> ViewQ1[View Query 1 Results<br/>45 videos]
    ClickTab2 --> ViewQ2[View Query 2 Results<br/>32 videos]
    ClickTabN --> ViewQN[View Query N Results]
    
    ViewQ1 --> SelectVideos[Select Videos]
    ViewQ2 --> SelectVideos
    ViewQN --> SelectVideos
    
    SelectVideos --> Export[Export Selected]
    SelectVideos --> BulkTranscribe[Send to Bulk Transcribe]
    SelectVideos --> AIFilter[AI Filter Selected]
    
    ViewQ1 --> BackToAll[Click All Results]
    ViewQ2 --> BackToAll
    ViewQN --> BackToAll
    
    BackToAll --> ViewAll
    
    style Default fill:#4caf50,color:#fff
    style ViewAll fill:#81c784
    style ViewQ1 fill:#64b5f6
    style ViewQ2 fill:#64b5f6
    style ViewQN fill:#64b5f6
    style SelectVideos fill:#ffb74d
```

## State Machine: Query Status Transitions

```mermaid
stateDiagram-v2
    [*] --> Queued: Query Added
    Queued --> Running: Execution Starts
    Running --> Completed: Success
    Running --> Failed: Error Occurs
    Running --> NoResults: Zero Videos Returned
    Failed --> Queued: Retry Clicked
    Completed --> [*]: User Views Results
    NoResults --> [*]: User Views Empty State
    Failed --> [*]: User Dismisses Error
```

## Data Flow: Results Aggregation

```mermaid
flowchart TD
    Q1[Query 1 Results<br/>45 videos] --> Dedup[Deduplication Engine]
    Q2[Query 2 Results<br/>32 videos] --> Dedup
    Q3[Query 3 Results<br/>28 videos] --> Dedup
    Q4[Query 4 Results<br/>22 videos] --> Dedup
    
    Dedup --> AllResults[All Results View<br/>98 unique videos]
    
    Q1 --> Q1Tab[Query 1 Tab<br/>45 videos]
    Q2 --> Q2Tab[Query 2 Tab<br/>32 videos]
    Q3 --> Q3Tab[Query 3 Tab<br/>28 videos]
    Q4 --> Q4Tab[Query 4 Tab<br/>22 videos]
    
    AllResults --> Summary[Summary Cards<br/>Total: 127<br/>Dedup: 98]
    
    Q1Tab --> UserAction1[User Actions]
    Q2Tab --> UserAction1
    Q3Tab --> UserAction1
    Q4Tab --> UserAction1
    AllResults --> UserAction1
    
    UserAction1 --> Export[Export]
    UserAction1 --> Transcribe[Bulk Transcribe]
    UserAction1 --> Filter[AI Filter]
    
    style Dedup fill:#ff9800,color:#fff
    style AllResults fill:#4caf50,color:#fff
    style Summary fill:#2196f3,color:#fff
```

## Layout Grid Structure

```mermaid
graph TB
    subgraph "Step 3 Container (100% width)"
        subgraph "Row 1: Summary (100% width)"
            S1[Card 1: Total Queries<br/>25% width]
            S2[Card 2: Completed<br/>25% width]
            S3[Card 3: Total Results<br/>25% width]
            S4[Card 4: Deduplicated<br/>25% width]
        end
        
        subgraph "Row 2: Navigation (100% width)"
            N1[All Results Tab]
            N2[Query 1 Tab]
            N3[Query 2 Tab]
            N4[Query N Tab]
            N5[More Dropdown]
        end
        
        subgraph "Row 3: Status Strip (100% width)"
            ST[Status Information Bar]
        end
        
        subgraph "Row 4: Table (100% width, scrollable)"
            T[Results Table<br/>Max Height: 400px]
        end
        
        subgraph "Row 5: Controls (100% width)"
            C1[Pagination]
            C2[Export Actions]
            C3[Bulk Actions]
        end
    end
    
    style S1 fill:#e3f2fd
    style S2 fill:#e8f5e9
    style S3 fill:#fff3e0
    style S4 fill:#f3e5f5
    style N1 fill:#4caf50,color:#fff
    style ST fill:#fff9c4
    style T fill:#f5f5f5
```

## Table Column Layout Comparison

```mermaid
graph LR
    subgraph "All Results View"
        A1[☑<br/>5%]
        A2[Thumbnail<br/>10%]
        A3[Title<br/>30%]
        A4[Channel<br/>12%]
        A5[Date<br/>10%]
        A6[Duration<br/>8%]
        A7[Views<br/>10%]
        A8[Query Source<br/>15%]
    end
    
    subgraph "Single Query View"
        B1[☑<br/>5%]
        B2[Thumbnail<br/>12%]
        B3[Title<br/>35%]
        B4[Channel<br/>15%]
        B5[Date<br/>12%]
        B6[Duration<br/>10%]
        B7[Views<br/>11%]
    end
    
    style A8 fill:#ff9800,color:#fff
```

## Error State Flow

```mermaid
flowchart TD
    QueryRunning[Query Running] --> CheckResult{Result?}
    
    CheckResult -->|Success| ShowResults[Show Results Table]
    CheckResult -->|Rate Limit| ShowRateLimit[Show Rate Limit Error]
    CheckResult -->|API Error| ShowAPIError[Show API Error]
    CheckResult -->|Zero Results| ShowZeroResults[Show Zero Results Placeholder]
    
    ShowRateLimit --> RetryOption{User Action?}
    ShowAPIError --> RetryOption
    ShowZeroResults --> EditOption{User Action?}
    
    RetryOption -->|Click Retry| RetryQuery[Retry Query]
    RetryOption -->|Dismiss| DismissError[Mark as Failed]
    
    EditOption -->|Edit Query| EditQuery[Return to Step 2]
    EditOption -->|Dismiss| DismissError
    
    RetryQuery --> QueryRunning
    DismissError --> ShowFailedState[Show Failed State in Tab]
    ShowResults --> UserActions[User Can Select/Export]
    
    style ShowRateLimit fill:#ffcdd2
    style ShowAPIError fill:#ffcdd2
    style ShowZeroResults fill:#fff9c4
    style ShowResults fill:#c8e6c9
```
