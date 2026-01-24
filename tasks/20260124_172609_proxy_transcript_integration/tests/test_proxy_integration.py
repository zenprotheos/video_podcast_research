"""
Integration test for proxy-based transcript extraction.

This test validates that:
1. The proxy extractor module loads correctly
2. The proxy configuration is valid
3. A transcript can be extracted using the proxy method

Run with: python -m pytest tasks/20260124_172609_proxy_transcript_integration/tests/test_proxy_integration.py -v
Or directly: python tasks/20260124_172609_proxy_transcript_integration/tests/test_proxy_integration.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(project_root / ".env")


def test_proxy_health():
    """Test that the proxy extractor is properly configured."""
    from src.bulk_transcribe.proxy_transcript import check_proxy_health

    health = check_proxy_health()
    print(f"Proxy Health Check: {health}")

    assert health["healthy"], f"Proxy health check failed: {health['message']}"
    assert health["proxy_count"] > 0, "No proxies loaded"
    print(f"[OK] Loaded {health['proxy_count']} proxies")


def test_single_video_extraction():
    """Test extracting a transcript from a single video."""
    from src.bulk_transcribe.proxy_transcript import get_proxy_transcript

    # Use one of the test URLs from the POC
    test_url = "https://www.youtube.com/watch?v=RE_NqKDKmqM"

    print(f"Testing extraction for: {test_url}")
    result = get_proxy_transcript(test_url)

    print(f"Result: success={result.success}, method={result.method}")

    if result.success:
        print(f"Transcript length: {len(result.transcript_text or '')} characters")
        print(f"Preview: {(result.transcript_text or '')[:200]}...")
    else:
        print(f"Error: {result.error_message}")

    assert result.success, f"Extraction failed: {result.error_message}"
    assert result.transcript_text, "No transcript text returned"
    assert len(result.transcript_text) > 100, "Transcript too short"

    print("[OK] Single video extraction successful!")


def test_transcript_result_interface():
    """Test that the TranscriptResult interface is compatible."""
    from src.bulk_transcribe.proxy_transcript import get_proxy_transcript
    from src.bulk_transcribe.youtube_transcript import TranscriptResult

    test_url = "https://www.youtube.com/watch?v=huVuqgZdlLM"

    result = get_proxy_transcript(test_url)

    # Verify it's a TranscriptResult
    assert isinstance(result, TranscriptResult), f"Expected TranscriptResult, got {type(result)}"

    # Verify all expected fields exist
    assert hasattr(result, "success")
    assert hasattr(result, "method")
    assert hasattr(result, "transcript_text")
    assert hasattr(result, "error_message")

    print("[OK] TranscriptResult interface compatible!")


def main():
    """Run all tests."""
    print("=" * 80)
    print("PROXY TRANSCRIPT INTEGRATION TESTS")
    print("=" * 80)
    print()

    # Check environment
    proxy_file = os.getenv("WEBSHARE_PROXY_FILE")
    print(f"WEBSHARE_PROXY_FILE: {proxy_file}")

    if not proxy_file:
        print("[!] WEBSHARE_PROXY_FILE not set in environment.")
        print("    Add this to your .env file:")
        print("    WEBSHARE_PROXY_FILE=my_assets/Webshare residential proxies.txt")
        return False

    if not os.path.exists(proxy_file):
        # Try relative to project root
        full_path = project_root / proxy_file
        if not full_path.exists():
            print(f"[!] Proxy file not found: {proxy_file}")
            return False
        else:
            print(f"[OK] Proxy file found at: {full_path}")

    print()
    tests = [
        ("Health Check", test_proxy_health),
        ("Single Video Extraction", test_single_video_extraction),
        ("Interface Compatibility", test_transcript_result_interface),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
            results.append((name, True, None))
        except Exception as e:
            print(f"[FAILED] {e}")
            results.append((name, False, str(e)))

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    for name, ok, error in results:
        status = "[OK]" if ok else "[FAILED]"
        print(f"  {status} {name}")
        if error:
            print(f"       Error: {error}")

    print()
    print(f"Passed: {passed}/{total}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
