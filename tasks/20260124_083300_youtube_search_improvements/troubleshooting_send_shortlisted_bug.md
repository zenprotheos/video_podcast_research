# Troubleshooting: Send Shortlisted Button Only Captures One Query's Results

## Problem Statement
After executing 5 planned search queries resulting in 130 URLs, clicking "Send Shortlisted to Transcript Tool" only captures results from one search query instead of all queries' aggregated results.

## Systematic Analysis

### 1. Question-Answer Matrix

#### Q1: How are multiple planned query results aggregated?
**A:** In `pages/01_YouTube_Search.py` lines 798-801, results from each query are aggregated into `aggregated_items` with deduplication by `video_id`. When a duplicate video is found, it's skipped entirely rather than merging query sources.

**Evidence:**
```python
for item in search_result.items:
    if item.video_id not in seen_video_ids:
        aggregated_items.append(item)
        seen_video_ids.add(item.video_id)
```

#### Q2: How are query sources tracked per video?
**A:** In `src/bulk_transcribe/youtube_search.py` line 184, each `VideoSearchItem` is created with `query_sources=[query_text]` when parsed. However, when deduplicating during aggregation, duplicate videos are skipped without merging their `query_sources` lists.

**Evidence:**
- `parse_search_item()` sets: `query_sources=[query_text] if query_text else []`
- Aggregation loop skips duplicates without merging sources

#### Q3: What determines which videos are sent to the transcript tool?
**A:** In `pages/01_YouTube_Search.py` lines 1081-1100, the logic prioritizes:
1. Selected videos (if any checkboxes checked)
2. Filtered results (if AI filtering was applied)
3. All search results (fallback)

**Evidence:**
```python
if st.session_state.filtered_results and st.session_state.filtered_results.success:
    action_videos = st.session_state.filtered_results.relevant_videos
    action_source = "youtube_search_filtered"
    action_label = "Shortlisted"
```

#### Q4: Does AI filtering process all aggregated results or just one query?
**A:** In `pages/01_YouTube_Search.py` line 1054, `filter_videos_by_relevance()` receives `search_results.items`, which should contain all aggregated results. However, the filtering function in `src/bulk_transcribe/video_filter.py` line 24 receives the full list and processes all videos.

**Evidence:** Filtering receives `search_results.items` which is the aggregated `SearchResult` from line 821.

#### Q5: What happens to query_sources when videos are deduplicated?
**A:** **CRITICAL BUG IDENTIFIED**: When a video appears in multiple query results, only the first occurrence is kept. The `query_sources` from subsequent queries are lost because the duplicate is skipped entirely.

**Evidence:** Lines 798-801 show no merging logic for `query_sources`.

#### Q6: Could filtered results only contain one query's videos?
**A:** Potentially, if:
- The aggregation bug causes videos to lose query source information
- The filtering somehow filters based on query source (unlikely, but needs verification)
- The filtered results are stored incorrectly

**Evidence:** Need to trace the filtering flow more carefully.

### 2. Element Inventory

#### Files Involved
- `pages/01_YouTube_Search.py` (main UI logic)
  - Lines 741-838: Planned query execution and aggregation
  - Lines 1081-1147: Action buttons and transcript handoff
  - Lines 1097-1100: Filtered results selection logic
- `src/bulk_transcribe/youtube_search.py`
  - Lines 135-189: `parse_search_item()` - creates VideoSearchItem with query_sources
  - Line 184: Sets `query_sources=[query_text]`
- `src/bulk_transcribe/video_filter.py`
  - Lines 24-105: `filter_videos_by_relevance()` - filters all provided videos
- `src/bulk_transcribe/metadata_transfer.py`
  - Lines 10-26: `video_search_item_to_dict()` - converts items for session state

#### Functions & Variables
- `aggregated_items` (line 752): List accumulating all query results
- `seen_video_ids` (line 753): Set tracking deduplication
- `action_videos` (lines 1084-1100): Final list sent to transcript tool
- `st.session_state.filtered_results.relevant_videos`: AI-filtered video list
- `st.session_state.search_results.items`: All aggregated search results

