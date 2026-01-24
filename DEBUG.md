# Debug Guide

## Enabling Debug Logging

To see detailed error messages and debug info, check the Streamlit console/terminal where you ran the app.

## Common Errors

### DEAPI 422 Errors

**Error**: `422 Client Error: Unprocessable Entity`

**Possible causes**:
- Invalid video URL format
- Video URL not accessible (private, deleted, region-restricted)
- Missing required parameters

**What to check**:
1. Verify the YouTube URL is valid and publicly accessible
2. Check that `DEAPI_API_KEY` is set correctly
3. Try the URL in a browser to confirm it's accessible

### YouTube Video Unavailable

**Error**: `Video unavailable`

**Possible causes**:
- Video was deleted
- Video is private/unlisted
- Video is region-restricted
- Video ID is invalid

**What happens**:
- The app will try YouTube captions first (fails)
- Then tries DEAPI fallback (may also fail if video is truly unavailable)
- Status will show "✗ Video Unavailable" or "✗ Failed"

## Viewing Detailed Errors

Errors are shown in the status table in the app UI. For more detail:

1. Check the Streamlit console/terminal output
2. Check the session folder's `manifest.json` for error details
3. Look at individual `.metadata.json` files for YouTube metadata errors

## Testing Individual URLs

To test if a specific URL works:

```python
from src.bulk_transcribe.youtube_transcript import get_youtube_transcript
import os

url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
api_key = os.getenv("DEAPI_API_KEY")

result = get_youtube_transcript(url, api_key)
print(f"Success: {result.success}")
print(f"Method: {result.method}")
if result.error_message:
    print(f"Error: {result.error_message}")
```
