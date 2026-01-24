#!/usr/bin/env python3
"""
Transcription Failure Diagnostic Tool

Tests individual video transcription to identify root causes of failures.
Checks rate limits, API key validity, and video-specific issues.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from bulk_transcribe.youtube_transcript import get_youtube_transcript, try_deapi_transcription
from bulk_transcribe.youtube_metadata import fetch_youtube_metadata


class TranscriptionDiagnostic:
    """Diagnose transcription failures with detailed testing."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEAPI_API_KEY", "")
        self.results = []

    def check_api_key_validity(self) -> Dict:
        """Test if DEAPI API key is valid by making a simple request."""
        print("🔍 Checking DEAPI API key validity...")

        import requests

        base_url = os.getenv("DEAPI_BASE_URL", "https://api.deapi.ai")
        endpoint = f"{base_url}/api/v1/client/vid2txt"

        # Test with a known short YouTube video
        test_video = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Very short test video

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "video_url": test_video,
            "include_ts": False,
            "model": "WhisperLargeV3",
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            print(f"API Key test response: {response.status_code}")

            if response.status_code == 401:
                return {"valid": False, "error": "Invalid API key (401 Unauthorized)"}
            elif response.status_code == 402:
                return {"valid": False, "error": "Insufficient credits (402 Payment Required)"}
            elif response.status_code == 429:
                return {"valid": True, "error": "Rate limited (429 Too Many Requests)"}
            elif response.status_code == 200:
                # Cancel the request immediately to avoid wasting credits
                request_id = response.json().get("data", {}).get("request_id")
                if request_id:
                    cancel_url = f"{base_url}/api/v1/client/request-status/{request_id}"
                    try:
                        requests.delete(cancel_url, headers=headers, timeout=5)
                    except:
                        pass
                return {"valid": True, "error": None}
            else:
                return {"valid": False, "error": f"Unexpected response: {response.status_code} - {response.text[:200]}"}

        except requests.exceptions.Timeout:
            return {"valid": False, "error": "Request timed out - check internet connection"}
        except requests.exceptions.ConnectionError:
            return {"valid": False, "error": "Connection error - check DEAPI service status"}
        except Exception as e:
            return {"valid": False, "error": f"Unexpected error: {str(e)}"}

    def test_video_accessibility(self, youtube_url: str) -> Dict:
        """Test if a YouTube video is accessible."""
        print(f"🔍 Testing video accessibility: {youtube_url}")

        try:
            meta = fetch_youtube_metadata(youtube_url)
            if meta.error:
                return {
                    "accessible": False,
                    "error": f"YouTube metadata error: {meta.error}",
                    "title": None,
                    "duration": None
                }

            return {
                "accessible": True,
                "error": None,
                "title": meta.title,
                "duration": meta.duration,
                "view_count": meta.view_count,
                "video_id": meta.video_id
            }
        except Exception as e:
            return {
                "accessible": False,
                "error": f"Metadata fetch failed: {str(e)}",
                "title": None,
                "duration": None
            }

    def test_transcription_with_timing(self, youtube_url: str) -> Dict:
        """Test transcription with detailed timing and error reporting."""
        print(f"🎙️ Testing transcription: {youtube_url}")

        start_time = time.time()

        # First check if YouTube captions are available (fast)
        try:
            from bulk_transcribe.youtube_transcript import try_youtube_captions
            captions_result = try_youtube_captions(youtube_url)
            has_captions = captions_result is not None
        except:
            has_captions = False

        # Now test full transcription
        result = get_youtube_transcript(youtube_url, self.api_key)

        elapsed = time.time() - start_time

        return {
            "url": youtube_url,
            "success": result.success,
            "method": result.method,
            "error": result.error_message,
            "has_captions": has_captions,
            "duration_seconds": elapsed,
            "deapi_request_id": result.deapi_request_id,
            "transcript_length": len(result.transcript_text or "") if result.success else 0
        }

    def test_rate_limiting(self) -> Dict:
        """Test for rate limiting by making multiple quick requests."""
        print("⏱️ Testing for rate limiting...")

        if not self.api_key:
            return {"rate_limited": False, "error": "No API key available"}

        # Make 3 quick requests to test rate limiting
        test_video = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

        results = []
        for i in range(3):
            print(f"  Request {i+1}/3...")
            result = self.test_transcription_with_timing(test_video)
            results.append(result)

            # Small delay between requests
            if i < 2:
                time.sleep(0.5)

        # Check if any requests failed due to rate limiting
        rate_limited = any(
            "rate limit" in (r.get("error") or "").lower() or
            "429" in (r.get("error") or "")
            for r in results
        )

        return {
            "rate_limited": rate_limited,
            "requests_made": len(results),
            "successful_requests": sum(1 for r in results if r["success"]),
            "rate_limit_errors": sum(1 for r in results if "rate limit" in (r.get("error") or "").lower()),
            "results": results
        }

    def run_full_diagnostic(self, test_urls: List[str]) -> Dict:
        """Run complete diagnostic suite."""
        print("🚀 Starting full transcription diagnostic...")

        diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "api_key_check": self.check_api_key_validity(),
            "rate_limit_test": self.test_rate_limiting(),
            "video_tests": []
        }

        print("\n📊 API Key Status:", "✅ Valid" if diagnostic_results["api_key_check"]["valid"] else "❌ Invalid")
        if diagnostic_results["api_key_check"]["error"]:
            print(f"   Error: {diagnostic_results['api_key_check']['error']}")

        print(f"\n⏱️ Rate Limit Test: {'❌ Limited' if diagnostic_results['rate_limit_test']['rate_limited'] else '✅ OK'}")
        print(f"   Successful requests: {diagnostic_results['rate_limit_test']['successful_requests']}/3")

        print("\n🎥 Testing individual videos...")
        for url in test_urls:
            # Test accessibility first
            accessibility = self.test_video_accessibility(url)
            print(f"   Video accessible: {'✅ Yes' if accessibility['accessible'] else '❌ No'}")
            if not accessibility["accessible"]:
                print(f"     Error: {accessibility['error']}")

            # Test transcription
            transcription = self.test_transcription_with_timing(url)
            print(f"   Transcription: {'✅ Success' if transcription['success'] else '❌ Failed'}")
            print(f"     Method: {transcription['method']}")
            if transcription["error"]:
                print(f"     Error: {transcription['error']}")
            print(".2f")

            diagnostic_results["video_tests"].append({
                "url": url,
                "accessibility": accessibility,
                "transcription": transcription
            })

        return diagnostic_results

    def save_results(self, results: Dict, filename: str = "diagnostic_results.json"):
        """Save diagnostic results to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {filename}")


def main():
    """Main diagnostic function."""
    print("🎯 Bulk Transcribe - Transcription Failure Diagnostic")
    print("=" * 60)

    # Load API key
    api_key = os.getenv("DEAPI_API_KEY", "")
    if not api_key:
        print("❌ DEAPI_API_KEY environment variable not set!")
        return

    # Create diagnostic instance
    diag = TranscriptionDiagnostic(api_key)

    # Test URLs from the failed session (sample of failed and successful ones)
    test_urls = [
        "https://www.youtube.com/watch?v=67MX3_N4Lfo",  # This one succeeded
        "https://www.youtube.com/watch?v=LTdWTf1OGKg",  # Failed
        "https://www.youtube.com/watch?v=sr9fzxRW0bA",  # Failed
        "https://www.youtube.com/watch?v=NyLbwKohcII",  # This one succeeded
        "https://www.youtube.com/watch?v=ZQ-U8U1EX_A",  # Failed
    ]

    # Run diagnostic
    results = diag.run_full_diagnostic(test_urls)

    # Save results
    diag.save_results(results, "transcription_diagnostic_results.json")

    # Print summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)

    api_check = results["api_key_check"]
    rate_check = results["rate_limit_test"]

    print(f"API Key Valid: {'✅' if api_check['valid'] else '❌'}")
    if api_check["error"]:
        print(f"  Issue: {api_check['error']}")

    print(f"Rate Limited: {'❌ YES' if rate_check['rate_limited'] else '✅ No'}")
    print(f"Rate Test Success Rate: {rate_check['successful_requests']}/3")

    successful_videos = sum(1 for v in results["video_tests"] if v["transcription"]["success"])
    total_videos = len(results["video_tests"])
    print(f"Video Success Rate: {successful_videos}/{total_videos}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 20)

    if not api_check["valid"]:
        print("• Fix API key issue first")
        if "402" in str(api_check["error"]):
            print("  → Add credits to your DEAPI account")
        elif "401" in str(api_check["error"]):
            print("  → Verify your API key is correct")

    if rate_check["rate_limited"]:
        print("• Reduce request frequency (increase delays between requests)")
        print("• Consider upgrading to Premium account for higher limits")
        print("• Batch requests with longer intervals")

    if successful_videos < total_videos:
        print("• Some videos have specific issues:")
        for video in results["video_tests"]:
            if not video["transcription"]["success"]:
                print(f"  → {video['url'][:50]}...: {video['transcription']['error']}")


if __name__ == "__main__":
    main()