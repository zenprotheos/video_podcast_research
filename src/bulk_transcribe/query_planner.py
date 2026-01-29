"""Query planning helper using OpenRouter for YouTube searches."""

import json
import re
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import requests


@dataclass
class QueryPlanResult:
    """Result of query planning."""
    queries: List[str]
    success: bool
    error_message: Optional[str] = None
    raw_response: Optional[str] = None
    timing_info: Optional[Dict[str, float]] = None  # call durations, validation time, etc.
    retry_count: int = 0  # how many repair calls were made


def plan_search_queries(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    max_queries: int = 5,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> QueryPlanResult:
    """
    Generate distinct YouTube search queries based on a chat conversation.

    Args:
        messages: Chat messages with roles (user/assistant).
        model: OpenRouter model identifier.
        api_key: OpenRouter API key.
        max_queries: Maximum number of queries to return.

    Returns:
        QueryPlanResult with query list and status.
    """
    if not messages:
        return QueryPlanResult([], False, "No chat messages provided")

    if not api_key:
        return QueryPlanResult([], False, "OpenRouter API key not provided")

    if not model or "/" not in model:
        return QueryPlanResult([], False, f"Invalid model format: '{model}'")

    system_prompt = (
        "You create distinct YouTube search queries from the user's research intent.\n\n"
        "CRITICAL OUTPUT RULES:\n"
        "1. Your response MUST be ONLY a valid JSON array of strings.\n"
        "2. No markdown code fences (no ```json or ```).\n"
        "3. No prose, no explanations, no bullet points.\n"
        "4. Each string must be a standalone YouTube search query (5-15 words).\n"
        "5. Start with '[' and end with ']'.\n\n"
        "EXPECTED OUTPUT STRUCTURE:\n"
        '["b2b saas demand gen 2026","product-led growth b2b saas case study","saas positioning framework 2025"]\n\n'
        "ONLY output the JSON structure and nothing else!"
    )

    conversation_lines = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant"
        conversation_lines.append(f"{label}: {content}")

    user_prompt = (
        "Conversation context:\n"
        + "\n".join(conversation_lines)
        + f"\n\nReturn up to {max_queries} distinct YouTube search queries.\n"
        + "ONLY output the JSON array and nothing else!"
    )

    timing_info: Dict[str, float] = {}
    retry_count = 0

    def _call_once(prompt: str, call_label: str) -> str:
        if progress_callback:
            progress_callback(f"Calling OpenRouter API ({call_label})...")
        start = time.time()
        try:
            result = _call_openrouter_api(
                system_prompt=system_prompt,
                user_prompt=prompt,
                model=model,
                api_key=api_key,
                max_queries=max_queries,
            )
            elapsed = time.time() - start
            timing_info[f"{call_label}_duration"] = elapsed
            if progress_callback:
                progress_callback(f"{call_label} completed in {elapsed:.1f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            timing_info[f"{call_label}_duration"] = elapsed
            raise

    try:
        response_text = _call_once(user_prompt, "Call 1")
    except Exception as exc:
        return QueryPlanResult([], False, str(exc), timing_info=timing_info, retry_count=0)

    if progress_callback:
        progress_callback("Validating response format...")
    validation_start = time.time()
    queries, validation_error = _parse_queries_strict(response_text)
    validation_time = time.time() - validation_start
    timing_info["validation_duration"] = validation_time

    if validation_error:
        if progress_callback:
            progress_callback(f"Validation failed: {validation_error}. Retrying once...")
        # Feedback + retry (1x only). Fix root cause, don't mask with retries.
        last_text = response_text
        retry_count = 1
        repair_prompt = (
            user_prompt
            + "\n\nERROR: Your previous response was invalid.\n"
            + f"Validation error: {validation_error}\n\n"
            + "CRITICAL: Fix it now by returning ONLY a JSON array of strings.\n"
            + "EXPECTED OUTPUT STRUCTURE:\n"
            + '["b2b saas demand gen 2026","product-led growth b2b saas case study","saas positioning framework 2025"]\n\n'
            + "RULES:\n"
            + "- The first character must be '[' and the last character must be ']'.\n"
            + "- No markdown code fences (no ```json or ```).\n"
            + "- No prose, no explanations, no bullet points.\n"
            + "- If you cannot comply, return [] (empty JSON array).\n\n"
            + "ONLY output the JSON structure and nothing else!"
        )
        try:
            repaired_text = _call_once(repair_prompt, "Repair call")
        except Exception as exc:
            return QueryPlanResult([], False, str(exc), raw_response=last_text, timing_info=timing_info, retry_count=retry_count)

        if progress_callback:
            progress_callback("Validating repair response...")
        validation_start = time.time()
        last_text = repaired_text
        queries, validation_error = _parse_queries_strict(repaired_text)
        validation_time = time.time() - validation_start
        timing_info["repair_validation_duration"] = validation_time

        if not validation_error:
            response_text = repaired_text
            if progress_callback:
                progress_callback("Repair succeeded!")
        else:
            if progress_callback:
                progress_callback(f"Repair also failed: {validation_error}. Attempting heuristic extraction...")
            # Last-resort safety net: extract plausible queries heuristically so the UI
            # can still function, but keep the raw response for debugging.
            extracted = _extract_queries_heuristic(last_text)
            if extracted:
                response_text = last_text
                queries = extracted
                if progress_callback:
                    progress_callback(f"Heuristic extraction found {len(extracted)} queries")
            else:
                return QueryPlanResult(
                    [],
                    False,
                    f"Model did not return valid JSON after 1 retry: {validation_error}",
                    raw_response=last_text,
                    timing_info=timing_info,
                    retry_count=retry_count,
                )

    cleaned = []
    seen = set()
    for query in queries:
        normalized = query.strip()
        if not normalized:
            continue
        if normalized.lower() in seen:
            continue
        cleaned.append(normalized)
        seen.add(normalized.lower())
        if len(cleaned) >= max_queries:
            break

    if not cleaned:
        return QueryPlanResult([], False, "No valid queries after cleaning", raw_response=response_text, timing_info=timing_info, retry_count=retry_count)

    if progress_callback:
        progress_callback(f"Success! Generated {len(cleaned)} queries.")
    return QueryPlanResult(cleaned, True, raw_response=response_text, timing_info=timing_info, retry_count=retry_count)


def _parse_queries_strict(response_text: str) -> tuple[List[str], Optional[str]]:
    """
    Strictly parse a JSON array of strings.

    Returns (queries, error). error is None on success.
    """
    if not response_text or not response_text.strip():
        return [], "Empty response text"

    text = response_text.strip()

    def _try_load(s: str) -> tuple[Optional[object], Optional[str]]:
        try:
            return json.loads(s), None
        except json.JSONDecodeError:
            return None, "Response was not valid JSON"

    parsed, err = _try_load(text)
    if err:
        # Accept a very common wrapper: markdown code fences around JSON.
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            parsed, err = _try_load(fence_match.group(1).strip())

    if err:
        # Accept a second common wrapper: extra prose with a single JSON array inside.
        # We still validate the final parsed structure strictly.
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1].strip()
            parsed, err = _try_load(candidate)

    if err:
        return [], err

    if not isinstance(parsed, list):
        return [], f"Expected a JSON array, got {type(parsed).__name__}"

    queries: List[str] = []
    for i, item in enumerate(parsed):
        if not isinstance(item, str):
            return [], f"All items must be strings; item[{i}] was {type(item).__name__}"
        s = item.strip()
        if not s:
            continue
        queries.append(s)

    if not queries:
        return [], "JSON array contained no non-empty strings"

    # Simple sanity checks to catch prose accidentally wrapped as strings
    too_long = [q for q in queries if len(q) > 160]
    if too_long:
        return [], "One or more query strings were too long (likely prose)"

    return queries, None


def _extract_queries_heuristic(response_text: str) -> List[str]:
    """
    Best-effort extraction for non-JSON responses.
    Used only after strict validation + repair attempts fail.
    """
    if not response_text:
        return []

    text = response_text.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    extracted: List[str] = []

    bullet_re = re.compile(r"^(\d+[\).\]]|\-|\*|•)\s+")
    for ln in lines:
        if not bullet_re.match(ln):
            continue
        candidate = bullet_re.sub("", ln).strip()
        candidate = candidate.strip("“”\"'`")
        for sep in (" — ", " - ", " – "):
            if sep in candidate:
                candidate = candidate.split(sep, 1)[0].strip()
        if candidate:
            extracted.append(candidate)

    if extracted:
        return extracted

    # Quoted substrings (straight or curly quotes)
    quoted = re.findall(r"[\"“”']([^\"“”']{6,160})[\"“”']", text)
    return [q.strip() for q in quoted if q.strip()]


def _call_openrouter_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    api_key: str,
    max_queries: int = 5,
    timeout: int = 30,
) -> str:
    """Call OpenRouter API for chat completion."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/bulk-transcribe",
        "X-Title": "Bulk Transcribe - Query Planner",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        # Scale tokens with number of queries: ~150 tokens per query + overhead.
        # This prevents over-allocation (slower generation) while ensuring completeness.
        "max_tokens": min(150 * max_queries + 300, 2000),
    }

    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    result = response.json()
    first_choice = (result.get("choices") or [{}])[0] if isinstance(result, dict) else {}
    message = first_choice.get("message") or {}
    content = (message.get("content") or "").strip()

    # Some providers/models return content via a separate "reasoning" field while leaving
    # "content" empty. If so, fall back to reasoning text.
    if not content:
        reasoning = message.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            content = reasoning.strip()

    if not content:
        keys = list(result.keys()) if isinstance(result, dict) else "not dict"
        finish_reason = first_choice.get("finish_reason")
        msg_keys = list(message.keys()) if isinstance(message, dict) else "not dict"
        raise Exception(
            "Empty response from OpenRouter API "
            f"(response_keys={keys}, message_keys={msg_keys}, finish_reason={finish_reason})"
        )

    return content
