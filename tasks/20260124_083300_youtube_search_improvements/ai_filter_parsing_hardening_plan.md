# AI Filter Parsing Hardening — Implementation Plan

**Created:** 2026-01-26  
**Source:** `ai_filter_feedback.md` (engineering feedback)  
**Principle:** Correctness > speed. Never trust positional alignment alone.

---

## Adopted Prioritization

Your feedback correctly reframes the risk: the bottleneck is **parsing and verification**, not batching or UX.

| Previous focus        | Your focus              | New order                         |
|-----------------------|-------------------------|-----------------------------------|
| UX clarity, progress  | Parsing/verification    | **Parsing hardening first**       |
| Redo message, Clear   | ID-anchored decisions   | Layer 1–4 before new UX features  |

This document integrates `ai_filter_feedback.md` into a concrete, code-located implementation plan and reprioritizes the roadmap so parsing hardening is P0.

---

## Current vs. Required Contract

### Current (Fragile)

```
Prompt:  "Video 1: Title: ..."   "Video 2: Title: ..."
Output:  "1. RELEVANT - reason"   "2. NOT_RELEVANT - reason"
Map:     line_number n → batch[n-1]   (positional only)
Check:   none
```

- No video ID in prompt or output.
- Parser assumes `model_line_number == prompt_video_index`; not verified.
- Silent misclassification (e.g. off-by-one) is possible.

### Required (Your Contract)

```
Prompt:  "1. [VIDEO_ID=abc123] Title: ..."   "2. [VIDEO_ID=def456] Title: ..."
Output:  Strict JSON only — no text-format fallback
Map:     output video_id → input VideoSearchItem by video_id
Check:   All input IDs present, no unknown IDs, each ID once.
```

- Every decision anchored to a stable ID.
- **JSON only:** Parsing and validation are JSON-based; no fallback to text format.
- **On validation failure:** Console logs for troubleshooting, retry 1x, then stop and surface a dev-facing error.
- **Log files:** Human-readable, minimal — only what’s needed to manually validate decisions.
- **Token limit:** 10,000 `max_tokens` per API call.

---

## Implementation Plan by Layer

### Layer 1 — ID-Anchored Prompt (Critical)

**Goal:** Every video in the prompt is labelled with its YouTube video ID.

**File:** `src/bulk_transcribe/video_filter.py`  
**Function:** `_build_user_prompt()`

**Change:**

- Keep "Video 1:", "Video 2:" for readability, but add an explicit ID line or inline tag:
  - **Option A (explicit line):**  
    `Video 1:\nID: {video.video_id}\nTitle: ...`
  - **Option B (inline, matches your spec):**  
    `1. [VIDEO_ID={video.video_id}]\nTitle: ...`

Use the same convention in the "Respond in this exact format" instruction (see Layer 2).

**Example (Option B):**

```
1. [VIDEO_ID=abc123]
   Title: ...
   Channel: ...
   Description: ...
   Published: ...

2. [VIDEO_ID=def456]
   ...
```

**Acceptance:** Every video block in the prompt contains `video_id` in a parseable form.

---

### Layer 2 — JSON-Only Output Contract (No Text Fallback)

**Goal:** Model returns strict JSON. Parser uses JSON only; no text-format fallback.

**File:** `src/bulk_transcribe/video_filter.py`  
**Functions:**  
- `_build_user_prompt()` — update the “Respond in this exact format” section.  
- Replace `_parse_relevance_response()` with `_parse_and_validate_json_response()` — `json.loads()`, schema check, then validation (Layer 4).

**Required JSON schema (model output):**

```json
{
  "decisions": [
    {
      "video_id": "abc123",
      "relevant": true,
      "reason": "Directly discusses proxy evasion"
    }
  ]
}
```

**Prompt addition:** Tell the model to respond with **only** valid JSON in this exact shape. Emphasise: one object per video, use the `[VIDEO_ID=...]` from each block as `video_id`; include `relevant` (boolean) and `reason` (string).

**Parser contract:**

- Input: `response_text`, `expected_video_ids: Set[str]`.
- Steps: `json.loads(response_text)` then validate schema (required keys, types) then run ID validation (Layer 4).
- Output: `Dict[str, Tuple[bool, str]]` — map `video_id -> (is_relevant, reason)`.
- **No fallback:** If JSON parse or schema check fails, do not try text format. Proceed to **Validation Failure & Retry** (see below).

**Acceptance:** Parsing is JSON-only; any parse/schema failure triggers the validation-failure flow (console logs, retry 1x, then stop with dev error).

---

### Layer 3 — Token Limit

**Goal:** Allow enough output for large batches and detailed reasons.

**File:** `src/bulk_transcribe/video_filter.py`  
**Location:** `_call_openrouter_api()` (and any wrapper that sets request payload).

