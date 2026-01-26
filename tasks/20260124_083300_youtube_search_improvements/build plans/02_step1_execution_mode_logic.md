# Build Plan 2: Step 1 Search Execution Mode Logic

**Status:** Pending  
**Estimated Complexity:** Medium  
**Dependencies:** None (but works with Build Plan 1)  
**Related Feedback Items:** #8

## Objective

Make Step 1 search execution mode dynamic and context-aware:
1. Auto-select "Planned queries" mode when queries were generated in Step 0
2. Hide irrelevant options when "Planned queries" mode is selected
3. Show only "Run planned queries" button when in planned mode

## Current Issues

1. **Wrong default:** After generating queries in Step 0, Step 1 defaults to "Single query" instead of "Planned queries"
2. **Confusing UI:** When "Planned queries" is selected, users still see:
   - "Search Query:" input field
   - "Enter YouTube search terms..." placeholder
   - "Search YouTube" button
3. **Poor UX:** These elements are irrelevant when using planned queries

## Implementation Tasks

### Task 2.1: Auto-select Planned Query Mode
- [ ] Detect when planned queries exist: `st.session_state.planned_queries` has items
- [ ] Auto-set `st.session_state.search_execution_mode = "planned"` when:
  - Planned queries exist AND
  - User just generated queries (or queries were added/edited)
- [ ] Logic location: In Step 1 section, before the radio button
- [ ] Only auto-select if mode hasn't been manually changed by user (track user preference)

### Task 2.2: Conditionally Hide Single Query UI
- [ ] When `search_execution_mode == "planned"`:
  - Hide or disable "Search Query:" text input
  - Hide "Search YouTube" button
  - Show only "Run planned queries" button
- [ ] When `search_execution_mode == "single"`:
  - Show "Search Query:" input
  - Show "Search YouTube" button
  - Hide "Run planned queries" button
- [ ] Use `st.container()` or conditional rendering with `if/else`

### Task 2.3: Improve Visual Feedback
- [ ] When planned mode is active, show clear indicator
- [ ] Display count: "X planned queries ready to run"
- [ ] Consider info message: "Using X planned queries from Step 0"

## Code Locations

**File:** `pages/01_YouTube_Search.py`

- **Step 1 Section:** Lines ~578-652
- **Search execution mode radio:** Lines ~611-624
- **Search input and button:** Lines ~626-638
- **Planned search button:** Lines ~640-648

## Implementation Details

### Auto-selection Logic
```python
# Before radio button in Step 1
if st.session_state.input_mode == "search":
    # Auto-select planned mode if queries exist and mode hasn't been manually set
    if (st.session_state.planned_queries 
        and len(st.session_state.planned_queries) > 0
        and not st.session_state.get('execution_mode_manually_set', False)):
        st.session_state.search_execution_mode = "planned"
```

### Conditional UI Rendering
```python
# Search input section
if st.session_state.search_execution_mode == "single":
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(...)
    with col2:
        search_button = st.button("Search YouTube", ...)
    planned_search_button = False
else:  # planned mode
    st.info(f"Using {len(st.session_state.planned_queries)} planned queries from Step 0")
    planned_search_button = st.button("Run planned queries", ...)
    search_query = ""  # Not used but maintain state
    search_button = False
```

## Testing Checklist

- [ ] After generating queries in Step 0, Step 1 auto-selects "Planned queries"
- [ ] When planned mode selected, single query UI is hidden
- [ ] When single mode selected, planned query UI is hidden
- [ ] "Run planned queries" button works correctly
- [ ] Switching modes works smoothly
- [ ] No broken state when switching between modes
- [ ] Session state persists correctly

## Success Criteria

- Dynamic mode selection based on context
- Clean UI without irrelevant options
- Clear visual feedback about which mode is active
- No confusion about what will execute

## Edge Cases

- What if user generates queries, then deletes them all? → Should switch back to single mode
- What if user manually switches to single mode? → Should respect user choice
- What if planned queries exist but user wants single query? → Allow manual override

## Notes

- Consider adding a "switch to single query" link when in planned mode (if user wants to override)
- Track user preference to avoid auto-switching after manual selection
