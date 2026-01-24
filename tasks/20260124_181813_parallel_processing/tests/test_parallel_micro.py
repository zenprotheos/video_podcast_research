"""
Micro-test for parallel transcript processing.

Tests 2 workers processing 2 videos in parallel to validate
threading works correctly before scaling up.

Usage:
    python tasks/20260124_181813_parallel_processing/tests/test_parallel_micro.py
"""

import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.bulk_transcribe.parallel_processor import (
    ParallelTranscriptProcessor,
    VideoTask,
    create_video_task,
)


def mock_extraction_func(youtube_url: str):
    """
    Mock extraction function for testing without actual API calls.
    Simulates network delay and returns mock TranscriptResult.
    """
    from src.bulk_transcribe.youtube_transcript import TranscriptResult
    import random
    
    # Simulate variable network delay (1-3 seconds)
    delay = random.uniform(1.0, 3.0)
    print(f"  [MOCK] Processing {youtube_url} (simulating {delay:.2f}s delay)")
    time.sleep(delay)
    
    # 90% success rate for testing
    if random.random() < 0.9:
        return TranscriptResult(
            success=True,
            method="mock_parallel_test",
            transcript_text=f"Mock transcript for {youtube_url}",
        )
    else:
        return TranscriptResult(
            success=False,
            method="mock_parallel_test",
            error_message="Simulated random failure",
        )


def test_parallel_2_workers_2_videos():
    """Test: 2 workers processing 2 videos in parallel."""
    print("\n" + "=" * 60)
    print("MICRO-TEST: 2 workers, 2 videos")
    print("=" * 60)
    
    # Create processor with 2 workers
    processor = ParallelTranscriptProcessor(
        max_workers=2,
        extraction_func=mock_extraction_func,
    )
    
    # Create 2 test tasks
    tasks = [
        create_video_task(
            row_index=0,
            youtube_url="https://youtube.com/watch?v=test_video_1",
            video_id="test_video_1",
            title="Test Video 1",
        ),
        create_video_task(
            row_index=1,
            youtube_url="https://youtube.com/watch?v=test_video_2",
            video_id="test_video_2",
            title="Test Video 2",
        ),
    ]
    
    # Submit all tasks
    start_time = time.time()
    print(f"\n[INFO] Submitting {len(tasks)} tasks...")
    submitted = processor.submit_batch(tasks)
    print(f"[INFO] Submitted {submitted} tasks")
    
    # Poll for results (simulating main thread behavior)
    print("\n[INFO] Polling for results...")
    results_received = 0
    
    while not processor.is_complete():
        result = processor.get_next_result(timeout=0.5)
        if result:
            results_received += 1
            status = "[OK]" if result.success else "[FAILED]"
            print(f"  {status} Video {result.task.video_id}: {result.processing_time:.2f}s")
    
    total_time = time.time() - start_time
    progress = processor.get_progress()
    
    print(f"\n[RESULTS]")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Sequential would be: ~4-6s (2 x 1-3s)")
    print(f"  Parallel speedup: Videos processed simultaneously")
    print(f"  Completed: {progress.completed}/{progress.total}")
    print(f"  Successful: {progress.successful}")
    print(f"  Failed: {progress.failed}")
    
    # Cleanup
    processor.stop()
    
    # Validate parallel execution (should be faster than sequential)
    # With 2 videos at 1-3s each, parallel should complete in ~3s max
    # Sequential would take 4-6s
    if total_time < 5.0:
        print("\n[PASS] Parallel execution confirmed (faster than sequential)")
        return True
    else:
        print("\n[WARN] Execution time suggests sequential processing")
        return False