**Change:** Set `max_tokens: 10_000` in the chat-completions payload used for filtering. (Current value is 1000.)

**Acceptance:** Filter API calls use `max_tokens: 10000`.

---

### Layer 4 — Parser Validation Rules (Non-Negotiable)

**Goal:** Every batch is verifiable; silent misclassification is impossible when validation is applied.

**File:** `src/bulk_transcribe/video_filter.py`  
**Where:** In/next to the function that turns raw response into a dict of decisions (e.g. `_parse_relevance_response()` or `_parse_and_validate_batch()`).

**Rules:**

1. **Coverage:** Set of `video_id` in parsed output == set of `video_id` in input batch.  
   - If any input ID missing → validation fail.  
   - If any output ID not in input → validation fail.

2. **Uniqueness:** Each ID appears exactly once in the parsed output.

3. **Optional (Layer 3):** If `confidence` is present, assert `0 <= confidence <= 1`.

**On validation failure:**

- Treat batch as failed (do not merge partial decisions into “relevant”).
- Emit **console logs** for troubleshooting (batch id, expected vs parsed IDs, raw response snippet).
- **Retry 1x** (same batch, same request).
- If validation still fails after retry: **stop the task** and surface a **dev-facing error message** (do not continue with other batches).

**Acceptance:** No batch is accepted when ID coverage or uniqueness is wrong; failed batches trigger console logs, one retry, then task stop and dev error.

---

## Validation Failure & Retry (Mandatory)

**Goal:** Deterministic behaviour when JSON parse or ID validation fails.

**Flow:**

1. **On parse/schema failure or validation failure:**  
   - Write **console logs** for troubleshooting: batch index, expected video_ids, parsed video_ids (if any), raw response snippet (e.g. first 500 chars), and the specific error (parse error vs missing IDs vs unknown IDs).
2. **Retry 1x:** Re-run the same batch (same prompt, same API call). If it succeeds, continue; if it fails again, go to step 3.
3. **After failed retry:**  
   - **Stop the task** (do not process further batches).  
   - Return a **dev-facing error** (e.g. `FilteringResult(success=False, error_message="...")`) that includes batch id and a short hint (e.g. "JSON validation failed for batch 2 after 1 retry").
4. **No fallback** to text-format parsing.

**Acceptance:** Parse/validation failures produce console logs, at most one retry, then task stop and dev error; no silent continuation.

---

### Layer 5 — Log Files (Human-Readable, Minimal)

**Goal:** Persist just enough for humans to manually validate decisions when needed. Not verbose; only what is necessary to audit why a video was included or excluded.

**Content (per batch) — minimal:** batch_id, video_ids, decisions (list of {video_id, relevant, reason}), validation_errors. Do not include full prompt, full raw output, or PII. Location: e.g. `logs/ai_filter/`; filename includes timestamp and batch id.

**Implementation:**

- **When to write:** After each batch that completes successfully (post-validation). Optionally on validation failure (before retry) if a log dir is configured.
- **Content (per batch) — minimal:** batch_id, video_ids, decisions (list of {video_id, relevant, reason}), validation_errors (empty on success; on failure, short list).
- **Do not include:** Full prompt text, full raw model output, PII. Optionally include a short raw_snippet (e.g. first 200 chars) only when writing a failure log.
- **Location:** Dedicated dir, e.g. `logs/ai_filter/` or under `output/sessions/`. One file per run or per batch; filename includes timestamp and batch id.
- **Implementation:** Parameter (e.g. `log_batch_artifacts: bool` or `log_dir: Optional[str]`) on `filter_videos_by_relevance()` or `_filter_video_batch()`.
- When enabled, write a small JSON or structured text file per batch with batch_id, video_ids, decisions, validation_errors.

**Acceptance:** Logs exist when enabled; they are human-readable and sufficient to validate decisions without clutter.

---

### Layer 6 — Quality Heuristics (Soft Warnings)

**Goal:** Flag suspicious outcomes without blocking.

**Examples:**

- 0% relevant in a batch → suspicious.
- > 90% relevant in a batch → suspicious.
- All confidence scores identical (when used) → suspicious.
- All reasons very short or generic → suspicious.

**Implementation:**

- After validation, compute heuristics; append warnings to a list or logger.
- Surface in UI as non-blocking messages (e.g. “Unusual: this batch had 0% relevant”) or in logs only for now.

**Acceptance:** Heuristics run and warnings are visible in logs or UI; they do not change accept/reject of the batch.

---

## Minimal Rollout (Aligned With Your Phases)

### Phase 1 — Immediate (Layers 1, 2, 3, 4 + Validation Failure & Retry + Log Files)

