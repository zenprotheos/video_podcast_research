# Direct Input for AI Video Filtering - Implementation Brainstorm

## Problem Statement
Users want to paste YouTube URLs and/or JSON data directly into the app to use with AI filtering, rather than only being able to search YouTube first. This enables testing the AI filtering with custom datasets and integrating with external sources.

## Current State Analysis

### Available Test Data
- **JSON Format**: `tests/sample_youtube_JSON_list.json` - Array of video objects with full metadata
- **URL List**: `tests/sample_youtube_URL_list.md` - Simple list of YouTube URLs (one per line)

### Existing Workflow
1. User searches YouTube → gets results
2. User adds research context
3. User enables AI filtering
4. User clicks "Filter Videos with AI"
5. AI processes search results

### Desired Workflow Addition
1. User pastes URLs/JSON directly
2. System parses and converts to VideoSearchItem format
3. User adds research context
4. User enables AI filtering
5. User clicks "Filter Videos with AI"
6. AI processes the pasted data

## Proposed Solution Architecture

### 1. New UI Component: "Direct Input Mode"

Add a new section in the YouTube Search page with a toggle between:
- **Search Mode** (current): Search YouTube API
- **Direct Input Mode** (new): Paste URLs or JSON

```python
input_mode = st.radio(
    "Input Mode:",
    ["🔍 Search YouTube", "📝 Direct Input"],
    horizontal=True
)
```

### 2. Direct Input Interface

When "Direct Input Mode" is selected:

#### Input Methods
- **Textarea for URLs**: Multi-line text area accepting one URL per line
- **Textarea for JSON**: Accepts JSON array of video objects
- **File Upload**: Optional file upload for larger datasets

#### Auto-Detection
- Detect if input contains `youtube.com` or `youtu.be` → treat as URL list
- Detect if input starts with `[` and ends with `]` → treat as JSON array
- Detect if input contains `{` and `}` → attempt JSON parsing

#### Sample Input Prompts
```
# URLs (one per line):
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2

# OR JSON array:
[
  {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "channel_title": "Channel Name",
    "description": "Video description...",
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }
]
```

### 3. Data Processing Pipeline

#### URL List Processing
1. Split by newlines, filter empty lines
2. Extract video IDs using existing `extract_video_id()` function
3. Fetch metadata for each video using `fetch_youtube_metadata()`
4. Convert to `VideoSearchItem` objects

#### JSON Processing
1. Parse JSON array
2. Validate required fields: `video_id`, `title`, `video_url`
3. Map JSON fields to `VideoSearchItem` dataclass
4. Fill missing fields with defaults or fetched data

#### Unified Output
- Both processing paths output `List[VideoSearchItem]`
- Store in session state as `direct_input_videos`
- Create mock `SearchResult` object for UI consistency

### 4. Integration with AI Filtering

#### Modified Workflow
1. **Input Phase**: User selects input mode and provides data
2. **Processing Phase**: System converts input to `VideoSearchItem` list
3. **Context Phase**: User adds research context (same as current)
4. **Filtering Phase**: AI processes the direct input videos (same logic)

#### UI State Management
- `st.session_state.input_mode = "search" | "direct"`
- `st.session_state.direct_input_videos = List[VideoSearchItem]`
- `st.session_state.direct_input_raw = str` (for display/edit)

#### Error Handling
- Invalid URLs: Show warnings, skip invalid entries
- Malformed JSON: Show parsing errors with line numbers
- Missing metadata: Attempt to fetch, show warnings for failures
- Empty results: Clear messaging about what went wrong

### 5. Enhanced User Experience

#### Progressive Disclosure
- Show input area only when Direct Input mode is selected
- Expand advanced options (file upload, format hints) in collapsible sections
- Show processing status with spinners and progress

#### Data Validation & Feedback
- Real-time validation as user types
- Preview of parsed videos before filtering
- Error highlighting for problematic entries
- Success metrics: "Loaded X videos from your input"

#### Integration with Existing Features
- Direct Input results work with all existing actions (copy, send to transcript)
- AI filtering works identically on direct input vs search results
- Session state persistence for input data

