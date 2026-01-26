# Build Plan 1: Step 0 UI/UX Improvements

**Status:** Pending  
**Estimated Complexity:** Low-Medium  
**Dependencies:** None  
**Related Feedback Items:** #1, #2, #5

## Objective

Improve the user experience in Step 0 (Query Planning) by:
1. Adding helpful tips about editing queries
2. Removing confusing "Clear planned queries" button
3. Adding "required terms in title and description" field
4. Reorganizing the queries section for better visual flow

## Current Issues

1. **Missing user guidance:** Users don't know they can freely edit the search queries
2. **Confusing UI flow:** When user pastes queries and presses Ctrl+Enter, the "queries to run" section appears, which doesn't make logical sense
3. **Unnecessary button:** "Clear planned queries" button is confusing - users can just select all and delete manually
4. **Missing feature:** No field for "required terms in title and description" that could inform both search queries and AI filter

## Implementation Tasks

### Task 1.1: Add User Tip
- [ ] Add an info tip or help text near the "Planned queries" text area
- [ ] Message: "💡 Tip: You can freely edit the search queries or add your own list here. One query per line."
- [ ] Position: Above or below the text area, visually clear but not intrusive

### Task 1.2: Remove "Clear planned queries" Button
- [ ] Remove the button at line ~570 in `pages/01_YouTube_Search.py`
- [ ] Remove associated session state clearing logic (or keep minimal cleanup if needed)
- [ ] Verify no other code depends on this button

### Task 1.3: Add "Required Terms" Field
- [ ] Add new text input field: "Required terms in title and description"
- [ ] Position: In Step 0, after "Optional guidance for the planner" field
- [ ] Store in session state: `st.session_state.required_terms`
- [ ] Add help text: "Keywords that must appear in video titles or descriptions. These will inform both search query generation and AI filtering."
- [ ] This field will be used in:
  - Query planner prompt (add to messages)
  - AI filter prompt (in Build Plan 3/4)

### Task 1.4: Reorganize Queries Section
- [ ] Move "Queries to run" number input to a more logical location
- [ ] Consider placing it:
  - After query generation but before the text area, OR
  - In the "Query planning settings" expander
- [ ] Ensure visual flow: Generate → Review/Edit → Configure → Execute

## Code Locations

**File:** `pages/01_YouTube_Search.py`

- **Step 0 Section:** Lines ~456-576
- **Planned queries text area:** Lines ~548-559
- **Queries to run input:** Lines ~561-574
- **Clear button:** Lines ~570-574

## Testing Checklist

- [ ] Tip appears and is helpful/clear
- [ ] "Clear planned queries" button is removed
- [ ] Required terms field appears and stores value correctly
- [ ] Required terms are included in query planner messages
- [ ] Visual flow makes sense when pasting queries
- [ ] No console errors or broken functionality
- [ ] Session state persists correctly across reruns

## Success Criteria

- Users understand they can edit queries
- No confusing UI elements remain
- Required terms field works and integrates with query planning
- Better visual flow in Step 0

## Notes

- The "queries to run" section location issue might be resolved by better organization
- Required terms will need integration in later build plans (AI filter)
- Consider making the tip dismissible if it becomes annoying for frequent users
