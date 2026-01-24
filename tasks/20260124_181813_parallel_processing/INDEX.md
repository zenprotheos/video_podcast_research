# Parallel Processing Implementation

## Overview
Implement parallel/concurrent transcript extraction using ThreadPoolExecutor with Streamlit-compatible patterns.

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
1. Create parallel_processor.py with ThreadPoolExecutor wrapper
2. Make RateLimiter thread-safe with locks
3. Integrate into Streamlit page with main-thread UI updates
4. Add concurrency slider control

## Files Modified/Created
- `src/bulk_transcribe/parallel_processor.py` - NEW
- `src/bulk_transcribe/paid_proxy_extractor.py` - MODIFY (thread-safe rate limiter)
- `pages/03_Bulk_Transcribe_Proxy.py` - MODIFY (parallel integration)
