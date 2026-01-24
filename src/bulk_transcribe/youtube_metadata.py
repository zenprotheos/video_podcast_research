import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from yt_dlp import YoutubeDL


@dataclass
class YouTubeMetadata:
    video_id: str
    title: str
    webpage_url: str
    raw: Dict[str, Any]


def fetch_youtube_metadata(youtube_url: str) -> YouTubeMetadata:
    """
    Fetch rich metadata using yt-dlp without downloading the media.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    video_id = str(info.get("id") or "")
    title = str(info.get("title") or "")
    webpage_url = str(info.get("webpage_url") or youtube_url)
    return YouTubeMetadata(video_id=video_id, title=title, webpage_url=webpage_url, raw=info)


def save_metadata_json(path: str, meta: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

