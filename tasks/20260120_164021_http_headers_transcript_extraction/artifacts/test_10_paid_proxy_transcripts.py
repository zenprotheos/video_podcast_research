#!/usr/bin/env python3
"""
Test 10 YouTube URLs using Paid Residential Proxies

Creates transcripts in the same format as the original DEAPI app.
Outputs to: output/sessions/{session_id}/youtube/
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

from paid_proxy_transcript_extractor import PaidProxyYouTubeExtractor


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def write_transcript_markdown(
    output_path: str,
    source_type: str,
    source_url: str,
    transcript_text: str,
    title: str = None,
    description: str = None,
    episode_url: str = None,
    video_id: str = None,
    method: str = "unknown",
    youtube_metadata: dict = None,
    podcast_metadata: dict = None,
) -> None:
    """
    Write a transcript Markdown file with Obsidian-friendly YAML frontmatter.
    """
    # Build frontmatter
    frontmatter = {
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


def generate_filename(video_id: str = None, title: str = None, source_type: str = "unknown") -> str:
    """Generate a safe filename for the transcript."""
    if video_id:
        base = f"{slugify(title or 'video')}__{video_id}"
    else:
        base = slugify(title or f"{source_type}_transcript")

    return f"{base}.md"


def fetch_youtube_metadata(video_id: str) -> dict:
    """Simple YouTube metadata fetcher."""
    # For now, return basic metadata
    return {
        "channel": "Unknown Channel",
        "upload_date": "Unknown",
        "duration": 0,
        "view_count": 0,
    }


def create_test_session():
    """Create a test session directory for outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"session_{timestamp}"

    # Create session directory structure
    output_base = Path(__file__).parent.parent.parent / "output" / "sessions" / session_id
    youtube_dir = output_base / "youtube"

    youtube_dir.mkdir(parents=True, exist_ok=True)

    return output_base, youtube_dir, session_id


