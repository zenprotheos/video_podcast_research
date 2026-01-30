# YouTube Search Workflow Spec

## Purpose
Document the YouTube search workflow, including optional query planning, configuration guardrails, and search execution behavior.

## Workflow Steps
### Step 0: Query Planning (optional, search mode only)
- Users enter a research prompt and optional guidance in a fixed, top-of-page form.
- **Required terms in title and description:** Optional. When set, the query planner uses them to generate search queries (each term or phrase as a quoted phrase for phrase-matched results). Separate multiple terms with commas; each comma-separated term is quoted in search queries. When left empty and the user clicks Generate search queries, the app first infers **one** conservative required term (1–3 words) from the research prompt, pre-fills this field, then generates search queries **using that term as input** so the planned queries include quoted phrases around it. User can edit or clear the field. The AI filter (Step 3) enforces required terms when cleaning up results.
- The query planner uses OpenRouter to propose distinct search queries.
- Output is a list of queries (one per line) that users can review and edit; planned queries are run as-is (including any quoted phrases).
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
- **AI filter input:** The filter prompt includes video title, channel, description, tags (up to 15), and published date. Tags help improve relevance filtering by providing keyword context.

### Step 3: Results & Actions
- Results display supports selection, export, and transcript handoff.
- **Results table:** Column widths are rebalanced so action columns (e.g. Watch, Date) remain readable. Description and query-source columns use resizable text areas (user can drag to expand). Videos are enriched with full metadata via `videos.list` after search (post-dedupe, batched, cached in session).
- **Enriched metadata columns:** Duration (formatted as MM:SS or H:MM:SS) and Views (formatted as 1.2M, 45K, etc.) are displayed in the results table.
- **Full metadata stored:** All enriched fields (duration, view_count, like_count, comment_count, tags, category_id, has_captions) are stored and passed through to Bulk Transcribe for pipeline continuity.
- When multiple queries are run, results are aggregated and de-duplicated by video ID.
- Planned query telemetry is surfaced through:
  - A run summary card row (total queries, counts by status, total/ deduplicated results, last update).
  - Tabbed navigation for `All Results (combined)` plus each query, ensuring a dedicated table per query.
  - Query status strips showing status, fetched vs requested results, pages completed, and error summaries.
  - Query-level cap notices, collapsible progress tracker, and retry affordances for failed queries.
  - A query source column in the aggregate table to expose which query produced each video.

### Step 4: Final Actions
- Copy URLs, Copy IDs, and Copy as JSON copy to clipboard on first click when possible (server clipboard or browser clipboard).
- Success feedback: brief message only; the exported list is not shown unless clipboard is unavailable.
- If clipboard is unavailable, the app shows the exported text in a code block with instructions to copy manually.

## Configuration Guardrails
- Results per request are limited to the YouTube API maximum of 50.
- Max pages per query limits pagination to control quota usage.
- Planned query execution respects both limits.

## Data Handling
- Aggregated results are stored as a single SearchResult with pagination disabled.
- AI filtering uses the combined query list as context.
- **Required terms (title/description):** When set in Step 0, they are used for query planning (planner outputs each term/phrase as a quoted phrase; comma-separated terms become multiple quoted phrases in queries) and for AI filter cleanup (exclude videos that do not contain or clearly discuss them). When empty, the app infers **one** conservative term (1–3 words), pre-fills Step 0, then generates search queries with that term in context so planned queries include quoted phrases. Planned queries are executed as-is (quotes included) for better search relevance.

## Dependencies
- Query planning uses OpenRouter via `src/bulk_transcribe/query_planner.py`.
- Search and pagination use `src/bulk_transcribe/youtube_search.py`.
