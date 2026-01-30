# Specs Impact: AI Filter Prompt Flexibility

## Affected spec

- `docs/specs/youtube_search_workflow.md`

## Changes

- **Filter:** Relevance uses reasonable conceptual breadth (related terminology included); when "Required terms in title/description" is provided, filter enforces them.
- **Query planner:** Outputs each required term/phrase as a quoted phrase; comma-separated terms become multiple quoted phrases per query. When required terms empty, app first infers **one** conservative term (1–3 words) via infer_single_required_term(), pre-fills Step 0, then generates search queries with that term in messages so planned queries include quoted phrases (two-phase flow).
- **Data flow:** No step-order or SearchResult structure change. `required_terms` passed explicitly to filter; planner receives them via messages; Phase 2 pre-fills same field (single source of truth).

## Spec update (optional)

If formalizing: add one sentence under Step 0 or Data Handling that required terms (when set) are used for query planning (quoted phrases) and for AI filter cleanup; planned queries are run as-is.
