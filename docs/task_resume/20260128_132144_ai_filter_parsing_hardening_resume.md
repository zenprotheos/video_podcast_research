# AI Filter Parsing Hardening — Task Resume

**Created:** 2026-01-28  
**Timestamp:** 20260128_132144  
**Status:** Plan complete; Phase 1 implementation pending  
**Purpose:** Resumable session prompt for new chat — full instructions, context, file paths, and references.

---

## Task Objective

Implement **Phase 1** of the AI filter parsing hardening plan in `src/bulk_transcribe/video_filter.py`: ID-anchored prompts, **JSON-only** parsing/validation, 10k token limit, validation-failure flow (console logs → retry 1x → stop + dev error), and minimal human-readable log files.

**Principle:** Correctness > speed. Never trust positional alignment alone.

---

## Context

- **Source of truth:** `tasks/20260124_083300_youtube_search_improvements/ai_filter_parsing_hardening_plan.md`
- **Engineering feedback:** `tasks/20260124_083300_youtube_search_improvements/ai_filter_feedback.md` — parsing/verification is P0; positional output is fragile.
- **Related build plan:** Build Plan 5 — AI Filter Documentation & Redo Logic (see `tasks/.../build plans/05_ai_filter_documentation_redo_logic.md`).
- **Current behaviour:** Prompt uses "Video 1:", "Video 2:"; model returns "1. RELEVANT - reason"; parser maps line number → batch index. No video IDs in prompt or output; no validation.
- **Required behaviour:** Prompt includes `[VIDEO_ID=...]` per video; model returns strict JSON `{ "decisions": [ { "video_id", "relevant", "reason" } ] }`; parser uses IDs only; validate coverage/uniqueness; on failure: console logs, retry 1x, then stop and return dev error. No text-format fallback.

---

## Phase 1 Scope (Implement in Order)

| # | Layer / area | What to do |
|---|--------------|------------|
| 1 | **Layer 1 — ID-anchored prompt** | In `_build_user_prompt()`: add `[VIDEO_ID={video.video_id}]` (or equivalent) to each video block; keep prompt readable. |
| 2 | **Layer 2 — JSON-only output** | In `_build_user_prompt()`: instruct model to respond with **only** valid JSON in schema `{ "decisions": [ { "video_id", "relevant", "reason" } ] }`. Replace `_parse_relevance_response()` with `_parse_and_validate_json_response()`: `json.loads()`, schema check, then ID validation (Layer 4). Output `Dict[str, Tuple[bool, str]]` by video_id. No text fallback. |
| 3 | **Layer 3 — Token limit** | In `_call_openrouter_api()` (or the payload built for filtering): set `max_tokens: 10_000`. (Current value is 1000.) |
| 4 | **Layer 4 — Validation** | In parser/validation: assert `set(parsed_ids) == set(expected_ids)` and each ID appears exactly once. On failure: do not accept batch. |
| 5 | **Validation failure & retry** | On parse/schema or ID validation failure: (1) emit **console logs** (batch id, expected/parsed IDs, raw snippet, error type), (2) **retry 1x** same batch, (3) if still failing: **stop task** and return `FilteringResult(success=False, error_message="...")` with batch id and short hint. Do not process further batches. No fallback to text parsing. |
| 6 | **Layer 5 — Log files** | Add parameter (e.g. `log_batch_artifacts: bool` or `log_dir: Optional[str]`) to `filter_videos_by_relevance()` / `_filter_video_batch()`. When enabled, write minimal per-batch log: `batch_id`, `video_ids`, `decisions`, `validation_errors`. Location e.g. `logs/ai_filter/`; filename includes timestamp and batch id. Human-readable, minimal; no full prompt, no full raw output, no PII. |

---

## Key File Paths

| Purpose | Path |
|--------|------|
| **Implement here** | `src/bulk_transcribe/video_filter.py` |
| **Plan (full spec)** | `tasks/20260124_083300_youtube_search_improvements/ai_filter_parsing_hardening_plan.md` |
| **Engineering feedback** | `tasks/20260124_083300_youtube_search_improvements/ai_filter_feedback.md` |
| **Build plan 5** | `tasks/20260124_083300_youtube_search_improvements/build plans/05_ai_filter_documentation_redo_logic.md` |
| **Agent/workflow rules** | `tasks/20260124_083300_youtube_search_improvements/build plans/AGENT_INSTRUCTIONS.md` |
| **Caller (filter button)** | `pages/01_YouTube_Search.py` — filter calls `filter_videos_by_relevance()`; ensure call sites still pass `videos`, `search_query`, `research_context`, `model`, `api_key`. New optional args for logging are fine. |

---

## Concrete Code Touchpoints (from plan)

- `_build_user_prompt()` — add `[VIDEO_ID=...]` to each block; instruct JSON-only output in required schema.
- Replace `_parse_relevance_response()` with `_parse_and_validate_json_response()` — `json.loads()`, schema check, ID validation → `Dict[str, Tuple[bool, str]]`.
- `_filter_video_batch()` — call new parser with `expected_video_ids`; map parsed dict to `(relevant_videos, filtered_out_videos)` by `video_id`; on failure: console logs, retry 1x, then stop and return error.
- `_call_openrouter_api()` or the code that builds the filter request — set `max_tokens: 10_000` for filter calls.
- Optional: `log_batch_artifacts` / `log_dir`; when set, write minimal per-batch log under e.g. `logs/ai_filter/`.

---

## Required JSON Schema (model output)

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

Parser must validate: `decisions` is a list; each item has `video_id` (str), `relevant` (bool), `reason` (str); set of `video_id`s equals set of input batch IDs; each ID appears exactly once.

---

## What NOT to Do (from plan)

- No parallel batching.
- No caching of filter results.
- No ranking or confidence-weighted ordering before verification.
- No regex-only parsing without ID-based validation.
- No fallback to text-format parsing when JSON fails.

---

## Success Criteria (Definition of Done)

- Every relevance decision is ID-anchored (prompt + output + parser).
- Every batch is verifiable (validation passes or batch fails).
- Silent misclassification is structurally impossible (validation enforces coverage and uniqueness).
- On parse/validation failure: console logs, retry 1x, then stop and dev-facing error.
- Log files, when enabled, are human-readable and sufficient to manually validate decisions.

---

## Suggested Next Steps for New Chat

1. Open `tasks/20260124_083300_youtube_search_improvements/ai_filter_parsing_hardening_plan.md` and use it as the implementation spec.
2. Edit `src/bulk_transcribe/video_filter.py`: implement Layers 1–4, Validation Failure & Retry, and Layer 5 (log files) per Phase 1.
3. Run syntax/import checks and any existing tests; add or run tests for parser and validation as needed.
4. Manually test: run YouTube Search → run AI filter on a small result set; confirm JSON request/response and that validation/retry/stop behave as specified.

---

## References in This Repo

- **CLAUDE.md** — run app, env, project layout.
- **AGENT.md** — repo agent rules.
- **.cursor/rules/00-core.mdc** — task-centric work, no ad-hoc in root, specs as source of truth.
- **docs/standards/import_standards.md** — import order and style.
