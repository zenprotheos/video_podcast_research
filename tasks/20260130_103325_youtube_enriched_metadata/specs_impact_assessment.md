# Specs Impact Assessment: YouTube Enriched Metadata

## Affected Specs

### docs/specs/youtube_search_workflow.md
**Impact: MODERATE**

Changes needed:
- Document new data fields available in VideoSearchItem
- Update results table column documentation to include Duration, Views
- Document that enrichment now includes contentDetails and statistics
- Document that AI filter prompt now includes video tags

### CLAUDE.md
**Impact: LOW**

Changes needed:
- Update youtube_search.py module description to mention enriched metadata extraction
- Note that video_filter.py now uses tags in AI filtering

---

## Design Principle: Store All, Use Selectively

All metadata flows through the entire pipeline for future stages (Bulk Transcribe, future Summarizer tool), but each stage only uses fields relevant to its task.

### Metadata Usage by Stage

| Stage | Uses | Purpose |
|-------|------|---------|
| YouTube Search - AI Filter | tags | Improve relevance filtering |
| YouTube Search - UI | duration, views | User decision support |
| Bulk Transcribe | title, description, URL | Transcript labeling |
| Future Summarizer | TBD | All metadata available |

---

## Data Model Changes

### VideoSearchItem (youtube_search.py)
New optional fields (definition EXCLUDED):
```python
duration: Optional[str] = None           # ISO 8601 format
duration_seconds: Optional[int] = None   # Parsed for display
view_count: Optional[int] = None
like_count: Optional[int] = None
comment_count: Optional[int] = None
tags: List[str] = field(default_factory=list)
category_id: Optional[str] = None
has_captions: Optional[bool] = None
```

---

## API Changes

### enrich_items_with_full_descriptions() -> enrich_items_with_metadata()
- Function renamed to reflect broader purpose
- `part` parameter expanded: `"snippet"` -> `"snippet,contentDetails,statistics"`
- `fields` restriction removed to get all available data
- Cache structure changed from `Dict[str, str]` to `Dict[str, Dict]`

### _build_user_prompt() in video_filter.py
- Now includes `Tags: tag1, tag2, ...` line for each video (up to 15 tags)

---

## Backward Compatibility
- All new fields are optional with default values
- Existing code continues to work
- Cache structure change requires session state variable rename

---

## UI Changes
- Results table gains Duration and Views columns
- Formatting utilities for human-readable display (e.g., "15:33", "1.2M views")

---

## Pipeline Flow

```
YouTube Search
    |
    v
[VideoSearchItem with ALL metadata]
    |
    +---> AI Filter (uses: tags)
    |
    +---> Results Table (displays: duration, views)
    |
    v
Bulk Transcribe (receives: all metadata)
    |
    v
Future Summarizer (receives: all metadata + transcripts)
```
