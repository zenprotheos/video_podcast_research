"""Direct input parsing for YouTube URLs and JSON data."""

import json
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .youtube_search import VideoSearchItem, SearchResult
from .youtube_metadata import fetch_youtube_metadata
from .youtube_transcript import extract_video_id


@dataclass
class DirectInputResult:
    """Result of direct input processing."""
    videos: List[VideoSearchItem]
    errors: List[str]
    warnings: List[str]
    processed_count: int
    success: bool


def parse_direct_input(input_text: str) -> DirectInputResult:
    """
    Main entry point - auto-detect and parse input text.

    Args:
        input_text: Raw input text (URLs or JSON)

    Returns:
        DirectInputResult with parsed videos and any errors/warnings
    """
    input_text = input_text.strip()
    if not input_text:
        return DirectInputResult([], ["No input provided"], [], 0, False)

    # Auto-detection logic
    if _is_json_input(input_text):
        return json_to_video_items(input_text)
    elif _is_url_list_input(input_text):
        return urls_to_video_items(input_text)
    else:
        return DirectInputResult(
            [],
            ["Unable to detect input format. Please provide either:\n"
             "• A list of YouTube URLs (one per line)\n"
             "• A JSON array of video objects"],
            [],
            0,
            False
        )


def urls_to_video_items(input_text: str) -> DirectInputResult:
    """
    Convert URL list to video items with metadata fetching.

    Args:
        input_text: Multi-line text with YouTube URLs

    Returns:
        DirectInputResult with parsed videos
    """
    urls = _extract_urls_from_text(input_text)
    if not urls:
        return DirectInputResult([], ["No valid YouTube URLs found"], [], 0, False)

    videos = []
    errors = []
    warnings = []

    for url in urls:
        try:
            # Extract video ID
            video_id = extract_video_id(url)
            if not video_id:
                warnings.append(f"Skipping invalid URL: {url}")
                continue

            # Fetch metadata using yt-dlp
            metadata = fetch_youtube_metadata(url)

            # Create VideoSearchItem
            video_item = VideoSearchItem(
                video_id=video_id,
                title=metadata.title or f"Video {video_id}",
                description="",  # yt-dlp doesn't provide description in basic mode
                channel_title="",  # Not available in basic yt-dlp mode
                channel_id="",  # Not available in basic yt-dlp mode
                published_at="",  # Not available in basic yt-dlp mode
                thumbnail_url="",  # Not available in basic yt-dlp mode
                thumbnail_high_url="",  # Not available in basic yt-dlp mode
                video_url=metadata.webpage_url,
                raw_data=metadata.raw
            )

            videos.append(video_item)

        except Exception as e:
            errors.append(f"Failed to process URL {url}: {str(e)}")
            continue

    success = len(videos) > 0
    return DirectInputResult(videos, errors, warnings, len(urls), success)


def json_to_video_items(json_text: str) -> DirectInputResult:
    """
    Parse JSON array into video items.

    Args:
        json_text: JSON array string

    Returns:
        DirectInputResult with parsed videos
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return DirectInputResult(
            [],
            [f"Invalid JSON format: {str(e)}"],
            [],
            0,
            False
        )

    if not isinstance(data, list):
        return DirectInputResult(
            [],
            ["Input must be a JSON array of video objects"],
            [],
            0,
            False
        )

    videos = []
    errors = []
    warnings = []

    for i, item in enumerate(data):
        try:
            if not isinstance(item, dict):
                warnings.append(f"Item {i+1}: Skipping non-object item")
                continue

            # Extract required fields
            video_id = item.get('video_id', '').strip()
            if not video_id:
                warnings.append(f"Item {i+1}: Missing required field 'video_id'")
                continue

            title = item.get('title', f'Video {video_id}').strip()
            channel_title = item.get('channel_title', '').strip()
            published_at = item.get('published_at', '').strip()
            video_url = item.get('video_url', f'https://www.youtube.com/watch?v={video_id}').strip()
            description = item.get('description', '').strip()

            # Validate video URL if provided
            if video_url and extract_video_id(video_url) != video_id:
                warnings.append(f"Item {i+1}: video_url doesn't match video_id, using generated URL")

            # Create VideoSearchItem
            video_item = VideoSearchItem(
                video_id=video_id,
                title=title,
                description=description,
                channel_title=channel_title,
                channel_id="",  # Not provided in JSON
                published_at=published_at,
                thumbnail_url="",  # Not provided in JSON
                thumbnail_high_url="",  # Not provided in JSON
                video_url=video_url,
                raw_data=item  # Store original JSON item
            )

            videos.append(video_item)

        except Exception as e:
            errors.append(f"Failed to process item {i+1}: {str(e)}")
            continue

    success = len(videos) > 0
    return DirectInputResult(videos, errors, warnings, len(data), success)


def create_search_result_from_items(items: List[VideoSearchItem]) -> SearchResult:
    """
    Create SearchResult wrapper for UI consistency.

    Args:
        items: List of VideoSearchItem objects

    Returns:
        SearchResult object for display
    """
    return SearchResult(
        items=items,
        total_results=len(items),
        results_per_page=len(items),
        next_page_token=None,
        prev_page_token=None
    )


def _is_json_input(text: str) -> bool:
    """Check if input text appears to be JSON."""
    text = text.strip()
    return (text.startswith('[') and text.endswith(']')) or \
           (text.startswith('{') and text.endswith('}'))


def _is_url_list_input(text: str) -> bool:
    """Check if input text appears to be a list of URLs."""
    lines = text.strip().split('\n')
    url_count = 0
    total_lines = len(lines)

    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            continue
        if 'youtube.com' in line or 'youtu.be' in line:
            url_count += 1

    # Consider it a URL list if at least 50% of non-empty lines contain YouTube URLs
    return url_count > 0 and url_count >= (total_lines - lines.count('')) * 0.5


def _extract_urls_from_text(text: str) -> List[str]:
    """Extract YouTube URLs from multi-line text."""
    urls = []
    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for YouTube URLs in the line
        if 'youtube.com' in line or 'youtu.be' in line:
            # Simple URL extraction - take the whole line if it looks like a URL
            if line.startswith('http'):
                urls.append(line)
            else:
                # Try to find URL within the line
                import re
                url_pattern = r'https?://[^\s]+'
                matches = re.findall(url_pattern, line)
                urls.extend(matches)

    return urls