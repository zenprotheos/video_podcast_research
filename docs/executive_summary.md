# Bulk Transcribe - Executive Summary

**Version:** 1.0  
**Last Updated:** January 2026

---

## Overview

**Bulk Transcribe** is a web-based productivity tool that combines YouTube search, AI-powered content filtering, and bulk transcript extraction into a unified workflow. It enables researchers, content creators, and knowledge workers to efficiently discover, filter, and transcribe YouTube videos at scale.

The application outputs structured, metadata-rich Markdown files optimized for knowledge management systems like Obsidian, transforming video content into searchable, organized text.

---

## Unique Selling Proposition (USP)

> **"From Search Query to Organized Transcripts in One Workflow"**

Unlike standalone transcript tools or YouTube scrapers, Bulk Transcribe offers:

1. **End-to-End Workflow** - Search, filter, and transcribe without switching tools
2. **AI-Powered Curation** - LLM-based relevance filtering to surface content that matters
3. **Zero Manual Transcription** - Three-tier extraction strategy maximizes success rate
4. **Knowledge-Ready Output** - Obsidian-formatted Markdown with rich metadata frontmatter
5. **Batch Processing** - Parallel processing handles hundreds of videos efficiently

---

## Core Value Proposition

```
+-------------------+     +-------------------+     +-------------------+
|   DISCOVER        | --> |   CURATE          | --> |   EXTRACT         |
|                   |     |                   |     |                   |
| - YouTube Search  |     | - AI Filtering    |     | - Bulk Transcribe |
| - Query Planning  |     | - Required Terms  |     | - Parallel Proc.  |
| - Multi-Query     |     | - Topic Relevance |     | - Rich Metadata   |
+-------------------+     +-------------------+     +-------------------+
                                   |
                                   v
                    +----------------------------+
                    |    ORGANIZED OUTPUT        |
                    |                            |
                    | - Obsidian Markdown        |
                    | - Session Folders          |
                    | - Manifest + CSV Tracking  |
                    +----------------------------+
```

---

## Key Features

### 1. YouTube Search with AI Query Planning

| Feature | Description |
|---------|-------------|
| **AI Query Generation** | LLM generates 1-10 search query variants from a research prompt |
| **Domain Decomposition** | Breaks topics into subcategories for broader coverage |
| **Advanced Filters** | Date range, HD video, captions, region, language |
| **Multi-Query Execution** | Run planned queries in batch with result deduplication |
| **Query Source Tracking** | Tracks which query found each video for analysis |

### 2. AI-Powered Video Filtering

| Feature | Description |
|---------|-------------|
| **Two-Layer Filtering** | Required terms (strict) + topic relevance (flexible) |
| **Batch Processing** | Evaluates videos in optimized batches |
| **Multiple Models** | GPT-4o-mini (default), Claude Haiku, Llama options |
| **Transparent Results** | Per-batch summaries and validation logs |
| **Graceful Degradation** | Continues processing even if individual batches fail |

### 3. Bulk Transcript Extraction

| Feature | Description |
|---------|-------------|
| **Three-Tier Strategy** | Captions API (free) --> Residential Proxies --> DEAPI (fallback) |
| **Parallel Processing** | 2-20 concurrent workers with thread-safe progress |
| **Pre-Validation** | Filters private/deleted videos before expensive extraction |
| **Rich Metadata** | Captures channel, views, likes, tags, description, thumbnails |
| **Obsidian Output** | YAML frontmatter + formatted transcript content |

### 4. Session-Based Output Management

| Feature | Description |
|---------|-------------|
| **Timestamped Sessions** | Each run creates isolated `session_YYYYMMDD_HHMMSS/` folder |
| **Manifest Tracking** | JSON manifest with session metadata and item status |
| **CSV Export** | Processing results for analysis and auditing |
| **Organized Structure** | Separate directories for YouTube vs. podcast content |

---

## Technical Architecture

### High-Level System Diagram

```
+---------------------------------------------------------+
|                    STREAMLIT WEB UI                      |
|  +------------------+  +------------------+              |
|  | YouTube Search   |  | Bulk Transcribe  |              |
|  | (01_*.py)        |  | (03_*_Proxy.py)  |              |
|  +--------+---------+  +--------+---------+              |
|           |                     |                        |
|           +----------+----------+                        |
|                      |                                   |
+---------------------------------------------------------+
                       |
                       v
+---------------------------------------------------------+
|                 CORE MODULES (src/bulk_transcribe/)      |
|                                                          |
|  +---------------+  +---------------+  +---------------+ |
|  | query_planner |  | video_filter  |  | parallel_proc | |
|  | (AI queries)  |  | (AI curation) |  | (threading)   | |
|  +---------------+  +---------------+  +---------------+ |
|                                                          |
|  +---------------+  +---------------+  +---------------+ |
|  | youtube_trans |  | proxy_trans   |  | transcript_wr | |
|  | (captions)    |  | (residential) |  | (Markdown)    | |
|  +---------------+  +---------------+  +---------------+ |
|                                                          |
|  +---------------+  +---------------+  +---------------+ |
|  | sheet_ingest  |  | session_mgr   |  | youtube_meta  | |
|  | (parsing)     |  | (output org)  |  | (yt-dlp)      | |
|  +---------------+  +---------------+  +---------------+ |
+---------------------------------------------------------+
                       |
                       v
+---------------------------------------------------------+
|                  EXTERNAL SERVICES                       |
|                                                          |
|  +--------------+  +--------------+  +--------------+   |
|  | YouTube API  |  | OpenRouter   |  | WebShare     |   |
|  | (Data v3)    |  | (AI Models)  |  | (Proxies)    |   |
|  +--------------+  +--------------+  +--------------+   |
|                                                          |
|  +--------------+  +--------------+                     |
|  | yt-dlp       |  | DEAPI        |                     |
|  | (metadata)   |  | (fallback)   |                     |
|  +--------------+  +--------------+                     |
+---------------------------------------------------------+
```

### Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Streamlit (multipage app), Pandas (data tables) |
| **Backend** | Python 3.x, ThreadPoolExecutor, session state management |
| **AI Integration** | OpenRouter API (GPT-4o-mini, Claude Haiku, Llama) |
| **Extraction** | youtube-transcript-api, yt-dlp, DEAPI |
| **Proxies** | WebShare residential proxy network |
| **Data** | YouTube Data API v3, google-api-python-client |
| **File Handling** | openpyxl (Excel), csv (spreadsheets), JSON |

---

## Data Flow Pipeline

```
1. INPUT
   |-- Parse files (CSV/TSV/XLSX/TXT)
   |-- Normalize columns
   |-- Validate URLs
   v
2. OPTIONAL: PRE-VALIDATION
   |-- Check video availability (YouTube API)
   |-- Filter private/deleted videos
   v
3. OPTIONAL: AI FILTERING
   |-- Batch videos (10 per batch)
   |-- LLM relevance evaluation
   |-- Two-layer filtering
   v
4. SESSION CREATION
   |-- Timestamped directory
   |-- Initialize manifest.json
   v
5. PARALLEL EXTRACTION
   |-- ThreadPoolExecutor (2-20 workers)
   |-- Three-tier fallback strategy
   |-- Queue-based result collection
   v
6. OUTPUT GENERATION
   |-- Obsidian Markdown with YAML frontmatter
   |-- Rich metadata preservation
   |-- Session manifest update
```

---

## Competitive Advantages

| Advantage | Description |
|-----------|-------------|
| **Integrated Workflow** | No tool-switching between search, filter, and transcribe |
| **AI Curation** | LLM-based filtering beats keyword-only approaches |
| **Three-Tier Extraction** | Higher success rate than single-method tools |
| **Knowledge-Ready Output** | Obsidian-optimized vs. raw text dumps |
| **Parallel Processing** | 2-20x faster than sequential processing |
| **Error Resilience** | Automatic retries, fallbacks, and graceful degradation |
| **Cost Optimization** | Free methods first, paid services as fallback |
| **Session Isolation** | Each run is self-contained and auditable |

---

## Target Users

### Primary Personas

| Persona | Use Case | Key Features Used |
|---------|----------|-------------------|
| **Researchers** | Collect video transcripts for analysis | AI filtering, bulk extraction, metadata |
| **Content Creators** | Research competitors and trends | YouTube search, query planning |
| **Knowledge Workers** | Build searchable content libraries | Obsidian output, session management |
| **Analysts** | Market research and monitoring | Pre-validation, parallel processing |

### Example Use Cases

1. **Academic Research** - Transcribe 100+ interview videos for qualitative analysis
2. **Competitive Analysis** - Extract transcripts from competitor YouTube channels
3. **Content Curation** - Build topic-specific video transcript libraries
4. **Market Research** - Analyze customer testimonial videos at scale
5. **Educational Content** - Create text versions of lecture series

---

## Output Structure

```
output/sessions/session_20260130_143000/
|
+-- manifest.json          # Session metadata and tracking
+-- items.csv              # Processing results (URL, status, path)
|
+-- youtube/
|   +-- Video_Title_1__VIDEO_ID.md          # Transcript + frontmatter
|   +-- Video_Title_1__VIDEO_ID.metadata.json
|   +-- Video_Title_2__VIDEO_ID.md
|   +-- ...
|
+-- podcasts/              # Future: podcast transcripts
    +-- ...
```

### Markdown Output Format

```yaml
---
title: "Video Title Here"
channel: "Channel Name"
published: "2026-01-15"
duration: "12:34"
views: 15234
likes: 892
tags: ["tag1", "tag2"]
source_url: "https://youtube.com/watch?v=..."
extraction_method: "captions"
---

[Transcript content here...]
```

---

## System Requirements

### API Keys Required

| Service | Purpose | Required For |
|---------|---------|--------------|
| `YOUTUBE_DATA_API_KEY` | YouTube search and pre-validation | YouTube Search |
| `OPENROUTER_API_KEY` | AI query planning and filtering | AI Features |
| `DEAPI_API_KEY` | Fallback transcript extraction | DEAPI Fallback |
| `WEBSHARE_PROXY_FILE` | Residential proxy configuration | Proxy Extraction |

### Dependencies

- Python 3.9+
- Streamlit 1.32+
- youtube-transcript-api 1.0+
- yt-dlp 2024.12+
- google-api-python-client 2.100+
- pandas 2.0+
- requests 2.31+
- openpyxl 3.1+
- python-dotenv 1.0+

---

## Quick Start

```powershell
# 1. Setup (first time)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure API keys in .env
# YOUTUBE_DATA_API_KEY=your_key
# OPENROUTER_API_KEY=your_key

# 3. Run the app
.\run_app.ps1
# Or: streamlit run app.py
```

---

## Summary

Bulk Transcribe solves the problem of extracting actionable knowledge from YouTube video content. By combining intelligent search, AI-powered filtering, and robust transcript extraction into one workflow, it transforms what would be hours of manual work into an automated, repeatable process.

**Key Differentiators:**
- End-to-end workflow (search --> filter --> transcribe)
- AI-powered curation with LLM relevance filtering
- Three-tier extraction strategy for maximum success
- Knowledge-ready Obsidian Markdown output
- Parallel processing for batch efficiency

The result: researchers and content professionals can focus on analysis and insights rather than data collection and formatting.
