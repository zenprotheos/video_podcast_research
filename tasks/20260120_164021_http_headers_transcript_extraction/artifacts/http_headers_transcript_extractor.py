#!/usr/bin/env python3
"""
HTTP Headers YouTube Transcript Extractor

This module implements browser-like HTTP headers approach to extract YouTube transcripts,
replicating how sites like downloadyoutubesubtitles.com work to bypass IP blocking.

Key Features:
- Browser-like HTTP headers and session management
- YouTube watch page prefetching
- Caption URL discovery from ytInitialPlayerResponse
- Same-session transcript fetching
- Request pacing and error handling
- Support for manual and auto-generated captions

Author: AI Assistant
Created: 2026-01-20
"""

import re
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptSegment:
    """Represents a single transcript segment with text and timing."""
    text: str
    start: float
    duration: Optional[float] = None

@dataclass
class TranscriptResult:
    """Complete transcript extraction result."""
    text: str
    segments: List[TranscriptSegment]
    language: str
    is_generated: bool
    video_id: str
    metadata: Dict

class YouTubeTranscriptExtractor:
    """
    Extract YouTube transcripts using browser-like HTTP headers approach.

    This class mimics how real browsers and transcript sites fetch YouTube captions
    by using proper headers, session management, and YouTube's internal endpoints.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the extractor with browser-like session configuration.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_browser_session()

    def _create_browser_session(self) -> requests.Session:
        """
        Create a requests session that closely mimics real browser behavior.

        Returns:
            Configured requests session with comprehensive browser-like headers and behavior
        """
        session = requests.Session()

        # Comprehensive browser-like headers that closely mimic Chrome 120
        headers = {
            # Core browser identification
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

            # Content negotiation
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',

            # Browser capabilities
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',

            # Connection and protocol
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',

            # Privacy and tracking
            'DNT': '1',

            # Platform specifics
            'sec-ch-ua-platform-version': '"15.0.0"',
        }

        session.headers.update(headers)

        # Configure retry strategy with more realistic backoff
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[403, 429, 500, 502, 503, 504],  # Include 403 for blocking
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2,  # More aggressive backoff
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats.

        Args:
            url: YouTube URL

        Returns:
            Video ID string or None if invalid
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def fetch_watch_page(self, video_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Fetch YouTube watch page HTML with realistic browser behavior and extract player response data.

        Args:
            video_id: YouTube video ID

        Returns:
            Tuple of (html_content, player_response_dict)
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            # Step 1: Simulate visiting YouTube homepage first (common user behavior)
            logger.info("Simulating YouTube homepage visit...")
            homepage_headers = self.session.headers.copy()
            homepage_headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Priority': 'u=0, i',
            })

            # Quick homepage visit to establish session
            self.session.get("https://www.youtube.com/", headers=homepage_headers, timeout=self.timeout)
            time.sleep(0.5)  # Brief pause like real browsing

            # Step 2: Fetch the actual watch page with proper referer chain
            logger.info(f"Fetching watch page for video: {video_id}")
            watch_headers = self.session.headers.copy()
            watch_headers.update({
                'Referer': 'https://www.youtube.com/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Priority': 'u=0, i',
                'Pragma': 'no-cache',
            })

            response = self.session.get(url, headers=watch_headers, timeout=self.timeout)

            # Check for blocking indicators
            if response.status_code == 429:
                logger.warning("Rate limited (429). Implementing longer delay...")
                time.sleep(5)
                # Retry once with longer delay
                response = self.session.get(url, headers=watch_headers, timeout=self.timeout)

            response.raise_for_status()

            html_content = response.text

            # Detect blocking or CAPTCHA responses early
            lower_html = html_content.lower()
            if any(token in lower_html for token in ["captcha", "unusual traffic", "verify you are", "detected unusual"]):
                logger.error("Blocking detected: CAPTCHA or bot challenge returned")
                return None, None

            # Step 3: Extract ytInitialPlayerResponse JSON
            player_response = self._extract_player_response(html_content)

            # Step 4: Simulate additional page resource requests (CSS, JS) for realism
            if player_response:
                logger.info("Simulating additional resource requests...")
                self._simulate_page_resources(video_id)

            return html_content, player_response

        except requests.RequestException as e:
            logger.error(f"Failed to fetch watch page: {e}")
            return None, None

    def _simulate_page_resources(self, video_id: str):
        """
        Simulate loading additional page resources to mimic real browser behavior.

        Args:
            video_id: YouTube video ID for context
        """
        # Simulate loading of common YouTube page resources
        resource_urls = [
            "https://www.youtube.com/s/desktop/abc123/cssbin/www-main-desktop-watch-page-skeleton.css",
            "https://www.youtube.com/s/desktop/abc123/jsbin/web-animations-next-lite.min.vflset/web-animations-next-lite.min.js",
        ]

        resource_headers = self.session.headers.copy()
        resource_headers.update({
            'Referer': f'https://www.youtube.com/watch?v={video_id}',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
        })

        # Only make 1-2 resource requests to avoid being too aggressive
        for url in resource_urls[:1]:  # Just one for realism
            try:
                self.session.get(url, headers=resource_headers, timeout=5)
                time.sleep(0.1)  # Tiny delay
            except:
                pass  # Ignore resource loading failures

    def _extract_player_response(self, html: str) -> Optional[Dict]:
        """
        Extract ytInitialPlayerResponse JSON from YouTube page HTML.

        Args:
            html: YouTube watch page HTML

        Returns:
            Parsed player response dictionary or None
        """
        # Look for ytInitialPlayerResponse in script tags
        patterns = [
            r'ytInitialPlayerResponse\s*=\s*({.+?});',
            r'ytInitialPlayerResponse"\s*:\s*({.+?})',
            r'"playerResponse"\s*:\s*({.+?})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1)
                    # Clean up the JSON string
                    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)  # Remove comments
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse player response JSON: {e}")
                    continue

        logger.warning("Could not find ytInitialPlayerResponse in page HTML")
        return None

    def find_caption_tracks(self, player_response: Dict, language: str = 'en') -> List[Dict]:
        """
        Find available caption tracks from player response data.

        Args:
            player_response: YouTube player response dictionary
            language: Preferred language code

        Returns:
            List of available caption track dictionaries
        """
        tracks = []

        try:
            if 'captions' in player_response and 'playerCaptionsTracklistRenderer' in player_response['captions']:
                renderer = player_response['captions']['playerCaptionsTracklistRenderer']

                if 'captionTracks' in renderer:
                    for track in renderer['captionTracks']:
                        track_info = {
                            'baseUrl': track.get('baseUrl', ''),
                            'languageCode': track.get('languageCode', ''),
                            'name': track.get('name', {}).get('simpleText', ''),
                            'kind': track.get('kind', ''),
                            'isTranslatable': track.get('isTranslatable', False)
                        }

                        # Prioritize requested language
                        if track_info['languageCode'].startswith(language):
                            tracks.insert(0, track_info)
                        else:
                            tracks.append(track_info)

            logger.info(f"Found {len(tracks)} caption tracks")
            return tracks

        except KeyError as e:
            logger.error(f"Error parsing caption tracks: {e}")
            return []

    def fetch_transcript_xml(self, caption_url: str, video_id: str = None) -> Optional[str]:
        """
        Fetch transcript XML data with highly realistic browser behavior.

        Args:
            caption_url: Caption track base URL
            video_id: Video ID for proper referer (optional)

        Returns:
            XML content string or None if failed
        """
        # Comprehensive transcript-specific headers that mimic real browser requests
        transcript_headers = self.session.headers.copy()
        transcript_headers.update({
            # Content type expectations
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,*;q=0.5',

            # Proper referer chain
            'Referer': f'https://www.youtube.com/watch?v={video_id}' if video_id else 'https://www.youtube.com/',

            # Fetch metadata that matches real browser transcript requests
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',  # YouTube captions are often cross-site

            # Additional browser-like headers
            'X-Requested-With': 'XMLHttpRequest',
            'X-YouTube-Client-Name': '1',  # Web client identifier
            'X-YouTube-Client-Version': '2.20240101.01.00',

            # Performance and caching
            'Priority': 'u=1, i',

            # Disable compression for transcript requests (common pattern)
            'Accept-Encoding': 'identity',
        })

        # Remove gzip encoding for transcript requests (they're usually small)
        if 'Accept-Encoding' in transcript_headers:
            transcript_headers['Accept-Encoding'] = 'identity'

        try:
            logger.info(f"Fetching transcript with realistic headers from: {caption_url}")

            # Add small delay to mimic user interaction
            time.sleep(0.5)

            response = self.session.get(caption_url, headers=transcript_headers, timeout=self.timeout)

            # Handle different blocking scenarios
            if response.status_code == 403:
                logger.warning("403 Forbidden - possible blocking detected")
                # Try with slightly different headers
                transcript_headers['Sec-Fetch-Site'] = 'same-origin'
                time.sleep(2)
                response = self.session.get(caption_url, headers=transcript_headers, timeout=self.timeout)

            elif response.status_code == 429:
                logger.warning("Rate limited - implementing longer delay")
                time.sleep(3)
                response = self.session.get(caption_url, headers=transcript_headers, timeout=self.timeout)

            response.raise_for_status()

            content = response.text

            # Validate that we got XML content
            if not content.strip().startswith('<'):
                logger.warning("Response doesn't appear to be XML")
                return None

            return content

        except requests.RequestException as e:
            logger.error(f"Failed to fetch transcript: {e}")
            return None

    def parse_transcript_xml(self, xml_content: str) -> List[TranscriptSegment]:
        """
        Parse YouTube transcript XML into transcript segments.

        Args:
            xml_content: Raw XML transcript data

        Returns:
            List of TranscriptSegment objects
        """
        segments = []

        try:
            # Remove XML declaration if present
            xml_content = re.sub(r'<\?xml.*?\?>', '', xml_content)

            root = ET.fromstring(xml_content)

            for elem in root.findall('.//text'):
                text = elem.text or ""
                start = float(elem.get('start', 0))
                duration = float(elem.get('dur', 0)) if elem.get('dur') else None

                # Clean up the text
                text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
                text = text.strip()

                if text:  # Only add non-empty segments
                    segments.append(TranscriptSegment(
                        text=text,
                        start=start,
                        duration=duration
                    ))

            logger.info(f"Parsed {len(segments)} transcript segments")
            return segments

        except ET.ParseError as e:
            logger.error(f"Failed to parse transcript XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing transcript: {e}")
            return []

    def parse_transcript_json3(self, json_content: str) -> List[TranscriptSegment]:
        """
        Parse YouTube JSON3 transcript into transcript segments.

        Args:
            json_content: Raw JSON transcript data

        Returns:
            List of TranscriptSegment objects
        """
        segments = []

        try:
            data = json.loads(json_content)
            events = data.get("events", [])
            for event in events:
                segs = event.get("segs")
                if not segs:
                    continue

                start_ms = float(event.get("tStartMs", 0))
                duration_ms = float(event.get("dDurationMs", 0)) if "dDurationMs" in event else None

                text = "".join(seg.get("utf8", "") for seg in segs)
                text = text.replace("\n", " ").strip()

                if text:
                    segments.append(TranscriptSegment(
                        text=text,
                        start=start_ms / 1000.0,
                        duration=(duration_ms / 1000.0) if duration_ms is not None else None,
                    ))

            logger.info(f"Parsed {len(segments)} transcript segments from JSON3")
            return segments

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse transcript JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing transcript JSON: {e}")
            return []

    def extract_transcript(self, video_url: str, language: str = 'en') -> Optional[TranscriptResult]:
        """
        Main method to extract transcript from YouTube video.

        Args:
            video_url: YouTube video URL
            language: Preferred language code

        Returns:
            TranscriptResult object or None if extraction failed
        """
        # Extract video ID
        video_id = self.extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            return None

        logger.info(f"Starting transcript extraction for video: {video_id}")

        # Step 1: Fetch watch page and player response
        html_content, player_response = self.fetch_watch_page(video_id)
        if not player_response:
            logger.error("Failed to fetch or parse watch page")
            return None

        # Add small delay to mimic human behavior
        time.sleep(1)

        # Step 2: Find available caption tracks
        caption_tracks = self.find_caption_tracks(player_response, language)
        if not caption_tracks:
            logger.warning("No caption tracks found for this video")
            return None

        # Step 3: Try to fetch transcript from first available track
        selected_track = caption_tracks[0]
        logger.info(f"Selected caption track: {selected_track['languageCode']} - {selected_track['name']}")

        xml_content = self.fetch_transcript_xml(selected_track['baseUrl'])
        if not xml_content:
            logger.error("Failed to fetch transcript XML")
            return None

        # Step 4: Parse transcript XML
        segments = self.parse_transcript_xml(xml_content)
        if not segments:
            logger.error("Failed to parse transcript segments")
            return None

        # Step 5: Build complete transcript text
        full_text = ' '.join(segment.text for segment in segments)

        # Determine if captions are auto-generated
        is_generated = selected_track.get('kind') == 'asr' or 'auto-generated' in selected_track.get('name', '').lower()

        # Create result object
        result = TranscriptResult(
            text=full_text,
            segments=segments,
            language=selected_track['languageCode'],
            is_generated=is_generated,
            video_id=video_id,
            metadata={
                'track_name': selected_track['name'],
                'track_kind': selected_track.get('kind'),
                'available_tracks': len(caption_tracks),
                'extraction_method': 'http_headers',
                'timestamp': time.time()
            }
        )

        logger.info(f"Successfully extracted transcript: {len(segments)} segments, {len(full_text)} characters")
        return result

def main():
    """Command-line interface for testing the extractor."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python http_headers_transcript_extractor.py <youtube_url> [language]")
        print("Example: python http_headers_transcript_extractor.py https://www.youtube.com/watch?v=dQw4w9WgXcQ en")
        sys.exit(1)

    video_url = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'en'

    extractor = YouTubeTranscriptExtractor()

    print(f"Extracting transcript from: {video_url}")
    print(f"Language: {language}")
    print("-" * 50)

    result = extractor.extract_transcript(video_url, language)

    if result:
        print("✅ Transcript extracted successfully!")
        print(f"Language: {result.language}")
        print(f"Auto-generated: {result.is_generated}")
        print(f"Segments: {len(result.segments)}")
        print(f"Total characters: {len(result.text)}")
        print("\n" + "="*50)
        print("FULL TRANSCRIPT:")
        print("="*50)
        print(result.text)
    else:
        print("❌ Failed to extract transcript")
        sys.exit(1)

if __name__ == "__main__":
    main()