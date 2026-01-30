"""Write transcript Markdown files with YAML frontmatter."""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.bulk_transcribe.utils import slugify


def _format_yaml_value(value: Any, indent: int = 0) -> str:
    """
    Format a value for YAML output with proper escaping and structure.
    
    Args:
        value: The value to format
        indent: Current indentation level (number of spaces)
    
    Returns:
        Formatted YAML string
    """
    prefix = " " * indent
    
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # Escape strings that need quoting (contain special chars or look like other types)
        needs_quoting = any([
            ":" in value,
            "#" in value,
            value.startswith("-"),
            value.startswith("["),
            value.startswith("{"),
            "\n" in value,
            value.lower() in ("true", "false", "null", "yes", "no"),
        ])
        if needs_quoting:
            # Use double quotes and escape internal quotes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return f'"{escaped}"'
        return value
    elif isinstance(value, list):
        if not value:
            return "[]"
        # Format as YAML list
        items = []
        for item in value:
            formatted = _format_yaml_value(item, 0)
            items.append(f"{prefix}- {formatted}")
        return "\n" + "\n".join(items)
    elif isinstance(value, dict):
        if not value:
            return "{}"
        # Format as nested YAML dict
        lines = []
        for k, v in value.items():
            if v is not None:
                formatted = _format_yaml_value(v, indent + 2)
                if isinstance(v, (list, dict)) and v:
                    lines.append(f"{prefix}{k}:{formatted}")
                else:
                    lines.append(f"{prefix}{k}: {formatted}")
        return "\n" + "\n".join(lines)
    else:
        return str(value)


def write_transcript_markdown(
    output_path: str,
    source_type: str,
    source_url: str,
    transcript_text: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    episode_url: Optional[str] = None,
    video_id: Optional[str] = None,
    method: str = "unknown",
    youtube_metadata: Optional[Dict] = None,
    podcast_metadata: Optional[Dict] = None,
) -> None:
    """
    Write a transcript Markdown file with Obsidian-friendly YAML frontmatter.
    
    Args:
        output_path: Path to write the markdown file
        source_type: Type of source (youtube, podcast)
        source_url: URL of the source video/audio
        transcript_text: The transcript content
        title: Optional title of the video/episode
        description: Optional description
        episode_url: Optional episode URL (for podcasts)
        video_id: Optional YouTube video ID
        method: Extraction method used
        youtube_metadata: Optional dict with YouTube-specific metadata:
            - channel_title: Channel name
            - channel_id: Channel ID
            - published_at: ISO timestamp of publication
            - duration: Duration string (e.g., "PT15M33S")
            - duration_seconds: Duration in seconds
            - view_count: Number of views
            - like_count: Number of likes
            - comment_count: Number of comments
            - has_captions: Whether captions are available
            - tags: List of video tags
            - category_id: YouTube category ID
            - thumbnail_url: Thumbnail image URL
        podcast_metadata: Optional dict with podcast-specific metadata
    """
    # Build frontmatter
    frontmatter: Dict[str, Any] = {
        "source_type": source_type,
        "source_url": source_url,
        "date_processed": datetime.now().isoformat(),
        "method": method,
    }
    
    if title:
        frontmatter["title"] = title
    if description:
        frontmatter["description"] = description
    if episode_url:
        frontmatter["episode_url"] = episode_url
    if video_id:
        frontmatter["video_id"] = video_id
    
    if youtube_metadata:
        frontmatter["youtube"] = youtube_metadata
    if podcast_metadata:
        frontmatter["podcast"] = podcast_metadata
    
    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        # Write YAML frontmatter
        f.write("---\n")
        for key, value in frontmatter.items():
            if value is not None:
                if isinstance(value, (dict, list)) and value:
                    formatted = _format_yaml_value(value, 2)
                    f.write(f"{key}:{formatted}\n")
                else:
                    formatted = _format_yaml_value(value, 0)
                    f.write(f"{key}: {formatted}\n")
        f.write("---\n\n")
        
        # Write transcript
        f.write("## Transcript\n\n")
        f.write(transcript_text)
        f.write("\n")


def generate_filename(video_id: Optional[str], title: Optional[str], source_type: str) -> str:
    """Generate a safe filename for the transcript."""
    if video_id:
        base = f"{slugify(title or 'video')}__{video_id}"
    else:
        base = slugify(title or f"{source_type}_transcript")
    
    return f"{base}.md"
