# Add Visible Confirm Button to URL Input

## Task Overview
Add a visible confirm button alongside the existing ctrl+enter keyboard shortcut for URL input submission. The current interface relies only on ctrl+enter which is not intuitive for users.

## Current State
- URL input uses `st.text_area` with placeholder text
- Only ctrl+enter keyboard shortcut triggers submission
- No visible button for confirmation

## Desired State
- Keep existing ctrl+enter functionality
- Add visible "Submit URLs" button below the textarea
- Button should be prominent and clearly indicate the action
- Maintain current layout and styling consistency

## Technical Details
- Located in `pages/1_Bulk_Transcribe.py` around line 204-210
- Need to modify the input section to include button alongside textarea
- Button should trigger the same processing logic as ctrl+enter

## Success Criteria
- [ ] Visible confirm button appears below URL input textarea
- [ ] Button triggers URL processing when clicked
- [ ] ctrl+enter keyboard shortcut still works
- [ ] Button styling matches Streamlit design patterns
- [ ] No regression in existing functionality