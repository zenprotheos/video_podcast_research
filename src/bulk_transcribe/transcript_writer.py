"""Write transcript Markdown files with YAML frontmatter."""
import os
from datetime import datetime
from typing import Dict, Optional

from src.bulk_transcribe.utils import slugify


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
    """
    # Build frontmatter
    frontmatter: Dict[str, any] = {
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
                if isinstance(value, str):
                    f.write(f"{key}: {value}\n")
                elif isinstance(value, dict):
                    f.write(f"{key}:\n")
                    for k, v in value.items():
                        if v is not None:
                            f.write(f"  {k}: {v}\n")
                else:
                    f.write(f"{key}: {value}\n")
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
