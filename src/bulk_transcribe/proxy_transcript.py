"""
Proxy-based YouTube transcript extraction wrapper.

Provides a compatible interface with the existing TranscriptResult dataclass
for use with the paid residential proxy extractor.
"""

import logging
import os
from typing import Optional

from src.bulk_transcribe.youtube_transcript import TranscriptResult

logger = logging.getLogger(__name__)

# Lazy-loaded extractor instance (singleton pattern for session reuse)
_extractor_instance = None


def _get_extractor():
    """Get or create the extractor instance."""
    global _extractor_instance

    if _extractor_instance is None:
        from src.bulk_transcribe.paid_proxy_extractor import PaidProxyYouTubeExtractor

        proxy_file = os.getenv("WEBSHARE_PROXY_FILE")
        if not proxy_file:
            raise ValueError(
                "WEBSHARE_PROXY_FILE environment variable not set. "
                "Please set it to the path of your WebShare proxy credentials file."
            )

        if not os.path.exists(proxy_file):
            raise FileNotFoundError(
                f"Proxy file not found: {proxy_file}. "
                "Please check the WEBSHARE_PROXY_FILE path."
            )

        _extractor_instance = PaidProxyYouTubeExtractor(proxy_file)
        logger.info(f"Initialized proxy extractor with file: {proxy_file}")

    return _extractor_instance


def get_proxy_transcript(youtube_url: str) -> TranscriptResult:
    """
    Extract transcript using paid residential proxies.

    This function wraps the PaidProxyYouTubeExtractor to provide a
    TranscriptResult-compatible interface matching the existing
    youtube_transcript.py module.

    Args:
        youtube_url: YouTube video URL to extract transcript from

    Returns:
        TranscriptResult with success status and transcript text or error message
    """
    try:
        extractor = _get_extractor()
    except (ValueError, FileNotFoundError) as e:
        return TranscriptResult(
            success=False,
            method="proxy_residential",
            error_message=str(e),
        )

    try:
        # Debug output for Streamlit console
        print(f"[PROXY_DEBUG] Extracting transcript for: {youtube_url}")
        print(f"[PROXY_DEBUG] Working directory: {os.getcwd()}")
        print(f"[PROXY_DEBUG] Extractor proxy count: {len(extractor.proxy_credentials)}")
        print(f"[PROXY_DEBUG] Proxy file path: {extractor.proxy_file_path}")
        
        logger.info(f"Extracting transcript for: {youtube_url}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Extractor proxy count: {len(extractor.proxy_credentials)}")
        
        result = extractor.extract_transcript(youtube_url)
        
        print(f"[PROXY_DEBUG] Extractor result type: {type(result)}")

        logger.info(f"Extractor returned: {type(result)}")
        if result:
            logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            logger.info(f"Result text length: {len(result.get('text', '')) if isinstance(result, dict) else 'N/A'}")
            logger.info(f"Result method: {result.get('method', 'N/A') if isinstance(result, dict) else 'N/A'}")

        if result and result.get("text"):
            return TranscriptResult(
                success=True,
                method="proxy_residential",
                transcript_text=result["text"],
            )
        else:
            # Log more details about why we got no transcript
            if result is None:
                error_detail = "Extractor returned None"
            elif not isinstance(result, dict):
                error_detail = f"Extractor returned non-dict: {type(result)}"
            elif "text" not in result:
                error_detail = f"Result has no 'text' key. Keys: {list(result.keys())}"
            else:
                error_detail = f"Result text is empty/falsy: {repr(result.get('text'))}"
            
            print(f"[PROXY_DEBUG] FAILED: {error_detail}")
            logger.warning(f"Proxy extraction failed: {error_detail}")
            return TranscriptResult(
                success=False,
                method="proxy_residential",
                error_message=f"Proxy extraction returned no transcript: {error_detail}",
            )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Proxy transcript extraction failed: {error_msg}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        return TranscriptResult(
            success=False,
            method="proxy_residential",
            error_message=f"Proxy extraction error: {error_msg}",
        )


def check_proxy_health() -> dict:
    """
    Check if the proxy extractor is properly configured and can be initialized.

    Returns:
        dict with keys:
            - healthy (bool): True if extractor is ready
            - message (str): Status message
            - proxy_count (int): Number of loaded proxies (if healthy)
    """
    try:
        extractor = _get_extractor()
        proxy_count = len(extractor.proxy_credentials)
        return {
            "healthy": True,
            "message": f"Proxy extractor ready with {proxy_count} proxies",
            "proxy_count": proxy_count,
        }
    except ValueError as e:
        return {
            "healthy": False,
            "message": f"Configuration error: {e}",
            "proxy_count": 0,
        }
    except FileNotFoundError as e:
        return {
            "healthy": False,
            "message": f"File not found: {e}",
            "proxy_count": 0,
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Unexpected error: {e}",
            "proxy_count": 0,
        }


def reset_extractor() -> None:
    """
    Reset the extractor instance.

    Useful if proxy credentials have been updated or for testing.
    """
    global _extractor_instance
    _extractor_instance = None
    logger.info("Proxy extractor instance reset")