### 6. Technical Implementation Details

#### New Functions Needed
```python
def parse_direct_input(input_text: str) -> List[VideoSearchItem]:
    """Parse URLs or JSON into VideoSearchItem list"""

def urls_to_video_items(urls: List[str]) -> List[VideoSearchItem]:
    """Convert URL list to video items with metadata fetching"""

def json_to_video_items(json_data: str) -> List[VideoSearchItem]:
    """Convert JSON array to video items"""

def create_search_result_from_items(items: List[VideoSearchItem]) -> SearchResult:
    """Create SearchResult object for UI consistency"""
```

#### File Structure
```
pages/2_YouTube_Search.py (modified)
├── Input mode selector
├── Search interface (existing)
├── Direct input interface (new)
└── Results display (modified)

src/bulk_transcribe/direct_input.py (new)
├── parse_direct_input()
├── urls_to_video_items()
├── json_to_video_items()
└── create_search_result_from_items()
```

#### Dependencies
- Reuse existing `fetch_youtube_metadata()` for URL processing
- Reuse existing `extract_video_id()` for URL parsing
- Add `json` module for JSON processing (already imported)

### 7. Testing Strategy

#### Test Cases
1. **URL List**: Various URL formats (youtube.com, youtu.be, with/without query params)
2. **JSON Array**: Full metadata, minimal metadata, malformed JSON
3. **Mixed Input**: URLs + JSON detection
4. **Error Cases**: Invalid URLs, network failures, quota limits
5. **Integration**: Direct input → AI filtering → transcript tool

#### Sample Data Integration
- Pre-populate examples from `tests/` directory
- "Load Sample Data" buttons for quick testing
- Clear examples for production use

### 8. Benefits & Use Cases

#### User Benefits
- **Testing**: Easy testing of AI filtering with known datasets
- **Integration**: Import data from other tools/sources
- **Flexibility**: Work with pre-curated video lists
- **Offline Workflow**: Process videos without API calls

#### Technical Benefits
- **Modular Design**: Clean separation between search and direct input
- **Reusability**: AI filtering logic works with any video source
- **Extensibility**: Easy to add more input formats (CSV, etc.)

## Implementation Phases

### Phase 1: Core Direct Input (Priority: High)
- Basic URL and JSON parsing
- Integration with existing AI filtering
- Error handling and validation

### Phase 2: Enhanced UX (Priority: Medium)
- File upload support
- Better validation and feedback
- Sample data integration

### Phase 3: Advanced Features (Priority: Low)
- CSV/TSV support
- Bulk metadata fetching optimization
- Export/import of processed datasets

## Risks & Mitigations

### Performance Risks
- **Multiple API calls**: For URL lists, batch metadata fetching
- **Large datasets**: Pagination for display, chunking for processing
- **Rate limits**: Queue requests, show progress, handle failures gracefully

### Data Quality Risks
- **Incomplete metadata**: Graceful degradation, clear warnings
- **Inconsistent formats**: Robust parsing with fallbacks
- **Invalid data**: Input validation with helpful error messages

### UX Risks
- **Mode confusion**: Clear labeling, progressive disclosure
- **Error overwhelm**: Prioritize critical errors, batch warnings
- **Workflow disruption**: Maintain existing search functionality

## Success Criteria

- Users can paste URL lists and get them processed into filterable video data
- Users can paste JSON arrays and get them converted to video items
- AI filtering works identically on direct input vs search results
- Clear error messages guide users when input is invalid
- Performance is acceptable for reasonable dataset sizes (50-200 videos)
- Integration with existing transcript workflow is seamless

## Open Questions

1. **Batch Size Limits**: What's the reasonable limit for direct input processing?
2. **Caching Strategy**: Should we cache metadata fetches to avoid repeated API calls?
3. **Validation Strictness**: How strict should we be about required fields in JSON input?
4. **Progress Indication**: For large datasets, how detailed should the processing progress be?
5. **Session Persistence**: Should direct input data persist across page refreshes?

---

*Ready for implementation approval. This design maintains backward compatibility while adding powerful direct input capabilities for AI filtering testing and integration.*