import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import requests


def check_deapi_balance(api_key: str, base_url: str = "https://api.deapi.ai") -> Dict[str, any]:
    """
    Check DEAPI account balance and return formatted information.

    Returns:
        dict: {
            "success": bool,
            "balance": float or None,
            "currency": str or None,
            "error": str or None
        }
    """
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(f"{base_url}/api/v1/client/balance", headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Extract balance information - adjust based on actual API response structure
            balance = data.get("balance") or data.get("credits") or data.get("amount")
            currency = data.get("currency", "USD")

            return {
                "success": True,
                "balance": balance,
                "currency": currency,
                "raw_data": data
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "error": "Invalid API key"
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text[:100]}"
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }


def categorize_error(error_msg: str, is_code_error: bool = False) -> tuple[str, str]:
    """
    Categorize errors accurately based on DEAPI API responses.
    Returns (icon, description) tuple.
    """
    if is_code_error:
        return "💥", f"Code bug: {error_msg}"

    error_lower = error_msg.lower()

    # Check for specific DEAPI error patterns first
    if "resource_exhausted" in error_lower or "429" in error_msg:
        return "⏸️", "Rate limited - wait before retrying"
    elif "payment_required" in error_lower or "402" in error_msg:
        return "💰", "Credits exhausted - add funds to account"
    elif "unauthorized" in error_lower or "401" in error_msg:
        return "🔐", "API key invalid - check credentials"
    elif "validation error" in error_lower or "422" in error_msg:
        return "❌", "Invalid request - check video URL/format"
    elif "server error" in error_lower or "500" in error_msg or "503" in error_msg:
        return "🔧", "DEAPI server error - try again later"
    elif "timeout" in error_lower:
        return "⏰", "Request timeout - DEAPI may be busy"
    elif "network" in error_lower or "connection" in error_lower:
        return "🌐", "Network error - check internet"
    elif "video unavailable" in error_lower:
        return "🚫", "Video unavailable - may be private/deleted"
    elif "private" in error_lower:
        return "🔒", "Private video - cannot access"

    # Generic failures
    return "❌", error_msg[:50] if len(error_msg) > 50 else error_msg


def update_status_safe(status_data: list, new_status: dict, status_table):
    """
    Safely update status table with error handling to prevent crashes.
    """
    try:
        status_data.insert(0, new_status)
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
        return True
    except Exception as update_error:
        # Fallback: show error directly if table update fails
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


@dataclass
class AppConfig:
    output_root: str
    deapi_api_key_present: bool


def load_app_config() -> AppConfig:
    output_root = os.path.join(".", "output", "sessions")
    deapi_api_key_present = bool(os.getenv("DEAPI_API_KEY", "").strip())
    return AppConfig(output_root=output_root, deapi_api_key_present=deapi_api_key_present)


st.set_page_config(page_title="Bulk Transcribe - Transcript Tool", layout="wide")
st.title("📝 Bulk Transcribe - Transcript Tool")

cfg = load_app_config()

with st.sidebar:
    st.header("Config")
    st.write(f"Output root: `{cfg.output_root}`")
    if cfg.deapi_api_key_present:
        st.success("DEAPI_API_KEY is set")

        # Check and display balance
        api_key = os.getenv("DEAPI_API_KEY", "").strip()
        if api_key:
            with st.spinner("Checking balance..."):
                balance_info = check_deapi_balance(api_key)

            if balance_info["success"]:
                balance = balance_info.get("balance")
                currency = balance_info.get("currency", "USD")
                if balance is not None:
                    st.info(f"💰 DEAPI Balance: {balance} {currency}")
                else:
                    st.info("💰 DEAPI Balance: Available")
            else:
                st.warning(f"⚠️ Balance check failed: {balance_info.get('error', 'Unknown error')}")
    else:
        st.warning("DEAPI_API_KEY is not set (DEAPI fallback + podcast transcription will fail)")
        st.caption("Set it in your environment, then restart Streamlit.")

st.header("1) Input URLs")

