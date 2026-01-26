# UI/UX Strategy: Planned Query Results (Step 3)

## Goal
Provide clear, intuitive visibility into results for every planned query, including progress, partial results, and final outcomes, while preserving the existing aggregate workflow for filtering and bulk transcription.

## Primary UX Problems Observed
- Users run multiple planned queries but only see an aggregated table with a fixed cap (e.g., 50 rows), which hides what happened for the other queries.
- There is no per-query visibility, so it is unclear which queries completed, were rate-limited, or returned zero results.

## Proposed Information Architecture
Introduce a two-level results structure:
1. **Run Summary (global)**: Shows overall status across all planned queries.
2. **Per-Query Results (scoped)**: Each query has its own result set with status and counts.

This ensures users can always reconcile which queries produced which results while still preserving an overall combined view for downstream steps.

## Step 3 Layout Proposal
### A) Planned Query Run Summary (top of Step 3)
A compact summary card row:
- **Total queries planned**
- **Queries completed / in progress / failed / no results**
- **Total results fetched** (sum across all queries)
- **Deduplicated results**
- **Last updated time**

### B) Query Results Navigation (below summary)
A segmented control or tabs with:
- **All Results (combined)**
- **Query 1: <query text>**
- **Query 2: <query text>**
- ...

For more than 5 queries, use a dropdown + search to pick a specific query while keeping an “All Results” tab visible.

### C) Query Status Strip (under tabs)
A small status row for the selected query (or combined view):
- **Status**: queued, running, completed, failed
- **Results fetched** vs **Target results**
- **Pages queried**
- **Errors / warnings** (if any)

### D) Results Table (main content)
The table view should adapt based on the selected tab:
- **All Results**: show deduplicated aggregate results across all queries.
- **Specific Query**: show results exclusively from that query, without truncation unless pagination is needed.

#### Table Columns (suggested)
- Title
- Channel
- Published date
- Duration
- View count
- Query source (only visible in All Results)
- Actions (open, add, exclude)

### E) Pagination and Fetch Controls
If there is a max results cap, it must be visible per query:
- **Per-query max results input** should be shown in Step 2 but reflected here as read-only metadata.
- If results are truncated due to caps, show a note: “Showing 50 of 120 results for this query (cap).”

## Interaction and State Design
### Query Execution
- When the user clicks “Run planned queries”, the UI should show a live per-query progress tracker.
- Each query row shows:
  - Query text
  - Current page / max pages
  - Results count
  - Status icon (queued, running, complete, failed)
- Clicking a query row jumps to its results tab.

### Error Handling
- If a query fails, it should still appear in the tab list with a failure indicator.
- The query tab should display a clear error panel with retry option.

### Zero Results
- Queries returning zero results should still appear and show a placeholder state with suggestions.

## Proposed Data Model (UI-facing)
- `queries[]`:
  - `id`
  - `text`
  - `status` (queued | running | complete | failed)
  - `requested_results`
  - `fetched_results`
  - `pages_completed`
  - `max_pages`
  - `errors[]`
  - `results[]`
- `aggregate_results[]`: deduplicated results across all queries

## User Flow (Step 3)
1. User runs planned queries.
2. Summary panel updates as each query completes.
3. User can switch between All Results and per-query tabs.
4. User can inspect errors for specific queries.
5. User continues with AI filtering or bulk transcription using the All Results view.

## Recommended UI Components
- Summary cards (4-up)
- Tabbed navigation (with overflow dropdown)
- Status chips
- Results table with pagination
- Query progress list (collapsible)

## Success Criteria
- Users can identify which query produced each result.
- Users can see if any query failed, returned zero results, or is still running.
- Aggregate results remain available for downstream steps.

## Open Questions for Approval
- Preferred navigation: tabs vs expandable query list with inline tables?
- Should the All Results view remain the default, or should it auto-switch to the active query?
- Should per-query pagination be independent from aggregate view?
