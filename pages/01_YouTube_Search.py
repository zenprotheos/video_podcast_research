"""YouTube Search Tool - Phase 1"""
import os
from datetime import datetime, date
from typing import List, Optional

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

from src.bulk_transcribe.youtube_search import (
    search_youtube,
    VideoSearchItem,
    SearchResult,
    get_search_filters_dict,
)
from src.bulk_transcribe.video_filter import filter_videos_by_relevance, FilteringResult
from src.bulk_transcribe.direct_input import parse_direct_input, create_search_result_from_items, DirectInputResult
from src.bulk_transcribe.metadata_transfer import video_search_item_to_dict


# Helper Functions
def _display_results_table(items, search_result, title_suffix="", show_checkboxes=True):
    """Display a results table with the given items."""
    if not items:
        st.info(f"No results found {title_suffix}")
        return

    # Results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Results Found {title_suffix}", len(items))
    with col2:
        st.metric("Total Available", f"{search_result.total_results:,}")
    with col3:
        st.metric("Showing", f"{search_result.results_per_page} per page")

    # Selection controls (only show if checkboxes are enabled)
    if show_checkboxes:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Select All", use_container_width=True, help="Select all videos for manual processing"):
                st.session_state.selected_video_ids = {item.video_id for item in items}
                st.session_state.selection_update_counter += 1
                st.rerun()
        with col2:
            if st.button("Clear All", use_container_width=True, help="Deselect all videos"):
                st.session_state.selected_video_ids.clear()
                st.session_state.selection_update_counter += 1
                st.rerun()
        with col3:
            selected_count = len(st.session_state.selected_video_ids)
            total_count = len(items)
            st.caption(f"{selected_count} of {total_count} videos selected")

    # Results table with interactive checkboxes - scrollable container for large lists
    with st.container(height=400):
        for item in items:
            # Create a row container
            with st.container():
                cols = st.columns([0.5, 1, 4, 2, 1.5, 3, 1]) if show_checkboxes else st.columns([1, 4, 2, 1.5, 3, 1])

                col_idx = 0

                # Checkbox column (only if enabled)
                if show_checkboxes:
                    with cols[col_idx]:
                        # Create unique key for each checkbox that includes update counter
                        checkbox_key = f"select_{item.video_id}_{st.session_state.selection_update_counter}"
                        # Checkbox state - sync with session state
                        new_state = st.checkbox(
                            "",
                            value=item.video_id in st.session_state.selected_video_ids,
                            key=checkbox_key,
                            label_visibility="collapsed",
                            help=f"Select {item.title[:30]}..."
                        )
                        # Sync with session state
                        if new_state:
                            st.session_state.selected_video_ids.add(item.video_id)
                        else:
                            st.session_state.selected_video_ids.discard(item.video_id)
                    col_idx += 1

                # Thumbnail
                with cols[col_idx]:
                    if item.thumbnail_url:
                        st.image(item.thumbnail_url, width=60)
                    else:
                        st.write("📺")
                col_idx += 1

                # Title
                with cols[col_idx]:
                    # Truncate long titles and prevent wrapping
                    title = item.title[:60] + "..." if len(item.title) > 60 else item.title
                    st.markdown(f"**{title}**", help=item.title)  # Full title in tooltip
                col_idx += 1

                # Channel
                with cols[col_idx]:
                    # Truncate channel names and prevent wrapping
                    channel = (item.channel_title or "Unknown")[:20] + "..." if len(item.channel_title or "Unknown") > 20 else (item.channel_title or "Unknown")
                    st.text(channel, help=item.channel_title or "Unknown")
                col_idx += 1

                # Published
                with cols[col_idx]:
                    st.text(item.published_at[:10] if item.published_at else "")
                col_idx += 1

                # Description
                with cols[col_idx]:
                    desc = item.description[:80] + "..." if len(item.description) > 80 else item.description
                    st.text(desc, help=item.description)  # Full description in tooltip
                col_idx += 1

                # URL
                with cols[col_idx]:
                    st.link_button("Watch", item.video_url, help=f"Watch {item.title[:30]}...")

                # Add some spacing between rows
                st.divider()


# Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "").strip()
if not YOUTUBE_API_KEY:
    st.error("❌ YouTube Data API key not found. Please set YOUTUBE_DATA_API_KEY in your .env file.")
    st.stop()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini")


st.set_page_config(page_title="YouTube Search - Bulk Transcribe", layout="wide")
st.title("🔍 YouTube Search Tool")

