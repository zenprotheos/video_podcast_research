# YouTube API Description Research

## Summary
- **Problem:** `search.list` returns a **truncated** `snippet.description` (insufficient for AI filtering).
- **Solution:** Use **`videos.list(part=snippet)`** to retrieve the **full** description for the video IDs returned by search.

## Evidence
- Google Search resource docs describe `snippet.description` but do not mention truncation explicitly: `https://developers.google.com/youtube/v3/docs/search`
- Community + issue evidence that `search.list` description is truncated by design:
  - `https://stackoverflow.com/questions/31373843/i-cannot-get-the-full-description-of-a-youtube-video-when-using-youtube-api-v3`
  - `https://issuetracker.google.com/issues/35174042`

## Best-practice implementation approach
- **Enrich once after de-duplication** (avoid re-fetching duplicates across queries/pages).
- **Batch IDs** (50 per request limit).
- Use `fields='items(id,snippet(description))'` to reduce payload.
- **Cache** full descriptions in session state to prevent quota burn on Streamlit reruns.

## Quota note
- `videos.list` costs **1 unit per request**, not per video. With 50 IDs per request, that’s effectively **1 unit per 50 unique videos enriched**.

