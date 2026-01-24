#!/usr/bin/env python3
"""
Test YouTube Transcript Extraction with WebShare Proxies

Tests if WebShare residential proxies can bypass YouTube's IP blocking
for transcript extraction.

Author: AI Assistant
Created: 2026-01-20
"""

import requests
from typing import Optional, Dict
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyYouTubeTranscriptExtractor:
    """YouTube transcript extractor using WebShare proxies."""

    def __init__(self, proxy_string: str):
        """
        Initialize with WebShare proxy credentials.

        Args:
            proxy_string: Format "IP:PORT:USERNAME:PASSWORD"
        """
        ip, port, username, password = proxy_string.split(':')
        self.proxies = {
            "http": f"http://{username}:{password}@{ip}:{port}/",
            "https": f"http://{username}:{password}@{ip}:{port}/"
        }
        self.session = requests.Session()

    def test_proxy_connection(self) -> bool:
        """Test if proxy is working."""
        try:
            response = self.session.get(
                "https://ipv4.webshare.io/",
                proxies=self.proxies,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Proxy test failed: {e}")
            return False

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID."""
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

    def fetch_watch_page(self, video_id: str) -> Optional[str]:
        """Fetch YouTube watch page through proxy."""
        url = f"https://www.youtube.com/watch?v={video_id}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        try:
            logger.info(f"Fetching watch page for {video_id} via proxy...")
            response = self.session.get(
                url,
                headers=headers,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()

            # Check if we got blocked content
            if 'blocked' in response.text.lower() or 'captcha' in response.text.lower():
                logger.warning("Detected blocking/captcha in response")
                return None

            return response.text

        except requests.RequestException as e:
            logger.error(f"Failed to fetch watch page: {e}")
            return None

    def extract_player_response(self, html: str) -> Optional[Dict]:
        """Extract ytInitialPlayerResponse from HTML."""
        import re
        import json

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
                    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        return None

    def find_caption_tracks(self, player_response: Dict) -> list:
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

    def fetch_transcript(self, caption_url: str) -> Optional[str]:
        """Fetch transcript XML through proxy."""
        headers = {
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,*;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        try:
            logger.info(f"Fetching transcript via proxy...")
            response = self.session.get(
                caption_url,
                headers=headers,
                proxies=self.proxies,
                timeout=15
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch transcript: {e}")
            return None

    def extract_transcript(self, video_url: str) -> Optional[Dict]:
        """Main extraction method."""
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return None

        # Test proxy first
        if not self.test_proxy_connection():
            logger.error("Proxy connection test failed")
            return None

        # Fetch watch page
        html = self.fetch_watch_page(video_id)
        if not html:
            return None

        # Extract player response
        player_response = self.extract_player_response(html)
        if not player_response:
            logger.warning("No player response found")
            return None

        # Find caption tracks
        tracks = self.find_caption_tracks(player_response)
        if not tracks:
            logger.warning("No caption tracks found")
            return None

        logger.info(f"Found {len(tracks)} caption tracks")

        # Try to fetch transcript from first track
        selected_track = tracks[0]
        logger.info(f"Using track: {selected_track['languageCode']} - {selected_track['name']}")

        transcript_xml = self.fetch_transcript(selected_track['baseUrl'])
        if not transcript_xml:
            return None

        # Basic XML parsing to extract text
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(transcript_xml)
            segments = []

            for elem in root.findall('.//text'):
                text = elem.text or ""
                start = float(elem.get('start', 0))
                text = text.strip()
                if text:
                    segments.append({'text': text, 'start': start})

            full_text = ' '.join(segment['text'] for segment in segments)

            return {
                'video_id': video_id,
                'language': selected_track['languageCode'],
                'text': full_text,
                'segments': segments,
                'track_name': selected_track['name'],
                'proxy_used': True
            }

        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            return None

def test_proxy(proxy_string: str, video_url: str) -> Dict:
    """Test a single proxy with a video URL."""
    result = {
        'proxy': proxy_string.split(':')[0],  # Just IP for privacy
        'success': False,
        'error': None,
        'transcript_info': None,
        'timing': {}
    }

    start_time = time.time()

    try:
        extractor = ProxyYouTubeTranscriptExtractor(proxy_string)
        transcript = extractor.extract_transcript(video_url)

        result['timing']['total'] = time.time() - start_time

        if transcript:
            result['success'] = True
            result['transcript_info'] = {
                'segments_count': len(transcript['segments']),
                'text_length': len(transcript['text']),
                'language': transcript['language']
            }
        else:
            result['error'] = "Extraction failed"

    except Exception as e:
        result['timing']['total'] = time.time() - start_time
        result['error'] = str(e)

    return result

def main():
    """Test WebShare proxies for YouTube transcript extraction."""

    # Read proxies from file
    try:
        with open('my_assets/Webshare 10 proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Proxy file not found: my_assets/Webshare 10 proxies.txt")
        return

    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=RE_NqKDKmqM",
        "https://www.youtube.com/watch?v=huVuqgZdlLM"
    ]

    print("Testing WebShare Proxies for YouTube Transcript Extraction")
    print("=" * 70)
    print(f"Found {len(proxies)} proxies")
    print(f"Testing {len(test_urls)} URLs")
    print()

    # Test first 2 proxies only (as requested)
    successful_proxies = []

    for i, proxy in enumerate(proxies[:2], 1):
        print(f"Testing Proxy {i}: {proxy.split(':')[0]}")

        proxy_results = []

        for url in test_urls:
            print(f"   Testing URL: {url.split('v=')[1]}")
            result = test_proxy(proxy, url)
            proxy_results.append(result)

            if result['success']:
                print("   SUCCESS")
                print(f"   Segments: {result['transcript_info']['segments_count']}")
                print(".2f")
                print(f"   Language: {result['transcript_info']['language']}")
                successful_proxies.append(proxy.split(':')[0])
            else:
                print("   FAILED")
                print(f"   Error: {result['error']}")

        print("-" * 50)

        # Don't test all URLs if proxy failed first one
        if not any(r['success'] for r in proxy_results):
            print("   Skipping remaining URLs for this proxy (all failed)")
            break

    # Summary
    print("\nTEST SUMMARY")
    print("=" * 50)
    print(f"Proxies tested: {min(2, len(proxies))}")
    print(f"Successful proxies: {len(successful_proxies)}")

    if successful_proxies:
        print("SUCCESS: WebShare proxies work for YouTube transcript extraction!")
        print("Working proxy IPs:")
        for proxy_ip in successful_proxies:
            print(f"  • {proxy_ip}")
    else:
        print("FAILED: WebShare proxies did not bypass YouTube blocking")
        print("   Consider different proxy service or approach")

if __name__ == "__main__":
    main()