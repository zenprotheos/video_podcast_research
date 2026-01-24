"""YouTube transcript extraction - tries captions first, falls back to DEAPI."""

# Standard library imports
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

# Third-party imports
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Local imports
from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata


@dataclass
class TranscriptResult:
    """Result of transcript extraction."""
    success: bool
    method: str  # "youtube_captions" or "deapi_vid2txt" or "failed"
    transcript_text: Optional[str] = None
    error_message: Optional[str] = None
    deapi_request_id: Optional[str] = None
    # Raw DEAPI response data for debugging
    raw_response_data: Optional[dict] = None
    raw_response_text: Optional[str] = None
    http_status_code: Optional[int] = None


def extract_video_id(youtube_url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    import re
    
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    return None


def try_youtube_captions(youtube_url: str) -> Optional[str]:
    """
    Try to get YouTube captions/transcript.
    Returns transcript text if successful, None if not available.
    """
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return None
        
        # Validate video ID length (should be 11 characters)
        if len(video_id) != 11:
            return None
        
        # Try to get transcript (auto-detects language)
        # First try without language list (auto-detect)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except NoTranscriptFound:
            # Try common languages as fallback
            for lang_code in ['en', 'en-US', 'en-GB']:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                    break
                except (NoTranscriptFound, TranscriptsDisabled):
                    continue
            else:
                # No transcript found in any language
                return None
        
        # Combine all text segments
        text_parts = [item["text"] for item in transcript_list]
        return " ".join(text_parts)
    except (TranscriptsDisabled, NoTranscriptFound):
        # No captions available - this is expected for some videos
        return None
    except Exception as e:
        # Log the error but don't fail - we'll try DEAPI fallback
        # Video unavailable, private, deleted, etc.
        error_msg = str(e)
        if "Video unavailable" in error_msg or "Private video" in error_msg:
            # These are expected errors - return None to trigger fallback or fail gracefully
            return None
        # Any other error - return None to trigger fallback
        return None


def try_deapi_transcription(youtube_url: str, api_key: str, max_retries: int = 3) -> TranscriptResult:
    """
    Fallback: Use DEAPI vid2txt endpoint with retry logic.
    Returns TranscriptResult with success status.
    """

    base_url = os.getenv("DEAPI_BASE_URL", "https://api.deapi.ai")
    endpoint = f"{base_url}/api/v1/client/vid2txt"

    # Add delay before DEAPI request to avoid rate limits
    time.sleep(1)

    # Retry logic for transient failures
    last_error = None
    for attempt in range(max_retries):
        if attempt > 0:
            # Exponential backoff: 10s, 20s, 40s
            delay = 10 * (2 ** (attempt - 1))
            print(f"DEAPI retry {attempt}/{max_retries} after {delay}s delay...")
            time.sleep(delay)

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "video_url": youtube_url,
                "include_ts": False,  # We want clean text (no timestamps)
                "model": "WhisperLargeV3",  # Explicit model (optional but recommended)
            }

            return _try_deapi_transcription_once(youtube_url, api_key, base_url, endpoint, headers, payload)
        except Exception as e:
            last_error = str(e)
            error_msg = last_error.lower()

            # Check if this is a retryable error
            retryable = any(keyword in error_msg for keyword in [
                'rate limit', '429', 'timeout', 'network', 'connection',
                'temporary', 'server error', '502', '503', '504'
            ])

            if not retryable or attempt == max_retries - 1:
                # Not retryable or last attempt - return error
                return TranscriptResult(
                    success=False,
                    method="deapi_vid2txt",
                    error_message=f"DEAPI failed after {attempt + 1} attempts: {last_error}",
                )

    # Should not reach here, but just in case
    return TranscriptResult(
        success=False,
        method="deapi_vid2txt",
        error_message=f"DEAPI failed after {max_retries} attempts: {last_error}",
    )




