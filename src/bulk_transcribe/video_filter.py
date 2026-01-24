"""AI-powered video relevance filtering using OpenRouter API."""

import os
import re
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

import requests

from .youtube_search import VideoSearchItem


@dataclass
class FilteringResult:
    """Result of AI-based video filtering."""
    relevant_videos: List[VideoSearchItem]
    filtered_out_videos: List[VideoSearchItem]
    total_processed: int
    success: bool
    error_message: Optional[str] = None


def filter_videos_by_relevance(
    videos: List[VideoSearchItem],
    search_query: str,
    research_context: str,
    model: str,
    api_key: str,
    batch_size: int = 10
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
                error_msg += ". Try: 'openai/gpt-4o-mini', 'anthropic/claude-haiku-4.5', or 'meta-llama/llama-3.2-3b-instruct'"
            return FilteringResult([], [], 0, False, f"API connection test failed: {error_msg}")
    except Exception as e:
        return FilteringResult([], [], 0, False, f"API connection test failed: {str(e)}")

    all_relevant = []
    all_filtered_out = []

    # Process videos in batches to avoid token limits
    for i in range(0, len(videos), batch_size):
        batch = videos[i:i + batch_size]

        try:
            batch_result = _filter_video_batch(
                batch=batch,
                search_query=search_query,
                research_context=research_context,
                model=model,
                api_key=api_key
            )

            all_relevant.extend(batch_result[0])
            all_filtered_out.extend(batch_result[1])

        except Exception as e:
            # On error, include all remaining videos in filtered_out
            remaining_videos = videos[i:]
            all_filtered_out.extend(remaining_videos)

            return FilteringResult(
                relevant_videos=all_relevant,
                filtered_out_videos=all_filtered_out,
                total_processed=len(videos),
                success=False,
                error_message=f"Error processing batch {i//batch_size + 1}: {str(e)}"
            )

    return FilteringResult(
        relevant_videos=all_relevant,
        filtered_out_videos=all_filtered_out,
        total_processed=len(videos),
        success=True
    )


def _filter_video_batch(
    batch: List[VideoSearchItem],
    search_query: str,
    research_context: str,
    model: str,
    api_key: str
) -> Tuple[List[VideoSearchItem], List[VideoSearchItem]]:
    """
    Filter a single batch of videos using OpenRouter API.

    Returns:
        Tuple of (relevant_videos, filtered_out_videos)
    """
    # Build the prompt
    system_prompt = "You are a video relevance filter. Evaluate YouTube videos based on their metadata to determine if they match the user's research goal."

    user_prompt = _build_user_prompt(batch, search_query, research_context)

    # Make API call
    response_text = _call_openrouter_api(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        api_key=api_key
    )

    # Parse response
    relevance_decisions = _parse_relevance_response(response_text, len(batch))

    # Separate videos based on decisions
    relevant_videos = []
    filtered_out_videos = []

    for i, video in enumerate(batch):
        if i < len(relevance_decisions):
            is_relevant, _ = relevance_decisions[i]
            if is_relevant:
                relevant_videos.append(video)
            else:
                filtered_out_videos.append(video)
        else:
            # If we don't have enough decisions, assume not relevant
            filtered_out_videos.append(video)

    return relevant_videos, filtered_out_videos


def _build_user_prompt(
    videos: List[VideoSearchItem],
    search_query: str,
    research_context: str
) -> str:
    """Build the user prompt for the LLM."""
    prompt_parts = [
        f"Search Query: {search_query}",
        f"Research Context: {research_context}",
        "",
        "Evaluate the following videos. For each video, respond with ONLY 'RELEVANT' or 'NOT_RELEVANT' followed by a brief reason.",
        "",
    ]

    for i, video in enumerate(videos, 1):
        prompt_parts.append(f"Video {i}:")
        prompt_parts.append(f"Title: {video.title}")
        prompt_parts.append(f"Channel: {video.channel_title}")

        # Truncate description to avoid token limits
        description = video.description[:500] if video.description else ""
        if len(description) == 500:
            description += "..."
        prompt_parts.append(f"Description: {description}")

        # Format published date nicely
        published = video.published_at[:10] if video.published_at else "Unknown"
        prompt_parts.append(f"Published: {published}")
        prompt_parts.append("")

    prompt_parts.append("Respond in this exact format:")
    for i in range(len(videos)):
        prompt_parts.append(f"{i+1}. RELEVANT/NOT_RELEVANT - reason")

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
    timeout: int = 30
) -> str:
    """
    Call OpenRouter API for chat completion.

    Args:
        system_prompt: System message for the LLM
        user_prompt: User message with video evaluation task
        model: Model identifier (e.g., 'openai/gpt-4o-mini')
        api_key: OpenRouter API key
        timeout: Request timeout in seconds

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
        "max_tokens": 1000,  # Should be enough for video evaluations
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


def _parse_relevance_response(
    response_text: str,
    expected_count: int
) -> List[Tuple[bool, str]]:
    """
    Parse the LLM response to extract relevance decisions.

    Args:
        response_text: Raw response from LLM
        expected_count: Number of videos we expected decisions for

    Returns:
        List of (is_relevant: bool, reason: str) tuples
    """
    decisions = []

    # Split response into lines and look for numbered decisions
    lines = response_text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for patterns like "1. RELEVANT - reason" or "2. NOT_RELEVANT - reason"
        match = re.match(r'^\d+\.\s*(RELEVANT|NOT_RELEVANT)\s*-\s*(.*)$', line, re.IGNORECASE)
        if match:
            decision_text = match.group(1).upper()
            reason = match.group(2).strip()

            is_relevant = decision_text == "RELEVANT"
            decisions.append((is_relevant, reason))

    # If we didn't get enough decisions, pad with False (not relevant)
    while len(decisions) < expected_count:
        decisions.append((False, "Unable to determine relevance"))

    return decisions[:expected_count]  # Don't return more than expected


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