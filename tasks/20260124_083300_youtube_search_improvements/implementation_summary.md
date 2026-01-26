# Implementation Summary: Query Source Merging Fix

## Date
2026-01-26

## Problem
After executing 5 planned search queries resulting in 130 URLs, clicking "Send Shortlisted to Transcript Tool" only captured results from one search query instead of all queries' aggregated results.

## Root Cause
The aggregation logic in `pages/01_YouTube_Search.py` skipped duplicate videos without merging their `query_sources` lists. When a video appeared in multiple query results, only the first occurrence was kept, losing query source information from subsequent queries.

## Solution Implemented

### 1. Fixed Query Source Merging (CRITICAL)
**Location:** `pages/01_YouTube_Search.py` lines 798-824 and 291-307

**Change:** Modified aggregation logic to merge `query_sources` when duplicate videos are detected:

```python
for item in search_result.items:
    if item.video_id not in seen_video_ids:
        aggregated_items.append(item)
        seen_video_ids.add(item.video_id)
    else:
        # Merge query_sources for duplicate videos
        existing_item = next(
            (x for x in aggregated_items if x.video_id == item.video_id),
            None
        )
        if existing_item:
            # Merge query_sources, avoiding duplicates
            existing_sources = set(existing_item.query_sources or [])
            new_sources = set(item.query_sources or [])
            existing_item.query_sources = sorted(list(existing_sources | new_sources))
```

**Applied to:**
- Planned query execution (lines 809-824)
- Retry query function (lines 291-307)

### 2. Added Validation Logging
**Location:** `pages/01_YouTube_Search.py` lines 832-844

**Change:** Added validation after aggregation to detect queries that returned no unique results:

```python
# Validate aggregation: count videos per query source
query_source_counts = {}
for item in aggregated_items:
    sources = getattr(item, "query_sources", []) or []
    for source in sources:
        query_source_counts[source] = query_source_counts.get(source, 0) + 1

# Log validation (for debugging)
if len(planned_queries) > 1:
    missing_queries = [q for q in planned_queries if q not in query_source_counts]
    if missing_queries:
        st.warning(...)
```

### 3. Added User Feedback
**Location:** `pages/01_YouTube_Search.py` lines 1124-1132 and 1158-1175

**Changes:**
- Added `_get_query_source_breakdown()` helper function to analyze query distribution
- Added query breakdown display before action buttons showing distribution (e.g., "Q1: 25, Q2: 18, Q3: 12")
- Added validation for filtered results to warn if any queries have no videos after filtering
- Enhanced success message when sending to transcript tool to show query count

### 4. Added Metadata Validation
**Location:** `pages/01_YouTube_Search.py` lines 1158-1175

**Change:** Added validation before storing metadata in session state:

```python
is_valid, errors = validate_metadata_list(metadata_list)
if not is_valid:
    st.error(f"Metadata validation failed: {', '.join(errors[:3])}")
else:
    # Store in session state
```

## Files Modified
1. `pages/01_YouTube_Search.py`
   - Fixed aggregation logic (2 locations)
   - Added validation logging
   - Added user feedback functions and displays
   - Added metadata validation

2. `src/bulk_transcribe/metadata_transfer.py`
   - Imported `validate_metadata_list` (already existed, just needed import)

## Testing Status
- ✅ Syntax validation passed (`python -m py_compile`)
- ✅ AST parsing passed
- ⏳ End-to-end testing pending (manual test required)

## Expected Behavior After Fix

### Before Fix:
```
Query 1 → Video A (sources=["Q1"])
Query 2 → Video A (sources=["Q2"]) ← SKIPPED, sources lost
Query 3 → Video B (sources=["Q3"])

Aggregated: [Video A (sources=["Q1"]), Video B (sources=["Q3"])]
Send → Only videos from Q1 and Q3 sent ❌
```

### After Fix:
```
Query 1 → Video A (sources=["Q1"])
Query 2 → Video A (sources=["Q2"]) ← MERGED
Query 3 → Video B (sources=["Q3"])

Aggregated: [Video A (sources=["Q1", "Q2"]), Video B (sources=["Q3"])]
Send → All videos from all queries sent ✅
```

## Validation Checklist
- [x] Query sources are merged when duplicates are found
- [x] Validation logging detects missing queries
- [x] User feedback shows query breakdown
- [x] Metadata validation before storing
- [ ] Manual end-to-end test: 5 queries → filter → send → verify all queries represented

## Next Steps
1. Manual testing: Execute 5 planned queries with overlapping results
2. Verify filtered results contain videos from all queries
3. Verify "Send Shortlisted" includes videos from all queries
4. Check session state contains complete metadata with all query sources