#### Data Flow Touch Points
1. **Query Execution** → `search_youtube()` → `parse_search_item()` → `VideoSearchItem` with `query_sources`
2. **Aggregation** → Deduplication by `video_id` → **BUG: query_sources not merged**
3. **Filtering** → `filter_videos_by_relevance()` → `FilteringResult.relevant_videos`
4. **Action Selection** → `action_videos` determination → `video_search_item_to_dict()` → Session state

### 3. Input/Output Mapping

```
┌─────────────────────────────────────────────────────────────┐
│ MULTIPLE PLANNED QUERIES EXECUTION                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ For each query:                                            │
│   search_youtube(query) → SearchResult.items               │
│   Each item has: query_sources=[query_text]                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ AGGREGATION (lines 798-801)                                │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ BUG: Duplicate videos skip without merging sources    │  │
│ │ if video_id in seen_video_ids: SKIP                   │  │
│ │ else: ADD to aggregated_items                         │  │
│ └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ st.session_state.search_results = SearchResult(            │
│   items=aggregated_items  # May have incomplete sources    │
│ )                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ AI FILTERING (if enabled)                                  │
│ filter_videos_by_relevance(                                │
│   videos=search_results.items  # All aggregated items     │
│ ) → FilteringResult.relevant_videos                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ ACTION BUTTON LOGIC (lines 1097-1100)                      │
│ if filtered_results exists:                                │
│   action_videos = filtered_results.relevant_videos        │
│ else if selected_video_ids:                                │
│   action_videos = selected videos                           │
│ else:                                                       │
│   action_videos = search_results.items                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ SEND TO TRANSCRIPT (lines 1136-1142)                        │
│ urls = [item.video_url for item in action_videos]          │
│ metadata_list = [video_search_item_to_dict(item)           │
│                  for item in action_videos]                 │
│ st.session_state['transcript_urls'] = urls                  │
│ st.session_state['transcript_metadata'] = metadata_list    │
└─────────────────────────────────────────────────────────────┘
```

### 4. Risk Assessment

#### Primary Failure Point: Query Source Merging
**Risk Level:** CRITICAL
**Location:** `pages/01_YouTube_Search.py` lines 798-801
**Impact:** Videos found by multiple queries lose query source information. This may cause:
- Incorrect filtering behavior if filtering considers query sources
- Loss of traceability for which queries found which videos
- Potential data loss if downstream logic depends on complete query_sources

**Mitigation:** Implement query source merging during deduplication.

#### Secondary Failure Point: Filtered Results Scope
**Risk Level:** MEDIUM
**Location:** `pages/01_YouTube_Search.py` lines 1097-1100
**Impact:** If filtered results only contain videos from one query (due to aggregation bug or filtering logic), only those videos are sent.

**Mitigation:** Verify filtered results contain videos from all queries. Add validation logging.

#### Tertiary Failure Point: Session State Persistence
**Risk Level:** LOW
**Location:** `pages/01_YouTube_Search.py` lines 1139-1141
**Impact:** Session state may not persist correctly if data structure is invalid.

**Mitigation:** Add validation before storing in session state.

### 5. Root Cause Analysis

#### Primary Root Cause
**The aggregation logic skips duplicate videos without merging their `query_sources` lists.**

When Query 1 finds Video A:
- Video A added with `query_sources=["query 1"]`

When Query 2 also finds Video A:
- Video A already in `seen_video_ids`
- Video A skipped (not added again)
- `query_sources` from Query 2 is lost

#### Secondary Contributing Factors
1. **No validation** that filtered results contain videos from all queries
2. **No logging** to track which queries contributed to final results
3. **No user feedback** showing how many queries contributed to shortlisted results

### 6. Testing Strategy

