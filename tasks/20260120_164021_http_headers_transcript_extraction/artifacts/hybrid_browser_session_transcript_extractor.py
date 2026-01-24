#!/usr/bin/env python3
"""
Hybrid Browser-Session YouTube Transcript Extractor

This approach uses a real browser session (Selenium) to obtain a validated
YouTube session and then reuses those cookies/headers for HTTP transcript fetches.

Why this helps:
- YouTube's anti-bot stack often blocks pure HTTP requests.
- A browser session solves JS, fingerprinting, and session validation.
- We then reuse that session to fetch transcript URLs reliably and cheaply.
"""

import json
import logging
import time
import os
from typing import Dict, Optional

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from http_headers_transcript_extractor import YouTubeTranscriptExtractor, TranscriptResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridYouTubeTranscriptExtractor:
    """Hybrid extractor using Selenium session + HTTP transcript fetch."""

    def __init__(self, timeout: int = 30, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.http_extractor = YouTubeTranscriptExtractor(timeout=timeout, max_retries=3)

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,720")
        options.add_argument("--lang=en-US")
        return webdriver.Chrome(options=options)

    def _wait_for_player_response(self, driver: webdriver.Chrome, timeout: int = 15) -> Optional[Dict]:
        """Wait until ytInitialPlayerResponse is available."""
        def player_response_ready(_driver):
            return _driver.execute_script("return window.ytInitialPlayerResponse || null;")

        try:
            return WebDriverWait(driver, timeout).until(player_response_ready)
        except Exception:
            return None

    def _build_session_from_browser(self, driver: webdriver.Chrome) -> requests.Session:
        """Create a requests.Session using browser cookies and user agent."""
        session = requests.Session()
        session.headers.update(self.http_extractor.session.headers)

        try:
            user_agent = driver.execute_script("return navigator.userAgent;")
            if user_agent:
                session.headers["User-Agent"] = user_agent
        except Exception:
            pass

        for cookie in driver.get_cookies():
            session.cookies.set(
                cookie.get("name"),
                cookie.get("value"),
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

        return session

    def _fetch_transcript_with_session(self, session: requests.Session, caption_url: str, video_id: str) -> Optional[str]:
        headers = session.headers.copy()
        headers.update({
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Referer": f"https://www.youtube.com/watch?v={video_id}",
            "X-Requested-With": "XMLHttpRequest",
        })

        try:
            response = session.get(caption_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            if not response.text.strip().startswith("<"):
                return None
            return response.text
        except Exception as exc:
            logger.error("Transcript fetch failed: %s", exc)
            return None

    def _fetch_transcript_via_browser(self, driver: webdriver.Chrome, caption_url: str) -> Optional[str]:
        """Fetch transcript using browser fetch API to bypass HTTP rate limits."""
        try:
            script = """
                const url = arguments[0];
                const callback = arguments[1];
                fetch(url, { credentials: 'include' })
                    .then(resp => resp.text())
                    .then(text => callback(text))
                    .catch(() => callback(null));
            """
            return driver.execute_async_script(script, caption_url)
        except Exception as exc:
            logger.error("Browser fetch failed: %s", exc)
            return None

    def extract_transcript(self, video_url: str, language: str = "en") -> Optional[TranscriptResult]:
        video_id = self.http_extractor.extract_video_id(video_url)
        if not video_id:
            logger.error("Invalid YouTube URL: %s", video_url)
            return None

        driver = self._create_driver()
        try:
            logger.info("Loading video page in browser session...")
            driver.get(video_url)
            time.sleep(2)

            player_response = self._wait_for_player_response(driver, timeout=20)
            if not player_response:
                logger.error("Could not access ytInitialPlayerResponse via browser session")
                return None

            caption_tracks = self.http_extractor.find_caption_tracks(player_response, language)
            if not caption_tracks:
                logger.warning("No caption tracks found for this video")
                return None

            session = self._build_session_from_browser(driver)
            selected_track = caption_tracks[0]

            xml_content = self._fetch_transcript_with_session(
                session,
                selected_track["baseUrl"],
                video_id,
            )
            if not xml_content:
                logger.warning("HTTP transcript fetch failed, trying browser fetch...")
                xml_content = self._fetch_transcript_via_browser(driver, selected_track["baseUrl"])
                if not xml_content:
                    logger.error("Failed to fetch transcript XML with browser fetch")
                    return None

            segments = self.http_extractor.parse_transcript_xml(xml_content)
            if not segments:
                # Try JSON3 parsing fallback
                if xml_content.strip().startswith("{"):
                    segments = self.http_extractor.parse_transcript_json3(xml_content)
            if not segments:
                # Save raw response for debugging
                try:
                    debug_path = os.path.join(os.path.dirname(__file__), "debug_transcript_response.txt")
                    with open(debug_path, "w", encoding="utf-8") as handle:
                        handle.write(xml_content[:2000])
                except Exception:
                    pass
                logger.error("Failed to parse transcript segments")
                return None

            full_text = " ".join(segment.text for segment in segments)
            is_generated = selected_track.get("kind") == "asr" or "auto-generated" in selected_track.get("name", "").lower()

            return TranscriptResult(
                text=full_text,
                segments=segments,
                language=selected_track["languageCode"],
                is_generated=is_generated,
                video_id=video_id,
                metadata={
                    "track_name": selected_track["name"],
                    "track_kind": selected_track.get("kind"),
                    "available_tracks": len(caption_tracks),
                    "extraction_method": "hybrid_browser_session",
                    "timestamp": time.time(),
                },
            )
        finally:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hybrid_browser_session_transcript_extractor.py <youtube_url> [language] [--headed]")
        sys.exit(1)

    video_url = sys.argv[1]
    language = "en"
    headless = True
    if len(sys.argv) > 2 and sys.argv[2].strip().lower() != "--headed":
        language = sys.argv[2]
    if "--headed" in sys.argv:
        headless = False

    extractor = HybridYouTubeTranscriptExtractor(headless=headless, timeout=30)
    result = extractor.extract_transcript(video_url, language)

    if result:
        print("SUCCESS: Transcript extracted")
        print(f"Language: {result.language}")
        print(f"Auto-generated: {result.is_generated}")
        print(f"Segments: {len(result.segments)}")
        print(f"Total characters: {len(result.text)}")
    else:
        print("FAILED: Transcript extraction failed")


if __name__ == "__main__":
    main()
