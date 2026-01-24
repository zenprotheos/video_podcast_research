# Implementation Guide: Add Visible Confirm Button

## Target Location
File: `pages/1_Bulk_Transcribe.py`
Lines: ~204-210 (URL input section)

## Current Code Structure

```python
# Option 1: Paste URLs directly
input_method = st.radio(
    "Choose input method:",
    ["Paste URLs (one per line)", "Upload file"],
    horizontal=True
)

parsed: Optional[ParsedSheet] = None

if input_method == "Paste URLs (one per line)":
    # Pre-fill with URLs from search tool if available
    default_text = ""
    if prepopulated_urls:
        default_text = "\n".join(prepopulated_urls)

    url_text = st.text_area(
        "Paste YouTube URLs or MP3 links (one per line):",
        height=200,
        placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2\nhttps://example.com/podcast.mp3",
        help="Paste URLs directly here. One URL per line. Blank lines are ignored.",
        value=default_text
    )
```

## Proposed Implementation

### Option 1: Simple Button Below Textarea (Recommended)

```python
if input_method == "Paste URLs (one per line)":
    # Pre-fill with URLs from search tool if available
    default_text = ""
    if prepopulated_urls:
        default_text = "\n".join(prepopulated_urls)

    url_text = st.text_area(
        "Paste YouTube URLs or MP3 links (one per line):",
        height=200,
        placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2\nhttps://example.com/podcast.mp3",
        help="Paste URLs directly here. One URL per line. Blank lines are ignored.",
        value=default_text
    )

    # Add visible confirm button
    submit_urls = st.button(
        "Submit URLs",
        type="primary",
        help="Click to parse and validate the URLs above, or press ctrl+enter",
        use_container_width=True
    )

    # Process URLs if button clicked OR if ctrl+enter was used (existing logic)
    if submit_urls or (url_text and url_text != default_text):
        # Existing URL processing logic here...
```

### Option 2: Horizontal Layout (Alternative)

```python
if input_method == "Paste URLs (one per line)":
    col1, col2 = st.columns([3, 1])

    with col1:
        url_text = st.text_area(
            "Paste YouTube URLs or MP3 links (one per line):",
            height=200,
            placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2\nhttps://example.com/podcast.mp3",
            help="Paste URLs directly here. One URL per line. Blank lines are ignored.",
            value=default_text
        )

    with col2:
        st.write("")  # Spacing
        st.write("")
        submit_urls = st.button(
            "Submit URLs",
            type="primary",
            help="Click to parse and validate the URLs above",
            use_container_width=True
        )

    # Process URLs if button clicked OR if ctrl+enter was used
    if submit_urls or (url_text and url_text != default_text):
        # Existing URL processing logic here...
```

## Key Implementation Details

### 1. Button Parameters
- `label`: "Submit URLs" (clear, action-oriented)
- `type`: "primary" (prominent styling)
- `help`: Descriptive text explaining both input methods
- `use_container_width`: True (better visual balance)

### 2. Event Handling Logic
The button should trigger the same URL processing logic as ctrl+enter:

```python
# Check if user activated submission (button click OR ctrl+enter)
user_submitted = submit_urls or (url_text and url_text.strip())

if user_submitted:
    # Parse URLs and create ParsedSheet
    # ... existing logic ...
```

### 3. State Management
- Preserve existing prepopulation from search tools
- Handle empty input gracefully
- Show appropriate success/error messages

### 4. Styling Considerations
- Button should be visually prominent but not overwhelming
- Maintain consistent spacing with existing UI elements
- Consider mobile responsiveness

## Testing Checklist

### Functionality Tests
- [ ] Button appears below textarea
- [ ] Button click triggers URL parsing
- [ ] ctrl+enter still works
- [ ] Empty input shows appropriate message
- [ ] Invalid URLs show validation errors
- [ ] Prepopulated URLs work with button

### UI/UX Tests
- [ ] Button styling matches app theme
- [ ] Button is clearly associated with textarea
- [ ] Help text is informative
- [ ] Responsive on different screen sizes

### Integration Tests
- [ ] Column mapping section appears after submission
- [ ] Session creation works
- [ ] Error handling preserved
- [ ] Progress tracking unaffected

## Rollback Plan

If issues arise, the button can be easily removed by:
1. Deleting the `st.button()` call
2. Removing the `submit_urls` variable
3. Reverting the condition to original logic

The ctrl+enter functionality will remain intact as fallback.