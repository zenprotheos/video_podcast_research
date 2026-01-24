#!/usr/bin/env python3
"""
Fast Path Paid Residential Proxy YouTube Transcript Extractor

Priority: Get basic transcript extraction working with paid WebShare proxies.
Uses session-based rotation for IP diversity and rate limiting for reliability.
"""

import requests
import time
import random
import logging
from typing import Optional, Dict, List
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PaidProxyYouTubeExtractor:
    """YouTube transcript extractor using WebShare paid residential proxies."""

    def __init__(self, proxy_file_path: str):
        """
        Initialize with paid proxy credentials.

        Args:
            proxy_file_path: Path to file containing proxy credentials
        """
        self.proxy_credentials = self._load_proxy_credentials(proxy_file_path)
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(requests_per_second=2.0)  # Conservative start

    def _load_proxy_credentials(self, file_path: str) -> List[str]:
        """Load proxy credentials from file."""
        try:
            with open(file_path, 'r') as f:
                # Take first 100 proxies for initial testing
                proxies = [line.strip() for line in f if line.strip()][:100]
            logger.info(f"Loaded {len(proxies)} proxy credentials")
            return proxies
        except FileNotFoundError:
            raise FileNotFoundError(f"Proxy file not found: {file_path}")

    def _get_random_proxy(self) -> Dict[str, str]:
        """Get a random proxy from the pool."""
        if not self.proxy_credentials:
            raise ValueError("No proxy credentials available")

        # Randomly select a proxy credential
        proxy_line = random.choice(self.proxy_credentials)
        host, port, username, password = proxy_line.split(':')

        proxy_url = f"http://{username}:{password}@{host}:{port}"
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _fetch_watch_page(self, video_id: str) -> Optional[str]:
        """Fetch YouTube watch page through residential proxy."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        self.rate_limiter.wait_if_needed()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Exclude 'br' to avoid brotli compression
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                proxies = self._get_random_proxy()
                logger.info(f"Fetching watch page for {video_id} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=15
                )

                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                logger.info(f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")

                response.raise_for_status()

                # Check if we got blocked content - be more specific to avoid false positives
                content = response.text
                content_lower = content.lower()

                # More specific blocking detection
                blocking_indicators = [
                    'our systems have detected unusual traffic',
                    'unusual traffic from your computer network',
                    'verify you are human',
                    'sorry for the inconvenience',
                    'automated queries',
                    'too many requests'
                ]

                is_blocked = any(indicator in content_lower for indicator in blocking_indicators)

                if is_blocked:
                    logger.warning(f"Detected blocking on attempt {attempt + 1}")
                    # Save blocked content for debugging
                    with open(f'debug_blocked_response_{video_id}_{attempt + 1}.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None

                # Save successful response for debugging
                with open(f'debug_watch_page_{video_id}.html', 'w', encoding='utf-8') as f:
                    f.write(content)

                return content

            except requests.RequestException as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def _extract_player_response(self, html: str) -> Optional[Dict]:
        """Extract ytInitialPlayerResponse from HTML."""
        import re
        import json

        # First try the old patterns
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
                    # Clean up common issues
                    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Try to find captionTracks directly in the HTML and extract surrounding JSON
        try:
            # Look for captionTracks in the HTML
            caption_index = html.find('captionTracks')
            if caption_index != -1:
                # Find the start of the JSON object containing captionTracks
                # Look backwards for the opening brace
                brace_count = 0
                start_pos = caption_index
                while start_pos > 0:
                    char = html[start_pos]
                    if char == '{':
                        brace_count += 1
                        if brace_count == 1:
                            # Found the start of the JSON object
                            break
                    elif char == '}':
                        brace_count -= 1
                    start_pos -= 1

                if brace_count == 1:
                    # Now find the end of this JSON object
                    end_pos = caption_index
                    brace_count = 1
                    while end_pos < len(html):
                        char = html[end_pos]
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found the end of the JSON object
                                json_str = html[start_pos:end_pos + 1]
                                try:
                                    # Clean up and parse
                                    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                                    data = json.loads(json_str)

                                    # Check if this contains captions data
                                    if 'captions' in data and 'playerCaptionsTracklistRenderer' in data['captions']:
                                        return data

                                except json.JSONDecodeError:
                                    pass
                        end_pos += 1

        except Exception as e:
            logger.debug(f"Failed to extract JSON around captionTracks: {e}")

        # Try the ytAtR approach as fallback
        try:
            # Look for window.ytAtR = 'escaped_json_data'
            ytatr_pattern = r'window\.ytAtR\s*=\s*[\'"]([^\'"]*)[\'"]'
            ytatr_match = re.search(ytatr_pattern, html, re.DOTALL)
            if ytatr_match:
                escaped_data = ytatr_match.group(1)
                try:
                    # Handle the deprecation warning by using raw strings
                    decoded_json = escaped_data.encode('raw_unicode_escape').decode('utf-8')
                    data = json.loads(decoded_json)

                    # Look for playerResponse in the data
                    if 'playerResponse' in data:
                        return data['playerResponse']

                except Exception as decode_error:
                    logger.debug(f"Failed to decode ytAtR data: {decode_error}")

        except Exception as e:
            logger.debug(f"Failed to parse ytAtR format: {e}")

        return None

    def _find_caption_tracks(self, player_response: Dict) -> List[Dict]:
        """Find caption tracks from player response."""
        tracks = []

        try:
            if 'captions' in player_response and 'playerCaptionsTracklistRenderer' in player_response['captions']:
                renderer = player_response['captions']['playerCaptionsTracklistRenderer']

                if 'captionTracks' in renderer:
                    for track in renderer['captionTracks']:
                        tracks.append({
                            'baseUrl': track.get('baseUrl', ''),
                            'languageCode': track.get('languageCode', ''),
                            'name': track.get('name', {}).get('simpleText', ''),
                        })

        except KeyError:
            pass

        return tracks

    def _fetch_transcript(self, caption_url: str) -> Optional[str]:
        """Fetch transcript XML through proxy."""
        self.rate_limiter.wait_if_needed()

        headers = {
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,*;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                proxies = self._get_random_proxy()
                logger.info(f"Fetching transcript (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(
                    caption_url,
                    headers=headers,
                    proxies=proxies,
                    timeout=15
                )
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                logger.error(f"Transcript fetch failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    def extract_transcript(self, video_url: str, language: str = 'en') -> Optional[Dict]:
        """
        Main extraction method using paid residential proxies with youtube-transcript-api.

        Args:
            video_url: YouTube video URL
            language: Language code (default: 'en')

        Returns:
            dict: Transcript data or None if failed
        """
        start_time = time.time()
        video_id = self._extract_video_id(video_url)

        if not video_id:
            logger.error("Could not extract video ID from URL")
            return None

        logger.info(f"Starting extraction for video: {video_id}")

        # Try using youtube-transcript-api with WebShare proxy config
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api.proxies import WebshareProxyConfig

            logger.info("Attempting transcript extraction with youtube-transcript-api + WebShare proxies")

            # Parse proxy credentials for WebShare config
            # Format: p.webshare.io:80:ifevmzvf-1:mfhbw7w35a6x
            sample_proxy = self.proxy_credentials[0]  # Use first proxy for base credentials
            parts = sample_proxy.split(':')
            base_username = parts[2].rsplit('-', 1)[0]  # Remove session ID to get base username
            password = parts[3]

            # Create WebShare proxy config
            proxy_config = WebshareProxyConfig(
                proxy_username=base_username,
                proxy_password=password,
                retries_when_blocked=5  # Reduce retries for faster testing
            )

            # Create API instance with proxy support
            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)

            # Get available transcripts
            transcript_list = ytt_api.list(video_id)

            # Find transcript in preferred language
            try:
                transcript = transcript_list.find_transcript([language, 'en'])
                transcript_data = transcript.fetch()

                # transcript_data is a FetchedTranscript containing FetchedTranscriptSnippet objects
                segments = []
                for item in transcript_data:
                    segments.append({
                        'text': item.text,
                        'start': item.start,
                        'duration': item.duration
                    })

                full_text = ' '.join(segment['text'] for segment in segments)
                extraction_time = time.time() - start_time

                result = {
                    'video_id': video_id,
                    'language': transcript.language_code,
                    'text': full_text,
                    'segments': segments,
                    'track_name': f'{transcript.language_code} ({transcript.language})',
                    'extraction_time': extraction_time,
                    'proxy_used': True,
                    'method': 'youtube-transcript-api'
                }

                logger.info(".2f")
                logger.info(f"Extracted {len(segments)} segments using youtube-transcript-api")
                return result

            except Exception as find_error:
                logger.warning(f"Could not find transcript for language {language}: {find_error}")

        except ImportError:
            logger.warning("youtube-transcript-api not available, falling back to manual method")
        except Exception as api_error:
            logger.warning(f"youtube-transcript-api failed: {api_error}, falling back to manual method")

        # Fallback to manual method if youtube-transcript-api fails
        logger.info("Falling back to manual HTML parsing method")

        # Step 1: Fetch watch page
        html = self._fetch_watch_page(video_id)
        if not html:
            logger.error("Failed to fetch watch page")
            return None

        # Step 2: Extract player response
        player_response = self._extract_player_response(html)
        if not player_response:
            logger.warning("No player response found - checking if video has captions...")
            # Check if HTML contains caption-related content
            if 'captionTracks' in html:
                logger.info("Found captionTracks in HTML but couldn't parse player response")
            elif 'captions' in html:
                logger.info("Found captions in HTML but couldn't parse player response")
            else:
                logger.info("No caption-related content found in HTML")

            # Save HTML for debugging
            with open(f'debug_no_player_response_{video_id}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return None

        # Step 3: Find caption tracks
        tracks = self._find_caption_tracks(player_response)
        if not tracks:
            logger.warning("No caption tracks found")
            return None

        # Find English track (or requested language)
        selected_track = None
        for track in tracks:
            if track['languageCode'].startswith(language):
                selected_track = track
                break

        # If no exact match, take first available
        if not selected_track and tracks:
            selected_track = tracks[0]
            logger.info(f"Using fallback language: {selected_track['languageCode']}")

        if not selected_track:
            logger.error("No suitable caption track found")
            return None

        logger.info(f"Selected track: {selected_track['languageCode']} - {selected_track['name']}")

        # Step 4: Fetch transcript
        transcript_xml = self._fetch_transcript(selected_track['baseUrl'])
        if not transcript_xml:
            logger.error("Failed to fetch transcript XML")
            return None

        # Step 5: Parse XML
        try:
            root = ET.fromstring(transcript_xml)
            segments = []

            for elem in root.findall('.//text'):
                text = elem.text or ""
                start = float(elem.get('start', 0))
                duration = float(elem.get('dur', 0))
                text = text.strip()
                if text:
                    segments.append({
                        'text': text,
                        'start': start,
                        'duration': duration
                    })

            full_text = ' '.join(segment['text'] for segment in segments)
            extraction_time = time.time() - start_time

            result = {
                'video_id': video_id,
                'language': selected_track['languageCode'],
                'text': full_text,
                'segments': segments,
                'track_name': selected_track['name'],
                'extraction_time': extraction_time,
                'proxy_used': True,
                'method': 'manual_html_parsing'
            }

            logger.info(".2f")
            logger.info(f"Extracted {len(segments)} segments using manual parsing")
            return result

        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            return None


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0

    def wait_if_needed(self):
        """Wait if needed to maintain rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()