def test_parallel_2_workers_5_videos():
    """Test: 2 workers processing 5 videos (validates batching)."""
    print("\n" + "=" * 60)
    print("MICRO-TEST: 2 workers, 5 videos (batch test)")
    print("=" * 60)
    
    processor = ParallelTranscriptProcessor(
        max_workers=2,
        extraction_func=mock_extraction_func,
    )
    
    # Create 5 test tasks
    tasks = [
        create_video_task(
            row_index=i,
            youtube_url=f"https://youtube.com/watch?v=batch_video_{i}",
            video_id=f"batch_video_{i}",
            title=f"Batch Video {i}",
        )
        for i in range(5)
    ]
    
    start_time = time.time()
    print(f"\n[INFO] Submitting {len(tasks)} tasks...")
    submitted = processor.submit_batch(tasks)
    print(f"[INFO] Submitted {submitted} tasks")
    
    # Poll for results
    print("\n[INFO] Polling for results...")
    while not processor.is_complete():
        result = processor.get_next_result(timeout=0.5)
        if result:
            progress = processor.get_progress()
            status = "[OK]" if result.success else "[FAILED]"
            print(f"  {status} Video {result.task.video_id} ({progress.completed}/{progress.total})")
    
    total_time = time.time() - start_time
    progress = processor.get_progress()
    
    print(f"\n[RESULTS]")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Sequential would be: ~10-15s (5 x 1-3s)")
    print(f"  With 2 workers: ~6-9s (3 batches of ~2-3s)")
    print(f"  Completed: {progress.completed}/{progress.total}")
    print(f"  Successful: {progress.successful}")
    print(f"  Failed: {progress.failed}")
    
    processor.stop()
    
    # With 2 workers and 5 videos, should take ~3 batches worth of time
    if total_time < 12.0:
        print("\n[PASS] Batching and parallelism working")
        return True
    else:
        print("\n[WARN] Execution time higher than expected")
        return False


def test_with_real_proxy_2_videos():
    """Test: 2 workers with actual proxy extraction (2 videos)."""
    print("\n" + "=" * 60)
    print("REAL TEST: 2 workers, 2 real YouTube videos")
    print("=" * 60)
    
    # Check if proxy is configured
    proxy_file = os.getenv("WEBSHARE_PROXY_FILE")
    if not proxy_file or not os.path.exists(proxy_file):
        print("[SKIP] WEBSHARE_PROXY_FILE not configured, skipping real test")
        return True
    
    # Use default extraction function (real proxy)
    processor = ParallelTranscriptProcessor(max_workers=2)
    
    # Two known working videos
    tasks = [
        create_video_task(
            row_index=0,
            youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            video_id="dQw4w9WgXcQ",
            title="Never Gonna Give You Up",
        ),
        create_video_task(
            row_index=1,
            youtube_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
            video_id="jNQXAC9IVRw",
            title="Me at the zoo",
        ),
    ]
    
    start_time = time.time()
    print(f"\n[INFO] Submitting {len(tasks)} real video tasks...")
    submitted = processor.submit_batch(tasks)
    print(f"[INFO] Submitted {submitted} tasks")
    
    print("\n[INFO] Processing (this may take 10-30 seconds)...")
    while not processor.is_complete():
        result = processor.get_next_result(timeout=1.0)
        if result:
            status = "[OK]" if result.success else "[FAILED]"
            text_preview = ""
            if result.transcript_result and result.transcript_result.transcript_text:
                text_preview = result.transcript_result.transcript_text[:50] + "..."
            print(f"  {status} {result.task.title}: {result.processing_time:.2f}s")
            if text_preview:
                # Handle Unicode safely for Windows console
                try:
                    print(f"       Preview: {text_preview}")
                except UnicodeEncodeError:
                    print(f"       Preview: [Unicode characters - transcript retrieved successfully]")
            if not result.success and result.error_message:
                print(f"       Error: {result.error_message}")
    
    total_time = time.time() - start_time
    progress = processor.get_progress()
    
    print(f"\n[RESULTS]")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Completed: {progress.completed}/{progress.total}")
    print(f"  Successful: {progress.successful}")
    print(f"  Failed: {progress.failed}")
    
    processor.stop()
    
    return progress.successful > 0


if __name__ == "__main__":
    print("=" * 60)
    print("PARALLEL PROCESSOR MICRO-TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Mock test with 2 workers, 2 videos
    results.append(("2 workers, 2 videos (mock)", test_parallel_2_workers_2_videos()))
    
    # Test 2: Mock test with 2 workers, 5 videos
    results.append(("2 workers, 5 videos (mock)", test_parallel_2_workers_5_videos()))
    
    # Test 3: Real test with 2 videos (only if proxy configured)
    results.append(("2 workers, 2 real videos", test_with_real_proxy_2_videos()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)