#### Unit Tests
1. **Test query source merging:**
   ```python
   def test_aggregate_merges_query_sources():
       # Create two items with same video_id but different query_sources
       item1 = VideoSearchItem(..., video_id="abc", query_sources=["query1"])
       item2 = VideoSearchItem(..., video_id="abc", query_sources=["query2"])
       # Aggregate should merge: query_sources=["query1", "query2"]
   ```

2. **Test filtered results contain all queries:**
   ```python
   def test_filtered_results_preserve_all_queries():
       # Create aggregated results from 5 queries
       # Apply filtering
       # Verify filtered results contain videos from all 5 queries
   ```

#### Integration Tests
1. **End-to-end planned queries → filtering → send:**
   - Execute 5 planned queries
   - Apply AI filtering
   - Click "Send Shortlisted"
   - Verify session state contains videos from all 5 queries

2. **Deduplication with query source preservation:**
   - Execute queries that return overlapping videos
   - Verify aggregated results have merged query_sources
   - Verify all query sources are preserved in metadata

#### Debug Logging
Add logging at key points:
- After aggregation: log count of videos per query source
- After filtering: log which queries contributed to filtered results
- Before sending: log summary of videos by query source

### 7. Implementation Plan

#### Phase 1: Fix Query Source Merging (CRITICAL)
1. **Modify aggregation logic** (lines 798-801):
   - When duplicate video found, merge `query_sources` instead of skipping
   - Update existing item in `aggregated_items` with merged sources

2. **Implementation:**
   ```python
   for item in search_result.items:
       if item.video_id not in seen_video_ids:
           aggregated_items.append(item)
           seen_video_ids.add(item.video_id)
       else:
           # MERGE: Find existing item and merge query_sources
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

#### Phase 2: Add Validation & Logging
1. **Add validation after aggregation:**
   - Log summary: videos per query source
   - Verify all planned queries are represented

2. **Add validation after filtering:**
   - Log which queries contributed to filtered results
   - Warn if any queries have zero videos in filtered results

3. **Add user feedback:**
   - Show query source breakdown in action buttons area
   - Display "X videos from Y queries" in success message

#### Phase 3: Testing & Verification
1. **Manual testing:**
   - Execute 5 planned queries with overlapping results
   - Apply AI filtering
   - Verify "Send Shortlisted" includes videos from all queries
   - Check session state contains complete metadata

2. **Automated testing:**
   - Run unit tests for query source merging
   - Run integration test for full workflow

### 8. Error Handling Specifications

#### Aggregation Errors
- **Error:** Failed to merge query_sources
- **Action:** Log warning, continue with first query's sources
- **Recovery:** Manual verification recommended

#### Filtering Errors
- **Error:** Filtered results empty or incomplete
- **Action:** Show warning, allow user to send all results instead
- **Recovery:** User can disable filtering and send all results

#### Session State Errors
- **Error:** Invalid metadata structure
- **Action:** Validate before storing, show error if invalid
- **Recovery:** Re-run search/filtering

### 9. Success Criteria

1. ✅ All videos from all planned queries are included in aggregated results
2. ✅ Query sources are merged when videos appear in multiple query results
3. ✅ Filtered results contain videos from all queries (if applicable)
4. ✅ "Send Shortlisted" button sends videos from all queries
5. ✅ Session state contains complete metadata with all query sources
6. ✅ User can see which queries contributed to final results

### 10. Next Steps

1. **IMMEDIATE:** Fix query source merging in aggregation logic
2. **HIGH PRIORITY:** Add validation logging to verify all queries are represented
3. **MEDIUM PRIORITY:** Add user feedback showing query breakdown
4. **LOW PRIORITY:** Add unit tests for query source merging

## Implementation Priority

**CRITICAL (Fix Now):**
- Fix query source merging during aggregation (Phase 1)

**HIGH (This Session):**
- Add validation logging (Phase 2)
- Manual testing (Phase 3)

**MEDIUM (Next Session):**
- User feedback improvements (Phase 2)
- Automated tests (Phase 3)
