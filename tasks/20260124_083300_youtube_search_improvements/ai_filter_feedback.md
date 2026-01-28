````markdown
# AI Filter Parsing & Reliability — Engineering Feedback for Implementation

**Audience:** Cursor IDE Agent / Engineering  
**Context:** YouTube Search Tool – AI relevance filtering  
**Goal:** Harden parsing, improve auditability, and make filtering trustworthy at scale

---

## Executive Summary

The current AI filtering pipeline is **architecturally sound but epistemically fragile**.

The core risk is not batching, cost, or model choice — it is **parsing and verification**.

Right now:
- The system relies on **positional numbering only**
- There are **no video IDs in model output**
- There is **no validation layer**
- There is **no way to debug or audit decisions**
- Silent misclassification is possible and undetectable

This document explains:
1. How parsing works today
2. Why it is risky
3. Concrete failure modes
4. A layered implementation plan to fix it
5. Suggested prompt + parser contracts
6. A minimal rollout strategy (low risk, incremental)

---

## 1. Current Parsing Logic (As Implemented Today)

### What the system assumes

1. Videos are sent to the model in a numbered list:
   - `1. Video A`
   - `2. Video B`
2. The model responds with numbered lines:
   - `1. RELEVANT`
   - `2. NOT_RELEVANT`
3. The parser maps:
   - Line number `n` → `batch[n-1]`

### What is NOT used

- ❌ YouTube video IDs
- ❌ Titles for matching
- ❌ Checksums or hashes
- ❌ Confidence scores
- ❌ Output validation beyond basic parsing

### Key invariant (fragile)

```text
model_line_number == prompt_video_index
````

This invariant is assumed, not verified.

---

## 2. Why This Is Risky (Failure Modes)

### Failure Mode A: Subtle Misalignment (Most Dangerous)

Model internally reasons correctly but outputs labels shifted by one index.

Result:

* Parser accepts output
* Wrong videos are marked relevant
* No error
* No signal
* Silent accuracy corruption

This is worse than a hard failure.

---

### Failure Mode B: Partial Output

Model returns fewer lines than expected.

Result:

* Entire batch is discarded
* Safe but noisy
* User sees fewer relevant videos

This is acceptable.

---

### Failure Mode C: Extra Commentary

Model adds prose before or after results.

Result:

* Parser may fail entirely
* Or incorrectly parse lines
* Behavior depends on implementation detail

---

## 3. Strategic Diagnosis

The system is currently:

* ✅ Deterministic in structure
* ✅ Cost efficient
* ❌ Not verifiable
* ❌ Not auditable
* ❌ Not resilient to LLM quirks

This is acceptable for Phase 1, but not for:

* Research workflows
* Automated pipelines
* Agentic extensions
* Iterative re-filtering with trust expectations

---

## 4. Design Principle Going Forward

**Never trust positional alignment alone.**

Every relevance decision must be:

1. Anchored to a stable identifier
2. Validated against input
3. Inspectable after the fact

---

## 5. Recommended Solution (Layered, Incremental)

### Layer 1 — ID-Anchored Prompt (Critical)

#### Prompt change (input)

Instead of:

```text
1. Title: ...
```

Use:

```text
1. [VIDEO_ID=abc123]
   Title: ...
```

Each video in the prompt must include:

* YouTube video ID
* Title (optional but useful)
* Description (already present)

---

### Layer 2 — ID-Based Output Contract

#### Enforced model output format

```text
abc123 | RELEVANT | brief reason
def456 | NOT_RELEVANT | brief reason
```

Rules:

* Order does not matter
* Every input ID must appear exactly once
* No extra IDs allowed

---

### Layer 3 — Strict JSON Output (Recommended)

Preferred format:

```json
{
  "decisions": [
    {
      "video_id": "abc123",
      "relevant": true,
      "confidence": 0.82,
      "reason": "Directly discusses proxy evasion and transcript scraping"
    }
  ]
}
```

Benefits:

* Deterministic parsing
* Schema validation
* Future extensibility

---

### Layer 4 — Parser Validation Rules (Non-Negotiable)

After parsing:

1. Assert:

   * All input video IDs are present
   * No unknown IDs exist
2. Assert:

   * Each ID appears exactly once
3. Assert:

   * `confidence` ∈ `[0, 1]` (if present)
4. If validation fails:

   * Mark batch as failed
   * Optionally retry once
   * Log artifact (see Layer 5)

---

### Layer 5 — Batch Artifact Logging (Debug / QA Mode)

For each batch, optionally persist:

```json
{
  "batch_id": "search_xyz_batch_2",
  "video_ids": ["abc123", "def456"],
  "prompt": "...",
  "raw_model_output": "...",
  "parsed_result": {...},
  "validation_errors": []
}
```

This enables:

* Debugging
* Sampling-based QA
* Regression testing
* Prompt iteration

This can be behind a feature flag.

---

### Layer 6 — Quality Heuristics (Soft Warnings)

Do NOT block execution. Just flag.

Examples:

* 0% relevant → suspicious
* > 90% relevant → suspicious
* All confidence scores identical → suspicious
* Extremely short reasons → suspicious

Surface as logs or UI info.

---

## 6. Minimal Rollout Plan (Low Risk)

### Phase 1 (Immediate, Safe)

1. Add video IDs to prompt
2. Switch to ID-based text output (not JSON yet)
3. Validate ID coverage
4. Fail batch on mismatch

### Phase 2 (Next)

1. Introduce JSON output
2. Add schema validation
3. Add debug artifact logging (optional)

### Phase 3 (Optional Enhancements)

* Confidence-weighted sorting
* Multi-pass filtering (coarse → fine)
* Progressive disclosure of borderline cases

---

## 7. What NOT to Do

* Do NOT add parallel batching yet
* Do NOT add caching yet
* Do NOT add ranking before verification
* Do NOT rely on regex-only parsing without validation

Correctness > speed at this stage.

---

## 8. Definition of “Done”

This filtering system can be considered robust when:

* Every relevance decision is ID-anchored
* Every batch is verifiable
* Silent misclassification is structurally impossible
* Engineers can inspect *why* a video was included
* Users can trust re-filtering results

---

## 9. Final Recommendation

Implement parsing hardening **before** adding new AI features.

The current system is a strong foundation — but without verification, it is not trustworthy enough to scale.

This document is intentionally explicit so it can be handed directly to an IDE agent or engineer without interpretation.

---