def _try_deapi_transcription_once(youtube_url: str, api_key: str, base_url: str, endpoint: str, headers: dict, payload: dict) -> TranscriptResult:
    """Single attempt at DEAPI transcription."""
    try:

        # Submit transcription request
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        # Handle 422 errors with more detail
        if response.status_code == 422:
            error_detail = response.text
            raw_response_data = None
            try:
                raw_response_data = response.json()
                error_detail = str(raw_response_data)
            except:
                pass
            return TranscriptResult(
                success=False,
                method="deapi_vid2txt",
                error_message=f"DEAPI validation error (422): {error_detail[:200]}",
                raw_response_data=raw_response_data,
                raw_response_text=response.text,
                http_status_code=response.status_code,
            )
        
        response.raise_for_status()
        
        result = response.json()
        # DEAPI returns {"data": {"request_id": "..."}}
        request_id = result.get("data", {}).get("request_id") or result.get("request_id")
        
        if not request_id:
            return TranscriptResult(
                success=False,
                method="deapi_vid2txt",
                error_message=f"DEAPI did not return request_id. Response: {result}",
                raw_response_data=result,
                raw_response_text=response.text,
                http_status_code=response.status_code,
            )
        
        # Poll for completion (simple polling, max 5 minutes)
        # DEAPI status endpoint format: GET /api/v1/client/request-status/{request_id}
        # According to docs: "GET /api/v1/client/request-status/{job_request}"
        status_endpoint = f"{base_url}/api/v1/client/request-status/{request_id}"
        max_attempts = 60  # 5 minutes max (5 sec intervals)
        
        for attempt in range(max_attempts):
            time.sleep(5)  # Wait 5 seconds between polls (docs recommend 5-15 sec for video transcription)
            
            try:
                status_response = requests.get(
                    status_endpoint,
                    headers=headers,
                    timeout=30,
                )
                
                if status_response.status_code == 404:
                    # 404 might mean request_id format is wrong or endpoint is different
                    # Try alternative: maybe the result is in the initial response?
                    return TranscriptResult(
                        success=False,
                        method="deapi_vid2txt",
                        error_message=f"DEAPI status endpoint returned 404. Request ID: {request_id}. Check DEAPI docs for correct status endpoint.",
                        deapi_request_id=request_id,
                        raw_response_text=status_response.text,
                        http_status_code=status_response.status_code,
                    )
                
                if status_response.status_code != 200:
                    if attempt < max_attempts - 1:
                        continue  # Retry
                    return TranscriptResult(
                        success=False,
                        method="deapi_vid2txt",
                        error_message=f"DEAPI status check failed: {status_response.status_code} - {status_response.text[:200]}",
                        deapi_request_id=request_id,
                        raw_response_text=status_response.text,
                        http_status_code=status_response.status_code,
                    )
                
                status_data = status_response.json()
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1:
                    continue  # Retry on network errors
                return TranscriptResult(
                    success=False,
                    method="deapi_vid2txt",
                    error_message=f"DEAPI status check network error: {str(e)}",
                    deapi_request_id=request_id,
                    raw_response_text=str(e),
                )
            
            # DEAPI response format: {"data": {"status": "done", "result": "...", ...}}
            data = status_data.get("data", {})
            status = str(data.get("status", "")).lower()
            
            if status == "done":
                # Get transcript from result field (per DEAPI docs)
                transcript_text = (
                    data.get("result") or 
                    data.get("transcript") or 
                    data.get("text") or
                    ""
                )
                if transcript_text:
                    return TranscriptResult(
                        success=True,
                        method="deapi_vid2txt",
                        transcript_text=transcript_text,
                        deapi_request_id=request_id,
                    )
                else:
                    # Done but no transcript - check result_url
                    result_url = data.get("result_url")
                    if result_url:
                        # Try to fetch from result_url
                        try:
                            result_resp = requests.get(result_url, timeout=30)
                            if result_resp.status_code == 200:
                                # Try to parse as JSON or text
                                try:
                                    result_data = result_resp.json()
                                    transcript_text = result_data.get("result") or result_data.get("transcript") or result_data.get("text") or ""
                                except:
                                    transcript_text = result_resp.text
                                
                                if transcript_text:
                                    return TranscriptResult(
                                        success=True,
                                        method="deapi_vid2txt",
                                        transcript_text=transcript_text,
                                        deapi_request_id=request_id,
                                    )
                        except:
                            pass
                    
                    return TranscriptResult(
                        success=False,
                        method="deapi_vid2txt",
                        error_message=f"DEAPI completed but no transcript found. Response: {str(status_data)[:300]}",
                        deapi_request_id=request_id,
                    )
            elif status == "error":
                error_msg = data.get("error") or "Unknown error"
                return TranscriptResult(
                    success=False,
                    method="deapi_vid2txt",
                    error_message=f"DEAPI failed: {error_msg}",
                    deapi_request_id=request_id,
                    raw_response_data=data,
                    raw_response_text=str(status_data),
                    http_status_code=200,  # Status check succeeded, but job failed
                )
            # Status is "pending" or "processing" - continue polling
            # Otherwise, still processing - continue polling
        
        return TranscriptResult(
            success=False,
            method="deapi_vid2txt",
            error_message="DEAPI request timed out (exceeded 5 minutes)",
            deapi_request_id=request_id,
            raw_response_text="Request timed out after 5 minutes of polling",
        )
        
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        # Try to get more detail from response if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)} - Response: {e.response.text[:200]}"
            except:
                pass
        return TranscriptResult(
            success=False,
            method="deapi_vid2txt",
            error_message=f"DEAPI request failed: {error_detail}",
            raw_response_text=error_detail,
            http_status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') and e.response else None,
        )
    except Exception as e:
        return TranscriptResult(
            success=False,
            method="deapi_vid2txt",
            error_message=f"Unexpected error: {str(e)}",
            raw_response_text=str(e),
        )


def get_youtube_transcript(youtube_url: str, deapi_api_key: Optional[str] = None) -> TranscriptResult:
    """
    Main function: Try YouTube captions first, fall back to DEAPI if needed.
    """
    # Try YouTube captions first (fast, free)
    transcript_text = try_youtube_captions(youtube_url)
    
    if transcript_text:
        return TranscriptResult(
            success=True,
            method="youtube_captions",
            transcript_text=transcript_text,
        )
    
    # Fallback to DEAPI if API key is available
    if deapi_api_key:
        return try_deapi_transcription(youtube_url, deapi_api_key)
    
    # No captions and no DEAPI key
    return TranscriptResult(
        success=False,
        method="failed",
        error_message="No YouTube captions available and DEAPI_API_KEY not set",
    )