def main():
    """Test the paid proxy transcript extractor."""
    import sys
    import os

    # Path to proxy file
    proxy_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'my_assets', 'Webshare residential proxies.txt')

    if not os.path.exists(proxy_file):
        print(f"ERROR: Proxy file not found: {proxy_file}")
        sys.exit(1)

    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=RE_NqKDKmqM",
        "https://www.youtube.com/watch?v=huVuqgZdlLM"
    ]

    print("=" * 80)
    print("PAID RESIDENTIAL PROXY YOUTUBE TRANSCRIPT EXTRACTION")
    print("=" * 80)
    print(f"Proxy file: {proxy_file}")
    print(f"Test URLs: {len(test_urls)}")
    print()

    # Initialize extractor
    try:
        extractor = PaidProxyYouTubeExtractor(proxy_file)
    except Exception as e:
        print(f"ERROR: Failed to initialize extractor: {e}")
        sys.exit(1)

    # Test each URL
    results = []
    for i, url in enumerate(test_urls, 1):
        print(f"\n[TEST {i}/{len(test_urls)}] {url}")
        print("-" * 60)

        result = extractor.extract_transcript(url)
        if result:
            print("SUCCESS")
            print(f"   Language: {result['language']}")
            print(f"   Segments: {len(result['segments'])}")
            print(".2f")
            print(f"   Text preview: {result['text'][:200]}...")
            results.append(True)
        else:
            print("FAILED")
            results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    successful = sum(results)
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0

    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(".1f")

    if successful > 0:
        print("\nSUCCESS! Paid residential proxies work for YouTube transcript extraction!")
        print("Ready to scale up testing and implement production solution.")
    else:
        print("\nAll tests failed. May need to adjust approach or check proxy credentials.")


if __name__ == "__main__":
    main()