# Add pre-validation option
pre_validate = st.checkbox(
    "🔍 Pre-validate videos before transcription",
    value=False,
    help="Use YouTube API to check video availability and privacy status before transcription. Prevents wasting DEAPI credits on inaccessible videos."
)

# Check for pre-populated data from YouTube Search tool
prepopulated_urls = None
prepopulated_metadata = None
input_type = detect_input_type(st.session_state)

if input_type == 'rich_metadata':
    prepopulated_metadata = st.session_state['transcript_metadata']
    prepopulated_urls = [item['video_url'] for item in prepopulated_metadata]  # Extract URLs for compatibility
    prepopulated_source = st.session_state.get('transcript_source', 'youtube_search_rich')

    # Validate metadata
    is_valid, errors = validate_metadata_list(prepopulated_metadata)
    if is_valid:
        st.success(f"📊 Rich metadata available from {prepopulated_source.replace('_', ' ').title()} - {len(prepopulated_metadata)} videos with complete details")
    else:
        st.warning(f"⚠️ Metadata validation issues: {', '.join(errors[:3])}")
        if len(errors) > 3:
            st.warning(f"... and {len(errors) - 3} more issues")

elif input_type == 'urls_only':
    prepopulated_urls = st.session_state['transcript_urls']
    prepopulated_source = st.session_state.get('transcript_source', 'unknown')
    st.info(f"🔗 URLs pre-populated from {prepopulated_source.replace('_', ' ').title()}")

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
    # Pre-fill based on input type
    default_text = ""
    if prepopulated_metadata:
        # For rich metadata, show URLs but indicate metadata is available
        default_text = "\n".join(prepopulated_urls)
        st.info("📊 Rich metadata available - video details will be preserved in the processing table")
    elif prepopulated_urls:
        # Legacy URL-only input
        default_text = "\n".join(prepopulated_urls)

    url_text = st.text_area(
        "Paste YouTube URLs or MP3 links (one per line):",
        height=200,
        placeholder="https://www.youtube.com/watch?v=VIDEO_ID_1\nhttps://www.youtube.com/watch?v=VIDEO_ID_2\nhttps://example.com/podcast.mp3",
        help="Paste URLs directly here. One URL per line. Blank lines are ignored.",
        value=default_text
    )

    # Add visible confirm button
    submit_urls = st.button(
        "Submit URLs",
        type="primary",
        help="Click to parse and validate the URLs above, or press ctrl+enter",
        use_container_width=True
    )

    # Handle different input types - rich metadata takes priority
    if prepopulated_metadata:
        # Use rich metadata directly when available - this is the primary input method
        parsed = metadata_to_parsed_sheet(prepopulated_metadata)
        st.success(f"Loaded {parsed.row_count} videos with rich metadata from {prepopulated_source}")
    elif submit_urls or url_text.strip():
        # Convert text to CSV-like format
        lines = [line.strip() for line in url_text.strip().split("\n") if line.strip()]
        if lines:
            # Determine source type based on URL
            rows = []
            for line in lines:
                if "youtube.com" in line or "youtu.be" in line:
                    rows.append({"source_type": "youtube", "youtube_url": line})
                elif line.endswith((".mp3", ".wav", ".m4a")) or "mp3" in line.lower():
                    rows.append({"source_type": "podcast", "mp3_url": line})
                else:
                    # Default to YouTube if unclear
                    rows.append({"source_type": "youtube", "youtube_url": line})

            # Create ParsedSheet-like structure
            parsed = ParsedSheet(
                columns=["source_type", "youtube_url", "mp3_url"],
                rows=rows
            )
            st.success(f"Loaded {parsed.row_count} URLs from text input")

else:
    # Option 2: File upload
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
st.caption("This will create a new session folder and begin processing rows.")

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

run_clicked = st.button("Start session", type="primary")
if not run_clicked:
    st.stop()