# Initialize session state early
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'current_page_token' not in st.session_state:
    st.session_state.current_page_token = None
if 'search_filters' not in st.session_state:
    st.session_state.search_filters = get_search_filters_dict()
if 'research_context' not in st.session_state:
    st.session_state.research_context = ""
if 'ai_filtering_enabled' not in st.session_state:
    st.session_state.ai_filtering_enabled = False
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = OPENROUTER_DEFAULT_MODEL
if 'filtered_results' not in st.session_state:
    st.session_state.filtered_results = None

# Direct input session state
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "search"  # "search" or "direct"
if 'direct_input_raw' not in st.session_state:
    st.session_state.direct_input_raw = ""
if 'direct_input_videos' not in st.session_state:
    st.session_state.direct_input_videos = None

# Selection state for manual video selection
if 'selected_video_ids' not in st.session_state:
    st.session_state.selected_video_ids = set()
if 'selection_update_counter' not in st.session_state:
    st.session_state.selection_update_counter = 0

# Initialize UI variables (needed for conditional rendering)
research_context = st.session_state.research_context
ai_filtering_enabled = st.session_state.ai_filtering_enabled
selected_model = st.session_state.selected_model

# Input Mode Selection
st.subheader("Input Mode")
input_mode = st.radio(
    "Choose how to provide video data:",
    ["🔍 Search YouTube", "📝 Direct Input"],
    index=0 if getattr(st.session_state, 'input_mode', 'search') == "search" else 1,
    horizontal=True,
    help="Search YouTube using the API or paste URLs/JSON data directly"
)

# Update session state
st.session_state.input_mode = "search" if input_mode == "🔍 Search YouTube" else "direct"

# Note: has_videos is checked dynamically to avoid stale state issues

# Step 1: Data Input Section
videos_loaded = st.session_state.search_results is not None and st.session_state.search_results.items
step1_icon = "✅" if videos_loaded else "📥"
st.header(f"{step1_icon} Step 1: Choose Input Method & Provide Data")

# Input method selection and data input UI
input_method_container = st.container()

with input_method_container:
    if st.session_state.input_mode == "search":
        # Search input
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "Search Query:",
                value=st.session_state.search_query,
                placeholder="Enter YouTube search terms...",
                help="Search for videos on YouTube"
            )

        with col2:
            search_button = st.button("🔍 Search YouTube", type="primary", use_container_width=True)

        # Update session state
        st.session_state.search_query = search_query

    else:  # Direct Input mode
        st.subheader("📝 Direct Input Data")

        direct_input_text = st.text_area(
            "Paste your video data:",
            value=st.session_state.direct_input_raw,
            height=200,
            placeholder="""Choose one of these formats:

📄 URLs (one per line):
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2

📋 OR JSON array:
[
  {
    "video_id": "VIDEO_ID",
    "title": "Video Title",
    "channel_title": "Channel Name",
    "description": "Video description...",
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID"
  }
]""",
            help="Paste YouTube URLs (one per line) or a JSON array of video objects. The system will auto-detect the format."
        )

        # Update session state
        st.session_state.direct_input_raw = direct_input_text

        # Process button
        if st.button("🔄 Process Input", type="primary", use_container_width=True):
            if direct_input_text.strip():
                with st.spinner("Processing your input..."):
                    try:
                        result = parse_direct_input(direct_input_text)

                        if result.success:
                            # Create SearchResult for UI consistency
                            search_result = create_search_result_from_items(result.videos)
                            st.session_state.search_results = search_result
                            st.session_state.direct_input_videos = result.videos

                            # Show success message
                            st.success(f"✅ Successfully processed {len(result.videos)} videos from your input")

                            # Show warnings if any
                            if result.warnings:
                                with st.expander("⚠️ Warnings", expanded=False):
                                    for warning in result.warnings:
                                        st.warning(warning)

                            # Clear filtered results and selection when new input is processed
                            st.session_state.filtered_results = None
                            st.session_state.selected_video_ids.clear()
                            st.session_state.selection_update_counter += 1

                            # Trigger rerun to show next steps
                            st.rerun()

                        else:
                            # Show errors
                            for error in result.errors:
                                st.error(error)

                            st.session_state.search_results = None
                            st.session_state.direct_input_videos = None

                    except Exception as e:
                        st.error(f"❌ Processing failed: {str(e)}")
                        st.session_state.search_results = None
                        st.session_state.direct_input_videos = None
            else:
                st.warning("Please enter some video data to process")

