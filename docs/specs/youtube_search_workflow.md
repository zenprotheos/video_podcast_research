# YouTube Search Workflow Spec

## Purpose
Document the YouTube search workflow, including optional query planning, configuration guardrails, and search execution behavior.

## Workflow Steps
### Step 0: Query Planning (optional, search mode only)
- Users enter a research prompt and optional guidance in a fixed, top-of-page form.
- The query planner uses OpenRouter to propose distinct search queries.
- Output is a list of queries (one per line) that users can review and edit.
- Users can set a maximum number of queries to generate and select how many to run.

### Step 1: Choose Input Method & Provide Data
- Input modes:
  - Search YouTube (API-driven)
  - Direct input (URLs or JSON)
- Search configuration includes:
  - Results per request (1–50)
  - Max pages per query (pagination budget)
  - **Date range:** Any time; rolling presets (last 3/6/12 months); or manual start/end dates, mapped to YouTube `publishedAfter` / `publishedBefore`.
- Execution modes for search:
  - Single query
  - Planned queries (uses the query planner list)

### Step 2: Configure AI Research (optional)
- Users can add research context for AI filtering.
- Optional AI filtering uses the selected OpenRouter model to shortlist results.

### Step 3: Results & Actions
- Results display supports selection, export, and transcript handoff.
- **Results table:** Column widths are rebalanced so action columns (e.g. Watch, Date) remain readable. Description and query-source columns use resizable text areas (user can drag to expand). Descriptions are enriched with full text via `videos.list` after search (post-dedupe, batched, cached in session).
- When multiple queries are run, results are aggregated and de-duplicated by video ID.
- Planned query telemetry is surfaced through:
  - A run summary card row (total queries, counts by status, total/ deduplicated results, last update).
  - Tabbed navigation for `All Results (combined)` plus each query, ensuring a dedicated table per query.
  - Query status strips showing status, fetched vs requested results, pages completed, and error summaries.
  - Query-level cap notices, collapsible progress tracker, and retry affordances for failed queries.
  - A query source column in the aggregate table to expose which query produced each video.

## Configuration Guardrails
- Results per request are limited to the YouTube API maximum of 50.
- Max pages per query limits pagination to control quota usage.
- Planned query execution respects both limits.

## Data Handling
- Aggregated results are stored as a single SearchResult with pagination disabled.
- AI filtering uses the combined query list as context.

## Dependencies
- Query planning uses OpenRouter via `src/bulk_transcribe/query_planner.py`.
- Search and pagination use `src/bulk_transcribe/youtube_search.py`.
