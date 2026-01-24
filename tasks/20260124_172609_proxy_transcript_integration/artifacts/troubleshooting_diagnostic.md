# Troubleshooting: Proxy Transcript Integration Failure

## Problem Statement

- Quick test script: **WORKS** (11,522 chars extracted)
- Streamlit page integration: **FAILS** (0/14 success, "No captions available")
- Same videos, same extractor code, different results

## Investigation Results

### Diagnostic Test (2026-01-24 17:36)

All tests PASSED from command line:
- Health check: 100 proxies loaded
- Video RE_NqKDKmqM: 11,522 chars extracted
- Video SYddTshkgZk (from user's failed list): 663 chars extracted

This proves:
1. The extractor code works correctly
2. The proxy configuration is valid
3. The videos DO have captions

### Root Cause Hypothesis

The Streamlit context has some difference that causes extraction to fail. Possible causes:

1. **Working Directory Issue**
   - Command line: Explicitly `os.chdir(project_root)`
   - Streamlit: May run from different CWD

2. **Environment Variable Timing**
   - The singleton might be created before .env is loaded

3. **Module State Corruption**
   - The singleton extractor might get into a bad state

## Debug Output Added

Added `[PROXY_DEBUG]` and `[EXTRACTOR_DEBUG]` print statements to:
- `src/bulk_transcribe/proxy_transcript.py`
- `src/bulk_transcribe/paid_proxy_extractor.py`

These will print to the Streamlit console (terminal where `streamlit run` is executed).

## Next Steps for User

1. Restart Streamlit (`streamlit run app.py`)
2. Navigate to "Bulk Transcribe Proxy" page
3. Run a test with 1-2 videos
4. Check the terminal output for `[PROXY_DEBUG]` and `[EXTRACTOR_DEBUG]` lines
5. Share the terminal output to identify the failure point

## Data Flow Diagram

```mermaid
flowchart TD
    subgraph StreamlitPage [03_Bulk_Transcribe_Proxy.py]
        A[load_dotenv] --> B[Import modules]
        B --> C[check_proxy_health in sidebar]
        C --> D[User clicks Start Session]
        D --> E[Processing loop for each video]
    end
    
    subgraph Processing [For each video]
        E --> F[fetch_youtube_metadata]
        F --> G[get_proxy_transcript]
        G --> H{Result?}
        H -->|Success| I[write_transcript_markdown]
        H -->|Fail| J[Log error]
    end
    
    subgraph ProxyTranscript [proxy_transcript.py]
        G --> K[_get_extractor singleton]
        K --> L[PaidProxyYouTubeExtractor.extract_transcript]
        L --> M{youtube-transcript-api}
        M -->|Success| N[Return dict with text]
        M -->|Fail| O[Fallback to manual method]
        O --> P{Manual parse}
        P -->|Success| N
        P -->|Fail| Q[Return None]
    end
```

## File Relationships

```mermaid
graph LR
    subgraph Pages
        A[03_Bulk_Transcribe_Proxy.py]
    end
    
    subgraph src/bulk_transcribe
        B[proxy_transcript.py]
        C[paid_proxy_extractor.py]
        D[youtube_transcript.py]
    end
    
    subgraph External
        E[youtube-transcript-api]
        F[WebShare Proxies]
    end
    
    A --> B
    B --> C
    B --> D
    C --> E
    C --> F
    
    D -.->|TranscriptResult dataclass| B
```