if errors:
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
            # Use YouTube API to check video availability and privacy status
            from src.bulk_transcribe.youtube_search import check_video_availability, build_youtube_service

            # Extract video ID
            from src.bulk_transcribe.youtube_transcript import extract_video_id
            video_id = extract_video_id(youtube_url)

            if not video_id:
                invalid_rows.append({
                    **row,
                    "validation_error": "Invalid YouTube URL - could not extract video ID"
                })
                continue

            # Check video status using YouTube API
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
                # Map status to user-friendly error message
                error_mapping = {
                    'private': 'Private video (not accessible)',
                    'not_found': 'Video not found (may be deleted)',
                    'error_unknown': 'Could not verify video status',
                }

                # Handle API errors
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
    prevalidate_status.write("✅ Pre-validation complete!")

    # Show validation results
    if invalid_rows:
        st.warning(f"⚠️ {len(invalid_rows)} out of {len(rows)} videos are not accessible and will be skipped.")

        # Show invalid videos in a table
        invalid_data = []
        for row in invalid_rows:
            invalid_data.append({
                "URL": row.get("youtube_url", "")[:60] + "..." if len(row.get("youtube_url", "")) > 60 else row.get("youtube_url", ""),
                "Issue": row.get("validation_error", "Unknown")
            })

        st.dataframe(invalid_data, use_container_width=True, hide_index=True)

        # Option to copy invalid URLs for manual checking
        invalid_urls = [row.get("youtube_url", "") for row in invalid_rows]
        if invalid_urls:
            st.text_area(
                "Invalid URLs (copy for manual checking):",
                value="\n".join(invalid_urls),
                height=min(200, len(invalid_urls) * 20),
                key="invalid_urls"
            )

    if valid_rows:
        st.success(f"✅ {len(valid_rows)} videos are accessible and will be processed.")
        rows = valid_rows  # Update rows to only include valid ones
    else:
        st.error("❌ No videos are accessible for transcription.")
        st.stop()

    st.divider()

# Process rows with live status updates
processing_step = "4" if pre_validate else "3"
st.header(f"{processing_step}) Processing")
st.caption("Processing each row and generating transcripts with live status updates...")

rows = normalize_rows(parsed, mapping)
deapi_key = os.getenv("DEAPI_API_KEY", "").strip() or None

# Initialize processing state
if 'processing_state' not in st.session_state:
    st.session_state.processing_state = {
        'is_running': False,
        'should_stop': False,
        'processed_count': 0,
        'success_count': 0,
        'failed_count': 0,
        'rate_limited_count': 0,
        'current_video_meta': {},
        'status_history': []
    }

total_rows = len(rows)
processed_count = st.session_state.processing_state['processed_count']
success_count = st.session_state.processing_state['success_count']
failed_count = st.session_state.processing_state['failed_count']
rate_limited_count = st.session_state.processing_state['rate_limited_count']

# Create enhanced UI layout
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("📊 Global Progress")
    global_progress_bar = st.empty()
    global_stats_display = st.empty()

with col2:
    st.subheader("🎯 Current Video")
    current_video_info = st.empty()
    current_video_meta = st.empty()

with col3:
    st.subheader("⚡ Controls")
    stop_button = st.button(
        "🛑 STOP PROCESSING",
        type="secondary",
        help="Stop processing remaining videos. Already processed videos will be saved.",
        disabled=not st.session_state.processing_state.get('is_running', False)
    )
    if stop_button:
        st.session_state.processing_state['should_stop'] = True
        st.rerun()

# Live status table
st.subheader("📋 Processing Status (Most Recent First)")
status_table = st.empty()

# Initialize status data from session state if resuming
# CRITICAL: Always ensure status_data is defined to prevent misleading error messages
status_data = st.session_state.processing_state.get('status_history', [])
if not isinstance(status_data, list):
    status_data = []  # Reset if corrupted

# Continue processing from where we left off
start_idx = processed_count

# CRITICAL: Wrap entire processing in exception handler to prevent misleading error messages
processing_crashed = False
crash_error = None