# Handle search button click (moved from later in the code)
if 'search_button' in locals() and search_button and search_query.strip():
    with st.spinner("Searching YouTube..."):
        try:
            # Prepare search parameters
            search_params = {
                'query': search_query.strip(),
                'api_key': YOUTUBE_API_KEY,
                'max_results': 50,  # Default for now
                'order': 'relevance',
                'type': 'video',
            }

            # Execute search
            search_result = search_youtube(**search_params)

            # Store results in session state
            st.session_state.search_results = search_result
            st.session_state.search_query = search_query
            st.session_state.current_page_token = None
            st.session_state.search_filters = get_search_filters_dict()
            # Clear previous selections and filtered results for new search
            st.session_state.selected_video_ids.clear()
            st.session_state.filtered_results = None
            st.session_state.selection_update_counter += 1

            st.success(f"✅ Found {len(search_result.items)} results")
            st.rerun()  # Show next steps

        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            st.session_state.search_results = None

st.divider()

# This section has been moved to Step 1 above

# Step 2: Research Configuration (only show after data is loaded)
if st.session_state.search_results is not None:
    research_configured = st.session_state.research_context.strip() or st.session_state.ai_filtering_enabled
    step2_icon = "✅" if research_configured else "🎯"
    st.header(f"{step2_icon} Step 2: Configure AI Research (Optional)")

    with st.expander("🤖 AI Research Context & Filtering", expanded=True):
        research_context = st.text_area(
            "Research Context/Goal:",
            value=st.session_state.research_context,
            height=80,
            placeholder="Describe your research goal or context (optional, but recommended for AI filtering). For example: 'Finding videos about AI entrepreneurship and startup strategies for 2026'",
            help="This context helps the AI understand what you're researching, enabling smarter video filtering"
        )

        # AI Filtering Toggle
        ai_filtering_enabled = st.checkbox(
            "🤖 Enable AI Filtering",
            value=st.session_state.ai_filtering_enabled,
            help="Use AI to automatically filter videos based on relevance to your research context"
        )

        # Model Selection (only when AI filtering is enabled)
        if ai_filtering_enabled:
            col1, col2 = st.columns([3, 1])

            with col1:
                model_options = ["openai/gpt-4o-mini", "anthropic/claude-haiku-4.5", "meta-llama/llama-3.2-3b-instruct", "Custom"]
                selected_model_option = st.selectbox(
                    "AI Model:",
                    model_options,
                    index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0,
                        help="Choose the AI model for video relevance filtering. Free models may have limits. OpenAI models are generally reliable. See https://openrouter.ai/models for all available options."
                )

            with col2:
                if selected_model_option == "Custom":
                    custom_model = st.text_input(
                        "Custom Model:",
                        value=st.session_state.selected_model if st.session_state.selected_model not in model_options[:-1] else "",
                        placeholder="e.g., openai/gpt-4, anthropic/claude-3-haiku",
                        help="Enter custom OpenRouter model identifier. Must be in format 'provider/model-name'. Check https://openrouter.ai/models for available options."
                    )
                    selected_model = custom_model.strip()

                    # Validate custom model input
                    if not selected_model:
                        st.error("❌ Please enter a custom model name when selecting 'Custom'.")
                        selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                    elif not "/" in selected_model:
                        st.error("❌ Custom model must be in format 'provider/model-name' (e.g., 'openai/gpt-4').")
                        selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                    else:
                        st.info(f"ℹ️ Using custom model: {selected_model}")
                else:
                    selected_model = selected_model_option
        else:
            selected_model = OPENROUTER_DEFAULT_MODEL

        # Update session state
        st.session_state.research_context = research_context
        st.session_state.ai_filtering_enabled = ai_filtering_enabled
        st.session_state.selected_model = selected_model

    st.divider()
else:
    # Placeholder for when no videos are loaded yet
    if st.session_state.input_mode == "search":
        st.info("👆 Enter a search query above and click 'Search YouTube' to load videos, then configure AI research options.")
    else:
        st.info("👆 Paste your video data above and click 'Process Input' to load videos, then configure AI research options.")

# Advanced search filters removed for simplified flow

# Step 3: Results & Actions (only show when videos are loaded)
if st.session_state.search_results is not None:
    filtered = st.session_state.filtered_results is not None and st.session_state.filtered_results.success
    step3_icon = "✅" if filtered else "📊"
    st.header(f"{step3_icon} Step 3: Results & Actions")

    # Status indicator
    status_container = st.empty()

# Initialize results container
results_container = st.container()

