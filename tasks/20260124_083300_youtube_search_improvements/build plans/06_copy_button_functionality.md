# Build Plan 6: Copy Button Functionality

**Status:** Pending  
**Estimated Complexity:** Low  
**Dependencies:** None  
**Related Feedback Items:** #10

## Objective

Fix copy buttons to copy data immediately on click, without requiring a second click. Show success/error feedback.

## Current Issues

1. **Two-click problem:** When user clicks "Copy" button:
   - First click: Shows green tip note + code block with data
   - User must click again (select code block) to actually copy
2. **Poor UX:** Unnecessary extra step
3. **Unclear feedback:** Success message says "select and copy the code block above" which is confusing

## Implementation Tasks

### Task 6.1: Implement Immediate Clipboard Copy
- [ ] Use Streamlit's clipboard functionality or `pyperclip` library
- [ ] On button click, immediately copy data to clipboard
- [ ] Remove the `st.code()` display (or keep as optional visual feedback)
- [ ] Show success message immediately after copy

### Task 6.2: Update All Copy Buttons
- [ ] "Copy URLs" button (Line ~1178)
- [ ] "Copy IDs" button (Line ~1185)
- [ ] "Copy as JSON" button (Line ~1192)
- [ ] Ensure all three buttons work the same way

### Task 6.3: Improve Feedback Messages
- [ ] Success: "✓ Copied X URLs to clipboard" (clear, immediate)
- [ ] Error: "Failed to copy to clipboard" (if copy fails)
- [ ] Remove confusing "select and copy the code block above" message

### Task 6.4: Add Error Handling
- [ ] Handle clipboard errors gracefully
- [ ] Fallback: If clipboard fails, show code block as before (with instructions)
- [ ] Log errors for debugging

## Code Locations

**File:** `pages/01_YouTube_Search.py`

- **Copy URLs button:** Lines ~1178-1182
- **Copy IDs button:** Lines ~1185-1189
- **Copy JSON button:** Lines ~1192-1207

## Implementation Details

### Using pyperclip (Recommended)
```python
import pyperclip

# In copy button handler
if st.button(f"Copy {action_label} URLs", ...):
    urls = [item.video_url for item in action_videos]
    urls_text = "\n".join(urls)
    
    try:
        pyperclip.copy(urls_text)
        st.success(f"✓ Copied {len(urls)} {action_label.lower()} URLs to clipboard")
    except Exception as e:
        st.error(f"Failed to copy to clipboard: {str(e)}")
        # Fallback: show code block
        st.code(urls_text, language=None)
        st.info("Please manually copy the text above")
```

### Using Streamlit's write (Alternative)
Streamlit doesn't have native clipboard API, so `pyperclip` is the best option.

### All Three Buttons
```python
# Copy URLs
if st.button(f"Copy {action_label} URLs", ...):
    urls = [item.video_url for item in action_videos]
    urls_text = "\n".join(urls)
    try:
        pyperclip.copy(urls_text)
        st.success(f"✓ Copied {len(urls)} URLs to clipboard")
    except Exception as e:
        st.error(f"Copy failed: {str(e)}")
        st.code(urls_text)

# Copy IDs
if st.button(f"Copy {action_label} IDs", ...):
    ids = [item.video_id for item in action_videos]
    ids_text = ",".join(ids)
    try:
        pyperclip.copy(ids_text)
        st.success(f"✓ Copied {len(ids)} video IDs to clipboard")
    except Exception as e:
        st.error(f"Copy failed: {str(e)}")
        st.code(ids_text)

# Copy JSON
if st.button(f"Copy {action_label} as JSON", ...):
    import json
    results_data = [...]
    json_text = json.dumps(results_data, indent=2, ensure_ascii=False)
    try:
        pyperclip.copy(json_text)
        st.success(f"✓ Copied {len(results_data)} results as JSON to clipboard")
    except Exception as e:
        st.error(f"Copy failed: {str(e)}")
        st.code(json_text, language="json")
```

## Dependencies

- **Add to requirements.txt:** `pyperclip>=1.8.2`
- **Install:** `pip install pyperclip`

## Testing Checklist

- [ ] Copy URLs button copies immediately on click
- [ ] Copy IDs button copies immediately on click
- [ ] Copy JSON button copies immediately on click
- [ ] Success message appears immediately
- [ ] Data is actually in clipboard (test by pasting)
- [ ] Error handling works if clipboard fails
- [ ] Fallback code block shows if copy fails
- [ ] No console errors

## Success Criteria

- One-click copy functionality works
- Clear success/error feedback
- No confusing messages
- Works across all three copy buttons
- Graceful error handling

## Edge Cases

- **Clipboard not available:** Some environments (Linux servers) might not have clipboard
- **Large data:** Very long URLs/JSON might have clipboard limits
- **Browser restrictions:** Some browsers restrict clipboard access

## Notes

- `pyperclip` is cross-platform and works well with Streamlit
- Consider keeping code block as optional visual feedback (toggle?)
- Success message should be brief and clear
- Test on Windows (user's OS) to ensure it works

## Alternative Approaches

1. **Browser clipboard API:** Would require JavaScript, more complex
2. **Streamlit component:** Could create custom component, but overkill
3. **pyperclip:** Simple, reliable, recommended