try:
    # Mark processing as running to enable stop button
    st.session_state.processing_state['is_running'] = True
    # Process rows starting from current index
    for idx in range(start_idx, total_rows):
        if st.session_state.processing_state['should_stop']:
            st.warning("⚠️ Processing stopped by user. Already completed videos were saved.")
            break

        row = rows[idx]
        row_index = row.get("_row_index", str(idx + 1))
        source_type = row.get("source_type", "").lower()
        youtube_url = row.get("youtube_url", "").strip()

        # Initialize status for this video
        video_status = {
            "Row": row_index,
            "URL": youtube_url[:40] + "..." if len(youtube_url) > 40 else youtube_url,
            "Title": "-",
            "Duration": "-",
            "Status": "🔄 Starting...",
            "Method": "-",
            "Error": "-",
            "Time": "-"
        }

        start_time = time.time()

        # Update current video info
        with current_video_info.container():
            st.write(f"**Processing:** {row_index}/{total_rows}")
            st.write(f"**URL:** {youtube_url[:60]}{'...' if len(youtube_url) > 60 else ''}")

        # Clear previous metadata
        with current_video_meta.container():
            st.empty()

        try:
            if source_type == "youtube" and youtube_url:
                # Process YouTube video
                from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata, save_metadata_json
                from src.bulk_transcribe.youtube_transcript import get_youtube_transcript
                from src.bulk_transcribe.transcript_writer import write_transcript_markdown, generate_filename
                from src.bulk_transcribe.utils import slugify

                # Step 1: Fetch metadata
                video_status["Status"] = "📊 Fetching metadata..."
                status_data.insert(0, video_status.copy())
                status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

                try:
                    meta = fetch_youtube_metadata(youtube_url)
                    video_id = meta.video_id
                    title = meta.title or row.get("title", "")

                    if not video_id:
                        video_status.update({
                            "Status": "❌ Failed",
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

                    # Update video metadata display
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

                    # Save metadata JSON
                    meta_path = os.path.join(session.youtube_dir, f"{slugify(title)}__{video_id}.metadata.json")
                    save_metadata_json(meta_path, meta.raw)

                    # Step 2: Get transcript
                    video_status["Status"] = "🎙️ Getting transcript..."
                    status_data[0] = video_status.copy()
                    status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

                    transcript_result = get_youtube_transcript(youtube_url, deapi_key)
                    elapsed = time.time() - start_time

                    if transcript_result.success:
                        # Write transcript Markdown
                        filename = generate_filename(video_id, title, "youtube")
                        transcript_path = os.path.join(session.youtube_dir, filename)

                        write_transcript_markdown(
                            output_path=transcript_path,
                            source_type="youtube",
                            source_url=youtube_url,
                            transcript_text=transcript_result.transcript_text or "",
                            title=title or meta.title,
                            description=row.get("description"),
                            video_id=video_id,
                            method=transcript_result.method,
                            youtube_metadata={
                                "channel": meta.raw.get("channel"),
                                "upload_date": meta.raw.get("upload_date"),
                                "duration": meta.raw.get("duration"),
                            },
                        )

                        video_status.update({
                            "Status": "✅ Success",
                            "Method": transcript_result.method,
                            "Time": f"{elapsed:.1f}s"
                        })
                        success_count += 1
                    else:
                        error_msg = transcript_result.error_message or "Unknown error"
                        # Use improved error categorization
                        status_icon, display_error = categorize_error(error_msg)

                        # Update counters based on error type
                        if "Rate limited" in display_error:
                            rate_limited_count += 1
                        # Note: failed_count is still incremented for all failures

                        # Show raw server response instead of categorized message
                        raw_error = transcript_result.raw_response_text or display_error
                        if len(raw_error) > 100:
                            raw_error = raw_error[:97] + "..."

                        video_status.update({
                            "Status": f"{status_icon} Failed",
                            "Method": transcript_result.method,
                            "Error": raw_error,
                            "Status Code": transcript_result.http_status_code or "N/A",
                            "Request ID": transcript_result.deapi_request_id or "N/A",
                            "Raw Response": transcript_result.raw_response_text or "N/A",
                            "Time": f"{elapsed:.1f}s"
                        })
                        failed_count += 1

                except Exception as e:
                    elapsed = time.time() - start_time
                    error_msg = str(e)

                    # CRITICAL: Use accurate error categorization to prevent misleading messages
                    status_icon, display_error = categorize_error(error_msg)

                    video_status.update({
                        "Status": f"{status_icon} Failed",
                        "Error": display_error,
                        "Status Code": "CODE_ERROR",
                        "Request ID": "N/A",
                        "Raw Response": f"Exception: {str(e)}",
                        "Time": f"{elapsed:.1f}s"
                    })
                    failed_count += 1

                    # Ensure status update happens even if categorization fails
                    update_status_safe(status_data, video_status, status_table)

            elif source_type == "podcast":
                video_status.update({
                    "Status": "⏸️ Skipped",
                    "Error": "Podcast processing not yet implemented"
                })
                update_status_safe(status_data, video_status, status_table)

            else:
                video_status.update({
                    "Status": "⏸️ Skipped",
                    "Error": "Invalid source_type or missing URL"
                })
                update_status_safe(status_data, video_status, status_table)

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)

            # CRITICAL: Mark as code error to prevent misleading "rate limit" messages
            status_icon, display_error = categorize_error(error_msg, is_code_error=True)

            video_status.update({
                "Status": f"{status_icon} Crash",
                "Error": display_error,
                "Time": f"{elapsed:.1f}s"
            })
            failed_count += 1

            # Ensure crash status is displayed immediately
            update_status_safe(status_data, video_status, status_table)

        # Update counters and status data
        processed_count += 1

        # Update global progress
        with global_progress_bar.container():
            progress_pct = processed_count / total_rows
            st.progress(progress_pct)
            st.write(f"**Overall Progress:** {processed_count}/{total_rows} videos")

        with global_stats_display.container():
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("✅ Successful", success_count)
            with col_b:
                st.metric("❌ Failed", failed_count)
            with col_c:
                st.metric("⏳ Remaining", total_rows - processed_count)

        # Add to status table (most recent first)
        status_data.insert(0, video_status)
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

        # Save progress to session state for recovery
        st.session_state.processing_state.update({
            'processed_count': processed_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'rate_limited_count': rate_limited_count,
            'status_history': status_data
        })

        # Rate limiting delay (skip for last video or if stopped)
        if idx < total_rows - 1 and not st.session_state.processing_state['should_stop']:
            delay = 1  # 1 second delay for Premium accounts (300 RPM = 0.2s per request, using 1s buffer)
            with st.spinner(f"Rate limiting: waiting {delay} seconds..."):
                time.sleep(delay)

        # Update manifest with current progress (for recovery if interrupted)
        try:
            current_items = manager.read_manifest(session.session_dir).get("items", [])
            # Update the status for this specific row
            for item in current_items:
                if item.get("row_index") == row_index:
                    if "✅" in video_status["Status"]:
                        item["status"] = "completed"
                    elif any(icon in video_status["Status"] for icon in ["❌", "⏸️", "🚫", "🔒", "💰", "⏰", "🌐", "💥"]):
                        item["status"] = "failed"
                    else:
                        item["status"] = "processing"
                    break

            # Write updated manifest
            manifest_data = {
                "session_id": session.session_id,
                "created_at": datetime.now().isoformat(),
                "items": current_items
            }
            manager.write_manifest(session.session_dir, manifest_data)
        except Exception as e:
            # Don't let manifest update errors stop processing
            pass

except Exception as processing_error:
    # CRITICAL: Catch any crash during processing and update status accurately
    processing_crashed = True
    crash_error = str(processing_error)

    # Create crash status entry
    crash_status = {
        "Row": "CRASH",
        "URL": "Processing interrupted",
        "Title": "N/A",
        "Duration": "N/A",
        "Status": "💥 CRASH",
        "Method": "N/A",
        "Error": f"Code error: {crash_error}",
        "Time": "N/A"
    }

    # Add crash status to table and display immediately
    status_data.insert(0, crash_status)
    try:
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)
    except:
        pass  # Don't let status update crash the error display

    # Show error to user with actual cause
    st.error(f"💥 Processing crashed due to code error: {crash_error}")
    st.error("**This is a bug in the application, not a rate limiting issue.**")

    # Update session state
    st.session_state.processing_state['is_running'] = False

