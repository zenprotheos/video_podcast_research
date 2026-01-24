#!/usr/bin/env python3
"""
Test Script for HTTP Headers YouTube Transcript Extraction

Tests the browser-like HTTP headers approach on the provided YouTube URLs.
This script validates the implementation and provides detailed results.

Test URLs:
- https://www.youtube.com/watch?v=RE_NqKDKmqM
- https://www.youtube.com/watch?v=huVuqgZdlLM

Author: AI Assistant
Created: 2026-01-20
"""

import sys
import os
import json
import time
from datetime import datetime
from http_headers_transcript_extractor import YouTubeTranscriptExtractor, TranscriptResult

def test_single_url(extractor: YouTubeTranscriptExtractor, url: str, language: str = 'en') -> dict:
    """
    Test transcript extraction for a single URL.

    Args:
        extractor: Configured transcript extractor
        url: YouTube URL to test
        language: Language code

    Returns:
        Dictionary with test results
    """
    result = {
        'url': url,
        'video_id': extractor.extract_video_id(url),
        'language': language,
        'success': False,
        'extraction_time': None,
        'error_message': None,
        'transcript_info': None,
        'performance_metrics': {}
    }

    start_time = time.time()

    try:
        transcript_result = extractor.extract_transcript(url, language)

        extraction_time = time.time() - start_time
        result['extraction_time'] = round(extraction_time, 2)

        if transcript_result:
            result['success'] = True
            result['transcript_info'] = {
                'segments_count': len(transcript_result.segments),
                'text_length': len(transcript_result.text),
                'language': transcript_result.language,
                'is_generated': transcript_result.is_generated,
                'video_id': transcript_result.video_id
            }

            # Store first 500 characters as preview
            result['transcript_preview'] = transcript_result.text[:500] + "..." if len(transcript_result.text) > 500 else transcript_result.text

            result['performance_metrics'] = {
                'extraction_time_seconds': extraction_time,
                'characters_per_second': len(transcript_result.text) / extraction_time if extraction_time > 0 else 0,
                'segments_per_second': len(transcript_result.segments) / extraction_time if extraction_time > 0 else 0
            }
        else:
            result['error_message'] = "Extraction returned None"

    except Exception as e:
        extraction_time = time.time() - start_time
        result['extraction_time'] = round(extraction_time, 2)
        result['error_message'] = str(e)

    return result

def run_comprehensive_test():
    """Run comprehensive testing on both provided URLs."""
    # Force UTF-8 stdout to avoid Windows encoding issues
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Test URLs provided by user
    test_urls = [
        "https://www.youtube.com/watch?v=RE_NqKDKmqM",
        "https://www.youtube.com/watch?v=huVuqgZdlLM"
    ]

    print("HTTP Headers YouTube Transcript Extraction Test")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test URLs: {len(test_urls)}")
    print()

    # Initialize extractor
    extractor = YouTubeTranscriptExtractor(timeout=30, max_retries=3)

    # Run tests
    results = []
    overall_stats = {
        'total_urls': len(test_urls),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'average_extraction_time': 0,
        'total_characters_extracted': 0
    }

    for i, url in enumerate(test_urls, 1):
        print(f"Testing URL {i}/{len(test_urls)}: {url}")

        # Extract video ID for display
        video_id = extractor.extract_video_id(url)
        print(f"   Video ID: {video_id}")

        # Run extraction test
        result = test_single_url(extractor, url)

        # Update overall stats
        if result['success']:
            overall_stats['successful_extractions'] += 1
            overall_stats['total_characters_extracted'] += result['transcript_info']['text_length']
        else:
            overall_stats['failed_extractions'] += 1

        if result['extraction_time']:
            overall_stats['average_extraction_time'] += result['extraction_time']

        results.append(result)

        # Print immediate results
        if result['success']:
            print("   SUCCESS")
            print(f"   Segments: {result['transcript_info']['segments_count']}")
            print(f"   Characters: {result['transcript_info']['text_length']}")
            print(f"   Language: {result['transcript_info']['language']}")
            print(f"   Auto-generated: {result['transcript_info']['is_generated']}")
            # Avoid printing transcript text to prevent encoding issues
            print("   Preview: [omitted]")
        else:
            print("   FAILED")
            print(f"   Error: {result['error_message']}")

        print("-" * 40)

        # Add delay between tests to be respectful
        if i < len(test_urls):
            print("Waiting 2 seconds before next test...")
            time.sleep(2)

    # Calculate final stats
    if overall_stats['successful_extractions'] > 0:
        overall_stats['average_extraction_time'] /= overall_stats['successful_extractions']

    success_rate = (overall_stats['successful_extractions'] / overall_stats['total_urls']) * 100

    # Print comprehensive results
    print("\nCOMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"Total URLs Tested: {overall_stats['total_urls']}")
    print(f"Successful Extractions: {overall_stats['successful_extractions']}")
    print(f"Failed Extractions: {overall_stats['failed_extractions']}")
    print(f"Success Rate: {success_rate:.1f}%")
    if overall_stats['successful_extractions'] > 0:
        print(f"Average Extraction Time: {overall_stats['average_extraction_time']:.2f} seconds")
        print(f"Total Characters Extracted: {overall_stats['total_characters_extracted']:,}")
    # Detailed results for each URL
    print("\nDETAILED RESULTS PER URL")
    print("-" * 60)

    for i, result in enumerate(results, 1):
        status = "SUCCESS" if result['success'] else "FAILED"
        print(f"{i}. {status} - {result['video_id']}")
        if result['success']:
            print(f"   - Language: {result['transcript_info']['language']}")
            print(f"   - Segments: {result['transcript_info']['segments_count']}")
            print(f"   - Characters: {result['transcript_info']['text_length']:,}")
            print(f"   - Extraction Time: {result['extraction_time']:.2f} seconds")
        else:
            print(f"   - Error: {result['error_message']}")
        print()

    # Save results to file
    output_file = "http_headers_extraction_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'method': 'http_headers',
                'extractor_version': '1.0.0'
            },
            'overall_stats': overall_stats,
            'individual_results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"Detailed results saved to: {output_file}")

    # Final assessment
    print("\nASSESSMENT")
    print("-" * 60)

    if success_rate >= 80:
        print("EXCELLENT: HTTP headers approach working very well!")
        print("   This method successfully bypasses YouTube's IP blocking.")
    elif success_rate >= 50:
        print("GOOD: HTTP headers approach working moderately well.")
        print("   May need some refinements but shows promise.")
    else:
        print("POOR: HTTP headers approach needs significant improvements.")
        print("   Consider alternative approaches or additional refinements.")

    print("\nRECOMMENDATIONS:")
    if success_rate > 0:
        print("- Implement this method as a free alternative to paid transcription")
        print("- Add caching to avoid repeated requests to the same videos")
        print("- Consider implementing request pacing for production use")
        print("- Monitor for YouTube API changes that might affect reliability")
    else:
        print("- Investigate why extraction is failing (check network, headers, YouTube changes)")
        print("- Compare with browser automation approach")
        print("- Consider additional header spoofing or proxy usage")

def main():
    """Main entry point."""
    try:
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()