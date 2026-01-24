# Proposed Solution Design: Metadata Preservation Between YouTube Search and Bulk Transcribe

## Solution Overview

Implement a metadata preservation mechanism that maintains rich video information when transferring data between the YouTube Search tool and Bulk Transcribe tool, while maintaining backward compatibility.

## Core Design Principles

1. **Zero Breaking Changes**: Existing functionality must continue to work
2. **Additive Enhancement**: New features build on existing patterns
3. **Graceful Degradation**: System works with partial or missing metadata
4. **Performance Conscious**: Minimize impact on session state and UI performance

## Solution Architecture

### 1. Enhanced Session State Structure

#### Current Session State (Limited)
```python
st.session_state['transcript_urls'] = ['https://youtube.com/watch?v=123', ...]
st.session_state['transcript_source'] = 'youtube_search'  # Optional
```

#### Proposed Session State (Enhanced)
```python
# Backward compatible - existing code continues to work
st.session_state['transcript_urls'] = ['https://youtube.com/watch?v=123', ...]
st.session_state['transcript_source'] = 'youtube_search_filtered'

# New metadata preservation
st.session_state['transcript_metadata'] = [
    {
        'video_id': 'abc123',
        'title': 'Video Title',
        'description': 'Video description...',
        'channel_title': 'Channel Name',
        'published_at': '2026-01-15T10:30:00Z',
        'thumbnail_url': 'https://img.youtube.com/vi/abc123/default.jpg',
        'video_url': 'https://youtube.com/watch?v=abc123',
        # ... other metadata fields
    },
    # ... more videos
]
```

### 2. Metadata Serialization Strategy

#### VideoSearchItem to Dict Conversion
```python
def video_search_item_to_dict(item: VideoSearchItem) -> Dict[str, Any]:
    """Convert VideoSearchItem to session-state compatible dict."""
    return {
        'video_id': item.video_id,
        'title': item.title,
        'description': item.description,
        'channel_title': item.channel_title,
        'channel_id': item.channel_id,
        'published_at': item.published_at,
        'thumbnail_url': item.thumbnail_url,
        'thumbnail_high_url': item.thumbnail_high_url,
        'video_url': item.video_url,
        'raw_data': item.raw_data,  # Full API response for debugging
    }
```

#### Dict to VideoSearchItem Reconstruction
```python
def dict_to_video_search_item(data: Dict[str, Any]) -> VideoSearchItem:
    """Reconstruct VideoSearchItem from dict."""
    return VideoSearchItem(
        video_id=data['video_id'],
        title=data.get('title', ''),
        description=data.get('description', ''),
        channel_title=data.get('channel_title', ''),
        channel_id=data.get('channel_id', ''),
        published_at=data.get('published_at', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
        thumbnail_high_url=data.get('thumbnail_high_url', ''),
        video_url=data.get('video_url', ''),
        raw_data=data.get('raw_data', {}),
    )
```

### 3. Bulk Transcribe Input Handler Enhancement

#### New Input Detection Logic
```python
def detect_input_type(session_state) -> str:
    """
    Detect the type of input available in session state.

    Returns:
        'rich_metadata' - Full metadata available
        'urls_only' - Only URLs available (legacy)
        'none' - No input available
    """
    has_metadata = 'transcript_metadata' in session_state and session_state['transcript_metadata']
    has_urls = 'transcript_urls' in session_state and session_state['transcript_urls']

    if has_metadata:
        return 'rich_metadata'
    elif has_urls:
        return 'urls_only'
    else:
        return 'none'
```

#### Metadata to ParsedSheet Conversion
```python
def metadata_to_parsed_sheet(metadata_list: List[Dict[str, Any]]) -> ParsedSheet:
    """
    Convert rich metadata to ParsedSheet format expected by bulk transcribe.
    """
    # Define all available columns
    columns = [
        'source_type', 'youtube_url', 'title', 'description',
        'channel_title', 'published_at', 'thumbnail_url', 'video_id'
    ]

    rows = []
    for item in metadata_list:
        row = {
            'source_type': 'youtube',
            'youtube_url': item.get('video_url', ''),
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'channel_title': item.get('channel_title', ''),
            'published_at': item.get('published_at', ''),
            'thumbnail_url': item.get('thumbnail_url', ''),
            'video_id': item.get('video_id', ''),
        }
        rows.append(row)

    return ParsedSheet(columns=columns, rows=rows)
```

