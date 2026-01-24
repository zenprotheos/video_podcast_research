"""
Paid Residential Proxy YouTube Transcript Extractor

Production-ready extractor using WebShare paid residential proxies.
Uses session-based rotation for IP diversity and rate limiting for reliability.
"""

import logging
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests

# Use module logger (inherits from app configuration)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0

    def wait_if_needed(self) -> None:
        """Wait if needed to maintain rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()


class PaidProxyYouTubeExtractor:
    """YouTube transcript extractor using WebShare paid residential proxies."""

    def __init__(self, proxy_file_path: Optional[str] = None):
        """
        Initialize with paid proxy credentials.

        Args:
            proxy_file_path: Path to file containing proxy credentials.
                            If None, uses WEBSHARE_PROXY_FILE environment variable.
        """
        if proxy_file_path is None:
            proxy_file_path = os.getenv("WEBSHARE_PROXY_FILE")
            if not proxy_file_path:
                raise ValueError(
                    "Proxy file path not provided and WEBSHARE_PROXY_FILE environment variable not set"
                )

        self.proxy_file_path = proxy_file_path
        self.proxy_credentials = self._load_proxy_credentials(proxy_file_path)
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(requests_per_second=2.0)

    def _load_proxy_credentials(self, file_path: str) -> List[str]:
        """Load proxy credentials from file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Proxy file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()][:100]

        if not proxies:
            raise ValueError(f"No proxy credentials found in file: {file_path}")

        logger.info(f"Loaded {len(proxies)} proxy credentials")
        return proxies

    def _get_random_proxy(self) -> Dict[str, str]:
        """Get a random proxy from the pool."""
        if not self.proxy_credentials:
            raise ValueError("No proxy credentials available")

        proxy_line = random.choice(self.proxy_credentials)
        parts = proxy_line.split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid proxy format: expected host:port:user:pass")

        host, port, username, password = parts
        proxy_url = f"http://{username}:{password}@{host}:{port}"
        return {"http": proxy_url, "https": proxy_url}

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                proxies = self._get_random_proxy()
                logger.debug(
                    f"Fetching watch page for {video_id} (attempt {attempt + 1}/{max_retries})"
                )

                response = self.session.get(
                    url, headers=headers, proxies=proxies, timeout=15
                )

                logger.debug(f"Response status: {response.status_code}")
                response.raise_for_status()

                content = response.text
                content_lower = content.lower()

                # Blocking detection
                blocking_indicators = [
                    "our systems have detected unusual traffic",
                    "unusual traffic from your computer network",
                    "verify you are human",
                    "sorry for the inconvenience",
                    "automated queries",
                    "too many requests",
                ]

                is_blocked = any(
                    indicator in content_lower for indicator in blocking_indicators
                )

                if is_blocked:
                    logger.warning(f"Detected blocking on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)
                        continue
                    return None

                return content

            except requests.RequestException as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    return None

        return None

    def _extract_player_response(self, html: str) -> Optional[Dict]:
        """Extract ytInitialPlayerResponse from HTML."""
        import json

        patterns = [
            r"ytInitialPlayerResponse\s*=\s*({.+?});",
            r'ytInitialPlayerResponse"\s*:\s*({.+?})',
            r'"playerResponse"\s*:\s*({.+?})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1)
                    json_str = re.sub(r"//.*?$", "", json_str, flags=re.MULTILINE)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Try to find captionTracks directly in HTML
        try:
            caption_index = html.find("captionTracks")
            if caption_index != -1:
                brace_count = 0
                start_pos = caption_index
                while start_pos > 0:
                    char = html[start_pos]
                    if char == "{":
                        brace_count += 1
                        if brace_count == 1:
                            break
                    elif char == "}":
                        brace_count -= 1
                    start_pos -= 1

                if brace_count == 1:
                    end_pos = caption_index
                    brace_count = 1
                    while end_pos < len(html):
                        char = html[end_pos]
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = html[start_pos : end_pos + 1]
                                try:
                                    json_str = re.sub(
                                        r"//.*?$", "", json_str, flags=re.MULTILINE
                                    )
                                    data = json.loads(json_str)
                                    if (
                                        "captions" in data
                                        and "playerCaptionsTracklistRenderer"
                                        in data["captions"]
                                    ):
                                        return data
                                except json.JSONDecodeError:
                                    pass
                        end_pos += 1

        except Exception as e:
            logger.debug(f"Failed to extract JSON around captionTracks: {e}")

        # Try ytAtR approach as fallback
        try:
            ytatr_pattern = r"window\.ytAtR\s*=\s*['\"]([^'\"]*)['\"]"
            ytatr_match = re.search(ytatr_pattern, html, re.DOTALL)
            if ytatr_match:
                escaped_data = ytatr_match.group(1)
                try:
                    decoded_json = escaped_data.encode("raw_unicode_escape").decode(
                        "utf-8"
                    )
                    data = json.loads(decoded_json)
                    if "playerResponse" in data:
                        return data["playerResponse"]
                except Exception as decode_error:
                    logger.debug(f"Failed to decode ytAtR data: {decode_error}")

        except Exception as e:
            logger.debug(f"Failed to parse ytAtR format: {e}")

        return None

    def _find_caption_tracks(self, player_response: Dict) -> List[Dict]:
        """Find caption tracks from player response."""
        tracks = []

        try:
            if (
                "captions" in player_response
                and "playerCaptionsTracklistRenderer" in player_response["captions"]
            ):
                renderer = player_response["captions"]["playerCaptionsTracklistRenderer"]

                if "captionTracks" in renderer:
                    for track in renderer["captionTracks"]:
                        tracks.append(
                            {
                                "baseUrl": track.get("baseUrl", ""),
                                "languageCode": track.get("languageCode", ""),
                                "name": track.get("name", {}).get("simpleText", ""),
                            }
                        )

        except KeyError:
            pass

        return tracks

    def _fetch_transcript(self, caption_url: str) -> Optional[str]:
        """Fetch transcript XML through proxy."""
        self.rate_limiter.wait_if_needed()

        headers = {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,*;q=0.5",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.youtube.com/",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                proxies = self._get_random_proxy()
                logger.debug(f"Fetching transcript (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(
                    caption_url, headers=headers, proxies=proxies, timeout=15
                )
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Transcript fetch failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        return None

    def extract_transcript(self, video_url: str, language: str = "en") -> Optional[Dict]:
        """
        Main extraction method using paid residential proxies.

        Args:
            video_url: YouTube video URL
            language: Language code (default: 'en')

        Returns:
            dict with keys: video_id, language, text, segments, track_name,
                           extraction_time, proxy_used, method
            None if extraction failed
        """
        start_time = time.time()
        video_id = self._extract_video_id(video_url)

        if not video_id:
            logger.error("Could not extract video ID from URL")
            return None

        logger.info(f"Starting proxy extraction for video: {video_id}")
        print(f"[EXTRACTOR_DEBUG] Starting extraction for video: {video_id}")

        # Try using youtube-transcript-api with WebShare proxy config
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api.proxies import WebshareProxyConfig

            print(f"[EXTRACTOR_DEBUG] Imported youtube-transcript-api successfully")
            logger.debug(
                "Attempting transcript extraction with youtube-transcript-api + WebShare proxies"
            )

            # Parse proxy credentials for WebShare config
            sample_proxy = self.proxy_credentials[0]
            parts = sample_proxy.split(":")
            base_username = parts[2].rsplit("-", 1)[0]
            password = parts[3]

            proxy_config = WebshareProxyConfig(
                proxy_username=base_username,
                proxy_password=password,
                retries_when_blocked=5,
            )

            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
            transcript_list = ytt_api.list(video_id)

            try:
                transcript = transcript_list.find_transcript([language, "en"])
                transcript_data = transcript.fetch()

                segments = []
                for item in transcript_data:
                    segments.append(
                        {
                            "text": item.text,
                            "start": item.start,
                            "duration": item.duration,
                        }
                    )

                full_text = " ".join(segment["text"] for segment in segments)
                extraction_time = time.time() - start_time

                result = {
                    "video_id": video_id,
                    "language": transcript.language_code,
                    "text": full_text,
                    "segments": segments,
                    "track_name": f"{transcript.language_code} ({transcript.language})",
                    "extraction_time": extraction_time,
                    "proxy_used": True,
                    "method": "youtube-transcript-api-proxy",
                }

                logger.info(
                    f"Extracted {len(segments)} segments in {extraction_time:.2f}s using youtube-transcript-api"
                )
                return result

            except Exception as find_error:
                print(f"[EXTRACTOR_DEBUG] find_transcript failed: {find_error}")
                logger.warning(
                    f"Could not find transcript for language {language}: {find_error}"
                )

        except ImportError as ie:
            print(f"[EXTRACTOR_DEBUG] ImportError: {ie}")
            logger.warning(
                "youtube-transcript-api not available, falling back to manual method"
            )
        except Exception as api_error:
            print(f"[EXTRACTOR_DEBUG] API error: {api_error}")
            import traceback
            print(f"[EXTRACTOR_DEBUG] Traceback: {traceback.format_exc()}")
            logger.warning(
                f"youtube-transcript-api failed: {api_error}, falling back to manual method"
            )

        # Fallback to manual method
        print(f"[EXTRACTOR_DEBUG] Falling back to manual HTML parsing method")
        logger.info("Falling back to manual HTML parsing method")

        html = self._fetch_watch_page(video_id)
        if not html:
            print(f"[EXTRACTOR_DEBUG] Failed to fetch watch page - returning None")
            logger.error("Failed to fetch watch page")
            return None

        player_response = self._extract_player_response(html)
        if not player_response:
            print(f"[EXTRACTOR_DEBUG] No player response found - returning None")
            logger.warning("No player response found in HTML")
            return None

        tracks = self._find_caption_tracks(player_response)
        if not tracks:
            print(f"[EXTRACTOR_DEBUG] No caption tracks found - returning None")
            logger.warning("No caption tracks found")
            return None

        # Find requested language or fallback
        selected_track = None
        for track in tracks:
            if track["languageCode"].startswith(language):
                selected_track = track
                break

        if not selected_track and tracks:
            selected_track = tracks[0]
            logger.info(f"Using fallback language: {selected_track['languageCode']}")

        if not selected_track:
            logger.error("No suitable caption track found")
            return None

        logger.debug(
            f"Selected track: {selected_track['languageCode']} - {selected_track['name']}"
        )

        transcript_xml = self._fetch_transcript(selected_track["baseUrl"])
        if not transcript_xml:
            logger.error("Failed to fetch transcript XML")
            return None

        try:
            root = ET.fromstring(transcript_xml)
            segments = []

            for elem in root.findall(".//text"):
                text = elem.text or ""
                start = float(elem.get("start", 0))
                duration = float(elem.get("dur", 0))
                text = text.strip()
                if text:
                    segments.append(
                        {"text": text, "start": start, "duration": duration}
                    )

            full_text = " ".join(segment["text"] for segment in segments)
            extraction_time = time.time() - start_time

            result = {
                "video_id": video_id,
                "language": selected_track["languageCode"],
                "text": full_text,
                "segments": segments,
                "track_name": selected_track["name"],
                "extraction_time": extraction_time,
                "proxy_used": True,
                "method": "manual_html_parsing",
            }

            logger.info(
                f"Extracted {len(segments)} segments in {extraction_time:.2f}s using manual parsing"
            )
            return result

        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            return None
