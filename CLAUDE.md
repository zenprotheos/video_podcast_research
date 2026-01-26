# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

### Quick Start
```powershell
.\run_app.ps1
```

### Manual Start (PowerShell with venv activated)
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

### First-Time Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Set up environment variables - create .env file with:
# DEAPI_API_KEY=your_key
# YOUTUBE_DATA_API_KEY=your_key
# OPENROUTER_API_KEY=your_key (for AI video filtering)
```

### Environment Variables
- `.env` file is used (see `env.example` for template)
- Required keys: `DEAPI_API_KEY`, `YOUTUBE_DATA_API_KEY`, `OPENROUTER_API_KEY`
- Dotfiles are blocked in workspace, so template is stored as `env.example`

## Testing

### Run Full Test Suite
```powershell
.\.venv\Scripts\python.exe -m pytest
```

### Run Specific Test
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_specific.py::test_name
```

### Test OpenRouter Integration
```powershell
python test_openrouter.py
```

## Project Architecture

### Entry Points
- **Main menu**: `app.py` - Routes to the search and transcription tools
- **YouTube Search**: `pages/01_YouTube_Search.py` - Search and filter videos, then send metadata/URLs to the current transcript workflow
- **Bulk Transcribe (Proxy)**: `pages/03_Bulk_Transcribe_Proxy.py` - The canonical transcript processor that uses residential proxies; YouTube Search is expected to hand off packets of selected videos here
- **Legacy Bulk Transcribe** (for reference only): `pages/02_Bulk_Transcribe.py` - Previous transcript page that still exists but is no longer the target for new automation
### Canonical Flow
YouTube Search → Store `transcript_urls`/`transcript_metadata` in `st.session_state` → `pages/03_Bulk_Transcribe_Proxy.py` consumes this data (rich metadata preferred) and runs the proxy-powered transcription pipeline.

### Core Modules (`src/bulk_transcribe/`)

#### Input Processing
- **`sheet_ingest.py`**: Parse spreadsheets (CSV/TSV/XLSX) and plain text URL lists
  - `ParsedSheet` dataclass for normalized input
  - Supports auto-detection of `.txt` files with one URL per line
  - Column mapping for flexible spreadsheet formats

#### Session Management
- **`session_manager.py`**: Create and manage output sessions
  - `SessionManager`: Organizes output into timestamped folders under `output/sessions/`
  - Creates `manifest.json` (session metadata) and `items.csv` (processing results)
  - Separates YouTube and podcast outputs into subdirectories

#### Transcript Extraction
- **`youtube_transcript.py`**: Extract from YouTube captions
  - Uses `youtube-transcript-api` first, falls back to DEAPI if needed
  - Fetches available captions, prioritizes English
- **`proxy_transcript.py`**: DEAPI video-to-text extraction with proxy support
  - Uses DEAPI's `/vid2txt` endpoint for videos without captions
  - Supports proxy configuration for geographic restrictions
- **`youtube_metadata.py`**: Rich metadata from videos
  - Uses `yt-dlp` to fetch video info (title, duration, channel, etc.)
  - Cached metadata for repeated lookups

#### Video Processing
- **`video_filter.py`**: Pre-validation using YouTube Data API v3
  - Checks video availability (public/private/deleted status) before transcription
  - Filters private and inaccessible videos early to save DEAPI quota
- **`query_planner.py`**: Generate distinct search queries
  - Uses OpenRouter API to create variant queries for YouTube search
  - Enables broader search result coverage
- **`parallel_processor.py`**: Thread-safe concurrent processing
  - `ThreadPoolExecutor` wrapper with rate limiting
  - Configurable worker count for UI control

#### Output & Utilities
- **`transcript_writer.py`**: Generate Obsidian-formatted Markdown
  - Creates readable transcript files with metadata headers
  - Organizes output per session
- **`metadata_transfer.py`**: Manage metadata across processing steps
- **`direct_input.py`**: Handle direct URL input (UI-driven)
- **`utils.py`**: Shared utilities (URL validation, formatting, etc.)

### Data Flow