## Implementation Plan

### Phase 1: YouTube Search Tool Changes

#### File: `pages/2_YouTube_Search.py`

**Location:** Around line 599-613 (Send to Transcript Tool button)

**Current Code:**
```python
with col4:
    if st.button(f"📝 Send {action_label} to Transcript Tool", type="primary", use_container_width=True):
        # Send videos to transcript tool
        urls = [item.video_url for item in action_videos]

        st.session_state['transcript_urls'] = urls
        st.session_state['transcript_source'] = action_source
```

**Proposed Code:**
```python
with col4:
    if st.button(f"📝 Send {action_label} to Transcript Tool", type="primary", use_container_width=True):
        # Send videos to transcript tool with rich metadata
        urls = [item.video_url for item in action_videos]

        # Preserve full metadata for enhanced experience
        metadata_list = [video_search_item_to_dict(item) for item in action_videos]

        st.session_state['transcript_urls'] = urls  # Backward compatibility
        st.session_state['transcript_metadata'] = metadata_list  # Rich metadata
        st.session_state['transcript_source'] = action_source
```

### Phase 2: Bulk Transcribe Tool Changes

#### File: `pages/1_Bulk_Transcribe.py`

**Location:** Around line 176-187 (Pre-populated URLs section)

**Current Code:**
```python
# Check for pre-populated URLs from YouTube Search tool
prepopulated_urls = None
if 'transcript_urls' in st.session_state:
    prepopulated_urls = st.session_state['transcript_urls']
    prepopulated_source = st.session_state.get('transcript_source', 'unknown')
```

**Proposed Code:**
```python
# Check for pre-populated data from YouTube Search tool
prepopulated_urls = None
prepopulated_metadata = None
input_type = detect_input_type(st.session_state)

if input_type == 'rich_metadata':
    prepopulated_metadata = st.session_state['transcript_metadata']
    prepopulated_urls = [item['video_url'] for item in prepopulated_metadata]  # Extract URLs for compatibility
    prepopulated_source = st.session_state.get('transcript_source', 'youtube_search_rich')
elif input_type == 'urls_only':
    prepopulated_urls = st.session_state['transcript_urls']
    prepopulated_source = st.session_state.get('transcript_source', 'unknown')
```

#### File: `pages/1_Bulk_Transcribe.py`

**Location:** Around line 198-242 (URL input processing)

**Current Code:**
```python
if input_method == "Paste URLs (one per line)":
    # Pre-fill with URLs from search tool if available
    default_text = ""
    if prepopulated_urls:
        default_text = "\n".join(prepopulated_urls)
```

**Proposed Code:**
```python
if input_method == "Paste URLs (one per line)":
    # Pre-fill based on input type
    default_text = ""
    if prepopulated_metadata:
        # For rich metadata, show URLs but indicate metadata is available
        default_text = "\n".join(prepopulated_urls)
        st.info("📊 Rich metadata available - video details will be preserved in the processing table")
    elif prepopulated_urls:
        # Legacy URL-only input
        default_text = "\n".join(prepopulated_urls)
```

#### New Processing Logic for Rich Metadata

**Location:** After URL processing, before ParsedSheet creation

**New Code:**
```python
# Handle different input types
if prepopulated_metadata and not url_text.strip():
    # Use rich metadata directly - bypass URL parsing
    parsed = metadata_to_parsed_sheet(prepopulated_metadata)
    st.success(f"Loaded {parsed.row_count} videos with rich metadata from {prepopulated_source}")
else:
    # Original URL parsing logic for manual input or legacy compatibility
    # ... existing code ...
```

### Phase 3: Helper Functions

#### New File: `src/bulk_transcribe/metadata_transfer.py`

