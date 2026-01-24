# Bulk Transcribe

A multipage web app for YouTube content processing with two main tools:

1. **📝 Bulk Transcribe** - Process spreadsheets or URL lists to generate transcripts from YouTube videos and podcasts
2. **🔍 YouTube Search** - Search YouTube and select videos for bulk transcription

Both tools generate organized Obsidian-friendly Markdown files into per-run session folders under `./output/sessions/`.

## Tool 1: 📝 Bulk Transcribe

Upload a spreadsheet (TSV/CSV/XLSX) or URL list (.txt) containing YouTube and podcast rows, generates transcripts, and saves organized Obsidian-friendly Markdown files.

**Features:**
- **Input Methods:**
  - Upload spreadsheets with columns: `source_type`, `youtube_url`, `mp3_url`
  - Upload simple `.txt` files with one URL per line
  - Direct URL pasting
- **Processing:**
  - **YouTube**: Captures rich metadata via `yt-dlp`, tries captions first; falls back to DEAPI `vid2txt`
  - **Podcast**: Downloads MP3, uploads to DEAPI `audiofile2txt`
- **Output:** One `.md` transcript file per item + `manifest.json` + `items.csv` under `output/sessions/session_YYYYMMDD_HHMMSS/`

## Tool 2: 🔍 YouTube Search (Phase 1)

Search YouTube using the Data API v3 and select videos for bulk transcription.

**Features:**
- **Search Capabilities:**
  - Full-text search with advanced filters
  - Date range filtering
  - HD video filter, captions filter
  - Region and language preferences
  - Sort by relevance, date, views, or rating
- **AI-Powered Filtering:**
  - Optional AI filtering based on research context
  - Choose from OpenAI GPT-4o-mini or Anthropic Claude-Haiku models
  - Automatic relevance evaluation of video metadata
  - Shortlisted results for more targeted transcription
- **Results Display:**
  - Always-visible results table with thumbnails
  - Pagination support (next/previous pages)
  - Video metadata display (title, channel, date, description)
  - Tabbed view for All Results vs AI-Shortlisted Results
- **Actions:**
  - Copy selected/all URLs to clipboard
  - Copy video IDs as CSV
  - Export results as JSON
  - Direct integration with Bulk Transcribe tool
- **Phase 2 Preview:** AI agent mode for automated research workflows (coming soon)

## Setup

### 1) Create virtual environment (recommended)

Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

Windows PowerShell (with venv activated):
```powershell
python -m pip install -r requirements.txt
```

Or if venv not activated:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3) Set API keys

**Required for transcription (DEAPI):**
```env
DEAPI_API_KEY=your_deapi_api_key_here
```

**Required for YouTube search:**
```env
YOUTUBE_DATA_API_KEY=your_youtube_data_api_key_here
```

**Required for AI video filtering:**
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**Option A: Use `.env` file (recommended)**

