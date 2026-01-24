#!/usr/bin/env python3
"""
Enhanced Bulk Transcribe with Live Status Updates

This is a proposed enhancement to pages/1_Bulk_Transcribe.py
that adds live status updates, global counters, and stop functionality.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import time

# Mock data for demonstration - replace with actual imports in real implementation
class MockSession:
    def __init__(self):
        self.youtube_dir = "mock/youtube"

class MockManager:
    def create_session(self):
        return MockSession()

# Enhanced processing function with live updates
def process_rows_with_live_updates(rows: List[Dict], deapi_key: Optional[str] = None):
    """
    Process rows with live status updates, global counters, and stop functionality.
    """

    total_rows = len(rows)
    processed_count = 0
    success_count = 0
    failed_count = 0
    stopped = False

    # Initialize session state for processing
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {
            'is_running': False,
            'should_stop': False,
            'current_idx': 0,
            'results': []
        }

    # Create UI elements
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("📊 Global Progress")
        global_progress = st.empty()
        global_stats = st.empty()

    with col2:
        st.subheader("🎯 Current Video")
        current_video_info = st.empty()
        current_video_meta = st.empty()

    with col3:
        st.subheader("⚡ Controls")
        stop_button = st.button(
            "🛑 STOP PROCESSING",
            type="secondary",
            help="Stop processing remaining videos. Already processed videos will be saved."
        )
        if stop_button:
            st.session_state.processing_status['should_stop'] = True
            st.rerun()

    # Live status table
    st.subheader("📋 Processing Status")
    status_table = st.empty()

    # Initialize status data
    status_data = []

    # Start processing
    st.session_state.processing_status['is_running'] = True

    for idx, row in enumerate(rows):
        if st.session_state.processing_status['should_stop']:
            stopped = True
            break

        row_index = row.get("_row_index", str(idx + 1))
        source_type = row.get("source_type", "").lower()
        youtube_url = row.get("youtube_url", "").strip()

        # Update current video info
        with current_video_info.container():
            st.write(f"**Processing:** {row_index}/{total_rows}")
            st.write(f"**URL:** {youtube_url[:60]}{'...' if len(youtube_url) > 60 else ''}")

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

        try:
            if source_type == "youtube" and youtube_url:
                # Step 1: Fetch metadata
                video_status["Status"] = "📊 Fetching metadata..."
                status_table.dataframe(pd.DataFrame([video_status] + status_data), use_container_width=True)

                try:
                    # Mock metadata fetch - replace with actual implementation
                    meta_title = f"Video Title {row_index}"
                    meta_duration = "10:30"
                    meta_channel = "Test Channel"

                    video_status.update({
                        "Title": meta_title[:30] + "..." if len(meta_title) > 30 else meta_title,
                        "Duration": meta_duration,
                        "Status": "🎙️ Getting transcript..."
                    })

                    # Update current video metadata display
                    with current_video_meta.container():
                        st.write(f"**Title:** {meta_title}")
                        st.write(f"**Duration:** {meta_duration}")
                        st.write(f"**Channel:** {meta_channel}")

                    # Update table
                    status_table.dataframe(pd.DataFrame([video_status] + status_data), use_container_width=True)

                except Exception as e:
                    video_status.update({
                        "Status": "❌ Metadata failed",
                        "Error": str(e)[:50]
                    })
                    failed_count += 1
                    processed_count += 1
                    status_data.insert(0, video_status)
                    continue

                # Step 2: Get transcript
                try:
                    # Mock transcript result - replace with actual implementation
                    transcript_success = idx % 3 != 2  # Simulate some failures
                    method = "deapi_vid2txt" if transcript_success else "failed"

                    elapsed = time.time() - start_time

                    if transcript_success:
                        video_status.update({
                            "Status": "✅ Success",
                            "Method": method,
                            "Time": f"{elapsed:.1f}s"
                        })
                        success_count += 1
                    else:
                        video_status.update({
                            "Status": "❌ Failed",
                            "Method": method,
                            "Error": "Rate limit exceeded" if idx > 20 else "API error",
                            "Time": f"{elapsed:.1f}s"
                        })
                        failed_count += 1

                except Exception as e:
                    elapsed = time.time() - start_time
                    video_status.update({
                        "Status": "❌ Error",
                        "Error": str(e)[:50],
                        "Time": f"{elapsed:.1f}s"
                    })
                    failed_count += 1

            else:
                video_status.update({
                    "Status": "⚠️ Skipped",
                    "Error": "Invalid source type or URL"
                })

        except Exception as e:
            elapsed = time.time() - start_time
            video_status.update({
                "Status": "💥 Crash",
                "Error": str(e)[:50],
                "Time": f"{elapsed:.1f}s"
            })
            failed_count += 1

        # Update counters
        processed_count += 1

        # Update global progress
        with global_progress.container():
            progress_pct = processed_count / total_rows
            st.progress(progress_pct)
            st.write(f"**Overall Progress:** {processed_count}/{total_rows} videos")

        with global_stats.container():
            st.metric("✅ Successful", success_count)
            st.metric("❌ Failed", failed_count)
            st.metric("⏳ Remaining", total_rows - processed_count)

        # Add to status table (most recent first)
        status_data.insert(0, video_status)
        status_table.dataframe(pd.DataFrame(status_data), use_container_width=True)

        # Rate limiting delay (mock)
        if idx < len(rows) - 1 and not stopped:
            delay = 2  # Much faster for demo, use 65 for production
            time.sleep(delay)

    # Final status
    st.session_state.processing_status['is_running'] = False
    st.session_state.processing_status['should_stop'] = False

    # Summary
    st.success("🎉 Processing Complete!"    st.write(f"**Final Results:** {success_count} successful, {failed_count} failed out of {processed_count} processed")

    if stopped:
        st.warning("⚠️ Processing was stopped by user. Already completed videos were saved.")

    return {
        'processed': processed_count,
        'successful': success_count,
        'failed': failed_count,
        'stopped': stopped
    }


# Mock data for testing
def create_mock_rows(count: int = 10) -> List[Dict]:
    """Create mock data for testing."""
    rows = []
    for i in range(count):
        rows.append({
            "_row_index": str(i + 1),
            "source_type": "youtube",
            "youtube_url": f"https://www.youtube.com/watch?v=VIDEO_ID_{i+1}",
            "title": f"Test Video {i+1}",
            "description": f"Description for video {i+1}"
        })
    return rows


# Demo function
def demo_live_updates():
    """Demo the live update functionality."""
    st.title("🎥 Enhanced Bulk Transcribe - Live Status Demo")

    st.write("This demo shows the proposed live status updates, global counters, and stop functionality.")

    if st.button("🚀 Start Demo Processing", type="primary"):
        rows = create_mock_rows(25)  # Process 25 videos for demo
        result = process_rows_with_live_updates(rows)

        st.write("---")
        st.write("**Processing Summary:**")
        st.json(result)


if __name__ == "__main__":
    demo_live_updates()