# Mark processing as complete
st.session_state.processing_state['is_running'] = False

# Final summary - handle crash case properly
if processing_crashed:
    st.error("💥 Processing failed due to application error")
    st.error(f"**Error:** {crash_error}")
    st.info("🔧 **Action Required:** This is a code bug that needs to be fixed by the developer.")
elif st.session_state.processing_state['should_stop']:
    st.warning("⚠️ Processing was stopped by user. Already completed videos were saved.")
else:
    st.success("🎉 Processing Complete!")

st.write("---")
st.write("**Final Results:**")
st.write(f"• **Total Processed:** {processed_count}/{total_rows} videos")
st.write(f"• **Successful:** {success_count} videos")
st.write(f"• **Failed:** {failed_count} videos")
st.write(f"• **Success Rate:** {(success_count/processed_count*100):.1f}%" if processed_count > 0 else "0%")

# Show detailed breakdown
if status_data:
    st.write("---")
    st.write("**Recent Processing Results:**")
    st.dataframe(pd.DataFrame(status_data[:10]), use_container_width=True)  # Show last 10

    # Show raw server responses for failed requests
    failed_with_responses = [s for s in status_data[:10] if "Failed" in s.get("Status", "") and s.get("Raw Response") != "N/A"]
    if failed_with_responses:
        with st.expander("🔍 View Raw Server Responses for Failed Requests"):
            for status in failed_with_responses:
                st.write(f"**Row {status['Row']}: {status['URL'][:50]}...**")
                st.write(f"**Status:** {status['Status']}")
                st.write(f"**HTTP Status Code:** {status.get('Status Code', 'N/A')}")
                if status.get('Request ID') != "N/A":
                    st.write(f"**Request ID:** {status['Request ID']}")

                raw_response = status.get('Raw Response', 'N/A')
                if raw_response != 'N/A':
                    st.code(raw_response, language="json")
                else:
                    st.write("*No raw response captured*")
                st.write("---")

