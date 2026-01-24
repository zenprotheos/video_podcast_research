#!/usr/bin/env python3
"""
Browser UI Transcript Extractor (Selenium)

This approach uses full browser UI automation:
1) Open YouTube video
2) Open the "More actions" menu
3) Click "Show transcript"
4) Read transcript text from the panel
"""

import time
import logging
import os
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserUITranscriptExtractor:
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout

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

    def _dismiss_consent_dialog(self, driver: webdriver.Chrome) -> None:
        """Try to dismiss cookie/consent dialogs if they appear."""
        candidates = [
            "//button//span[contains(text(),'I agree')]",
            "//button//span[contains(text(),'Accept all')]",
            "//button//span[contains(text(),'Reject all')]",
            "//button//span[contains(text(),'Got it')]",
        ]
        for xpath in candidates:
            try:
                button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button.click()
                time.sleep(1)
                return
            except Exception:
                continue

    def _open_transcript_panel(self, driver: webdriver.Chrome) -> bool:
        """Open transcript panel via the UI menu."""
        try:
            # Try to dismiss any consent dialog first
            self._dismiss_consent_dialog(driver)

            # Wait for the "More actions" (three dots) button
            menu_selectors = [
                "//button[@aria-label='More actions']",
                "//button[contains(@aria-label,'More actions')]",
                "//ytd-menu-renderer//button[@id='button']",
            ]
            menu_button = None
            for selector in menu_selectors:
                try:
                    menu_button = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except Exception:
                    continue
            if not menu_button:
                return False

            menu_button.click()
            time.sleep(1)

            # Click "Show transcript" in the menu
            transcript_selectors = [
                "//ytd-menu-service-item-renderer//yt-formatted-string[contains(text(),'Show transcript')]",
                "//ytd-menu-service-item-renderer//yt-formatted-string[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'transcript')]",
            ]
            transcript_item = None
            for selector in transcript_selectors:
                try:
                    transcript_item = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except Exception:
                    continue
            if not transcript_item:
                return False

            transcript_item.click()
            time.sleep(2)
            return True
        except Exception as exc:
            logger.error("Failed to open transcript panel: %s", exc)
            return False

    def _extract_transcript_segments(self, driver: webdriver.Chrome) -> List[Dict]:
        """Extract transcript segments from the transcript panel."""
        segments = []
        try:
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ytd-transcript-segment-renderer")
                )
            )

            segment_nodes = driver.find_elements(By.CSS_SELECTOR, "ytd-transcript-segment-renderer")
            for node in segment_nodes:
                try:
                    time_node = node.find_element(By.CSS_SELECTOR, ".segment-timestamp")
                    text_node = node.find_element(By.CSS_SELECTOR, ".segment-text")
                    segments.append({
                        "time": time_node.text.strip(),
                        "text": text_node.text.strip(),
                    })
                except Exception:
                    continue

            return segments
        except Exception as exc:
            logger.error("Failed to extract transcript segments: %s", exc)
            return []

    def extract_transcript(self, video_url: str) -> Optional[List[Dict]]:
        driver = self._create_driver()
        try:
            logger.info("Loading video page...")
            driver.get(video_url)
            time.sleep(3)
            logger.info("Current URL: %s", driver.current_url)
            logger.info("Page title: %s", driver.title)

            if not self._open_transcript_panel(driver):
                try:
                    debug_path = os.path.join(os.path.dirname(__file__), "debug_page_source.html")
                    with open(debug_path, "w", encoding="utf-8") as handle:
                        handle.write(driver.page_source[:50000])
                except Exception:
                    pass
                return None

            segments = self._extract_transcript_segments(driver)
            if not segments:
                logger.error("No transcript segments found.")
                return None

            return segments
        finally:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python browser_ui_transcript_extractor.py <youtube_url> [--headed]")
        sys.exit(1)

    url = sys.argv[1]
    headless = True
    if len(sys.argv) > 2 and sys.argv[2].strip().lower() == "--headed":
        headless = False

    extractor = BrowserUITranscriptExtractor(headless=headless, timeout=30)
    segments = extractor.extract_transcript(url)

    if segments:
        print("SUCCESS: Transcript extracted")
        print(f"Segments: {len(segments)}")
        print("Preview:")
        for seg in segments[:10]:
            print(f"{seg['time']} - {seg['text']}")
    else:
        print("FAILED: Could not extract transcript via UI")


if __name__ == "__main__":
    main()
