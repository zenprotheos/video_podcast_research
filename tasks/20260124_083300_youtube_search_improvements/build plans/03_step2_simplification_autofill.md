# Build Plan 3: Step 2 Simplification & Auto-fill

**Status:** ⚠️ **OBSOLETE - REPLACED BY BUILD PLAN 4**  
**Replaced By:** `04_step2_restructure_workflow.md`  
**Estimated Complexity:** Medium  
**Dependencies:** Build Plan 1 (for required terms integration)  
**Related Feedback Items:** #3, #5

## Objective

Simplify Step 2 and improve UX by:
1. Auto-filling the filter prompt with original research prompt + optional guidance from Step 0
2. Consider removing Step 2 entirely and moving AI filter to a checkbox/button after Step 3
3. Integrate "required terms" field into the filter prompt

## Current Issues

1. **Redundant input:** Step 2 asks for research context even though it was already provided in Step 0
2. **Poor UX:** Users have to re-enter information they already provided
3. **Unclear necessity:** Step 2 might not be needed if research prompt was already provided
4. **Missing integration:** Required terms from Step 0 aren't included in filter prompt

## Implementation Tasks

### Task 3.1: Auto-fill Filter Prompt
- [ ] When Step 2 appears, check if research prompt exists from Step 0
- [ ] Auto-populate "Research Context/Goal:" text area with:
  - Original research prompt from Step 0
  - Optional guidance from Step 0 (if provided)
  - Required terms from Step 0 (if provided) - format: "Required terms: [terms]"
- [ ] Allow user to edit the auto-filled prompt
- [ ] Use session state: `st.session_state.research_context` (already exists)

### Task 3.2: Evaluate Step 2 Removal
- [ ] **Option A (Simpler):** Keep Step 2 but auto-fill it
- [ ] **Option B (More radical):** Remove Step 2 entirely, move AI filter to Step 3
- [ ] Decision criteria:
  - If research prompt exists → Auto-fill Step 2 (Option A)
  - If no research prompt → Show Step 2 for manual entry (Option A)
  - OR: Always show AI filter checkbox/button in Step 3 (Option B)

### Task 3.3: Implement Auto-fill Logic
- [ ] Check if `st.session_state.query_planner_prompt` exists and has content
- [ ] Build combined prompt:
  ```python
  base_prompt = st.session_state.query_planner_prompt
  if st.session_state.query_planner_notes:
      base_prompt += f"\n\nAdditional guidance: {st.session_state.query_planner_notes}"
  if st.session_state.required_terms:  # From Build Plan 1
      base_prompt += f"\n\nRequired terms in title/description: {st.session_state.required_terms}"
  ```
- [ ] Only auto-fill if `st.session_state.research_context` is empty (don't overwrite user edits)
- [ ] Set auto-fill on first render of Step 2 after queries are generated/searched

### Task 3.4: Consider Step 2 Removal (Optional)
- [ ] If removing Step 2:
  - Move "Enable AI Filtering" checkbox to Step 3
  - Move model selection to Step 3 (in expander or collapsible section)
  - Auto-build research context from Step 0 data
  - Show "Filter Videos with AI" button immediately after results load
- [ ] This is a more significant change - evaluate with user feedback

## Code Locations

**File:** `pages/01_YouTube_Search.py`

- **Step 2 Section:** Lines ~896-966
- **Research context text area:** Lines ~902-908
- **AI filtering toggle:** Lines ~911-915
- **Model selection:** Lines ~918-957

## Implementation Details

### Auto-fill Logic
```python
# In Step 2 section, before text area
if not st.session_state.research_context.strip():
    # Auto-build from Step 0 data
    auto_fill_parts = []
    
    if st.session_state.query_planner_prompt.strip():
        auto_fill_parts.append(st.session_state.query_planner_prompt.strip())
    
    if st.session_state.query_planner_notes.strip():
        auto_fill_parts.append(f"Additional guidance: {st.session_state.query_planner_notes.strip()}")
    
    if st.session_state.get('required_terms', '').strip():
        auto_fill_parts.append(f"Required terms in title/description: {st.session_state.required_terms.strip()}")
    
    if auto_fill_parts:
        st.session_state.research_context = "\n\n".join(auto_fill_parts)
```

### Integration with Required Terms
- When building AI filter prompt in `video_filter.py`, include required terms
- Modify `_build_user_prompt()` to accept and use required terms
- Add keyword matching logic if needed (exact match vs. semantic)

## Testing Checklist

- [ ] Step 2 auto-fills when research prompt exists from Step 0
- [ ] Auto-fill includes: research prompt + optional guidance + required terms
- [ ] User can edit the auto-filled prompt
- [ ] Auto-fill doesn't overwrite user edits on rerun
- [ ] If no research prompt exists, Step 2 shows empty (manual entry)
- [ ] Required terms are included in AI filter evaluation
- [ ] No console errors or broken functionality

## Success Criteria

- Users don't have to re-enter information from Step 0
- Filter prompt is comprehensive and includes all relevant context
- Step 2 feels helpful, not redundant
- Required terms influence AI filtering

## Decision Point

**Should Step 2 be removed entirely?**

**Pros of removal:**
- Simpler workflow
- Less redundant input
- AI filter happens at the right time (after results)

**Cons of removal:**
- Less flexibility for users who want different filter prompts
- Model selection might clutter Step 3
- Harder to configure before seeing results

**Recommendation:** Start with auto-fill (Task 3.1-3.3), then evaluate removal based on user feedback.

## Notes

- Auto-fill should be smart: only fill if empty, preserve user edits
- Consider showing a badge/indicator: "Auto-filled from Step 0" so users know where it came from
- Required terms integration might need changes in `video_filter.py` (separate task or part of Build Plan 4)