# Clear processing state
if not st.session_state.processing_state['should_stop']:
    st.session_state.processing_state = {
        'is_running': False,
        'should_stop': False,
        'processed_count': 0,
        'success_count': 0,
        'failed_count': 0,
        'rate_limited_count': 0,
        'status_history': []
    }
skipped_count = sum(1 for s in status_data if "⏸" in s["Status"] and "Skipped" in s["Status"])

# Display results with actionable recommendations
if success_count == total_rows:
    st.success(f"🎉 Perfect! All {total_rows} videos transcribed successfully!")
elif success_count > 0:
    st.success(f"✅ Completed: {success_count} successful, {failed_count + rate_limited_count} failed/retryable out of {total_rows} total")
    if rate_limited_count > 0:
        st.warning(f"⚠️ {rate_limited_count} videos hit rate limits. Wait 1-2 minutes and try again with just the failed videos.")

        # Show details of rate limited requests
        rate_limited_items = [s for s in status_data if "Rate limited" in s.get("Error", "") or "429" in str(s.get("Status Code", ""))]
        if rate_limited_items:
            with st.expander(f"📋 Details of {len(rate_limited_items)} Rate Limited Requests"):
                for item in rate_limited_items[:5]:  # Show first 5
                    st.write(f"• **{item['URL'][:60]}...** - {item.get('Raw Response', 'No response')[:100]}...")
                if len(rate_limited_items) > 5:
                    st.write(f"*... and {len(rate_limited_items) - 5} more*")
    if failed_count > 0:
        st.error(f"❌ {failed_count} videos had permanent failures (private/deleted videos or API errors).")
else:
    st.error(f"❌ All {total_rows} videos failed. Check your DEAPI_API_KEY and try again.")

# Show retry recommendations if there were failures
retryable_urls = []
failed_urls = []

for status_info in status_data:
    url = status_info["URL"]
    if url.endswith("..."):  # Remove truncation for clean URLs
        url = status_info["URL"].replace("...", "")
    if "⏸" in status_info["Status"]:  # Rate limited or network errors
        retryable_urls.append(url)
    elif "✗" in status_info["Status"]:  # Permanent failures
        failed_urls.append(url)

