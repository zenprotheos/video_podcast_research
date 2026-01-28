"""YouTube Data API v3 search functionality."""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class VideoSearchItem:
    """Individual video search result item."""
    video_id: str
    title: str
    description: str
    channel_title: str
    channel_id: str
    published_at: str
    thumbnail_url: str
    thumbnail_high_url: str
    video_url: str
    raw_data: Dict[str, Any]  # Store full API response snippet
    query_id: Optional[str] = None
    query_text: Optional[str] = None
    query_sources: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Complete search results with pagination info."""
    items: List[VideoSearchItem]
    total_results: int
    results_per_page: int
    next_page_token: Optional[str]
    prev_page_token: Optional[str]


def build_youtube_service(api_key: str):
    """Build YouTube Data API service."""
    return build('youtube', 'v3', developerKey=api_key)


def search_youtube(
    query: str,
    api_key: str,
    max_results: int = 50,
    order: str = "relevance",
    type: str = "video",
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    video_caption: Optional[str] = None,  # "closedCaption" or "any"
    video_definition: Optional[str] = None,  # "high" or "any"
    region_code: Optional[str] = None,
    relevance_language: Optional[str] = None,
    page_token: Optional[str] = None
) -> SearchResult:
    """
    Search YouTube using Data API v3.

    Args:
        query: Search query string
        api_key: YouTube Data API key
        max_results: Results per page (1-50)
        order: Sort order (relevance, date, viewCount, rating)
        type: Resource type (video, playlist, channel)
        published_after: ISO 8601 date string
        published_before: ISO 8601 date string
        video_caption: Filter by captions ("closedCaption", "any")
        video_definition: Filter by quality ("high", "any")
        region_code: ISO 3166-1 alpha-2 country code
        relevance_language: ISO 639-1 language code
        page_token: For pagination

    Returns:
        SearchResult with items and pagination info
    """
    try:
        youtube = build_youtube_service(api_key)

        # Build request parameters
        request_params = {
            'q': query,
            'part': 'snippet',
            'maxResults': min(max_results, 50),  # API limit is 50
            'order': order,
            'type': type,
        }

        # Add optional filters
        if published_after:
            request_params['publishedAfter'] = published_after
        if published_before:
            request_params['publishedBefore'] = published_before
        if video_caption:
            request_params['videoCaption'] = video_caption
        if video_definition:
            request_params['videoDefinition'] = video_definition
        if region_code:
            request_params['regionCode'] = region_code
        if relevance_language:
            request_params['relevanceLanguage'] = relevance_language
        if page_token:
            request_params['pageToken'] = page_token

        # Make API request
        request = youtube.search().list(**request_params)
        response = request.execute()

        # Parse response
        items = []
        for item in response.get('items', []):
            search_item = parse_search_item(item, query_text=query)
            if search_item:
                items.append(search_item)

        return SearchResult(
            items=items,
            total_results=int(response.get('pageInfo', {}).get('totalResults', 0)),
            results_per_page=int(response.get('pageInfo', {}).get('resultsPerPage', 0)),
            next_page_token=response.get('nextPageToken'),
            prev_page_token=response.get('prevPageToken')
        )

    except HttpError as e:
        error_msg = f"YouTube API error: {e}"
        if e.resp.status == 403:
            error_msg = "YouTube API quota exceeded or invalid API key"
        elif e.resp.status == 400:
            error_msg = "Invalid search parameters"
        raise Exception(error_msg) from e
    except Exception as e:
        raise Exception(f"YouTube search failed: {str(e)}") from e


def parse_search_item(
    item: Dict[str, Any],
    query_text: Optional[str] = None,
    query_id: Optional[str] = None,
) -> Optional[VideoSearchItem]:
    """
    Parse a single YouTube search result item.

    Returns None if item is not a video or missing required data.
    """
    try:
        snippet = item.get('snippet', {})

        # Only process video items (ignore playlists/channels for now)
        if item.get('id', {}).get('kind') != 'youtube#video':
            return None

        video_id = item.get('id', {}).get('videoId')
        if not video_id:
            return None

        # Extract data from snippet
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        channel_title = snippet.get('channelTitle', '')
        channel_id = snippet.get('channelId', '')
        published_at = snippet.get('publishedAt', '')

        # Extract thumbnails
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = thumbnails.get('default', {}).get('url', '')
        thumbnail_high_url = thumbnails.get('high', {}).get('url', '')

        # Build video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        return VideoSearchItem(
            video_id=video_id,
            title=title,
            description=description,
            channel_title=channel_title,
            channel_id=channel_id,
            published_at=published_at,
            thumbnail_url=thumbnail_url,
            thumbnail_high_url=thumbnail_high_url,
            video_url=video_url,
            raw_data=snippet,  # Store full snippet for future use
            query_id=query_id,
            query_text=query_text,
            query_sources=[query_text] if query_text else [],
        )

    except Exception:
        # If parsing fails, skip this item
        return None


def enrich_items_with_full_descriptions(
    items: List[VideoSearchItem],
    api_key: str,
    cache: Optional[Dict[str, str]] = None,
) -> None:
    """
    Replace truncated search.list descriptions with full descriptions via videos.list.
    Mutates each item.description in place. Updates cache with fetched descriptions
    so reruns do not re-request (quota: 1 unit per 50 videos per request).
    """
    if not items:
        return
    cache = cache if cache is not None else {}
    # IDs we still need to fetch (not in cache)
    ids_to_fetch = [item.video_id for item in items if item.video_id and item.video_id not in cache]
    if not ids_to_fetch:
        # Hydrate from cache only
        for item in items:
            if item.video_id and item.video_id in cache:
                item.description = cache[item.video_id]
        return

    try:
        youtube = build_youtube_service(api_key)
        for i in range(0, len(ids_to_fetch), 50):
            batch = ids_to_fetch[i : i + 50]
            request = youtube.videos().list(
                part="snippet",
                id=",".join(batch),
                maxResults=50,
                fields="items(id,snippet(description))",
            )
            response = request.execute()
            for raw in response.get("items", []):
                vid = raw.get("id")
                desc = (raw.get("snippet") or {}).get("description") or ""
                if vid:
                    cache[vid] = desc

        for item in items:
            if item.video_id and item.video_id in cache:
                item.description = cache[item.video_id]
    except Exception:
        # On failure, leave items with existing (truncated) description
        pass


def get_search_filters_dict(
    order: str = "relevance",
    max_results: int = 50,
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    video_caption: Optional[str] = None,
    video_definition: Optional[str] = None,
    region_code: Optional[str] = None,
    relevance_language: Optional[str] = None
) -> Dict[str, Any]:
    """Convert filter parameters to a dictionary for display/logging."""
    return {
        'order': order,
        'max_results': max_results,
        'published_after': published_after,
        'published_before': published_before,
        'video_caption': video_caption,
        'video_definition': video_definition,
        'region_code': region_code,
        'relevance_language': relevance_language,
    }


def check_video_availability(youtube, video_ids: List[str]) -> Dict[str, str]:
    """
    Check video availability and privacy status using YouTube Data API.

    Args:
        youtube: YouTube API service instance
        video_ids: List of video IDs to check

    Returns:
        Dict mapping video_id to status: 'available', 'private', 'not_found', 'error'
    """
    availability = {}

    # Process in batches of 50 (API limit)
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]

        try:
            request = youtube.videos().list(
                part='status',
                id=','.join(batch),
                maxResults=50
            )
            response = request.execute()

            # Mark all videos in this batch as not found initially
            for video_id in batch:
                availability[video_id] = 'not_found'

            # Update status for videos that were found
            for item in response.get('items', []):
                video_id = item['id']
                status = item.get('status', {})
                privacy_status = status.get('privacyStatus', 'unknown')

                if privacy_status == 'private':
                    availability[video_id] = 'private'
                elif privacy_status in ['public', 'unlisted']:
                    availability[video_id] = 'available'
                else:
                    availability[video_id] = f'privacy_{privacy_status}'

        except HttpError as e:
            # On API error, mark all videos in this batch as error
            for video_id in batch:
                availability[video_id] = f'api_error_{e.resp.status}'
        except Exception as e:
            # On unexpected error, mark all videos in this batch as error
            for video_id in batch:
                availability[video_id] = f'error_{str(e)}'

    return availability


def filter_available_videos(items: List[VideoSearchItem], api_key: str) -> tuple[List[VideoSearchItem], Dict[str, List[str]]]:
    """
    Filter video list to only include available videos using YouTube API.

    Args:
        items: List of VideoSearchItem objects
        api_key: YouTube API key

    Returns:
        Tuple of (available_videos, filter_summary)
        filter_summary: Dict with keys 'available', 'private', 'not_found', 'error' mapping to lists of video_ids
    """
    if not items:
        return [], {}

    video_ids = [item.video_id for item in items]

    try:
        youtube = build_youtube_service(api_key)
        availability = check_video_availability(youtube, video_ids)
    except Exception as e:
        # If API setup fails, return all videos as available (fallback)
        return items, {'api_setup_failed': video_ids}

    available_videos = []
    filter_summary = {
        'available': [],
        'private': [],
        'not_found': [],
        'error': []
    }

    for item in items:
        status = availability.get(item.video_id, 'error_unknown')
        if status == 'available':
            available_videos.append(item)
            filter_summary['available'].append(item.video_id)
        elif status == 'private':
            filter_summary['private'].append(item.video_id)
        elif status == 'not_found':
            filter_summary['not_found'].append(item.video_id)
        else:
            filter_summary['error'].append(item.video_id)

    return available_videos, filter_summary