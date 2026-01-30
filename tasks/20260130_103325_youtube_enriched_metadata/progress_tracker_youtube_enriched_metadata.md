# Progress Tracker: YouTube Enriched Metadata Extraction

## Status: COMPLETED

## Overview
Extract all available YouTube metadata at no additional quota cost. Store all metadata for end-to-end pipeline flow, but use only relevant fields at each stage.

## Design Principle
- **Store All**: Every field extracted is stored and passed through the pipeline
- **Use Selectively**: Each stage only uses what's relevant for its task
- **Exclude**: definition (HD/SD) - not useful for any stage

## Phases

### Phase 1: Data Model Extension - COMPLETED
- [x] Add new fields to `VideoSearchItem` dataclass
  - [x] `duration: Optional[str]` (ISO 8601)
  - [x] `duration_seconds: Optional[int]` (parsed)
  - [x] `view_count: Optional[int]`
  - [x] `like_count: Optional[int]`
  - [x] `comment_count: Optional[int]`
  - [x] `tags: List[str]`
  - [x] `category_id: Optional[str]`
  - [x] `has_captions: Optional[bool]`
  - [x] ~~definition~~ EXCLUDED
- [x] Create `parse_iso8601_duration()` utility function

### Phase 2: API Enrichment - COMPLETED
- [x] Rename function: `enrich_items_with_full_descriptions()` -> `enrich_items_with_metadata()`
- [x] Update `part` parameter: `"snippet,contentDetails,statistics"`
- [x] Remove `fields` restriction
- [x] Parse all new fields from API response
- [x] Created helper functions: `_safe_int()`, `_hydrate_items_from_cache()`
- [x] Backward compatibility alias maintained

### Phase 3: Cache Enhancement - COMPLETED
- [x] Refactor cache to store full metadata dict (not just description string)
- [x] Update session state variable name: `full_description_by_id` -> `video_metadata_cache`
- [x] Update all 5 call sites in UI (planned query, single search, planned completion, prev/next page)

### Phase 4: UI Integration - COMPLETED
- [x] Add "Duration" column to results table (formatted as MM:SS or H:MM:SS)
- [x] Add "Views" column with formatting (1.2M, 45K)
- [x] Add `_format_duration()` utility
- [x] Add `_format_count()` utility
- [x] Update column config

### Phase 5: Metadata Transfer (Pipeline Pass-through) - COMPLETED
- [x] Update `video_search_item_to_dict()` with all new fields
- [x] Update `dict_to_video_search_item()` with all new fields
- [x] Update `metadata_to_parsed_sheet()` with duration, view_count, and all new fields

### Phase 6: AI Filter Enhancement - COMPLETED
- [x] Update `_build_user_prompt()` in video_filter.py
- [x] Add Tags line to each video block (limit to 15 tags)

### Phase 7: Validation & Testing - COMPLETED
- [x] Syntax validation on all modified files (py_compile)
- [x] AST validation on all modified files
- [x] No linter errors found
- [x] Updated specs (youtube_search_workflow.md)

## Files Modified
- `src/bulk_transcribe/youtube_search.py` - Extended dataclass, new enrichment function
- `src/bulk_transcribe/video_filter.py` - Tags in AI filter prompt
- `src/bulk_transcribe/metadata_transfer.py` - All new fields in conversion functions
- `pages/01_YouTube_Search.py` - Duration/Views columns, cache updates, formatting utilities
- `docs/specs/youtube_search_workflow.md` - Updated spec documentation

## Open Issues
(none)

## Next Actions
- Manual testing recommended: Run app and perform a search to verify Duration/Views display
- Verify AI filter receives tags in prompt during filtering