# Display results if available
if st.session_state.search_results:
    search_result = st.session_state.search_results

    # Determine which results to show
    show_filtered = st.session_state.filtered_results is not None and st.session_state.filtered_results.success

    if show_filtered:
        # Show tabs for All Results vs Shortlisted Results
        tab1, tab2 = st.tabs(["📋 All Results", "🎯 Shortlisted Results"])

        with tab1:
            _display_results_table(search_result.items, search_result, title_suffix="(All Results)", show_checkboxes=True)

        with tab2:
            filtered_result = st.session_state.filtered_results
            _display_results_table(filtered_result.relevant_videos, search_result, title_suffix="(AI Filtered)", show_checkboxes=False)

            # Show filtering summary
            st.info(f"🤖 AI filtered {filtered_result.total_processed} videos based on your research context. "
                   f"Found {len(filtered_result.relevant_videos)} relevant videos.")

    else:
        # Show all results only
        _display_results_table(search_result.items, search_result, show_checkboxes=True)

        # Show hint about AI filtering if enabled but not yet filtered
        if st.session_state.ai_filtering_enabled and not st.session_state.research_context.strip():
            st.info("💡 Add research context above and click 'Filter Videos with AI' to automatically shortlist relevant videos.")
        elif st.session_state.ai_filtering_enabled and st.session_state.research_context.strip():
            st.info("💡 Click 'Filter Videos with AI' in the Actions section below to automatically shortlist relevant videos.")

    # Add pagination controls for All Results tab when filtered results exist
    if show_filtered and search_result.items:
        # Pagination controls (only for All Results)
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if search_result.prev_page_token:
                if st.button("⬅️ Previous Page (All Results)"):
                    with st.spinner("Loading previous page..."):
                        try:
                            # Get previous page
                            search_params = st.session_state.search_filters.copy()
                            search_params.update({
                                'query': st.session_state.search_query,
                                'api_key': YOUTUBE_API_KEY,
                                'page_token': search_result.prev_page_token,
                            })

                            new_result = search_youtube(**search_params)
                            st.session_state.search_results = new_result
                            st.session_state.current_page_token = search_result.prev_page_token
                            # Clear filtered results and selections when paginating
                            st.session_state.filtered_results = None
                            st.session_state.selected_video_ids.clear()
                            st.session_state.selection_update_counter += 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load previous page: {str(e)}")

        with col3:
            if search_result.next_page_token:
                if st.button("Next Page (All Results) ➡️"):
                    with st.spinner("Loading next page..."):
                        try:
                            # Get next page
                            search_params = st.session_state.search_filters.copy()
                            search_params.update({
                                'query': st.session_state.search_query,
                                'api_key': YOUTUBE_API_KEY,
                                'page_token': search_result.next_page_token,
                            })

                            new_result = search_youtube(**search_params)
                            st.session_state.search_results = new_result
                            st.session_state.current_page_token = search_result.next_page_token
                            # Clear filtered results and selections when paginating
                            st.session_state.filtered_results = None
                            st.session_state.selected_video_ids.clear()
                            st.session_state.selection_update_counter += 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load next page: {str(e)}")

    # Actions Section (part of Step 3) - moved inside results condition
    # AI Filter Button (appears when AI filtering is enabled and context provided)
    if st.session_state.ai_filtering_enabled and st.session_state.research_context.strip():
        if st.button("🤖 Filter Videos with AI", type="secondary", use_container_width=True):
            with st.spinner("🤖 AI is evaluating video relevance..."):
                try:
                    # Call the filtering function
                    search_results = st.session_state.search_results
                    if search_results and hasattr(search_results, 'items') and search_results.items:
                        filter_result = filter_videos_by_relevance(
                            videos=search_results.items,
                            search_query=st.session_state.search_query,
                            research_context=st.session_state.research_context.strip(),
                            model=st.session_state.selected_model,
                            api_key=OPENROUTER_API_KEY
                        )

                        # Store filtered results in session state
                        st.session_state.filtered_results = filter_result
                    else:
                        st.error("No videos available for filtering")
                        filter_result = None
                        st.session_state.filtered_results = None

                    if filter_result.success:
                        st.success(f"✅ Filtered {filter_result.total_processed} videos: {len(filter_result.relevant_videos)} relevant, {len(filter_result.filtered_out_videos)} filtered out")
                        st.rerun()  # Refresh to show filtered results
                    else:
                        st.error(f"❌ Filtering failed: {filter_result.error_message}")

                except Exception as e:
                    st.error(f"❌ AI filtering error: {str(e)}")
                    if "API key" in str(e).lower():
                        st.info("💡 Make sure OPENROUTER_API_KEY is set in your .env file")

        st.divider()  # Visual separator

    # Get selected videos (this is a simplified version - in practice we'd need proper checkbox state management)
    # For now, we'll provide copy options for all results

    col1, col2, col3, col4 = st.columns(4)

    # Determine which videos to use for actions (filtered, selected, or all)
    search_results = st.session_state.search_results
    if search_results and hasattr(search_results, 'items') and search_results.items:
        # Check if user has manually selected videos
        if st.session_state.selected_video_ids:
            # Use manually selected videos
            action_videos = [item for item in search_results.items if item.video_id in st.session_state.selected_video_ids]
            action_source = "youtube_search_selected"
            action_label = "Selected"
        else:
            # No manual selection, use all videos
            action_videos = search_results.items
            action_source = "youtube_search"
            action_label = "All"
    else:
        action_videos = []
        action_source = "youtube_search"
        action_label = "All"

    # Override with filtered results if they exist (AI filtering takes precedence)
    if st.session_state.filtered_results and st.session_state.filtered_results.success:
        action_videos = st.session_state.filtered_results.relevant_videos
        action_source = "youtube_search_filtered"
        action_label = "Shortlisted"

    with col1:
        if st.button(f"📋 Copy {action_label} URLs", use_container_width=True):
            urls = [item.video_url for item in action_videos]
            urls_text = "\n".join(urls)
            st.code(urls_text, language=None)
            st.success(f"✅ Copied {len(urls)} {action_label.lower()} URLs to clipboard (select and copy the code block above)")

    with col2:
        if st.button(f"🔢 Copy {action_label} IDs", use_container_width=True):
            ids = [item.video_id for item in action_videos]
            ids_text = ",".join(ids)
            st.code(ids_text, language=None)
            st.success(f"✅ Copied {len(ids)} {action_label.lower()} video IDs to clipboard (select and copy the code block above)")

    with col3:
        if st.button(f"📄 Copy {action_label} as JSON", use_container_width=True):
            import json
            results_data = []
            for item in action_videos:
                results_data.append({
                    "video_id": item.video_id,
                    "title": item.title,
                    "channel_title": item.channel_title,
                    "published_at": item.published_at,
                    "video_url": item.video_url,
                    "description": item.description[:200] + "..." if len(item.description) > 200 else item.description,
                })
            json_text = json.dumps(results_data, indent=2, ensure_ascii=False)
            st.code(json_text, language="json")
            st.success(f"✅ Copied {len(results_data)} {action_label.lower()} results as JSON to clipboard (select and copy the code block above)")

    with col4:
        if st.button(f"📝 Send {action_label} to Transcript Tool", type="primary", use_container_width=True):
            # Send videos to transcript tool with rich metadata
            urls = [item.video_url for item in action_videos]

            # Preserve full metadata for enhanced experience
            metadata_list = [video_search_item_to_dict(item) for item in action_videos]

            st.session_state['transcript_urls'] = urls  # Backward compatibility
            st.session_state['transcript_metadata'] = metadata_list  # Rich metadata
            st.session_state['transcript_source'] = action_source

            st.success(f"✅ Prepared {len(urls)} {action_label.lower()} videos for transcription with rich metadata")
            st.page_link(
                "pages/02_Bulk_Transcribe.py",
                label="Go to Transcript Tool →",
                help="Continue to the transcript tool with selected videos"
            )

# Phase 2 Placeholder
st.header("🤖 AI Agent Mode (Phase 2 - Coming Soon)")

with st.expander("🚀 Future Features", expanded=False):
    st.info("""
    **Phase 2 will enable AI-powered research workflows:**

    🔍 **Multiple Query Generation**: AI generates comprehensive search queries for thorough research

    📊 **Bulk Processing**: Automatically fetch transcripts for hundreds of videos

    🤖 **Intelligent Selection**: AI ranks and filters videos by relevance before transcription

    📈 **Deep Analysis**: Automated summarization and insights extraction from transcripts

    🔄 **Iterative Research**: AI refines searches based on initial findings

    This will transform the tool from manual search to automated research assistant.
    """)

    st.button("🚀 Enable AI Agent Mode", disabled=True, help="Available in Phase 2")

# Footer
st.markdown("---")
st.caption("YouTube Search Tool - Phase 1 | Built with YouTube Data API v3")

# Function moved to top of file after imports