# Task: AI Filter Prompt Flexibility

**Date:** 20260129_152507  
**Source:** Plan `ai_filter_prompt_flexibility_2df74732.plan.md`

## Objective

1. **Filter:** Add conceptual flexibility (related terminology) and enforce required terms (title/description) via prompt and optional `required_terms` param.
2. **Query planner:** When required terms are present in messages, output search queries with those terms as **quoted phrases** so YouTube returns phrase-matched results at search time.
3. **UI:** Pass `st.session_state.required_terms` into `filter_videos_by_relevance`.

Required terms (user or Phase 2 inferred) drive query planning; planned queries are run as-is (quotes included); AI filter cleans up the result set.

## Scope

- `src/bulk_transcribe/video_filter.py`: system prompt expansion, `required_terms` param, user prompt line.
- `pages/01_YouTube_Search.py`: pass `required_terms` to filter.
- `src/bulk_transcribe/query_planner.py`: instruction for quoted phrases when required terms in messages.
- E2E tests in task `tests/e2e/`.
- Optional: `docs/specs/youtube_search_workflow.md` note.

## Out of scope (Phase 2)

- LLM-inferred required terms when user leaves field empty (pre-fill Step 0).
