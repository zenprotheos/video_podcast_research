# Comprehensive System Architecture Analysis
## DEAPI Requests Import Error - Complete System View

```mermaid
graph TB
    subgraph "Windows OS Layer"
        A[PowerShell Process] --> B[run_app.ps1 Script]
        B --> C[Process Environment Variables]
        C --> D[System PATH]
        D --> E[Python Executable Resolution]
    end

    subgraph "Python Runtime Layer"
        F[python.exe Entry Point] --> G[Streamlit Module Import]
        G --> H[App.py Execution]
        H --> I[Page Import Chain]
        I --> J[Transcription Logic]
    end

    subgraph "Virtual Environment Context"
        K[.venv Directory] --> L[Scripts/python.exe]
        L --> M[site-packages/]
        M --> N[requests-2.32.5.dist-info/]
        N --> O[requests Module Files]
    end

    subgraph "Import Failure Points"
        P[sys.path Resolution] --> Q[Module Search Path]
        Q --> R[Import System Caching]
        R --> S[Namespace Conflicts]
        S --> T[Execution Context Isolation]
    end

    A --> F
    E --> L
    J --> P
    M --> Q

    style P fill:#f8d7da
    style Q fill:#f8d7da
    style R fill:#f8d7da
    style S fill:#f8d7da
    style T fill:#f8d7da
```

## Process Execution Flow Analysis

```mermaid
sequenceDiagram
    participant PS as PowerShell
    participant Script as run_app.ps1
    participant Py as python.exe
    participant SL as Streamlit
    participant App as app.py
    participant Page as pages/1_*.py
    participant YT as youtube_transcript.py

    PS->>Script: Execute .\run_app.ps1
    Script->>Script: Check .venv exists
    Script->>Py: & .\.venv\Scripts\python.exe -m streamlit run app.py
    Py->>SL: Import streamlit module
    SL->>App: Execute app.py
    App->>Page: User navigates to Bulk Transcribe
    Page->>YT: Process URLs - get_youtube_transcript()
    YT->>YT: try_youtube_captions() fails
    YT->>YT: try_deapi_transcription() called
    YT->>YT: import requests (LINE 90)

    Note over YT: NameError: name 'requests' is not defined

    YT-->>Page: Return failed result
    Page-->>App: Display error
```

## Environment Context Boundaries

```mermaid
graph TD
    subgraph "System Global Context"
        A1[SYSTEM PATH] --> B1[PYTHONPATH]
        B1 --> C1[Conda Environment Hooks]
        C1 --> D1[System Python Installations]
    end

    subgraph "Process Context (PowerShell)"
        E1[Process Environment] --> F1[Current Directory]
        F1 --> G1[Working Directory Context]
    end

    subgraph "Virtual Environment Context"
        H1[.venv Activation State] --> I1[PYTHONHOME Override]
        I1 --> J1[site.py Execution]
        J1 --> K1[sys.path Modification]
        K1 --> L1[Module Search Path Update]
    end

    subgraph "Streamlit Execution Context"
        M1[Streamlit Process] --> N1[Module Import Isolation]
        N1 --> O1[Thread/Async Execution]
        O1 --> P1[Subprocess Creation]
        P1 --> Q1[Context Loss Points]
    end

    subgraph "Import Failure Context"
        R1[Local Function Scope] --> S1[import requests Statement]
        S1 --> T1[Module Resolution Failure]
        T1 --> U1[NameError Exception]
    end

    A1 --> E1
    E1 --> H1
    H1 --> M1
    M1 --> R1

    style Q1 fill:#f8d7da
    style T1 fill:#f8d7da
    style U1 fill:#f8d7da
```

## Module Loading Sequence Analysis

```mermaid
stateDiagram-v2
    [*] --> PowerShell_Execution
    PowerShell_Execution --> Script_Validation: Check .venv exists
    Script_Validation --> Python_Launch: & .\.venv\Scripts\python.exe
    Python_Launch --> VirtualEnv_Activation: site.py executes
    VirtualEnv_Activation --> Streamlit_Import: import streamlit
    Streamlit_Import --> App_Execution: app.py runs
    App_Execution --> Page_Load: User interaction
    Page_Load --> Transcription_Call: get_youtube_transcript()
    Transcription_Call --> Function_Entry: try_deapi_transcription()
    Function_Entry --> Import_Attempt: import requests (line 90)

    Import_Attempt --> Module_Resolution: Check sys.modules
    Module_Resolution --> Path_Search: Search sys.path
    Path_Search --> Cache_Check: Check import cache
    Cache_Check --> Load_Attempt: Load requests module

    Load_Attempt --> Context_Check: Verify execution context
    Context_Check --> Failure_Point: Context isolation issue
    Failure_Point --> NameError_Raised: name 'requests' is not defined

    NameError_Raised --> Exception_Handling: Error propagation
    Exception_Handling --> User_Display: Show error in UI

    note right of Failure_Point : This is where the error occurs
    note right of Context_Check : Virtual env context lost?

    style Failure_Point fill:#f8d7da
    style NameError_Raised fill:#f8d7da
```

## Streamlit Internal Architecture

```mermaid
graph TB
    subgraph "Streamlit Server Process"
        A[Main Process] --> B[Web Server Thread]
        A --> C[Script Runner Thread]
        A --> D[File Watcher Thread]
    end

    subgraph "Script Execution Context"
        E[Script Runner] --> F[Module Import Phase]
        F --> G[Code Execution Phase]
        G --> H[Widget Update Phase]
    end

    subgraph "Execution Isolation Points"
        I[Thread Boundaries] --> J[Import Context Loss]
        J --> K[Module Namespace Isolation]
        K --> L[Virtual Environment Leakage]
    end

    subgraph "Failure Scenarios"
        M[Direct Execution] --> N[Module Available ✓]
        O[Threaded Execution] --> P[Module Missing ✗]
        P --> Q[Context Not Inherited]
        Q --> R[Import Fails]
    end

    C --> E
    G --> I
    I --> O

    style P fill:#f8d7da
    style Q fill:#f8d7da
    style R fill:#f8d7da
```

## Root Cause Hypothesis Matrix

| Hypothesis | Evidence | Test Method | Likelihood |
|------------|----------|-------------|------------|
| **Virtual Environment Context Loss** | run_app.ps1 uses correct path, but error still occurs | Check sys.executable in failing context | High |
| **Streamlit Thread Isolation** | Import happens in function scope within Streamlit execution | Test import in different thread contexts | High |
| **Module Caching Conflict** | Previous imports or cached modules interfering | Clear import cache and test | Medium |
| **PATH Resolution Issue** | Conda hooks interfering with executable resolution | Check PATH order and resolution | Medium |
| **Streamlit Configuration Override** | Streamlit configured to use different Python | Check .streamlit/config.toml | Low |

## Detailed Investigation Plan

```mermaid
mindmap
  root((Root Cause Investigation))
    Process Analysis
      PowerShell execution context
      Virtual environment activation
      Python executable resolution
    Streamlit Architecture
      Multi-threading model
      Module import isolation
      Execution context boundaries
    Import System Deep Dive
      sys.path manipulation
      Module caching behavior
      Namespace resolution
    Environment Interactions
      Conda hook interference
      PATH precedence issues
      Environment variable inheritance
    Failure Reproduction
      Minimal test case creation
      Context isolation testing
      Step-by-step execution tracing
```