1. **User Input** → `sheet_ingest` (parse file) → normalized rows
2. **Optional Pre-validation** → `video_filter` (check availability) → filtered rows
3. **Parallel Processing** → `parallel_processor` (concurrent workers)
4. **Per-Item Processing**:
   - Extract metadata via `youtube_metadata` (yt-dlp)
   - Extract transcript via `youtube_transcript` (captions)
   - Fallback to `proxy_transcript` (DEAPI) if needed
5. **Output** → `transcript_writer` (Markdown) + `session_manager` (manifest/CSV)
6. **Results** → `output/sessions/session_YYYYMMDD_HHMMSS/`

### Output Structure
```
output/sessions/session_20260125_143000/
├── manifest.json          # Session metadata & item tracking
├── items.csv              # Processing results (URL, status, path)
├── youtube/
│   ├── video_title_1.md   # Transcript markdown
│   ├── video_title_2.md
│   └── ...
└── podcasts/
    ├── episode_title_1.md
    ├── episode_title_2.md
    ├── audio/
    │   ├── download_1.mp3 # Downloaded MP3s
    │   └── ...
    └── ...
```

## Repository Standards

### Import Organization
Follows PEP 8 with these rules (see `docs/standards/import_standards.md`):
- Group imports: stdlib → third-party → local
- One import per line, alphabetical within groups
- Module-level imports preferred (avoid function-level unless necessary for heavy libraries)
- Local imports use relative paths: `from .module import func`

### Key Import Pattern
```python
# Local imports in pages and modules
from src.bulk_transcribe.session_manager import SessionManager
from src.bulk_transcribe.sheet_ingest import parse_spreadsheet
```

### Workflow Organization
- **Core work**: `src/bulk_transcribe/` modules
- **Tasks**: `tasks/` (task-centric org per `AGENT.md`)
- **Specs**: `docs/specs/` (source of truth for features)
- **Standards**: `docs/standards/` (like import_standards.md)
- **No ad-hoc work** in repo root (see `.cursor/rules/00-core.mdc`)

### Code Quality
- No emojis in code (only UI text)
- Syntax validation required (Python -m py_compile)
- Indentation checked before commit
- Type hints encouraged but not required for existing code

## Key Dependencies
- **streamlit** (1.32+): Web UI framework
- **youtube-transcript-api** (1.0+): YouTube caption extraction
- **yt-dlp** (2024.12+): Video metadata & fallback extraction
- **requests** (2.31+): HTTP requests
- **pandas** (2.0+): Data processing
- **google-api-python-client** (2.100+): YouTube Data API v3
- **openpyxl** (3.1+): Excel file parsing
- **python-dotenv** (1.0+): Environment variable loading

## Important Files & Configs
- `.env`: API keys (not in repo, use `env.example`)
- `.cursor/rules/00-core.mdc`: Authoritative core rules
- `AGENT.md`: Agent-specific operating rules
- `run_app.ps1`: PowerShell launcher script
- `env.example`: Template for environment variables (blocked dotfiles workaround)

## UI Workflows

### YouTube Search (01_YouTube_Search.py)
1. Enter search query and filters (date range, HD, captions, etc.)
2. Optional: Enable AI filtering with research context
3. Click "Search YouTube"
4. Review results in always-visible table with pagination
5. Actions: Copy URLs, Export JSON, Direct to Bulk Transcribe

### Bulk Transcribe (02_Bulk_Transcribe.py)
1. Upload file (CSV/TSV/XLSX or `.txt` URL list)
2. Map columns to: `source_type`, `youtube_url`, `mp3_url`
3. Optional: Pre-validate videos (checks availability via YouTube API)
4. Optional: Enable parallel processing (configure worker count)
5. Click "Start session"
6. Track progress in real-time
7. Results: Markdown transcripts + manifest + items.csv

## Debugging

### Verbose Logging
Check `.claude` directory for session logs. Debug mode captures stack traces and API responses.

### Common Issues
- **"Video unavailable"**: Enable pre-validation to filter early
- **Rate limited**: System auto-retries with exponential backoff
- **Missing transcripts**: Check video has captions or DEAPI quota available
- **Empty OpenRouter response**: Verify OPENROUTER_API_KEY and account credits

See `DEBUG.md` and `README.md` for detailed troubleshooting.

