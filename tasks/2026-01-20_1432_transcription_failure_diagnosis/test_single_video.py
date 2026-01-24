#!/usr/bin/env python3
"""
Test single video transcription to verify rate limit fix.
"""

import os
import sys
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_transcribe.youtube_transcript import get_youtube_transcript

def test_single_video():
    """Test transcription of one failed video."""
    api_key = os.getenv("DEAPI_API_KEY", "")
    if not api_key:
        print("ERROR: DEAPI_API_KEY not set")
        return

    # Test one of the failed videos
    test_url = "https://www.youtube.com/watch?v=LTdWTf1OGKg"  # This one failed

    print(f"Testing transcription: {test_url}")
    print("This may take 2-5 minutes for DEAPI processing...")

    start_time = time.time()
    result = get_youtube_transcript(test_url, api_key)
    elapsed = time.time() - start_time

    print("
RESULTS:"    print(f"Success: {result.success}")
    print(f"Method: {result.method}")
    print(f"Time: {elapsed:.1f} seconds")

    if result.success:
        transcript_preview = result.transcript_text[:200] + "..." if len(result.transcript_text or "") > 200 else result.transcript_text
        print(f"Transcript preview: {transcript_preview}")
    else:
        print(f"Error: {result.error_message}")

    if result.success:
        print("\nSUCCESS: Rate limiting fix appears to work!")
    else:
        print(f"\nFAILED: Still having issues. Error: {result.error_message}")

if __name__ == "__main__":
    test_single_video()