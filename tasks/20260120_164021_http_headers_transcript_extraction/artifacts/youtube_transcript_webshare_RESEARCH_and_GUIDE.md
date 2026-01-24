# YouTube Transcript Extraction Using Paid Webshare Residential Proxies
# ------------------------------------------------------------
# This document outlines a complete approach to extracting YouTube transcripts
# using Webshare's rotating residential proxies via direct HTTP requests.
# It assumes use of the `youtube-transcript-api` library, `requests`, or similar tools.
#
# Goal: Use HTTP-based methods (not headless browsers) to extract transcript data
# while avoiding IP bans and respecting rate limits.

# -------------------------------
# 1. Requirements
# -------------------------------
# - Python 3.7+
# - Libraries:
#     - youtube-transcript-api
#     - requests
#     - requests[socks] (if testing SOCKS5/Tor proxy support)
#
# Install with:
# pip install youtube-transcript-api requests[socks]

# -------------------------------
# 2. Webshare Configuration
# -------------------------------
# Webshare rotating residential proxies:
# - Dashboard URL: https://proxy.webshare.io/
# - Plan: Rotating Residential
# - Bandwidth: 1 GB (≈ 3,000 videos)
# - IPs auto-rotate per request

# Authentication Format (for HTTP proxies):
#   http://USERNAME:PASSWORD@PROXY_HOST:PORT

# Example credentials (replace with actual):
USERNAME = "your_webshare_user"
PASSWORD = "your_webshare_pass"
PROXY_HOST = "proxy.webshare.io"
PROXY_PORT = "80"

# Full Proxy URL:
proxy_auth_url = f"http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

# Proxy dictionary for requests/youtube-transcript-api
PROXIES = {
    "http": proxy_auth_url,
    "https": proxy_auth_url
}

# -------------------------------
# 3. youtube-transcript-api Method
# -------------------------------
from youtube_transcript_api import YouTubeTranscriptApi

# Recommended headers (simulate real browser request)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36"
}

# Fetch transcript through proxy
video_id = "VIDEO_ID_HERE"

try:
    transcript = YouTubeTranscriptApi.get_transcript(
        video_id,
        proxies=PROXIES,
        cookies=None,  # Leave as None unless geo-restricted
        headers=HEADERS
    )
    print("\n".join([t['text'] for t in transcript]))
except Exception as e:
    print("Transcript fetch failed:", str(e))

# -------------------------------
# 4. Direct Requests to TimedText Endpoint (Alt Method)
# -------------------------------
import requests
import xml.etree.ElementTree as ET

# URL format (example with lang=en)
timedtext_url = f"https://video.google.com/timedtext?lang=en&v={video_id}"

response = requests.get(timedtext_url, headers=HEADERS, proxies=PROXIES, timeout=10)

if response.ok:
    # Parse basic text transcript from XML
    root = ET.fromstring(response.text)
    lines = [child.text for child in root if child.text]
    print("\n".join(lines))
else:
    print("Failed to retrieve timedtext:", response.status_code)

# -------------------------------
# 5. Best Practices
# -------------------------------
# ✅ Use proper User-Agent header to simulate real browser traffic
# ✅ Rotate video IDs when making batch requests (avoid hitting same endpoint)
# ✅ Avoid bursts: space requests (e.g., 2–5/sec max)
# ✅ Monitor usage to stay under bandwidth cap (1 GB = ~3,000 transcripts)
# ✅ Retry on 429 or connection errors with exponential backoff
# ✅ Use Webshare's session ID format if supported (to rotate IP more aggressively)
#     proxy_auth_url = f"http://{USERNAME}-session-{random_id}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
# ✅ Log bandwidth and response sizes for analytics

# -------------------------------
# 6. Debugging Tips
# -------------------------------
# - Check if proxy works: requests.get("https://httpbin.org/ip", proxies=PROXIES)
# - If transcript fails but page loads: might be geo-locked or no captions
# - Webshare free proxies likely won't work reliably (use paid rotating residential)
# - Avoid YouTube Data API – this method is purely non-official and uses public endpoints

# -------------------------------
# 7. Extras (Optional)
# -------------------------------
# - Use multiprocessing or asyncio for larger batch jobs (respect rate limits)
# - Use Tor as backup method if proxy pool is temporarily blocked
# - Use yt-dlp --write-auto-sub to extract captions as another fallback

# -------------------------------
# END OF DOCUMENT
# -------------------------------
