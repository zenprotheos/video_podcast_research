# Parallel Processing Implementation

## Overview
Parallel/concurrent transcript extraction is implemented using `ThreadPoolExecutor` with
Streamlit-compatible patterns (background work in threads, UI updates in the main thread).

## Goal
- Enable processing multiple videos simultaneously instead of sequentially
- Start with micro-tests (2 workers) before scaling to 20-50
- Use threading (optimal for I/O-bound network operations)
- Maintain Streamlit UI responsiveness

## Key Constraints
- Cannot call Streamlit commands from background threads
- Must update UI from main thread only
- Rate limiting must be thread-safe
- Error isolation per worker

## Approach
1. Create `parallel_processor.py` with a reusable `ThreadPoolExecutor` wrapper and queue-based
   result collection (used by tests/micro-benchmarks).
2. Make `RateLimiter` thread-safe with locks.
3. Integrate parallel processing directly into the Streamlit proxy page using a worker helper
   (`process_single_video_parallel`) plus `ThreadPoolExecutor` + `as_completed` for polling from
   the main thread.
4. Add a concurrency slider control (2–20 workers) and a toggle to fall back to sequential mode.

## Files Modified/Created
- `src/bulk_transcribe/parallel_processor.py` - NEW reusable processor class (currently used by tests).
- `src/bulk_transcribe/paid_proxy_extractor.py` - MODIFY (thread-safe rate limiter).
- `pages/03_Bulk_Transcribe_Proxy.py` - MODIFY (parallel integration via helper + ThreadPoolExecutor).
- `tasks/20260124_181813_parallel_processing/tests/test_parallel_micro.py` - NEW micro-tests
  validating parallel behavior in isolation.

## How It Works (Actual Runtime Flow)
1. **Streamlit UI (main thread)** collects inputs and configures parallelism.
2. **Worker threads** run `process_single_video_parallel`, which:
   - fetches YouTube metadata,
   - writes metadata JSON,
   - uses the proxy extractor to fetch transcript text,
   - writes transcript markdown on success.
3. **Main thread** polls futures with `as_completed`, then updates:
   - the status table,
   - progress bar + metrics,
   - session state counters.

This keeps all Streamlit UI updates on the main thread while allowing network-bound work to
execute concurrently.
