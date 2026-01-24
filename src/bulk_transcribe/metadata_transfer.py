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


def validate_metadata_list(metadata_list: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
    """
    Validate metadata list structure and return (is_valid, error_messages).

    Args:
        metadata_list: List of video metadata dictionaries

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not isinstance(metadata_list, list):
        errors.append("Metadata must be a list")
        return False, errors

    if not metadata_list:
        errors.append("Metadata list is empty")
        return False, errors

    for i, item in enumerate(metadata_list):
        if not isinstance(item, dict):
            errors.append(f"Item {i+1}: Must be a dictionary")
            continue

        # Check required fields
        required_fields = ['video_id', 'video_url']
        for field in required_fields:
            if field not in item or not item[field]:
                errors.append(f"Item {i+1}: Missing required field '{field}'")

        # Check URL format
        video_url = item.get('video_url', '')
        if video_url and not ('youtube.com' in video_url or 'youtu.be' in video_url):
            errors.append(f"Item {i+1}: Invalid YouTube URL format")

    return len(errors) == 0, errors