# Task Index: results_table_ui_description

## Goal
Fix YouTube Search Step 2 results table usability (column widths, long-text handling) and ensure AI filtering has full video descriptions by enriching `search.list` results via `videos.list`.

## Scope
- UI: `pages/01_YouTube_Search.py` results table layout improvements
- Data: `src/bulk_transcribe/youtube_search.py` enrichment (post-dedupe, batched, cached)
- Search UX: add date range filters (presets + manual) mapped to `publishedAfter/publishedBefore`
- Spec updates: `docs/specs/youtube_search_workflow.md`

## Key Files
- `pages/01_YouTube_Search.py`
- `src/bulk_transcribe/youtube_search.py`
- `docs/specs/youtube_search_workflow.md`