def test_10_urls():
    """Test 10 YouTube URLs with paid residential proxies."""

    # Test URLs from sample_youtube_URL_list.md
    test_urls = [
        "https://www.youtube.com/watch?v=67MX3_N4Lfo",
        "https://www.youtube.com/watch?v=LTdWTf1OGKg",
        "https://www.youtube.com/watch?v=sr9fzxRW0bA",
        "https://www.youtube.com/watch?v=ZQ-U8U1EX_A",
        "https://www.youtube.com/watch?v=tLggx01ICSA",
        "https://www.youtube.com/watch?v=gKDQhPmSnKI",
        "https://www.youtube.com/watch?v=NyLbwKohcII",
        "https://www.youtube.com/watch?v=KILHzgvWNEM",
        "https://www.youtube.com/watch?v=d4TF_WvMN_c",
        "https://www.youtube.com/watch?v=pzZkkoG_oQI",
    ]

    # Create session directories
    output_base, youtube_dir, session_id = create_test_session()

    print("=" * 100)
    print("TESTING 10 YOUTUBE URLs WITH PAID RESIDENTIAL PROXIES")
    print("=" * 100)
    print(f"Session ID: {session_id}")
    print(f"Output Directory: {output_base}")
    print(f"Test URLs: {len(test_urls)}")
    print()

    # Initialize extractor
    proxy_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'my_assets', 'Webshare residential proxies.txt')
    if not os.path.exists(proxy_file):
        print(f"ERROR: Proxy file not found: {proxy_file}")
        sys.exit(1)

    try:
        extractor = PaidProxyYouTubeExtractor(proxy_file)
    except Exception as e:
        print(f"ERROR: Failed to initialize extractor: {e}")
        sys.exit(1)

    # Track results
    results = []
    successful_transcripts = []

    # Process each URL
    for i, url in enumerate(test_urls, 1):
        print(f"\n[TEST {i}/{len(test_urls)}] Processing: {url}")
        print("-" * 80)

        try:
            # Extract video ID for metadata
            video_id = extractor._extract_video_id(url)
            if not video_id:
                print("FAILED: Could not extract video ID")
                results.append(False)
                continue

            # Fetch transcript using paid proxies
            print(f"Extracting transcript for video ID: {video_id}")
            transcript_result = extractor.extract_transcript(url)

            if transcript_result:
                print("SUCCESS: Transcript extracted")
                print(f"   Method: {transcript_result['method']}")
                print(".2f")
                print(f"   Segments: {len(transcript_result['segments'])}")
                print(f"   Text length: {len(transcript_result['text'])} characters")

                # Fetch YouTube metadata for the frontmatter
                try:
                    print("   Fetching YouTube metadata...")
                    metadata = fetch_youtube_metadata(video_id)
                    title = metadata.get('title', f'YouTube Video {video_id}')
                    youtube_meta = {
                        'channel': metadata.get('channel', 'Unknown'),
                        'upload_date': metadata.get('upload_date', 'Unknown'),
                        'duration': metadata.get('duration', 0),
                        'view_count': metadata.get('view_count', 0),
                    }
                except Exception as meta_error:
                    print(f"   Warning: Could not fetch metadata: {meta_error}")
                    title = f'YouTube Video {video_id}'
                    youtube_meta = {}

                # Generate filename and write transcript
                filename = generate_filename(video_id, title, 'youtube')
                output_path = youtube_dir / filename

                print(f"   Writing transcript to: {output_path}")

                write_transcript_markdown(
                    output_path=str(output_path),
                    source_type='youtube',
                    source_url=url,
                    transcript_text=transcript_result['text'],
                    title=title,
                    video_id=video_id,
                    method='paid_residential_proxy',
                    youtube_metadata=youtube_meta
                )

                results.append(True)
                successful_transcripts.append({
                    'url': url,
                    'video_id': video_id,
                    'title': title,
                    'segments': len(transcript_result['segments']),
                    'text_length': len(transcript_result['text']),
                    'extraction_time': transcript_result['extraction_time']
                })

                print(f"   ✅ Transcript saved successfully")

            else:
                print("FAILED: Transcript extraction failed")
                results.append(False)

        except Exception as e:
            print(f"FAILED: Unexpected error: {e}")
            results.append(False)

        # Small delay between tests to be respectful
        if i < len(test_urls):
            print("   Waiting 2 seconds before next test...")
            time.sleep(2)

    # Final Summary
    print("\n" + "=" * 100)
    print("FINAL TEST SUMMARY")
    print("=" * 100)
    successful = sum(results)
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0

    print(f"Total URLs tested: {total}")
    print(f"Successful transcripts: {successful}")
    print(".1f")

    if successful > 0:
        print("\nSUCCESS! Paid residential proxies extracted transcripts!")
        print(f"Transcripts saved to: {youtube_dir}")

        # Show details of successful transcripts
        print("\nSuccessful Transcripts:")
        for i, transcript in enumerate(successful_transcripts, 1):
            print(f"   {i}. {transcript['title'][:60]}...")
            print(".2f")
            print(f"      Segments: {transcript['segments']}, Length: {transcript['text_length']} chars")

        print("\nNext Steps:")
        print("   1. Review the generated transcript files")
        print("   2. Compare quality with DEAPI transcripts")
        print("   3. Test bulk processing performance")
        print("   4. Implement production monitoring")

    else:
        print("\n❌ All tests failed")
        print("   Check proxy credentials and network connectivity")

    # Save test manifest
    manifest_path = output_base / "manifest.json"
    import json
    manifest_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "test_type": "paid_residential_proxy_validation",
        "total_urls": total,
        "successful": successful,
        "success_rate": success_rate,
        "results": results,
        "successful_transcripts": successful_transcripts
    }

    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2, default=str)

    print(f"\n📄 Test manifest saved to: {manifest_path}")


if __name__ == "__main__":
    test_10_urls()