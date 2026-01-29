# Query Planner Model Reliability Analysis Results

**Date:** 2026-01-28  
**Test:** 6 models, 3 runs each, same research prompt  
**Prompt:** "research current marketing strategies for B2B SaaS companies that are working today (late 2025 to 2026), preferring more reputable sources and experts in the field. We should have a diverse topics covering all the core areas of marketing e2e."  
**max_queries:** 5

## Summary

All 6 models achieved **100% success rate** (3/3 runs). No prose-only or token-limit failures observed. The main differentiator is **speed** and **retry rate**.

## Results by Model

| Model | Success rate | Avg duration | Total retries (3 runs) | Recommendation |
|-------|--------------|--------------|------------------------|-----------------|
| openai/gpt-4o-mini | 100% (3/3) | 1.9s | 0 | **Default** – fast, reliable |
| openai/gpt-4.1-nano | 100% (3/3) | 1.8s | 0 | **Recommended** – fastest |
| google/gemini-2.5-flash-lite | 100% (3/3) | 1.8s | 0 | **Recommended** – fast |
| openai/gpt-oss-20b | 100% (3/3) | 3.0s | 0 | Recommended |
| openai/gpt-oss-120b | 100% (3/3) | 6.9s | 0 | OK – slower |
| openai/gpt-5-nano | 100% (3/3) | 20.9s | 2 | Use with caution – slowest, sometimes needs retry |

## Optimizations Applied

1. **Default model:** Set to `openai/gpt-4o-mini` (was `openai/gpt-5-nano`) for best balance of speed and reliability.
2. **Preset order (Step 0 and Step 3):** Reordered to prioritize fastest, zero-retry models:
   - openai/gpt-4o-mini
   - openai/gpt-4.1-nano
   - google/gemini-2.5-flash-lite
   - openai/gpt-5-nano
   - anthropic/claude-haiku-4.5
   - meta-llama/llama-3.2-3b-instruct
3. **Token scaling:** `max_tokens = min(150 * max_queries + 300, 2000)` – scales with requested query count.
4. **Retries:** Limited to 1 repair call (was 2) to reduce latency when validation fails.

## Root Cause Analysis

- **Prose responses:** 0  
- **Token limit issues:** 0  
- **Markdown-wrapped (minor):** 0  

Current prompt and token budget are sufficient for all tested models. The only model that occasionally needed a retry was `openai/gpt-5-nano` (2 retries across 3 runs); all others returned valid JSON on first call.

## How to Re-run

```powershell
$env:OPENROUTER_RUN_MODEL_TESTS="1"
.\.venv\Scripts\python.exe -m pytest tests/unit/test_model_reliability_analysis.py::test_model_reliability_analysis -v -s
```

Ensure `OPENROUTER_API_KEY` is set (e.g. in `.env`).