Create a `.env` file in the project root with all API keys:
```
DEAPI_API_KEY=your_deapi_api_key_here
YOUTUBE_DATA_API_KEY=your_youtube_data_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

The app will automatically load environment variables from `.env`.

**Option B: Environment variables**

Windows PowerShell:
```powershell
$env:DEAPI_API_KEY="YOUR_DEAPI_KEY_HERE"
$env:YOUTUBE_DATA_API_KEY="YOUR_YOUTUBE_KEY_HERE"
$env:OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY_HERE"
```

### 4) Run the app

Windows PowerShell (with venv activated):
```powershell
streamlit run app.py
```

Or:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The app will open with a main menu. Navigate between:
- **📝 Bulk Transcribe** - Process URLs from spreadsheets or lists
- **🔍 YouTube Search** - Search YouTube and select videos for transcription

### 5) Run tests

Windows PowerShell:
```powershell
.\.venv\Scripts\python.exe test_e2e.py
```

### Getting OpenRouter API Key

To use AI video filtering, you need an OpenRouter API key:

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Add credits to your account (starts with free credits)
4. Copy your API key from the dashboard

**Model Recommendations:**
- **OpenAI GPT-4o-mini**: Default choice - fast, cost-effective, good performance
- **Anthropic Claude-Haiku-4.5**: Alternative option - good performance, different reasoning style

## AI Video Filtering Guide

The YouTube Search tool includes optional AI-powered filtering to help you find the most relevant videos for your research.

### How It Works

1. **Enter Research Context**: Describe your research goal or topic in the text area
2. **Enable AI Filtering**: Check the "🤖 Enable AI Filtering" box
3. **Choose Model**: Select from available AI models (defaults to GPT-4o-mini)
4. **Search YouTube**: Perform your search as usual
5. **Filter with AI**: Click "🤖 Filter Videos with AI" to let AI evaluate relevance
6. **Review Results**: View filtered results in the "Shortlisted Results" tab

### Example Research Contexts

```
"Find videos about AI entrepreneurship and startup strategies for building AI companies in 2026"
```

```
"Content about machine learning deployment, MLOps, and production AI systems"
```

```
"Interviews and talks about the future of work, automation, and AI's impact on jobs"
```

### Tips for Better Filtering

- **Be Specific**: More detailed context leads to better filtering results
- **Include Keywords**: Mention key terms you want the AI to prioritize
- **Context Matters**: The AI evaluates video titles, descriptions, and channels
- **Iterate**: You can refine your context and filter again

### Cost Considerations

- AI filtering uses OpenRouter API calls
- Cost depends on model and text length
- GPT-4o-mini is typically the most cost-effective option
- Free OpenRouter credits are usually sufficient for moderate usage

## Advanced Features

### Pre-Validation (Recommended for Large Lists)

The bulk transcribe tool includes an optional pre-validation step that checks video availability before attempting expensive transcription:

- **When to use**: For large video lists (>20 videos) to avoid wasting time on inaccessible content
- **How it works**: Uses official YouTube Data API to check privacy status and availability
- **Benefits**: Filters out private, deleted, or region-restricted videos early using official API
- **API Usage**: ~1 quota unit per video (YouTube API cost) but saves DEAPI transcription costs
- **Trade-off**: Uses YouTube API quota but prevents failed transcription attempts

**Pre-validation catches these issues:**
- **Private videos**: Videos set to private by owner
- **Deleted videos**: Videos that have been removed
- **Not found**: Videos that don't exist or are inaccessible
- **API errors**: Temporary YouTube API issues

### Error Recovery & Retry Logic

The system now includes intelligent error handling:

- **Rate-limited requests**: Automatic retry with exponential backoff
- **Network issues**: Retry with increasing delays
- **Permanent failures**: Clear categorization (private videos, API quota, etc.)
- **Progress persistence**: Session status saved during processing

## Troubleshooting

### Bulk Transcription Issues

**"Many videos failing with 'Video unavailable'"**
- Enable pre-validation to filter out inaccessible videos before transcription
- Pre-validation uses official YouTube API to check privacy status
- Filters out: private videos, deleted videos, region-restricted content

**"Pre-validation shows API errors"**
- Ensure YOUTUBE_DATA_API_KEY is set correctly
- Check YouTube API quota hasn't been exceeded
- Pre-validation requires both DEAPI_API_KEY and YOUTUBE_DATA_API_KEY

**"Getting rate limited during transcription"**
- The system now automatically retries rate-limited requests with exponential backoff
- If persistent, wait 10-15 minutes and retry failed videos
- Consider upgrading DEAPI plan for higher limits
- Pre-validation uses additional YouTube API quota (~1 unit per video)

### AI Filtering Issues

**"Empty response from OpenRouter API"**
- Check your `OPENROUTER_API_KEY` in `.env` file
- Verify your OpenRouter account has credits
- Try a different model (some require special access)
- Run the test script: `python test_openrouter.py`

**"Model not found"**
- The selected model may not be available
- Try: `openai/gpt-4o-mini`, `anthropic/claude-haiku-4.5`, or `meta-llama/llama-3.2-3b-instruct`

**"Rate limit exceeded"**
- Wait a few minutes and try again
- Switch to a different model
- Check your OpenRouter account limits

**Getting OpenRouter API Key:**
1. Visit [https://openrouter.ai/](https://openrouter.ai/)
2. Sign up for an account
3. Add credits to your account (free credits available)
4. Copy your API key to `.env` file

## Input File Formats

- **`.txt`** - Simple URL list (one YouTube URL per line, blank lines ignored)
- **`.csv`** / **`.tsv`** - Spreadsheet with columns
- **`.xlsx`** - Excel file

The app auto-detects `.txt` files and converts them to the expected format. For spreadsheets, it includes a column mapping UI so your headers don't need to match exactly.

## Quick Start

See `QUICKSTART.md` for step-by-step instructions.

**TL;DR:**
```powershell
.\run_app.ps1
```
Then upload your `.txt` file with YouTube URLs (one per line).

## Env template

This workspace blocks dotfiles (like `.env.example`), so the env template is stored as `env.example`.

