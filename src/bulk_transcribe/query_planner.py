"""Query planning helper using OpenRouter for YouTube searches."""

from dataclasses import dataclass
import json
import re
from typing import Dict, List, Optional

import requests


@dataclass
class QueryPlanResult:
    """Result of query planning."""
    queries: List[str]
    success: bool
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


def plan_search_queries(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    max_queries: int = 5,
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
        "You are an assistant that creates distinct YouTube search queries based on a user's research intent. "
        "Return ONLY a JSON array of strings with concise, diverse search queries."
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
        + f"\n\nReturn up to {max_queries} distinct search queries."
    )

    try:
        response_text = _call_openrouter_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            api_key=api_key,
        )
    except Exception as exc:
        return QueryPlanResult([], False, str(exc))

    queries = _parse_queries(response_text)
    if not queries:
        return QueryPlanResult([], False, "No queries were returned", raw_response=response_text)

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
        return QueryPlanResult([], False, "No valid queries after cleaning", raw_response=response_text)

    return QueryPlanResult(cleaned, True, raw_response=response_text)


def _parse_queries(response_text: str) -> List[str]:
    """Parse a JSON array of query strings from the LLM response."""
    try:
        parsed = json.loads(response_text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return []
    return []


def _call_openrouter_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    api_key: str,
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
        "temperature": 0.2,
        "max_tokens": 300,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    result = response.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

    if not content:
        raise Exception("Empty response from OpenRouter API")

    return content.strip()
