"""AI-powered video relevance filtering using OpenRouter API."""

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import requests

from .youtube_search import VideoSearchItem


class FilterValidationError(Exception):
    """Raised when JSON parse/schema or ID validation fails after retry. Stops filtering."""
    pass


@dataclass
class FilteringResult:
    """Result of AI-based video filtering."""
    relevant_videos: List[VideoSearchItem]
    filtered_out_videos: List[VideoSearchItem]
    total_processed: int
    success: bool
    error_message: Optional[str] = None
    batch_summaries: Optional[List[Dict[str, Any]]] = None  # per-batch log for QA / dev console


def filter_videos_by_relevance(
    videos: List[VideoSearchItem],
    search_query: str,
    research_context: str,
    model: str,
    api_key: str,
    batch_size: int = 10,
    log_dir: Optional[str] = None,
    required_terms: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> FilteringResult:
    """
    Filter videos by relevance using OpenRouter API.

    Args:
        videos: List of videos to evaluate
        search_query: Original search query used
        research_context: User's research goal/context
        model: OpenRouter model identifier (e.g., 'openai/gpt-4o-mini')
        api_key: OpenRouter API key
        batch_size: Number of videos to evaluate in each API call
        log_dir: If set, write minimal per-batch log files (batch_id, video_ids, decisions)
                  under this directory, e.g. logs/ai_filter/
        required_terms: Optional. Terms that must appear or be clearly reflected in title/description.
                        When non-empty, the filter excludes videos that do not contain or discuss these.

    Returns:
        FilteringResult with relevant and filtered videos
    """
    if not videos:
        return FilteringResult([], [], 0, True)

    if not api_key:
        return FilteringResult([], [], 0, False, "OpenRouter API key not provided")

    # Validate model format
    if not model or "/" not in model:
        return FilteringResult([], [], 0, False, f"Invalid model format: '{model}'. Expected format: 'provider/model-name' (e.g., 'openai/gpt-4o-mini')")

    # Test API connection with a simple request first
    try:
        test_result = _test_openrouter_connection(model, api_key)
        if not test_result["success"]:
            error_msg = test_result['error']
            # Suggest alternative models if the current one fails
            if "not found" in error_msg.lower():
                error_msg += ". Try: 'openai/gpt-5-nano', 'anthropic/claude-haiku-4.5', or 'meta-llama/llama-3.2-3b-instruct'"
            return FilteringResult([], [], 0, False, f"API connection test failed: {error_msg}")
    except Exception as e:
        return FilteringResult([], [], 0, False, f"API connection test failed: {str(e)}")

    all_relevant = []
    all_filtered_out = []
    batch_summaries: List[Dict[str, Any]] = []

    # Process videos in batches to avoid token limits
    for i in range(0, len(videos), batch_size):
        batch = videos[i:i + batch_size]
        batch_index = i // batch_size

        try:
            batch_result = _filter_video_batch(
                batch=batch,
                search_query=search_query,
                research_context=research_context,
                model=model,
                api_key=api_key,
                batch_index=batch_index,
                log_dir=log_dir,
                required_terms=required_terms,
            )

            all_relevant.extend(batch_result[0])
            all_filtered_out.extend(batch_result[1])
            batch_summaries.append(batch_result[2])
            if progress_callback:
                n_in, n_out = len(batch_result[0]), len(batch_result[1])
                progress_callback(f"batch_{batch_index + 1}: {len(batch)} evaluated, {n_in} in / {n_out} out")

        except FilterValidationError as e:
            # Validation failed after retry; stop task and return dev-facing error
            remaining_videos = videos[i:]
            all_filtered_out.extend(remaining_videos)
            return FilteringResult(
                relevant_videos=all_relevant,
                filtered_out_videos=all_filtered_out,
                total_processed=len(videos),
                success=False,
                error_message=str(e),
                batch_summaries=batch_summaries if batch_summaries else None
            )
        except Exception as e:
            # On other error, include all remaining videos in filtered_out
            remaining_videos = videos[i:]
            all_filtered_out.extend(remaining_videos)
            return FilteringResult(
                relevant_videos=all_relevant,
                filtered_out_videos=all_filtered_out,
                total_processed=len(videos),
                success=False,
                error_message=f"Error processing batch {batch_index + 1}: {str(e)}",
                batch_summaries=batch_summaries if batch_summaries else None
            )

    return FilteringResult(
        relevant_videos=all_relevant,
        filtered_out_videos=all_filtered_out,
        total_processed=len(videos),
        success=True,
        batch_summaries=batch_summaries
    )


def _log_validation_failure(
    batch_id: str,
    expected_ids: Set[str],
    parsed_ids: Set[str],
    response_snippet: str,
    error: ValueError
) -> None:
    """Emit console logs for parse/schema or ID validation failure (dev-facing)."""
    snippet = (response_snippet[:500] + "...") if len(response_snippet) > 500 else response_snippet
    print(f"[AI Filter] validation failure {batch_id}: {type(error).__name__}: {error}")
    print(f"[AI Filter] expected_ids={sorted(expected_ids)}")
    print(f"[AI Filter] parsed_ids={sorted(parsed_ids) if parsed_ids else '(none)'}")
    print(f"[AI Filter] raw_snippet={snippet!r}")


def _write_batch_log(
    log_dir: str,
    batch_id: str,
    video_ids: List[str],
    decisions: Dict[str, Tuple[bool, str]],
    validation_errors: List[str]
) -> None:
    """Write minimal per-batch log when log_dir is set. Human-readable, no prompt/raw/PII."""
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        return
    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    path = os.path.join(log_dir, f"{batch_id}_{ts}.json")
    log_data = {
        "batch_id": batch_id,
        "video_ids": sorted(video_ids),
        "decisions": [
            {"video_id": vid, "relevant": rel, "reason": reason}
            for vid, (rel, reason) in sorted(decisions.items())
        ],
        "validation_errors": validation_errors,
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _filter_video_batch(
    batch: List[VideoSearchItem],
    search_query: str,
    research_context: str,
    model: str,
    api_key: str,
    batch_index: int = 0,
    log_dir: Optional[str] = None,
    required_terms: Optional[str] = None,
) -> Tuple[List[VideoSearchItem], List[VideoSearchItem], Dict[str, Any]]:
    """
    Filter a single batch of videos using OpenRouter API.
    Uses ID-anchored JSON output; on parse/validation failure: console logs, retry 1x, then raises FilterValidationError.

    Returns:
        Tuple of (relevant_videos, filtered_out_videos, batch_summary_dict for dev console / logs)
    """
    expected_video_ids = {v.video_id for v in batch}
    batch_id = f"batch_{batch_index}"
    system_prompt = (
        "You are a video relevance filter. Evaluate YouTube videos based on their metadata "
        "to determine if they match the user's research goal. "
        "Interpret the research goal with reasonable breadth: include videos that clearly "
        "support or overlap the goal even if they use different terminology (e.g., related "
        "tactics, adjacent domains, or different labels for the same idea). "
        "Exclude only when content is clearly off-topic. Respond with only valid JSON."
    )

    user_prompt = _build_user_prompt(batch, search_query, research_context, required_terms)

    def _do_call() -> str:
        return _call_openrouter_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            api_key=api_key,
            max_tokens=10_000
        )

    def _do_parse(response_text: str) -> Dict[str, Tuple[bool, str]]:
        return _parse_and_validate_json_response(response_text, expected_video_ids)

    response_text = _do_call()
    try:
        decisions = _do_parse(response_text)
    except ValueError as e:
        # Validation failure: log, retry once, then stop
        _log_validation_failure(batch_id, expected_video_ids, set(), response_text, e)
        try:
            response_text = _do_call()
            decisions = _do_parse(response_text)
        except ValueError as e2:
            _log_validation_failure(batch_id, expected_video_ids, set(), response_text, e2)
            raise FilterValidationError(
                f"JSON validation failed for {batch_id} after 1 retry: {e2}"
            ) from e2

    # Map by video_id to (relevant_videos, filtered_out_videos)
    relevant_videos = []
    filtered_out_videos = []
    for video in batch:
        is_relevant, reason = decisions.get(video.video_id, (False, ""))
        if is_relevant:
            relevant_videos.append(video)
        else:
            filtered_out_videos.append(video)

    vid_to_item = {v.video_id: v for v in batch}
    decision_list = []
    for vid, (rel, reason) in sorted(decisions.items()):
        item = vid_to_item.get(vid)
        d = {"video_id": vid, "relevant": rel, "reason": reason}
        if item:
            d["title"] = item.title or ""
            raw_desc = item.description or ""
            # Keep full description for QA; UI can choose how to truncate/display later.
            d["description"] = raw_desc
        else:
            d["title"] = ""
            d["description"] = ""
        decision_list.append(d)
    summary = {
        "batch_id": batch_id,
        "video_ids": sorted(expected_video_ids),
        "decisions": decision_list,
        "validation_errors": [],
    }
    if log_dir:
        _write_batch_log(log_dir, batch_id, list(expected_video_ids), decisions, [])

    return relevant_videos, filtered_out_videos, summary


def _build_user_prompt(
    videos: List[VideoSearchItem],
    search_query: str,
    research_context: str,
    required_terms: Optional[str] = None,
) -> str:
    """Build the user prompt for the LLM. Each video is ID-anchored with [VIDEO_ID=...]."""
    prompt_parts = [
        f"Search Query: {search_query}",
        f"Research Context: {research_context}",
    ]
    req_terms = (required_terms or "").strip()
    if req_terms:
        prompt_parts.append(
            f"Required terms (must appear or be clearly reflected in title/description): {req_terms}. "
            "Exclude videos that do not contain or clearly discuss these; apply flexibility only within this constraint."
        )
    prompt_parts.extend([
        "",
        "Evaluate the following videos. Respond with ONLY valid JSON in this exact shape (no other text):",
        '{"decisions": [{"video_id": "<id>", "relevant": <true|false>, "reason": "<string>"}, ...]}',
        "Use the [VIDEO_ID=...] from each block as the value for \"video_id\" in your response. One decision per video.",
        "",
    ])

    for i, video in enumerate(videos, 1):
        prompt_parts.append(f"{i}. [VIDEO_ID={video.video_id}]")
        prompt_parts.append(f"Title: {video.title}")
        prompt_parts.append(f"Channel: {video.channel_title}")

        # Truncate description to avoid token limits
        description = video.description[:500] if video.description else ""
        if len(description) == 500:
            description += "..."
        prompt_parts.append(f"Description: {description}")

        # Add tags if available (helpful for relevance filtering)
        video_tags = getattr(video, "tags", None) or []
        if video_tags:
            tags_str = ", ".join(video_tags[:15])  # Limit to 15 tags
            prompt_parts.append(f"Tags: {tags_str}")

        # Format published date nicely
        published = video.published_at[:10] if video.published_at else "Unknown"
        prompt_parts.append(f"Published: {published}")
        prompt_parts.append("")

    prompt_parts.append("Respond with ONLY this JSON structure, one object per video above:")
    prompt_parts.append('{"decisions": [{"video_id": "<from [VIDEO_ID=...]>", "relevant": true|false, "reason": "<brief reason>"}]}')

    return "\n".join(prompt_parts)


def _test_openrouter_connection(model: str, api_key: str) -> dict:
    """
    Test basic connectivity to OpenRouter API.

    Returns:
        dict with 'success': bool and 'error': str (if failed)
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Simple test payload
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say 'OK' if you can read this."}
        ],
        "max_tokens": 10,
        "temperature": 0,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        result = response.json()

        # Check if we got a valid response
        if "choices" in result and result["choices"] and "message" in result["choices"][0]:
            content = result["choices"][0]["message"].get("content", "").strip()
            if content:
                return {"success": True, "error": None}

        return {"success": False, "error": "API responded but returned empty or invalid content"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "API request timed out"}
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            if status_code == 401:
                return {"success": False, "error": "Invalid API key"}
            elif status_code == 403:
                return {"success": False, "error": "Access forbidden - model may not be available"}
            elif status_code == 404:
                return {"success": False, "error": f"Model '{model}' not found"}
            elif status_code == 429:
                return {"success": False, "error": "Rate limit exceeded"}
            elif status_code == 402:
                return {"success": False, "error": "Quota exceeded - add credits"}
        return {"success": False, "error": f"API request failed: {str(e)}"}


def _call_openrouter_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    api_key: str,
    timeout: int = 30,
    max_tokens: int = 10_000
) -> str:
    """
    Call OpenRouter API for chat completion.

    Args:
        system_prompt: System message for the LLM
        user_prompt: User message with video evaluation task
        model: Model identifier (e.g., 'openai/gpt-4o-mini')
        api_key: OpenRouter API key
        timeout: Request timeout in seconds
        max_tokens: Max tokens for completion (default 10_000 for filter batches)

    Returns:
        LLM response text

    Raises:
        Exception: On API errors or timeouts
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/bulk-transcribe",  # Your app's URL
        "X-Title": "Bulk Transcribe - AI Video Filter",  # Your app's display name
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Low temperature for consistent evaluation
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content:
            # More detailed error with response info
            error_msg = f"Empty response from OpenRouter API. Response keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}"
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                error_msg += f", choice keys: {list(choice.keys()) if isinstance(choice, dict) else 'not dict'}"
                if "message" in choice:
                    error_msg += f", message keys: {list(choice['message'].keys()) if isinstance(choice['message'], dict) else 'not dict'}"
            raise Exception(error_msg)

        return content.strip()

    except requests.exceptions.Timeout:
        raise Exception("OpenRouter API request timed out")
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response:
            status_code = e.response.status_code
            if status_code == 401:
                raise Exception("Invalid OpenRouter API key - check your OPENROUTER_API_KEY")
            elif status_code == 403:
                raise Exception("Access forbidden - model may not be available or requires credits")
            elif status_code == 429:
                raise Exception("OpenRouter API rate limit exceeded - try again later")
            elif status_code == 402:
                raise Exception("OpenRouter API quota exceeded - add credits to your account")
            elif status_code == 404:
                raise Exception(f"Model '{model}' not found - try a different model like 'openai/gpt-4o-mini' or 'anthropic/claude-haiku-4.5'")
            elif status_code == 400:
                # Check if it's a model validation error
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', '')
                    if 'not a valid model' in error_msg.lower() or 'model' in error_msg.lower():
                        raise Exception(f"Invalid model '{model}': {error_msg}. Please check available models at https://openrouter.ai/models")
                    else:
                        raise Exception(f"OpenRouter API request error (400): {error_msg}")
                except:
                    raise Exception(f"OpenRouter API request failed (400): Bad request - check model name and parameters")
            else:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                    raise Exception(f"OpenRouter API error ({status_code}): {error_msg}")
                except:
                    raise Exception(f"OpenRouter API request failed ({status_code}): {str(e)}")
        raise Exception(f"OpenRouter API request failed: {str(e)}")


def _parse_and_validate_json_response(
    response_text: str,
    expected_video_ids: Set[str]
) -> Dict[str, Tuple[bool, str]]:
    """
    Parse and validate JSON response from the model. No text-format fallback.

    Args:
        response_text: Raw response from LLM (must be valid JSON)
        expected_video_ids: Set of video IDs that were in the batch

    Returns:
        Dict mapping video_id -> (is_relevant, reason)

    Raises:
        ValueError: On parse error, schema violation, or ID validation failure
    """
    raw = response_text.strip()
    # Allow markdown code fences; strip them if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse error: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")

    decisions_list = data.get("decisions")
    if not isinstance(decisions_list, list):
        raise ValueError("Missing or invalid 'decisions' array")

    result: Dict[str, Tuple[bool, str]] = {}
    seen_ids: Set[str] = set()

    for i, item in enumerate(decisions_list):
        if not isinstance(item, dict):
            raise ValueError(f"decisions[{i}] is not an object")
        vid = item.get("video_id")
        if not isinstance(vid, str) or not vid.strip():
            raise ValueError(f"decisions[{i}] missing or invalid 'video_id'")
        vid = vid.strip()
        if vid in seen_ids:
            raise ValueError(f"Duplicate video_id in decisions: {vid}")
        seen_ids.add(vid)

        rel = item.get("relevant")
        if not isinstance(rel, bool):
            raise ValueError(f"decisions[{i}] 'relevant' must be boolean")
        reason = item.get("reason")
        if not isinstance(reason, str):
            reason = str(reason) if reason is not None else ""
        result[vid] = (rel, reason)

    parsed_ids = set(result.keys())
    missing = expected_video_ids - parsed_ids
    unknown = parsed_ids - expected_video_ids
    # Treat missing IDs as filtered out (model omitted them)
    for vid in missing:
        result[vid] = (False, "Omitted from model response")
    if unknown:
        raise ValueError(f"ID validation failed: unknown IDs: {sorted(unknown)}")

    return result


def get_available_models(api_key: Optional[str] = None) -> List[str]:
    """
    Get available models from OpenRouter API.

    This is mainly for future extensibility - for now we use hardcoded presets.
    """
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY", "")

    if not api_key:
        return []

    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        # Return model IDs
        return [model.get("id", "") for model in models if model.get("id")]

    except Exception:
        # Fallback to hardcoded models if API fails
        return ["openai/gpt-4o-mini", "anthropic/claude-haiku-4.5"]