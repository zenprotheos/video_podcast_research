# Task: YouTube Enriched Metadata Extraction

## Overview
Extract all available YouTube metadata (duration, views, likes, tags, etc.) at no additional quota cost. Store all metadata for end-to-end pipeline flow, but use only relevant fields at each stage.

## Design Principle: Store All, Use Selectively

```
STORAGE: All metadata extracted and passed through entire pipeline
USAGE:   Each stage uses only what's relevant for its specific task

YouTube Search
  - AI Filter uses: tags (improves relevance filtering)
  - UI displays: duration, views (user decision support)
  
Bulk Transcribe
  - Uses: title, description, URL (transcript labeling)
  - Passes through: ALL metadata
  
Future Summarizer (not built yet)
  - Receives: ALL metadata + transcripts
  - Uses: TBD based on consolidation task
```

## Problem Statement
- The `videos.list` endpoint costs **1 quota unit** regardless of how many `part` parameters are requested
- Current implementation only requests `part="snippet"` with `fields="items(id,snippet(description))"`
- We are missing: duration, viewCount, likeCount, commentCount, tags, categoryId, caption
- This data is effectively "free" since we're already paying the quota cost

## Scope
- **In scope**: YouTube Search stage only
- **Out of scope**: Bulk Transcribe updates (separate task)
- **Excluded field**: definition (HD/SD) - not useful for any stage

## Goals
1. Extend `VideoSearchItem` dataclass with new fields
2. Modify enrichment function to fetch `snippet,contentDetails,statistics`
3. Parse and populate all available fields
4. Add tags to AI filter prompt (relevance improvement)
5. Update UI table to display Duration and Views columns
6. Ensure all metadata passes through to Bulk Transcribe stage

## Files to Modify
- `src/bulk_transcribe/youtube_search.py` - VideoSearchItem dataclass, enrich function
- `src/bulk_transcribe/video_filter.py` - Add tags to AI filter prompt
- `pages/01_YouTube_Search.py` - Results table columns, cache structure
- `src/bulk_transcribe/metadata_transfer.py` - Conversion functions for pipeline

## Data Fields to Add

### From `contentDetails`:
| Field | Type | Used By |
|-------|------|---------|
| `duration` | string | Storage, UI display |
| `duration_seconds` | int | Storage, UI display |
| `has_captions` | bool | Storage only |

### From `statistics`:
| Field | Type | Used By |
|-------|------|---------|
| `view_count` | int | Storage, UI display |
| `like_count` | int | Storage only |
| `comment_count` | int | Storage only |

### From `snippet` (additional):
| Field | Type | Used By |
|-------|------|---------|
| `tags` | List[str] | Storage, AI filter |
| `category_id` | string | Storage only |

### Excluded:
| Field | Reason |
|-------|--------|
| `definition` | Not useful for any stage |

## Implementation Phases

### Phase 1: Data Model Extension
- Extend `VideoSearchItem` dataclass with new optional fields
- Add ISO 8601 duration parser utility function

### Phase 2: API Enrichment
- Rename `enrich_items_with_full_descriptions()` to `enrich_items_with_metadata()`
- Request `part="snippet,contentDetails,statistics"`
- Parse and populate all fields from response

### Phase 3: Cache Enhancement
- Update cache structure to store full metadata dict
- Rename session state variable for clarity

### Phase 4: UI Integration
- Add Duration column (formatted as MM:SS or H:MM:SS)
- Add Views column (formatted as 1.2M, 45K)

### Phase 5: Metadata Transfer
- Update conversion functions for pipeline pass-through
- Ensure all fields flow to Bulk Transcribe

### Phase 6: AI Filter Enhancement
- Add tags to `_build_user_prompt()` in video_filter.py
- Limit to 15 tags per video to control token usage

## Quota Impact
**None** - Same 1 unit cost per 50 videos, just extracting more data from the response.

## Success Criteria
- [ ] VideoSearchItem has all new fields populated
- [ ] Results table shows Duration and Views columns
- [ ] AI filter prompt includes video tags
- [ ] All metadata passes through to Bulk Transcribe
- [ ] Existing functionality continues to work
- [ ] No increase in quota usage

## Related Files
- `docs/specs/youtube_search_workflow.md` - Spec to update
- `tasks/20260128_173855_results_table_ui_description/` - Previous table improvement task
