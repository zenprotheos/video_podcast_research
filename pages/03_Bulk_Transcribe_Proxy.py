"""
Bulk Transcribe (Proxy) - Uses paid residential proxies for transcript extraction.

This is a variant of the Bulk Transcribe page that uses WebShare residential proxies
instead of the DEAPI service. Provides higher reliability for YouTube transcript extraction.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv


def _build_rich_youtube_metadata(row: dict, yt_dlp_meta: dict) -> dict:
    """
    Build comprehensive YouTube metadata dict from row (session state) and yt-dlp fallback.
    
    Prioritizes rich metadata from YouTube Search (in row) over yt-dlp fetched data.
    
    Args:
        row: Dict from parsed sheet containing session state metadata
        yt_dlp_meta: Dict from yt-dlp fetch_youtube_metadata().raw
    
    Returns:
        Dict with all available YouTube metadata for transcript frontmatter
    """
    metadata = {}
    
    # Channel info - prefer session state (channel_title) over yt-dlp (channel)
    if row.get("channel_title"):
        metadata["channel_title"] = row["channel_title"]
    elif yt_dlp_meta.get("channel"):
        metadata["channel_title"] = yt_dlp_meta["channel"]
    
    # Published date - prefer session state ISO format over yt-dlp format
    if row.get("published_at"):
        metadata["published_at"] = row["published_at"]
    elif yt_dlp_meta.get("upload_date"):
        metadata["upload_date"] = yt_dlp_meta["upload_date"]
    
    # Duration - prefer session state (seconds) over yt-dlp (string)
    if row.get("duration_seconds") is not None:
        metadata["duration_seconds"] = row["duration_seconds"]
    elif yt_dlp_meta.get("duration"):
        metadata["duration"] = yt_dlp_meta["duration"]
    
    # View/engagement stats (only from session state - yt-dlp doesn't fetch these reliably)
    if row.get("view_count") is not None:
        metadata["view_count"] = row["view_count"]
    if row.get("like_count") is not None:
        metadata["like_count"] = row["like_count"]
    if row.get("comment_count") is not None:
        metadata["comment_count"] = row["comment_count"]
    
    # Caption availability
    if row.get("has_captions") is not None:
        metadata["has_captions"] = row["has_captions"]
    
    # Tags (list)
    if row.get("tags"):
        metadata["tags"] = row["tags"]
    
    # Category
    if row.get("category_id"):
        metadata["category_id"] = row["category_id"]
    
    # Thumbnail URL
    if row.get("thumbnail_url"):
        metadata["thumbnail_url"] = row["thumbnail_url"]
    
    return metadata


def process_single_video_parallel(
    youtube_url: str,
    video_id: str,
    title: str,
    row: dict,
    session_youtube_dir: str,
) -> dict:
    """
    Process a single video for parallel execution.
    
    This function runs in a worker thread and should NOT call any Streamlit commands.
    Returns a dict with all results needed for UI updates.
    """
    import time
    from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata, save_metadata_json
    from src.bulk_transcribe.transcript_writer import write_transcript_markdown, generate_filename
    from src.bulk_transcribe.utils import slugify
    from src.bulk_transcribe.proxy_transcript import get_proxy_transcript
    
    start_time = time.time()
    result = {
        "success": False,
        "video_id": video_id,
        "title": title,
        "youtube_url": youtube_url,
        "method": "-",
        "error": None,
        "elapsed": 0.0,
        "transcript_path": None,
        "metadata": {},
        "blocked": False,
    }
    
    try:
        # Step 1: Fetch metadata via yt-dlp (for fallback and JSON export)
        meta = fetch_youtube_metadata(youtube_url)
        result["video_id"] = meta.video_id or video_id
        result["title"] = meta.title or title or row.get("title", "")
        
        # Build rich metadata from session state (row) with yt-dlp fallback
        rich_metadata = _build_rich_youtube_metadata(row, meta.raw)
        result["metadata"] = rich_metadata
        
        if not result["video_id"]:
            result["error"] = "Could not extract video ID from URL"
            result["elapsed"] = time.time() - start_time
            return result
        
        # Save yt-dlp metadata JSON (for debugging/future use)
        meta_path = os.path.join(
            session_youtube_dir, 
            f"{slugify(result['title'])}__{result['video_id']}.metadata.json"
        )
        save_metadata_json(meta_path, meta.raw)
        
        # Step 2: Get transcript using proxy method
        transcript_result = get_proxy_transcript(youtube_url)
        result["elapsed"] = time.time() - start_time
        result["method"] = transcript_result.method
        
        if transcript_result.success:
            # Step 3: Write transcript file with rich metadata
            filename = generate_filename(result["video_id"], result["title"], "youtube")
            transcript_path = os.path.join(session_youtube_dir, filename)
            
            write_transcript_markdown(
                output_path=transcript_path,
                source_type="youtube",
                source_url=youtube_url,
                transcript_text=transcript_result.transcript_text or "",
                title=result["title"],
                description=row.get("description"),
                video_id=result["video_id"],
                method=transcript_result.method,
                youtube_metadata=rich_metadata,
            )
            
            result["success"] = True
            result["transcript_path"] = transcript_path
        else:
            result["error"] = transcript_result.error_message or "Unknown error"
            if result["error"] and "blocked" in result["error"].lower():
                result["blocked"] = True
                
    except Exception as e:
        result["error"] = str(e)
        result["elapsed"] = time.time() - start_time
    
    return result


def categorize_error(error_msg: str, is_code_error: bool = False) -> tuple[str, str]:
    """
    Categorize errors for proxy-based extraction.
    Returns (icon, description) tuple.
    """
    if is_code_error:
        return "X", f"Code bug: {error_msg}"

    error_lower = error_msg.lower()

    # Proxy-specific error patterns
    if "proxy" in error_lower and ("not found" in error_lower or "not set" in error_lower):
        return "[CFG]", "Proxy file not configured - check WEBSHARE_PROXY_FILE"
    elif "blocked" in error_lower or "captcha" in error_lower:
        return "[BLK]", "Request blocked - will retry with different proxy"
    elif "timeout" in error_lower:
        return "[TMO]", "Request timeout - proxy may be slow"
    elif "connection" in error_lower or "network" in error_lower:
        return "[NET]", "Network error - check internet connection"
    elif "video unavailable" in error_lower:
        return "[!]", "Video unavailable - may be private/deleted"
    elif "private" in error_lower:
        return "[PVT]", "Private video - cannot access"
    elif "no transcript" in error_lower or "no caption" in error_lower:
        return "[NC]", "No captions available for this video"

    # Generic failures
    return "[X]", error_msg[:50] if len(error_msg) > 50 else error_msg


def update_status_safe(status_data: list, new_status: dict, status_table):
    """
    Safely update status table with error handling to prevent crashes.
    """
    try:
        status_data.insert(0, new_status)
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
        return True
    except Exception as update_error:
        st.error(f"Status update failed: {update_error}")
        st.error(f"Original status: {new_status.get('Status', 'Unknown')}")
        return False


# Load .env file if it exists
load_dotenv()

from src.bulk_transcribe.sheet_ingest import (
    ColumnMapping,
    ParsedSheet,
    normalize_rows,
    parse_spreadsheet,
    resolve_column_mapping,
    validate_normalized_rows,
)
from src.bulk_transcribe.session_manager import SessionConfig, SessionManager
from src.bulk_transcribe.metadata_transfer import detect_input_type, metadata_to_parsed_sheet, validate_metadata_list
from src.bulk_transcribe.proxy_transcript import get_proxy_transcript, check_proxy_health
from src.bulk_transcribe.parallel_processor import (
    ParallelTranscriptProcessor,
    VideoTask,
    create_video_task,
    ProcessingResult,
)


@dataclass
class AppConfig:
    output_root: str
    proxy_configured: bool


def load_app_config() -> AppConfig:
    output_root = os.path.join(".", "output", "sessions")
    proxy_file = os.getenv("WEBSHARE_PROXY_FILE", "").strip()
    proxy_configured = bool(proxy_file) and os.path.exists(proxy_file)
    return AppConfig(output_root=output_root, proxy_configured=proxy_configured)


st.set_page_config(page_title="Bulk Transcribe (Proxy) - Transcript Tool", layout="wide")
st.title("[PROXY] Bulk Transcribe - Transcript Tool")

cfg = load_app_config()

with st.sidebar:
    st.header("Config")
    st.write(f"Output root: `{cfg.output_root}`")

    # Check proxy health
    if cfg.proxy_configured:
        st.success("Proxy file configured")
        with st.spinner("Checking proxy health..."):
            health = check_proxy_health()

        if health["healthy"]:
            st.info(f"[OK] {health['message']}")
        else:
            st.warning(f"[!] {health['message']}")
    else:
        st.warning("WEBSHARE_PROXY_FILE is not set or file not found")
        st.caption("Set WEBSHARE_PROXY_FILE in your .env file to the path of your WebShare proxy credentials.")

    st.divider()
    st.caption("This page uses WebShare residential proxies for transcript extraction.")
    st.caption("No DEAPI credits are consumed.")

st.header("1) Input URLs")

# Add pre-validation option
pre_validate = st.checkbox(
    "[?] Pre-validate videos before transcription",
    value=False,
    help="Use YouTube API to check video availability and privacy status before transcription."
)

# Check for pre-populated data from YouTube Search tool
prepopulated_urls = None
prepopulated_metadata = None
input_type = detect_input_type(st.session_state)

if input_type == 'rich_metadata':
    prepopulated_metadata = st.session_state['transcript_metadata']
    prepopulated_urls = [item['video_url'] for item in prepopulated_metadata]
    prepopulated_source = st.session_state.get('transcript_source', 'youtube_search_rich')

    is_valid, errors = validate_metadata_list(prepopulated_metadata)
    if is_valid:
        st.success(f"[DATA] Rich metadata available from {prepopulated_source.replace('_', ' ').title()} - {len(prepopulated_metadata)} videos with complete details")
    else:
        st.warning(f"[!] Metadata validation issues: {', '.join(errors[:3])}")
        if len(errors) > 3:
            st.warning(f"... and {len(errors) - 3} more issues")

elif input_type == 'urls_only':
    prepopulated_urls = st.session_state['transcript_urls']
    prepopulated_source = st.session_state.get('transcript_source', 'unknown')
    st.info(f"[URL] URLs pre-populated from {prepopulated_source.replace('_', ' ').title()}")

# Clear button for both types
if prepopulated_urls or prepopulated_metadata:
    if st.button("Clear pre-populated data"):
        if 'transcript_urls' in st.session_state:
            del st.session_state['transcript_urls']
        if 'transcript_metadata' in st.session_state:
            del st.session_state['transcript_metadata']
        if 'transcript_source' in st.session_state:
            del st.session_state['transcript_source']
        st.rerun()

# Option 1: Paste URLs directly
input_method = st.radio(
    "Choose input method:",
    ["Paste URLs (one per line)", "Upload file"],
    horizontal=True
)

parsed: Optional[ParsedSheet] = None

if input_method == "Paste URLs (one per line)":
    default_text = ""
    if prepopulated_metadata:
        default_text = "\n".join(prepopulated_urls)
        st.info("[DATA] Rich metadata available - video details will be preserved in the processing table")
    elif prepopulated_urls:
        default_text = "\n".join(prepopulated_urls)

    url_text = st.text_area(
        "Paste YouTube URLs (one per line):",
        height=200,
        placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2",
        help="Paste YouTube URLs here. One URL per line. Blank lines are ignored.",
        value=default_text
    )

    submit_urls = st.button(
        "Submit URLs",
        type="primary",
        help="Click to parse and validate the URLs above, or press ctrl+enter",
        use_container_width=True
    )

    if prepopulated_metadata:
        parsed = metadata_to_parsed_sheet(prepopulated_metadata)
        st.success(f"Loaded {parsed.row_count} videos with rich metadata from {prepopulated_source}")
    elif submit_urls or url_text.strip():
        lines = [line.strip() for line in url_text.strip().split("\n") if line.strip()]
        if lines:
            rows = []
            for line in lines:
                if "youtube.com" in line or "youtu.be" in line:
                    rows.append({"source_type": "youtube", "youtube_url": line})
                else:
                    rows.append({"source_type": "youtube", "youtube_url": line})

            parsed = ParsedSheet(
                columns=["source_type", "youtube_url", "mp3_url"],
                rows=rows
            )
            st.success(f"Loaded {parsed.row_count} URLs from text input")

else:
    uploaded = st.file_uploader(
        "Upload TSV/CSV/XLSX spreadsheet OR .txt file with one YouTube URL per line",
        type=["tsv", "csv", "xlsx", "txt"]
    )

    if uploaded is not None:
        try:
            parsed = parse_spreadsheet(uploaded.name, uploaded.getvalue())
            st.success(f"Loaded {parsed.row_count} rows, {len(parsed.columns)} columns")
        except Exception as e:
            st.error(f"Failed to parse spreadsheet: {e}")
            st.stop()

if parsed is None or parsed.row_count == 0:
    st.info("Enter URLs or upload a file to continue.")
    st.stop()

st.header("2) Map columns")
st.caption("Pick which spreadsheet columns map to the required logical fields.")

mapping = resolve_column_mapping(parsed.columns)

col1, col2, col3 = st.columns(3)
with col1:
    mapping.source_type = st.selectbox("source_type", options=parsed.columns, index=parsed.columns.index(mapping.source_type) if mapping.source_type in parsed.columns else 0)
with col2:
    mapping.youtube_url = st.selectbox("youtube_url", options=["(none)"] + parsed.columns, index=(["(none)"] + parsed.columns).index(mapping.youtube_url) if mapping.youtube_url in parsed.columns else 0)
with col3:
    mapping.mp3_url = st.selectbox("mp3_url", options=["(none)"] + parsed.columns, index=(["(none)"] + parsed.columns).index(mapping.mp3_url) if mapping.mp3_url in parsed.columns else 0)

col4, col5, col6 = st.columns(3)
with col4:
    mapping.title = st.selectbox("title (optional)", options=["(none)"] + parsed.columns, index=(["(none)"] + parsed.columns).index(mapping.title) if mapping.title in parsed.columns else 0)
with col5:
    mapping.description = st.selectbox("description (optional)", options=["(none)"] + parsed.columns, index=(["(none)"] + parsed.columns).index(mapping.description) if mapping.description in parsed.columns else 0)
with col6:
    mapping.episode_url = st.selectbox("episode_url (optional)", options=["(none)"] + parsed.columns, index=(["(none)"] + parsed.columns).index(mapping.episode_url) if mapping.episode_url in parsed.columns else 0)

st.header("3) Run")
st.caption("This will create a new session folder and begin processing rows using proxy extraction.")

normalized_preview = normalize_rows(parsed, mapping)
errors, counts = validate_normalized_rows(normalized_preview)

with st.expander("Preview (first 25 normalized rows)", expanded=True):
    st.write(
        f"Counts: total={counts['total']}, youtube={counts['youtube']}, podcast={counts['podcast']}, invalid={counts['invalid']}"
    )
    st.dataframe(normalized_preview[:25], use_container_width=True)

if errors:
    st.error("Fix these issues (or adjust column mapping) before running:")
    st.code("\n".join(errors[:50]))

run_clicked = st.button("Start session (Proxy)", type="primary")
if not run_clicked:
    st.stop()

if errors:
    st.stop()

# Check proxy configuration before starting
if not cfg.proxy_configured:
    st.error("Cannot start: Proxy file is not configured. Set WEBSHARE_PROXY_FILE in your .env file.")
    st.stop()

session_cfg = SessionConfig(output_root=cfg.output_root)
manager = SessionManager(session_cfg)
session = manager.create_session()

rows = normalize_rows(parsed, mapping)
manager.write_items_csv(session.session_dir, rows)
manager.write_manifest(
    session.session_dir,
    {
        "session_id": session.session_id,
        "created_at": None,
        "extraction_method": "proxy_residential",
        "items": [
            {
                "row_index": r.get("_row_index"),
                "source_type": r.get("source_type"),
                "youtube_url": r.get("youtube_url"),
                "mp3_url": r.get("mp3_url"),
                "title": r.get("title"),
                "description": r.get("description"),
                "episode_url": r.get("episode_url"),
                "status": "pending",
            }
            for r in rows
        ],
    },
)

st.success(f"Session created: `{session.session_dir}`")

# Pre-validation step (optional)
if pre_validate and rows:
    st.header("3) Pre-Validation")
    st.caption("Checking video availability before transcription...")

    valid_rows = []
    invalid_rows = []

    prevalidate_progress = st.progress(0)
    prevalidate_status = st.empty()

    for idx, row in enumerate(rows):
        youtube_url = row.get("youtube_url", "").strip()
        prevalidate_progress.progress((idx + 1) / len(rows))
        prevalidate_status.write(f"Checking {idx + 1}/{len(rows)}: {youtube_url[:50]}...")

        try:
            from src.bulk_transcribe.youtube_search import check_video_availability, build_youtube_service
            from src.bulk_transcribe.youtube_transcript import extract_video_id
            video_id = extract_video_id(youtube_url)

            if not video_id:
                invalid_rows.append({
                    **row,
                    "validation_error": "Invalid YouTube URL - could not extract video ID"
                })
                continue

            youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY", "").strip()
            if not youtube_api_key:
                invalid_rows.append({
                    **row,
                    "validation_error": "YouTube API key not configured (YOUTUBE_DATA_API_KEY)"
                })
                continue

            youtube = build_youtube_service(youtube_api_key)
            availability = check_video_availability(youtube, [video_id])
            status = availability.get(video_id, 'error_unknown')

            if status == 'available':
                valid_rows.append(row)
            else:
                error_mapping = {
                    'private': 'Private video (not accessible)',
                    'not_found': 'Video not found (may be deleted)',
                    'error_unknown': 'Could not verify video status',
                }

                if status.startswith('api_error_'):
                    error_msg = f"YouTube API error (HTTP {status.replace('api_error_', '')})"
                elif status.startswith('error_'):
                    error_msg = f"Validation error: {status.replace('error_', '')}"
                else:
                    error_msg = error_mapping.get(status, f"Status: {status}")

                invalid_rows.append({
                    **row,
                    "validation_error": error_msg
                })

        except Exception as e:
            invalid_rows.append({
                **row,
                "validation_error": f"YouTube API check failed: {str(e)[:100]}"
            })

    prevalidate_progress.progress(1.0)
    prevalidate_status.write("[OK] Pre-validation complete!")

    if invalid_rows:
        st.warning(f"[!] {len(invalid_rows)} out of {len(rows)} videos are not accessible and will be skipped.")

        invalid_data = []
        for row in invalid_rows:
            invalid_data.append({
                "URL": row.get("youtube_url", "")[:60] + "..." if len(row.get("youtube_url", "")) > 60 else row.get("youtube_url", ""),
                "Issue": row.get("validation_error", "Unknown")
            })

        st.dataframe(invalid_data, use_container_width=True, hide_index=True)

        invalid_urls = [row.get("youtube_url", "") for row in invalid_rows]
        if invalid_urls:
            st.text_area(
                "Invalid URLs (copy for manual checking):",
                value="\n".join(invalid_urls),
                height=min(200, len(invalid_urls) * 20),
                key="invalid_urls"
            )

    if valid_rows:
        st.success(f"[OK] {len(valid_rows)} videos are accessible and will be processed.")
        rows = valid_rows
    else:
        st.error("[X] No videos are accessible for transcription.")
        st.stop()

    st.divider()

# Process rows with live status updates
processing_step = "4" if pre_validate else "3"
st.header(f"{processing_step}) Processing (Proxy Method)")
st.caption("Processing each row using residential proxy extraction with live status updates...")

rows = normalize_rows(parsed, mapping)

# Initialize processing state
if 'processing_state' not in st.session_state:
    st.session_state.processing_state = {
        'is_running': False,
        'should_stop': False,
        'processed_count': 0,
        'success_count': 0,
        'failed_count': 0,
        'blocked_count': 0,
        'current_video_meta': {},
        'status_history': []
    }

total_rows = len(rows)
processed_count = st.session_state.processing_state['processed_count']
success_count = st.session_state.processing_state['success_count']
failed_count = st.session_state.processing_state['failed_count']
blocked_count = st.session_state.processing_state.get('blocked_count', 0)

# Create enhanced UI layout
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("[PROG] Global Progress")
    global_progress_bar = st.empty()
    global_stats_display = st.empty()

with col2:
    st.subheader("[VID] Current Video")
    current_video_info = st.empty()
    current_video_meta = st.empty()

with col3:
    st.subheader("[CTL] Controls")

    # Parallel processing controls
    use_parallel = st.checkbox(
        "Enable parallel processing",
        value=True,
        help="Process multiple videos simultaneously for faster throughput",
        key="use_parallel_checkbox"
    )

    if use_parallel:
        max_workers = st.slider(
            "Concurrent tasks",
            min_value=2,
            max_value=20,
            value=5,
            help="Number of videos to process simultaneously. Start with 2-5 for testing.",
            key="max_workers_slider"
        )
    else:
        max_workers = 1

    if st.session_state.processing_state.get('is_running', False) and not st.session_state.processing_state.get('stop_requested', False):
        if st.button("[STOP] STOP PROCESSING",
                     key="stop_processing_button",
                     type="secondary",
                     help="Stop processing remaining videos. Already processed videos will be saved."):
            st.session_state.processing_state['stop_requested'] = True
            st.warning("Stop requested - stopping after current video completes...")
            st.rerun()

# Live status table
st.subheader("[LOG] Processing Status (Most Recent First)")
status_table = st.empty()

status_data = st.session_state.processing_state.get('status_history', [])
if not isinstance(status_data, list):
    status_data = []

start_idx = processed_count

processing_crashed = False
crash_error = None

# ============================================================================
# PARALLEL PROCESSING MODE
# ============================================================================
if use_parallel and max_workers > 1:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    st.info(f"[PARALLEL] Processing with {max_workers} concurrent workers")
    
    # Filter YouTube videos to process
    youtube_tasks = []
    for idx in range(start_idx, total_rows):
        row = rows[idx]
        source_type = row.get("source_type", "").lower()
        youtube_url = row.get("youtube_url", "").strip()
        row_index = row.get("_row_index", str(idx + 1))
        
        if source_type == "youtube" and youtube_url:
            # Extract video ID from URL for task creation
            import re
            video_id_match = re.search(
                r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
                youtube_url
            )
            video_id = video_id_match.group(1) if video_id_match else ""
            title = row.get("title", "")
            
            youtube_tasks.append({
                "idx": idx,
                "row_index": row_index,
                "row": row,
                "youtube_url": youtube_url,
                "video_id": video_id,
                "title": title,
            })
        else:
            # Non-YouTube entries are skipped
            video_status = {
                "Row": row_index,
                "URL": youtube_url[:40] + "..." if len(youtube_url) > 40 else youtube_url,
                "Title": "-",
                "Duration": "-",
                "Status": "[SKIP] Skipped",
                "Method": "-",
                "Error": "Non-YouTube or invalid source",
                "Time": "-"
            }
            status_data.insert(0, video_status)
            processed_count += 1
    
    # Update status table with skipped entries
    if status_data:
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
    
    # Process YouTube videos in parallel
    total_youtube = len(youtube_tasks)
    completed_parallel = 0
    
    try:
        st.session_state.processing_state['is_running'] = True
        
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="transcript") as executor:
            # Submit all tasks
            future_to_task = {}
            for task_info in youtube_tasks:
                future = executor.submit(
                    process_single_video_parallel,
                    task_info["youtube_url"],
                    task_info["video_id"],
                    task_info["title"],
                    task_info["row"],
                    session.youtube_dir,
                )
                future_to_task[future] = task_info
            
            # Poll for results and update UI (from main thread)
            for future in as_completed(future_to_task):
                if st.session_state.processing_state.get('should_stop', False):
                    # Cancel remaining futures
                    for f in future_to_task:
                        if not f.done():
                            f.cancel()
                    st.warning("[!] Processing stopped by user. Already completed videos were saved.")
                    break
                
                task_info = future_to_task[future]
                row_index = task_info["row_index"]
                youtube_url = task_info["youtube_url"]
                
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per video
                except Exception as e:
                    result = {
                        "success": False,
                        "video_id": task_info["video_id"],
                        "title": task_info["title"],
                        "youtube_url": youtube_url,
                        "method": "-",
                        "error": str(e),
                        "elapsed": 0.0,
                        "metadata": {},
                        "blocked": False,
                    }
                
                # Update counters
                completed_parallel += 1
                processed_count += 1
                
                # Build status entry
                video_status = {
                    "Row": row_index,
                    "URL": youtube_url[:40] + "..." if len(youtube_url) > 40 else youtube_url,
                    "Title": (result.get("title", "-")[:30] + "...") if len(result.get("title", "")) > 30 else result.get("title", "-"),
                    "Duration": result.get("metadata", {}).get("duration", "-"),
                    "Status": "[OK] Success" if result["success"] else "[X] Failed",
                    "Method": result.get("method", "-"),
                    "Error": "-" if result["success"] else (result.get("error", "Unknown")[:50] if result.get("error") else "-"),
                    "Time": f"{result.get('elapsed', 0):.1f}s"
                }
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
                    if result.get("blocked"):
                        blocked_count += 1
                
                # Update UI from main thread
                status_data.insert(0, video_status)
                status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
                
                with global_progress_bar.container():
                    progress_pct = processed_count / total_rows
                    st.progress(progress_pct)
                    st.write(f"**Overall Progress:** {processed_count}/{total_rows} videos")
                
                with global_stats_display.container():
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("[OK] Successful", success_count)
                    with col_b:
                        st.metric("[X] Failed", failed_count)
                    with col_c:
                        st.metric("[...] Remaining", total_rows - processed_count)
                
                with current_video_info.container():
                    st.write(f"**Completed:** {completed_parallel}/{total_youtube}")
                    st.write(f"**Last:** {result.get('title', 'Unknown')[:40]}")
                
                # Update session state
                st.session_state.processing_state.update({
                    'processed_count': processed_count,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'blocked_count': blocked_count,
                    'status_history': status_data
                })
        
    except Exception as e:
        processing_crashed = True
        crash_error = str(e)
        st.error(f"[CRASH] Parallel processing crashed: {crash_error}")
    
    st.session_state.processing_state['is_running'] = False

# ============================================================================
# SEQUENTIAL PROCESSING MODE (fallback or when parallel is disabled)
# ============================================================================
else:
    try:
        st.session_state.processing_state['is_running'] = True

        for idx in range(start_idx, total_rows):
            if st.session_state.processing_state['should_stop']:
                st.warning("[!] Processing stopped by user. Already completed videos were saved.")
                break

            row = rows[idx]
            row_index = row.get("_row_index", str(idx + 1))
            source_type = row.get("source_type", "").lower()
            youtube_url = row.get("youtube_url", "").strip()

            video_status = {
                "Row": row_index,
                "URL": youtube_url[:40] + "..." if len(youtube_url) > 40 else youtube_url,
                "Title": "-",
                "Duration": "-",
                "Status": "[...] Starting...",
                "Method": "-",
                "Error": "-",
                "Time": "-"
            }

            start_time = time.time()

            with current_video_info.container():
                st.write(f"**Processing:** {row_index}/{total_rows}")
                st.write(f"**URL:** {youtube_url[:60]}{'...' if len(youtube_url) > 60 else ''}")

            with current_video_meta.container():
                st.empty()

            try:
                if source_type == "youtube" and youtube_url:
                    from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata, save_metadata_json
                    from src.bulk_transcribe.transcript_writer import write_transcript_markdown, generate_filename
                    from src.bulk_transcribe.utils import slugify

                    # Step 1: Fetch metadata
                    video_status["Status"] = "[META] Fetching metadata..."
                    status_data.insert(0, video_status.copy())
                    status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

                    try:
                        meta = fetch_youtube_metadata(youtube_url)
                        video_id = meta.video_id
                        title = meta.title or row.get("title", "")

                        if not video_id:
                            video_status.update({
                                "Status": "[X] Failed",
                                "Error": "Could not extract video ID from URL"
                            })
                            failed_count += 1
                            processed_count += 1
                            status_data[0] = video_status
                            st.session_state.processing_state.update({
                                'processed_count': processed_count,
                                'failed_count': failed_count,
                                'status_history': status_data
                            })
                            continue

                        duration_str = meta.raw.get("duration", "Unknown")
                        channel_name = meta.raw.get("channel", "Unknown")

                        video_status.update({
                            "Title": title[:30] + "..." if len(title) > 30 else title,
                            "Duration": duration_str,
                        })

                        with current_video_meta.container():
                            st.write(f"**Title:** {title}")
                            st.write(f"**Duration:** {duration_str}")
                            st.write(f"**Channel:** {channel_name}")

                        meta_path = os.path.join(session.youtube_dir, f"{slugify(title)}__{video_id}.metadata.json")
                        save_metadata_json(meta_path, meta.raw)

                        # Step 2: Get transcript using proxy method
                        video_status["Status"] = "[PROXY] Extracting transcript..."
                        status_data[0] = video_status.copy()
                        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

                        # Use proxy-based extraction
                        transcript_result = get_proxy_transcript(youtube_url)
                        elapsed = time.time() - start_time

                        if transcript_result.success:
                            filename = generate_filename(video_id, title, "youtube")
                            transcript_path = os.path.join(session.youtube_dir, filename)

                            # Build rich metadata from session state with yt-dlp fallback
                            rich_metadata = _build_rich_youtube_metadata(row, meta.raw)

                            write_transcript_markdown(
                                output_path=transcript_path,
                                source_type="youtube",
                                source_url=youtube_url,
                                transcript_text=transcript_result.transcript_text or "",
                                title=title or meta.title,
                                description=row.get("description"),
                                video_id=video_id,
                                method=transcript_result.method,
                                youtube_metadata=rich_metadata,
                            )

                            video_status.update({
                                "Status": "[OK] Success",
                                "Method": transcript_result.method,
                                "Time": f"{elapsed:.1f}s"
                            })
                            success_count += 1
                        else:
                            error_msg = transcript_result.error_message or "Unknown error"
                            status_icon, display_error = categorize_error(error_msg)

                            if "blocked" in display_error.lower():
                                blocked_count += 1

                            video_status.update({
                                "Status": f"{status_icon} Failed",
                                "Method": transcript_result.method,
                                "Error": display_error,
                                "Time": f"{elapsed:.1f}s"
                            })
                            failed_count += 1

                    except Exception as e:
                        elapsed = time.time() - start_time
                        error_msg = str(e)
                        status_icon, display_error = categorize_error(error_msg)

                        video_status.update({
                            "Status": f"{status_icon} Failed",
                            "Error": display_error,
                            "Time": f"{elapsed:.1f}s"
                        })
                        failed_count += 1

                        update_status_safe(status_data, video_status, status_table)

                elif source_type == "podcast":
                    video_status.update({
                        "Status": "[SKIP] Skipped",
                        "Error": "Podcast processing not supported in proxy mode"
                    })
                    update_status_safe(status_data, video_status, status_table)

                else:
                    video_status.update({
                        "Status": "[SKIP] Skipped",
                        "Error": "Invalid source_type or missing URL"
                    })
                    update_status_safe(status_data, video_status, status_table)

            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)
                status_icon, display_error = categorize_error(error_msg, is_code_error=True)

                video_status.update({
                    "Status": f"{status_icon} Crash",
                    "Error": display_error,
                    "Time": f"{elapsed:.1f}s"
                })
                failed_count += 1

                update_status_safe(status_data, video_status, status_table)

            processed_count += 1

            with global_progress_bar.container():
                progress_pct = processed_count / total_rows
                st.progress(progress_pct)
                st.write(f"**Overall Progress:** {processed_count}/{total_rows} videos")

            with global_stats_display.container():
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("[OK] Successful", success_count)
                with col_b:
                    st.metric("[X] Failed", failed_count)
                with col_c:
                    st.metric("[...] Remaining", total_rows - processed_count)

            status_data.insert(0, video_status)
            status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

            st.session_state.processing_state.update({
                'processed_count': processed_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'blocked_count': blocked_count,
                'status_history': status_data
            })

            # Rate limiting delay (proxy method has built-in rate limiting, but add small buffer)
            if idx < total_rows - 1 and not st.session_state.processing_state['should_stop']:
                delay = 0.5  # Shorter delay since proxy method has internal rate limiting
                with st.spinner(f"Brief pause before next video..."):
                    time.sleep(delay)

            # Update manifest with current progress
            try:
                current_items = manager.read_manifest(session.session_dir).get("items", [])
                for item in current_items:
                    if item.get("row_index") == row_index:
                        if "[OK]" in video_status["Status"]:
                            item["status"] = "completed"
                        elif any(icon in video_status["Status"] for icon in ["[X]", "[SKIP]", "[BLK]", "[PVT]", "[NC]"]):
                            item["status"] = "failed"
                        else:
                            item["status"] = "processing"
                        break

                manifest_data = {
                    "session_id": session.session_id,
                    "created_at": datetime.now().isoformat(),
                    "extraction_method": "proxy_residential",
                    "items": current_items
                }
                manager.write_manifest(session.session_dir, manifest_data)
            except Exception as e:
                pass

    except Exception as processing_error:
        processing_crashed = True
        crash_error = str(processing_error)

        crash_status = {
            "Row": "CRASH",
            "URL": "Processing interrupted",
            "Title": "N/A",
            "Duration": "N/A",
            "Status": "[CRASH] CRASH",
            "Method": "N/A",
            "Error": f"Code error: {crash_error}",
            "Time": "N/A"
        }

        status_data.insert(0, crash_status)
        try:
            status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
        except:
            pass

        st.error(f"[CRASH] Processing crashed due to code error: {crash_error}")
        st.error("**This is a bug in the application, not a proxy issue.**")

        st.session_state.processing_state['is_running'] = False

    st.session_state.processing_state['is_running'] = False

# Final summary
if processing_crashed:
    st.error("[CRASH] Processing failed due to application error")
    st.error(f"**Error:** {crash_error}")
    st.info("[FIX] **Action Required:** This is a code bug that needs to be fixed by the developer.")
elif st.session_state.processing_state['should_stop']:
    st.warning("[!] Processing was stopped by user. Already completed videos were saved.")
else:
    st.success("[DONE] Processing Complete!")

st.write("---")
st.write("**Final Results:**")
st.write(f"- **Total Processed:** {processed_count}/{total_rows} videos")
st.write(f"- **Successful:** {success_count} videos")
st.write(f"- **Failed:** {failed_count} videos")
st.write(f"- **Blocked:** {blocked_count} videos (retried with different proxy)")
st.write(f"- **Success Rate:** {(success_count/processed_count*100):.1f}%" if processed_count > 0 else "0%")

if status_data:
    st.write("---")
    st.write("**Recent Processing Results:**")
    st.dataframe(pd.DataFrame(status_data[:10]), use_container_width=True)

# Clear processing state
if not st.session_state.processing_state['should_stop']:
    st.session_state.processing_state = {
        'is_running': False,
        'should_stop': False,
        'processed_count': 0,
        'success_count': 0,
        'failed_count': 0,
        'blocked_count': 0,
        'status_history': []
    }

skipped_count = sum(1 for s in status_data if "[SKIP]" in s.get("Status", ""))

# Display results with actionable recommendations
if success_count == total_rows:
    st.success(f"[PERFECT] All {total_rows} videos transcribed successfully!")
elif success_count > 0:
    st.success(f"[OK] Completed: {success_count} successful, {failed_count} failed out of {total_rows} total")
    if blocked_count > 0:
        st.warning(f"[!] {blocked_count} videos were blocked initially but retried with different proxies.")
else:
    st.error(f"[X] All {total_rows} videos failed. Check proxy configuration and try again.")

# Build comprehensive log text
log_lines = [
    f"Session: {session.session_id}",
    f"Session Directory: {session.session_dir}",
    f"Extraction Method: Proxy Residential",
    f"Started: {datetime.now().isoformat()}",
    f"Pre-validation: {'Enabled' if pre_validate else 'Disabled'}",
    f"Total Rows After Validation: {total_rows}",
    f"Successful: {success_count}",
    f"Failed: {failed_count}",
    f"Blocked (retried): {blocked_count}",
    f"Skipped: {skipped_count}",
    f"Success Rate: {(success_count/total_rows*100):.1f}%" if total_rows > 0 else "N/A",
    "",
    "=" * 80,
    "DETAILED STATUS LOG",
    "=" * 80,
    "",
]

for status_info in status_data:
    log_lines.append(f"Row {status_info['Row']}: {status_info['URL']}")
    log_lines.append(f"  Status: {status_info['Status']}")
    log_lines.append(f"  Method: {status_info['Method']}")
    if status_info.get('Error') and status_info['Error'] != "-":
        log_lines.append(f"  Error: {status_info['Error']}")
    log_lines.append("")

log_lines.extend([
    "=" * 80,
    "SUMMARY",
    "=" * 80,
    f"Session ID: {session.session_id}",
    f"Extraction Method: Proxy Residential",
    f"Completed: {datetime.now().isoformat()}",
    f"Pre-validation: {'Enabled' if pre_validate else 'Disabled'}",
    f"Total Processed: {total_rows}",
    f"Successful: {success_count}",
    f"Failed: {failed_count}",
    f"Blocked: {blocked_count}",
    f"Skipped: {skipped_count}",
    f"Success Rate: {(success_count/total_rows*100):.1f}%" if total_rows > 0 else "N/A",
])

log_text = "\n".join(log_lines)

log_filename = f"session_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_filepath = os.path.join(session.session_dir, log_filename)
with open(log_filepath, "w", encoding="utf-8") as f:
    f.write(log_text)

st.info(f"[FILE] Log file saved: `{log_filename}` in session directory")

# Show final status table
results_step = "5" if pre_validate else "4"
st.header(f"{results_step}) Results Summary")
df = pd.DataFrame(status_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Copy logs section
logs_step = "6" if pre_validate else "5"
st.header(f"{logs_step}) Copy Session Logs")
st.caption("Copy all session logs for debugging or record-keeping.")

with st.expander("View Full Session Logs", expanded=True):
    st.code(log_text, language="text")

st.text_area(
    "Select all and copy (Ctrl+A, Ctrl+C):",
    value=log_text,
    height=300,
    label_visibility="collapsed",
    key="log_text_area"
)

st.success("[OK] Logs are also saved to file: " + log_filename)