1. **Layer 1:** Add `[VIDEO_ID=...]` (or equivalent) to each video in the prompt.
2. **Layer 2:** Use **JSON-only** output: require model to respond with strict JSON `{ "decisions": [ { "video_id", "relevant", "reason" } ] }`. No text-format fallback.
3. **Layer 3:** Set `max_tokens: 10_000` in the filter API payload.
4. **Layer 4:** Implement validation (all input IDs present, no unknown IDs, each ID once). On failure: console logs, retry 1x, then stop task and surface dev-facing error.
5. **Validation Failure & Retry:** On parse/schema or ID validation failure: emit console logs (batch id, expected/parsed IDs, raw snippet, error type), retry 1x, then stop task and return dev error. No fallback to text parsing.
6. **Layer 5 — Log files:** Add log files for manual validation when needed. Human-readable, minimal: batch_id, video_ids, decisions, validation_errors. Location e.g. `logs/ai_filter/`; one file per batch or per run; filename includes timestamp and batch id.

**Deliverable:** ID-anchored prompts, JSON-only parsing and schema validation, 10k token limit, strict validation with retry/stop flow, and minimal log files for auditing.

**Files:**

- `src/bulk_transcribe/video_filter.py`:  
  - `_build_user_prompt()` — add VIDEO_ID to each block; instruct JSON-only output in required schema.  
  - Replace `_parse_relevance_response()` with `_parse_and_validate_json_response()` — `json.loads()`, schema check, ID validation.  
  - `_filter_video_batch()` — use parsed dict by video_id; on failure: console logs, retry 1x, then stop and return error.  
  - `_call_openrouter_api()` (or caller) — set `max_tokens: 10_000` for filter requests.  
  - Optional: parameter for log dir / log_batch_artifacts; write minimal per-batch log when enabled.

**Testing:**

- Unit tests: prompt contains each `video_id`; JSON parser and schema validation; validation rejects missing/unknown/duplicate IDs; retry/stop behaviour.
- Integration: run filter on a small batch; inspect decisions by video_id; trigger validation failure and check console logs and dev error.

---

### Phase 2 — Optional (Layer 6, UX, Progress)

1. **Layer 6:** Quality heuristics (soft warnings).
2. **UX:** Redo message, Clear Filter, etc.
3. **Progress:** Batch progress callback.

---

## What We Explicitly Defer (Per Your “What NOT to Do”)

- Parallel batching.
- Caching of filter results.
- Ranking or confidence-weighted ordering before verification.
- Regex-only parsing without ID-based validation.

Correctness and verifiability come first.

---

## Definition of “Done” (From Your Doc)

The filter is robust enough when:

- Every relevance decision is ID-anchored (prompt + output + parser).
- Every batch is verifiable (validation passes or batch fails).
- Silent misclassification is structurally impossible (validation enforces coverage and uniqueness).
- Engineers can inspect why a video was included (artifact logging when enabled).
- Users can trust re-filtering (same validation applies on every run).

---

## Concrete Code Touchpoints

| Layer | File | Function / Location |
|-------|------|---------------------|
| 1 | `video_filter.py` | `_build_user_prompt()` — add `[VIDEO_ID=...]` to each block; instruct JSON-only output in required schema |
| 2 | `video_filter.py` | Replace `_parse_relevance_response()` with `_parse_and_validate_json_response()` — `json.loads()`, schema check, ID validation |
| 2 | `video_filter.py` | `_filter_video_batch()` — call parser with expected video_ids; map parsed dict to (relevant, filtered_out) by video_id |
| 3 | `video_filter.py` | `_call_openrouter_api()` or caller — set `max_tokens: 10_000` for filter requests |
| 4 | `video_filter.py` | In parser/validation: set(parsed_ids)==set(input_ids), each ID once; on failure: console logs, retry 1x, then stop and dev error |
| Validation failure | `video_filter.py` | On parse/validation failure: console logs, retry 1x, then stop task and return FilteringResult(success=False, error_message=...) |
| 5 (log files) | `video_filter.py` | Parameter log_batch_artifacts or log_dir; when enabled, write minimal per-batch log to e.g. logs/ai_filter/ |

---

## Summary

- Your feedback is adopted as the main driver: **parsing and verification** are P0.
- **Phase 1** = Layers 1, 2, 3, 4 + Validation Failure & Retry + Log Files. **JSON-only**; no text fallback. **Token limit:** 10k. On validation failure: console logs, retry 1x, then stop and dev error.
- **Phase 2** = Layer 6, UX, progress (optional).
- This plan keeps “correctness > speed” and “never trust positional alignment alone” as the core rules.
- The existing docs (`ai_filter_process_uml.md`, `ai_filter_optimization_recommendations.md`) remain valid for batching, UX, and progress; they are reprioritized to run **after** parsing hardening.

Implementing Phase 1 (Layers 1, 2, 3, 4 + Validation Failure & Retry + Log Files) in `video_filter.py` is the next concrete step.