```python
"""
Metadata transfer utilities for preserving rich video data between tools.
"""

from typing import Dict, Any, List
from .youtube_search import VideoSearchItem
from .sheet_ingest import ParsedSheet


def video_search_item_to_dict(item: VideoSearchItem) -> Dict[str, Any]:
    """Convert VideoSearchItem to session-state compatible dict."""
    return {
        'video_id': item.video_id,
        'title': item.title,
        'description': item.description,
        'channel_title': item.channel_title,
        'channel_id': item.channel_id,
        'published_at': item.published_at,
        'thumbnail_url': item.thumbnail_url,
        'thumbnail_high_url': item.thumbnail_high_url,
        'video_url': item.video_url,
        'raw_data': item.raw_data,
    }


def dict_to_video_search_item(data: Dict[str, Any]) -> VideoSearchItem:
    """Reconstruct VideoSearchItem from dict."""
    return VideoSearchItem(
        video_id=data['video_id'],
        title=data.get('title', ''),
        description=data.get('description', ''),
        channel_title=data.get('channel_title', ''),
        channel_id=data.get('channel_id', ''),
        published_at=data.get('published_at', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
        thumbnail_high_url=data.get('thumbnail_high_url', ''),
        video_url=data.get('video_url', ''),
        raw_data=data.get('raw_data', {}),
    )


def detect_input_type(session_state) -> str:
    """
    Detect the type of input available in session state.
    """
    has_metadata = 'transcript_metadata' in session_state and session_state['transcript_metadata']
    has_urls = 'transcript_urls' in session_state and session_state['transcript_urls']

    if has_metadata:
        return 'rich_metadata'
    elif has_urls:
        return 'urls_only'
    else:
        return 'none'


def metadata_to_parsed_sheet(metadata_list: List[Dict[str, Any]]) -> ParsedSheet:
    """
    Convert rich metadata to ParsedSheet format expected by bulk transcribe.
    """
    columns = [
        'source_type', 'youtube_url', 'title', 'description',
        'channel_title', 'published_at', 'thumbnail_url', 'video_id'
    ]

    rows = []
    for item in metadata_list:
        row = {
            'source_type': 'youtube',
            'youtube_url': item.get('video_url', ''),
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'channel_title': item.get('channel_title', ''),
            'published_at': item.get('published_at', ''),
            'thumbnail_url': item.get('thumbnail_url', ''),
            'video_id': item.get('video_id', ''),
        }
        rows.append(row)

    return ParsedSheet(columns=columns, rows=rows)
```

## Error Handling and Edge Cases

### 1. Metadata Validation
- Validate required fields (video_url) before transfer
- Log warnings for missing optional fields
- Graceful fallback to URL-only mode if metadata is corrupted

### 2. Session State Size Limits
- Monitor session state size for large video lists
- Implement pagination or chunking if needed
- Provide user feedback for large transfers

### 3. Backward Compatibility
- All existing URL-only workflows continue to work
- No changes to existing user interfaces
- Legacy session state keys still supported

## Testing Strategy

### Unit Tests
```python
def test_metadata_serialization():
    # Test VideoSearchItem ↔ dict conversion
    original = VideoSearchItem(...)
    serialized = video_search_item_to_dict(original)
    reconstructed = dict_to_video_search_item(serialized)
    assert original == reconstructed

def test_input_type_detection():
    # Test detection logic
    assert detect_input_type({'transcript_metadata': [...]}) == 'rich_metadata'
    assert detect_input_type({'transcript_urls': [...]}) == 'urls_only'
    assert detect_input_type({}) == 'none'
```

### Integration Tests
- End-to-end metadata flow from search selection to bulk transcribe display
- Mixed input scenarios (metadata + manual URLs)
- Error recovery when metadata is corrupted

### User Acceptance Tests
- Verify metadata displays correctly in column mapping table
- Confirm thumbnails and rich information show properly
- Test performance with 50+ videos

## Performance Considerations

### Session State Optimization
- Only serialize essential metadata fields
- Compress large text fields if needed
- Implement lazy loading for thumbnails

### UI Performance
- Virtualize large tables if needed
- Lazy load images and rich content
- Provide loading states for metadata processing

## Rollback Plan

### Feature Flags
```python
METADATA_PRESERVATION_ENABLED = os.getenv('METADATA_PRESERVATION_ENABLED', 'true').lower() == 'true'
```

### Easy Disable
- Environment variable to disable feature
- Clear session state cleanup
- Fallback to URL-only mode

## Success Metrics

### Functional Metrics
- [ ] 100% metadata preservation for all transferred videos
- [ ] Correct display in bulk transcribe table
- [ ] Backward compatibility maintained

### Performance Metrics
- [ ] Session state size increase < 2x for typical use
- [ ] UI load time < 500ms for 50 videos
- [ ] No memory leaks or crashes

### User Experience Metrics
- [ ] Users can identify videos by title/channel in bulk transcribe
- [ ] No confusion between different videos
- [ ] Seamless workflow from search to transcription