if retryable_urls:
    st.info(f"🔄 **Retryable failures ({len(retryable_urls)} videos):** These can be retried later. Rate limits typically reset in 10-15 minutes.")
    with st.expander("Click to copy retryable URLs"):
        retry_text = "\n".join(retryable_urls)
        st.code(retry_text, language=None)
        st.caption("Copy these URLs and paste them back into the input for retry.")

if failed_urls:
    st.warning(f"❌ **Permanent failures ({len(failed_urls)} videos):** These videos are likely private, deleted, or unsupported.")
    with st.expander("Failed URLs (for reference)"):
        failed_text = "\n".join(failed_urls)
        st.code(failed_text, language=None)

# Build comprehensive log text
log_lines = [
    f"Session: {session.session_id}",
    f"Session Directory: {session.session_dir}",
    f"Started: {datetime.now().isoformat()}",
    f"Pre-validation: {'Enabled' if pre_validate else 'Disabled'}",
    f"Total Rows After Validation: {total_rows}",
    f"Successful: {success_count}",
    f"Permanent Failures: {failed_count}",
    f"Retryable Failures: {rate_limited_count}",
    f"Skipped: {skipped_count}",
    f"Success Rate: {(success_count/total_rows*100):.1f}%" if total_rows > 0 else "N/A",
    "",
    "=" * 80,
    "DETAILED STATUS LOG",
    "=" * 80,
    "",
]

# Add each row's status
for status_info in status_data:
    log_lines.append(f"Row {status_info['Row']}: {status_info['URL']}")
    log_lines.append(f"  Status: {status_info['Status']}")
    log_lines.append(f"  Method: {status_info['Method']}")
    if status_info.get('Error') and status_info['Error'] != "-":
        log_lines.append(f"  Error: {status_info['Error']}")
    if status_info.get('Status Code') and status_info['Status Code'] != "N/A":
        log_lines.append(f"  HTTP Status: {status_info['Status Code']}")
    if status_info.get('Request ID') and status_info['Request ID'] != "N/A":
        log_lines.append(f"  Request ID: {status_info['Request ID']}")
    if status_info.get('Raw Response') and status_info['Raw Response'] != "N/A":
        raw_resp = status_info['Raw Response']
        if len(raw_resp) > 500:  # Truncate very long responses
            raw_resp = raw_resp[:497] + "..."
        log_lines.append(f"  Raw Server Response: {raw_resp}")
    log_lines.append("")

# Add summary
log_lines.extend([
    "=" * 80,
    "SUMMARY",
    "=" * 80,
    f"Session ID: {session.session_id}",
    f"Completed: {datetime.now().isoformat()}",
    f"Pre-validation: {'Enabled' if pre_validate else 'Disabled'}",
    f"Total Processed: {total_rows}",
    f"Successful: {success_count}",
    f"Permanent Failures: {failed_count}",
    f"Retryable Failures: {rate_limited_count}",
    f"Skipped: {skipped_count}",
    f"Success Rate: {(success_count/total_rows*100):.1f}%" if total_rows > 0 else "N/A",
])

log_text = "\n".join(log_lines)

# Write log file to session directory with timestamp
log_filename = f"session_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_filepath = os.path.join(session.session_dir, log_filename)
with open(log_filepath, "w", encoding="utf-8") as f:
    f.write(log_text)

st.info(f"📁 Log file saved: `{log_filename}` in session directory")

# Show final status table (once, at the end)
results_step = "5" if pre_validate else "4"
st.header(f"{results_step}) Results Summary")
df = pd.DataFrame(status_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Copy logs section
logs_step = "6" if pre_validate else "5"
st.header(f"{logs_step}) Copy Session Logs")
st.caption("Copy all session logs for debugging or record-keeping.")

# Display logs in expandable section
with st.expander("View Full Session Logs", expanded=True):
    st.code(log_text, language="text")

# Simple copy button using text area (more reliable than JavaScript)
st.text_area(
    "Select all and copy (Ctrl+A, Ctrl+C):",
    value=log_text,
    height=300,
    label_visibility="collapsed",
    key="log_text_area"
)

st.success("✅ Logs are also saved to file: " + log_filename)