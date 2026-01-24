"""Async processing module for DEAPI calls - maintains UI compatibility."""

# Standard library imports
import asyncio
import os
import time
from dataclasses import dataclass
from typing import Optional

# Third-party imports
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    # Fallback to requests if httpx not available
    import requests

# Local imports
from src.bulk_transcribe.youtube_transcript import TranscriptResult


@dataclass
class AsyncConfig:
    """Configuration for async processing."""
    timeout: float = 30.0
    max_retries: int = 3
    poll_interval: float = 5.0
    max_poll_attempts: int = 60  # 5 minutes max


class AsyncVideoProcessor:
    """
    Async processor for video transcription that maintains UI compatibility.
    
    Uses async for API calls but keeps UI updates synchronous to avoid
    Streamlit threading issues.
    """
    
    def __init__(self, deapi_api_key: str, config: Optional[AsyncConfig] = None):
        """
        Initialize async processor.
        
        Args:
            deapi_api_key: DEAPI API key for authentication
            config: Optional configuration (uses defaults if None)
        """
        self.deapi_api_key = deapi_api_key
        self.config = config or AsyncConfig()
        self.base_url = os.getenv("DEAPI_BASE_URL", "https://api.deapi.ai")
        
        # Create async client if httpx available
        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Authorization": f"Bearer {deapi_api_key}",
                    "Content-Type": "application/json",
                }
            )
        else:
            self.client = None
    
    async def process_video_async(self, youtube_url: str) -> TranscriptResult:
        """
        Process a single video with async API calls.
        
        This method uses async for API calls but returns a synchronous
        TranscriptResult that can be used in the main UI thread.
        
        Args:
            youtube_url: YouTube video URL to transcribe
            
        Returns:
            TranscriptResult with success status and transcript or error
        """
        if not HTTPX_AVAILABLE:
            # Fallback to synchronous processing if httpx not available
            from src.bulk_transcribe.youtube_transcript import try_deapi_transcription
            return try_deapi_transcription(youtube_url, self.deapi_api_key)
        
        try:
            # Submit transcription request
            request_id = await self._submit_transcription_request(youtube_url)
            if not request_id:
                return TranscriptResult(
                    success=False,
                    method="deapi_vid2txt",
                    error_message="Failed to submit transcription request",
                )
            
            # Poll for completion
            return await self._poll_for_completion(request_id)
            
        except Exception as e:
            return TranscriptResult(
                success=False,
                method="deapi_vid2txt",
                error_message=f"Async processing error: {str(e)}",
                raw_response_text=str(e),
            )
    
    async def _submit_transcription_request(self, youtube_url: str) -> Optional[str]:
        """Submit transcription request and return request_id."""
        endpoint = f"{self.base_url}/api/v1/client/vid2txt"
        
        payload = {
            "video_url": youtube_url,
            "include_ts": False,
            "model": "WhisperLargeV3",
        }
        
        # Rate limiting delay
        await asyncio.sleep(1)
        
        last_error = None
        for attempt in range(self.config.max_retries):
            if attempt > 0:
                # Exponential backoff
                delay = 10 * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
            
            try:
                response = await self.client.post(endpoint, json=payload)
                
                if response.status_code == 422:
                    error_detail = response.text[:200]
                    try:
                        error_data = response.json()
                        error_detail = str(error_data)
                    except:
                        pass
                    # Return None to indicate failure
                    return None
                
                response.raise_for_status()
                result = response.json()
                
                # Extract request_id
                request_id = result.get("data", {}).get("request_id") or result.get("request_id")
                return request_id
                
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                if e.response.status_code not in [429, 502, 503, 504]:
                    # Not retryable
                    break
            except httpx.RequestError as e:
                last_error = str(e)
                if attempt == self.config.max_retries - 1:
                    break
        
        return None
    
    async def _poll_for_completion(self, request_id: str) -> TranscriptResult:
        """Poll for transcription completion."""
        status_endpoint = f"{self.base_url}/api/v1/client/request-status/{request_id}"
        
        for attempt in range(self.config.max_poll_attempts):
            await asyncio.sleep(self.config.poll_interval)
            
            try:
                response = await self.client.get(status_endpoint)
                
                if response.status_code == 404:
                    return TranscriptResult(
                        success=False,
                        method="deapi_vid2txt",
                        error_message=f"DEAPI status endpoint returned 404. Request ID: {request_id}",
                        deapi_request_id=request_id,
                        http_status_code=404,
                    )
                
                if response.status_code != 200:
                    if attempt < self.config.max_poll_attempts - 1:
                        continue  # Retry
                    return TranscriptResult(
                        success=False,
                        method="deapi_vid2txt",
                        error_message=f"DEAPI status check failed: {response.status_code}",
                        deapi_request_id=request_id,
                        http_status_code=response.status_code,
                    )
                
                status_data = response.json()
                data = status_data.get("data", {})
                status = str(data.get("status", "")).lower()
                
                if status == "done":
                    # Extract transcript
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
                    
                    # Try result_url if available
                    result_url = data.get("result_url")
                    if result_url:
                        try:
                            result_resp = await self.client.get(result_url)
                            if result_resp.status_code == 200:
                                try:
                                    result_data = result_resp.json()
                                    transcript_text = (
                                        result_data.get("result") or 
                                        result_data.get("transcript") or 
                                        result_data.get("text") or 
                                        result_resp.text
                                    )
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
                        error_message="DEAPI completed but no transcript found",
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
                    )
                
                # Status is "pending" or "processing" - continue polling
                
            except httpx.RequestError as e:
                if attempt < self.config.max_poll_attempts - 1:
                    continue  # Retry on network errors
                return TranscriptResult(
                    success=False,
                    method="deapi_vid2txt",
                    error_message=f"DEAPI status check network error: {str(e)}",
                    deapi_request_id=request_id,
                )
        
        return TranscriptResult(
            success=False,
            method="deapi_vid2txt",
            error_message="DEAPI request timed out (exceeded 5 minutes)",
            deapi_request_id=request_id,
        )
    
    async def close(self):
        """Close async client."""
        if self.client:
            await self.client.aclose()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def run_async_in_sync(coro):
    """
    Run async coroutine in synchronous context.
    
    This is a helper function to bridge async code with Streamlit's
    synchronous execution model.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Result of coroutine execution
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            # Create a new event loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(coro)
