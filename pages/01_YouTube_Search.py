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
from src.bulk_transcribe.query_planner import plan_search_queries
from src.bulk_transcribe.direct_input import parse_direct_input, create_search_result_from_items, DirectInputResult
from src.bulk_transcribe.metadata_transfer import video_search_item_to_dict, validate_metadata_list


# Helper Functions
def _display_results_table(items, search_result, title_suffix="", show_checkboxes=True, include_query_source=False, key_prefix=None):
    """Display a results table with the given items."""
    if not items:
        st.info(f"No results found {title_suffix}")
        return

    total_available = search_result.total_results if getattr(search_result, "total_results", None) is not None else len(items)
    results_per_page = search_result.results_per_page if getattr(search_result, "results_per_page", None) is not None else len(items)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"Results Found {title_suffix}", len(items))
    with col2:
        st.metric("Total Available", f"{total_available:,}")
    with col3:
        st.metric("Showing", f"{results_per_page} per page")

    prefix = key_prefix or "results_table"
    if show_checkboxes:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Select All", key=f"{prefix}_select_all", use_container_width=True, help="Select all videos for manual processing"):
                st.session_state.selected_video_ids = {item.video_id for item in items}
                st.session_state.selection_update_counter += 1
                st.rerun()
        with col2:
            if st.button("Clear All", key=f"{prefix}_clear_all", use_container_width=True, help="Deselect all videos"):
                st.session_state.selected_video_ids.clear()
                st.session_state.selection_update_counter += 1
                st.rerun()
        with col3:
            selected_count = len(st.session_state.selected_video_ids)
            total_count = len(items)
            st.caption(f"{selected_count} of {total_count} videos selected")

    column_weights = [0.5, 1, 4, 2, 1.5, 3, 1]
    if include_query_source:
        column_weights.append(1.5)

    with st.container(height=400):
        for item in items:
            with st.container():
                cols = st.columns(column_weights if show_checkboxes else column_weights[1:])
                col_idx = 0

                if show_checkboxes:
                    with cols[col_idx]:
                        checkbox_key = f"{prefix}_select_{item.video_id}_{st.session_state.selection_update_counter}"
                        new_state = st.checkbox(
                            f"Select {item.title[:50]}",
                            value=item.video_id in st.session_state.selected_video_ids,
                            key=checkbox_key,
                            label_visibility="collapsed",
                            help=f"Select {item.title[:30]}..."
                        )
                        if new_state:
                            st.session_state.selected_video_ids.add(item.video_id)
                        else:
                            st.session_state.selected_video_ids.discard(item.video_id)
                    col_idx += 1

                with cols[col_idx]:
                    if item.thumbnail_url:
                        st.image(item.thumbnail_url, width=60)
                    else:
                        st.write("Video")
                col_idx += 1

                with cols[col_idx]:
                    title = item.title[:60] + "..." if len(item.title) > 60 else item.title
                    st.markdown(f"**{title}**", help=item.title)
                col_idx += 1

                with cols[col_idx]:
                    channel = (item.channel_title or "Unknown")[:20] + "..." if len(item.channel_title or "Unknown") > 20 else (item.channel_title or "Unknown")
                    st.text(channel, help=item.channel_title or "Unknown")
                col_idx += 1

                with cols[col_idx]:
                    st.text(item.published_at[:10] if item.published_at else "")
                col_idx += 1

                with cols[col_idx]:
                    desc = item.description[:80] + "..." if len(item.description) > 80 else item.description
                    st.text(desc, help=item.description)
                col_idx += 1

                with cols[col_idx]:
                    st.link_button("Watch", item.video_url, help=f"Watch {item.title[:30]}...")
                col_idx += 1

                if include_query_source:
                    with cols[col_idx]:
                        sources = getattr(item, "query_sources", []) or []
                        st.caption(", ".join(sources) if sources else "–")
                    col_idx += 1

                st.divider()


def _get_planned_query_summary_data(search_result=None):
    runs = st.session_state.get('planned_query_runs', [])
    planned_queries = st.session_state.get('planned_queries', [])
    total_queries_planned = len(planned_queries)
    status_counts = {
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "no_results": 0,
    }
    for run in runs:
        status = (run.get('status') or 'queued').lower()
        if status not in status_counts:
            status = 'queued'
        status_counts[status] += 1

    total_fetched = sum(run.get('fetched_results', 0) for run in runs)
    total_requested = sum(run.get('requested_results', 0) for run in runs)
    pages_completed = sum(run.get('pages_completed', 0) for run in runs)
    all_results = len(search_result.items) if search_result and getattr(search_result, "items", None) else 0
    deduplicated = all_results

    return {
        "runs": runs,
        "planned_queries": planned_queries,
        "total_queries_planned": total_queries_planned,
        "status_counts": status_counts,
        "total_fetched": total_fetched,
        "total_requested": total_requested,
        "pages_completed": pages_completed,
        "deduplicated": deduplicated,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _render_planned_query_summary(status_container, search_result=None, summary_data=None):
    summary = summary_data or _get_planned_query_summary_data(search_result)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total queries planned", summary["total_queries_planned"])
    col2.metric(
        "Queries completed",
        f"{summary['status_counts']['completed']} / {summary['total_queries_planned'] or 1}",
    )
    col3.metric("Total results fetched", f"{summary['total_fetched']:,}")
    col4.metric("Deduplicated results", f"{summary['deduplicated']:,}")

    st.caption(
        "Status breakdown: "
        f"Queued {summary['status_counts']['queued']} • Running {summary['status_counts']['running']} • "
        f"Failed {summary['status_counts']['failed']} • No results {summary['status_counts']['no_results']}"
    )
    if status_container:
        target_display = f"{summary['total_requested']:,}" if summary['total_requested'] else "–"
        status_container.caption(
            f"Results fetched: {summary['total_fetched']} of {target_display} requested • "
            f"Pages completed: {summary['pages_completed']}"
        )
    st.caption(f"Last updated: {summary['last_updated']}")

    if not summary["runs"]:
        st.info(
            "Run planned queries to populate per-query summaries and navigation tabs. "
            "Aggregate results (if any) still appear below."
        )


def _build_query_tab_label(index: int, query_text: str, max_length: int = 30) -> str:
    trimmed = query_text.strip()
    if len(trimmed) > max_length:
        trimmed = trimmed[: max_length - 3] + "..."
    return f"Query {index + 1}: {trimmed}"


def _derive_aggregate_status(summary_data: dict) -> str:
    total = summary_data["total_queries_planned"]
    if total == 0:
        return "Idle"
    if summary_data["status_counts"]["failed"]:
        return "Failed"
    if summary_data["status_counts"]["running"]:
        return "Running"
    if summary_data["status_counts"]["queued"]:
        return "Queued"
    return "Completed"


def _render_status_strip(label: str, status: str, fetched: int, target: int, pages: int, max_pages: int, errors=None):
    target_display = f"{target:,}" if target else "–"
    pages_display = f"{pages}/{max_pages or '–'}"
    st.caption(
        f"{label} • Status: {status.capitalize()} • "
        f"Results: {fetched} of {target_display} • Pages: {pages_display}"
    )
    if errors:
        normalized = errors if isinstance(errors, list) else [errors]
        st.warning("Errors: " + " | ".join(str(item) for item in normalized))


def _render_cap_notice(run_data: dict):
    requested = run_data.get("requested_results")
    fetched = run_data.get("fetched_results")
    if requested and fetched >= requested:
        st.info(
            f"Showing {fetched} of {requested} results for this query (per-query cap reached). "
            "Adjust the max results/page or max pages in Step 1 to fetch more."
        )


def _filter_results_by_query(items, query_text: str):
    if not query_text:
        return []
    normalized = query_text.strip().lower()
    filtered = []
    for item in items:
        sources = getattr(item, "query_sources", []) or []
        if any(normalized == source.strip().lower() for source in sources):
            filtered.append(item)
        elif getattr(item, "query_text", None) and normalized == item.query_text.strip().lower():
            filtered.append(item)
    return filtered


def _get_query_source_breakdown(items):
    """
    Analyze query source distribution in a list of videos.
    
    Returns:
        dict mapping query text to count of videos from that query
    """
    breakdown = {}
    for item in items:
        sources = getattr(item, "query_sources", []) or []
        for source in sources:
            breakdown[source] = breakdown.get(source, 0) + 1
    return breakdown


def _retry_planned_query(query_index: int):
    planned_queries = st.session_state.planned_queries[: st.session_state.planned_queries_to_run]
    if query_index >= len(planned_queries):
        st.warning("Query no longer available.")
        return

    query_text = planned_queries[query_index].strip()
    if not query_text:
        st.warning("Cannot retry an empty query.")
        return

    if query_index >= len(st.session_state.planned_query_runs):
        st.warning("No run record available for this query.")
        return

    run_data = st.session_state.planned_query_runs[query_index]
    run_data["status"] = "running"
    run_data["errors"] = []
    run_data["results"] = []
    run_data["pages_completed"] = 0
    run_data["fetched_results"] = 0

    existing_items = st.session_state.search_results.items if st.session_state.search_results else []
    aggregated_items = list(existing_items)
    seen_video_ids = {item.video_id for item in aggregated_items}

    try:
        with st.spinner(f"Retrying Query {query_index + 1}..."):
            page_token = None
            for _ in range(st.session_state.max_pages_per_query):
                search_result = search_youtube(
                    query=query_text,
                    api_key=YOUTUBE_API_KEY,
                    max_results=st.session_state.max_results_per_page,
                    order='relevance',
                    type='video',
                    page_token=page_token,
                )
                run_data["pages_completed"] += 1
                run_data["fetched_results"] += len(search_result.items)
                run_data["results"].extend(search_result.items)

                for item in search_result.items:
                    if item.video_id not in seen_video_ids:
                        aggregated_items.append(item)
                        seen_video_ids.add(item.video_id)
                    else:
                        # Merge query_sources for duplicate videos
                        existing_item = next(
                            (x for x in aggregated_items if x.video_id == item.video_id),
                            None
                        )
                        if existing_item:
                            # Merge query_sources, avoiding duplicates
                            existing_sources = set(existing_item.query_sources or [])
                            new_sources = set(item.query_sources or [])
                            existing_item.query_sources = sorted(list(existing_sources | new_sources))
                page_token = search_result.next_page_token
                if not page_token:
                    break

            run_data["status"] = "completed"
            st.session_state.search_results = SearchResult(
                items=aggregated_items,
                total_results=len(aggregated_items),
                results_per_page=st.session_state.max_results_per_page,
                next_page_token=None,
                prev_page_token=None,
            )
            st.session_state.planned_query_runs[query_index] = run_data
            st.success(f"Query {query_index + 1} retried successfully.")
            st.experimental_rerun()
    except Exception as retry_error:
        run_data["status"] = "failed"
        run_data["errors"].append(str(retry_error))
        st.session_state.planned_query_runs[query_index] = run_data
        st.error(f"Retry failed: {retry_error}")


def _render_query_progress(summary_data: dict):
    planned_queries = summary_data.get("planned_queries", [])
    if not planned_queries:
        return

    with st.expander("Query execution progress", expanded=False):
        for idx, run_data in enumerate(summary_data.get("runs", [])):
            text = run_data.get("text", f"Query {idx + 1}")
            status = run_data.get("status", "queued").capitalize()
            pages_done = run_data.get("pages_completed", 0)
            max_pages = run_data.get("max_pages", st.session_state.max_pages_per_query)
            fetched = run_data.get("fetched_results", 0)
            target = run_data.get("requested_results", st.session_state.max_results_per_page * max_pages)

            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**Query {idx + 1}:** {text}")
            with col2:
                st.caption(f"Status: {status} | Pages: {pages_done}/{max_pages} | Results: {fetched}/{target}")
            with col3:
                if st.button(f"Highlight Query {idx + 1}", key=f"progress_focus_{idx}"):
                    st.session_state.focused_query_tab = idx + 1


# Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "").strip()
if not YOUTUBE_API_KEY:
    st.error("YouTube Data API key not found. Please set YOUTUBE_DATA_API_KEY in your .env file.")
    st.stop()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini")


st.set_page_config(page_title="YouTube Search - Bulk Transcribe", layout="wide")
st.title("YouTube Search Tool")

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
if 'planned_queries' not in st.session_state:
    st.session_state.planned_queries = []
if 'planned_queries_text' not in st.session_state:
    st.session_state.planned_queries_text = ""
if 'query_planner_model' not in st.session_state:
    st.session_state.query_planner_model = OPENROUTER_DEFAULT_MODEL
if 'query_plan_max_queries' not in st.session_state:
    st.session_state.query_plan_max_queries = 5
if 'planned_queries_to_run' not in st.session_state:
    st.session_state.planned_queries_to_run = 5
if 'query_planner_prompt' not in st.session_state:
    st.session_state.query_planner_prompt = ""
if 'query_planner_notes' not in st.session_state:
    st.session_state.query_planner_notes = ""
if 'max_results_per_page' not in st.session_state:
    st.session_state.max_results_per_page = 50
if 'max_pages_per_query' not in st.session_state:
    st.session_state.max_pages_per_query = 1
if 'search_execution_mode' not in st.session_state:
    st.session_state.search_execution_mode = "single"
if 'planned_query_runs' not in st.session_state:
    st.session_state.planned_query_runs = []
if 'focused_query_tab' not in st.session_state:
    st.session_state.focused_query_tab = None

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
    ["Search YouTube", "Direct Input"],
    index=0 if getattr(st.session_state, 'input_mode', 'search') == "search" else 1,
    horizontal=True,
    help="Search YouTube using the API or paste URLs/JSON data directly"
)

# Update session state
st.session_state.input_mode = "search" if input_mode == "Search YouTube" else "direct"

# Note: has_videos is checked dynamically to avoid stale state issues

# Step 0: Query Planning (optional, search mode only)
if st.session_state.input_mode == "search":
    st.header("Step 0: Plan search queries (optional)")
    st.caption("Provide the research prompt and generate distinct YouTube search queries.")

    research_prompt = st.text_area(
        "Research prompt",
        value=st.session_state.query_planner_prompt,
        height=140,
        placeholder="Describe the research goal, audience, and the kinds of videos you want to find.",
        help="This prompt is used to generate diverse, comprehensive search queries.",
    )
    st.session_state.query_planner_prompt = research_prompt

    research_notes = st.text_area(
        "Optional guidance for the planner",
        value=st.session_state.query_planner_notes,
        height=80,
        placeholder="Add constraints, exclusions, or specific subtopics to emphasize.",
        help="Use this field to refine the generated queries.",
    )
    st.session_state.query_planner_notes = research_notes

    with st.expander("Query planning settings", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            model_options = [
                "openai/gpt-4o-mini",
                "anthropic/claude-haiku-4.5",
                "meta-llama/llama-3.2-3b-instruct",
                "Custom",
            ]
            selected_model_option = st.selectbox(
                "Planner model",
                model_options,
                index=model_options.index(st.session_state.query_planner_model)
                if st.session_state.query_planner_model in model_options
                else 0,
                help="Choose the model to generate search queries.",
            )
        with col2:
            max_queries = st.number_input(
                "Max queries",
                min_value=1,
                max_value=10,
                value=st.session_state.query_plan_max_queries,
                step=1,
                help="Limit how many queries the planner will return.",
            )

        if selected_model_option == "Custom":
            custom_model = st.text_input(
                "Custom planner model",
                value=st.session_state.query_planner_model
                if st.session_state.query_planner_model not in model_options[:-1]
                else "",
                placeholder="e.g., openai/gpt-4, anthropic/claude-3-haiku",
                help="Enter a custom OpenRouter model identifier.",
            )
            query_planner_model = custom_model.strip()
        else:
            query_planner_model = selected_model_option

        st.session_state.query_plan_max_queries = max_queries
        st.session_state.query_planner_model = query_planner_model

    generate_queries = st.button("Generate search queries", use_container_width=True)
    if generate_queries:
        if not st.session_state.query_planner_prompt.strip():
            st.warning("Enter a research prompt before generating queries.")
        elif not OPENROUTER_API_KEY:
            st.error("OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env.")
        else:
            with st.spinner("Generating search queries..."):
                messages = [{"role": "user", "content": st.session_state.query_planner_prompt.strip()}]
                if st.session_state.query_planner_notes.strip():
                    messages.append(
                        {"role": "user", "content": f"Additional guidance: {st.session_state.query_planner_notes.strip()}"}
                    )
                result = plan_search_queries(
                    messages=messages,
                    model=st.session_state.query_planner_model,
                    api_key=OPENROUTER_API_KEY,
                    max_queries=st.session_state.query_plan_max_queries,
                )
                if result.success:
                    st.session_state.planned_queries = result.queries
                    st.session_state.planned_queries_text = "\n".join(result.queries)
                    st.success(f"Generated {len(result.queries)} queries.")
                else:
                    st.error(f"Query planning failed: {result.error_message}")

    planned_queries_text = st.text_area(
        "Planned queries (one per line):",
        value=st.session_state.planned_queries_text,
        height=140,
        help="Review and edit the planned queries. One query per line.",
    )
    st.session_state.planned_queries_text = planned_queries_text
    st.session_state.planned_queries = [
        line.strip()
        for line in planned_queries_text.splitlines()
        if line.strip()
    ]

    if st.session_state.planned_queries:
        st.session_state.planned_queries_to_run = st.number_input(
            "Queries to run",
            min_value=1,
            max_value=len(st.session_state.planned_queries),
            value=min(st.session_state.planned_queries_to_run, len(st.session_state.planned_queries)),
            step=1,
            help="Limit how many planned queries to execute.",
        )
        if st.button("Clear planned queries", use_container_width=True):
            st.session_state.planned_queries = []
            st.session_state.planned_queries_text = ""
            st.session_state.planned_queries_to_run = 1
            st.rerun()

    st.divider()

# Step 1: Data Input Section
videos_loaded = st.session_state.search_results is not None and st.session_state.search_results.items
st.header("Step 1: Choose Input Method & Provide Data")

# Input method selection and data input UI
input_method_container = st.container()

with input_method_container:
    if st.session_state.input_mode == "search":
        with st.expander("Search configuration", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                max_results_per_page = st.slider(
                    "Results per request",
                    min_value=1,
                    max_value=50,
                    value=st.session_state.max_results_per_page,
                    help="YouTube API returns up to 50 results per request.",
                )
            with col2:
                max_pages_per_query = st.number_input(
                    "Max pages per query",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.max_pages_per_query,
                    step=1,
                    help="Limits pagination requests per query to control quota usage.",
                )
            st.caption("Each additional page consumes YouTube API quota.")

        st.session_state.max_results_per_page = max_results_per_page
        st.session_state.max_pages_per_query = max_pages_per_query

        st.session_state.search_execution_mode = st.radio(
            "Search execution mode",
            ["Single query", "Planned queries"],
            index=0
            if st.session_state.search_execution_mode == "single"
            else 1,
            horizontal=True,
            help="Run a single query or execute the planned queries list.",
        )
        st.session_state.search_execution_mode = (
            "single"
            if st.session_state.search_execution_mode == "Single query"
            else "planned"
        )

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
            search_button = st.button("Search YouTube", type="primary", use_container_width=True)

        if st.session_state.search_execution_mode == "planned":
            st.info("Planned queries will be used instead of the single query input.")
            planned_search_button = st.button(
                "Run planned queries",
                type="primary",
                use_container_width=True,
            )
        else:
            planned_search_button = False

        # Update session state
        st.session_state.search_query = search_query

    else:  # Direct Input mode
        st.subheader("Direct Input Data")

        direct_input_text = st.text_area(
            "Paste your video data:",
            value=st.session_state.direct_input_raw,
            height=200,
            placeholder="""Choose one of these formats:

URLs (one per line):
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2

OR JSON array:
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
        if st.button("Process Input", type="primary", use_container_width=True):
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
                            st.success(f"Successfully processed {len(result.videos)} videos from your input")

                            # Show warnings if any
                            if result.warnings:
                                with st.expander("Warnings", expanded=False):
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
                        st.error(f"Processing failed: {str(e)}")
                        st.session_state.search_results = None
                        st.session_state.direct_input_videos = None
            else:
                st.warning("Please enter some video data to process")

# Handle search button click (moved from later in the code)
if (
    'search_button' in locals()
    and search_button
    and search_query.strip()
    and st.session_state.search_execution_mode == "single"
):
    with st.spinner("Searching YouTube..."):
        try:
            # Prepare search parameters
            search_params = {
                'query': search_query.strip(),
                'api_key': YOUTUBE_API_KEY,
                'max_results': st.session_state.max_results_per_page,
                'order': 'relevance',
                'type': 'video',
            }

            # Execute search
            search_result = search_youtube(**search_params)

            # Store results in session state
            st.session_state.search_results = search_result
            st.session_state.search_query = search_query
            st.session_state.current_page_token = None
            st.session_state.search_filters = get_search_filters_dict(
                max_results=st.session_state.max_results_per_page
            )
            # Clear previous selections and filtered results for new search
            st.session_state.selected_video_ids.clear()
            st.session_state.filtered_results = None
            st.session_state.selection_update_counter += 1

            st.success(f"Found {len(search_result.items)} results")
            st.rerun()  # Show next steps

        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            st.session_state.search_results = None

if (
    'planned_search_button' in locals()
    and planned_search_button
    and st.session_state.search_execution_mode == "planned"
):
    planned_queries = st.session_state.planned_queries[: st.session_state.planned_queries_to_run]
    if not planned_queries:
        st.warning("No planned queries available. Generate or enter queries above.")
    else:
        with st.spinner("Searching YouTube with planned queries..."):
            try:
                aggregated_items = []
                seen_video_ids = set()
                total_pages = st.session_state.max_pages_per_query * len(planned_queries)
                pages_completed = 0
                planned_runs = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, query in enumerate(planned_queries):
                    run_data = {
                        "id": str(idx + 1),
                        "text": query,
                        "status": "queued",
                        "requested_results": st.session_state.max_results_per_page * st.session_state.max_pages_per_query,
                        "fetched_results": 0,
                        "pages_completed": 0,
                        "max_pages": st.session_state.max_pages_per_query,
                        "errors": [],
                        "results": [],
                    }
                    planned_runs.append(run_data)

                    page_token = None
                    run_data["status"] = "running"
                    for _ in range(st.session_state.max_pages_per_query):
                        pages_completed += 1
                        progress_bar.progress(min(pages_completed / max(total_pages, 1), 1.0))
                        status_text.write(f"Searching: {query} (page {pages_completed} of {total_pages})")
                        try:
                            search_result = search_youtube(
                                query=query.strip(),
                                api_key=YOUTUBE_API_KEY,
                                max_results=st.session_state.max_results_per_page,
                                order='relevance',
                                type='video',
                                page_token=page_token,
                            )
                        except Exception as query_error:
                            run_data["status"] = "failed"
                            run_data["errors"].append(str(query_error))
                            status_text.write(f"Query {query} failed: {query_error}")
                            break
                        run_data["pages_completed"] += 1
                        run_data["fetched_results"] += len(search_result.items)
                        run_data["results"].extend(search_result.items)

                        for item in search_result.items:
                            if item.video_id not in seen_video_ids:
                                aggregated_items.append(item)
                                seen_video_ids.add(item.video_id)
                            else:
                                # Merge query_sources for duplicate videos
                                existing_item = next(
                                    (x for x in aggregated_items if x.video_id == item.video_id),
                                    None
                                )
                                if existing_item:
                                    # Merge query_sources, avoiding duplicates
                                    existing_sources = set(existing_item.query_sources or [])
                                    new_sources = set(item.query_sources or [])
                                    existing_item.query_sources = sorted(list(existing_sources | new_sources))
                        page_token = search_result.next_page_token
                        if not page_token:
                            break

                    if run_data.get("status") == "failed":
                        continue
                    run_data["status"] = "completed"

                progress_bar.progress(1.0)
                status_text.write("Search complete. Preparing results.")

                # Validate aggregation: count videos per query source
                query_source_counts = {}
                for item in aggregated_items:
                    sources = getattr(item, "query_sources", []) or []
                    for source in sources:
                        query_source_counts[source] = query_source_counts.get(source, 0) + 1

                # Log validation (for debugging)
                if len(planned_queries) > 1:
                    missing_queries = [q for q in planned_queries if q not in query_source_counts]
                    if missing_queries:
                        st.warning(
                            f"Note: {len(missing_queries)} query(s) returned no unique results: "
                            f"{', '.join(missing_queries[:3])}{'...' if len(missing_queries) > 3 else ''}"
                        )

                combined_result = SearchResult(
                    items=aggregated_items,
                    total_results=len(aggregated_items),
                    results_per_page=st.session_state.max_results_per_page,
                    next_page_token=None,
                    prev_page_token=None,
                )

                st.session_state.search_results = combined_result
                st.session_state.search_query = "; ".join(planned_queries)
                st.session_state.current_page_token = None
                st.session_state.search_filters = get_search_filters_dict(
                    max_results=st.session_state.max_results_per_page
                )
                st.session_state.selected_video_ids.clear()
                st.session_state.filtered_results = None
                st.session_state.selection_update_counter += 1
                st.session_state.planned_query_runs = planned_runs

                st.success(f"Found {len(aggregated_items)} results.")
                st.rerun()

            except Exception as e:
                st.error(f"Planned query search failed: {str(e)}")
                st.session_state.search_results = None

st.divider()

# This section has been moved to Step 1 above

# Step 2: Research Configuration (only show after data is loaded)
if st.session_state.search_results is not None:
    research_configured = st.session_state.research_context.strip() or st.session_state.ai_filtering_enabled
    st.header("Step 2: Configure AI Research (Optional)")

    with st.expander("AI Research Context & Filtering", expanded=True):
        research_context = st.text_area(
            "Research Context/Goal:",
            value=st.session_state.research_context,
            height=80,
            placeholder="Describe your research goal or context (optional, but recommended for AI filtering). For example: 'Finding videos about AI entrepreneurship and startup strategies for 2026'",
            help="This context helps the AI understand what you're researching, enabling smarter video filtering"
        )

        # AI Filtering Toggle
        ai_filtering_enabled = st.checkbox(
            "Enable AI Filtering",
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
                        st.error("Please enter a custom model name when selecting 'Custom'.")
                        selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                    elif not "/" in selected_model:
                        st.error("Custom model must be in format 'provider/model-name' (e.g., 'openai/gpt-4').")
                        selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                    else:
                        st.info(f"Using custom model: {selected_model}")
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
        st.info("Enter a search query above and click 'Search YouTube' to load videos, then configure AI research options.")
    else:
        st.info("Paste your video data above and click 'Process Input' to load videos, then configure AI research options.")

# Advanced search filters removed for simplified flow

# Step 3: Results & Actions (only show when videos are loaded)
if st.session_state.search_results is not None:
    filtered = st.session_state.filtered_results is not None and st.session_state.filtered_results.success
    st.header("Step 3: Results & Actions")

    # Status indicator
    status_container = st.empty()
    summary_data = _get_planned_query_summary_data(st.session_state.search_results)
    _render_planned_query_summary(status_container, st.session_state.search_results, summary_data=summary_data)
    _render_query_progress(summary_data)

# Initialize results container
results_container = st.container()

# Display results if available
if st.session_state.search_results:
    search_result = st.session_state.search_results
    filtered_result = st.session_state.filtered_results
    show_filtered = filtered_result is not None and filtered_result.success

    planned_queries = st.session_state.planned_queries[: st.session_state.planned_queries_to_run]
    tab_labels = ["All Results (combined)"]
    if planned_queries:
        for idx, query_text in enumerate(planned_queries):
            tab_labels.append(_build_query_tab_label(idx, query_text))

    tabs = st.tabs(tab_labels)
    with tabs[0]:
        aggregate_errors = []
        for run_data in summary_data["runs"]:
            errors = run_data.get('errors')
            if errors:
                if isinstance(errors, list):
                    aggregate_errors.extend(errors)
                else:
                    aggregate_errors.append(errors)
        total_max_pages = sum(
            run_data.get('max_pages', st.session_state.max_pages_per_query)
            for run_data in summary_data["runs"]
        )
        if not total_max_pages:
            total_max_pages = st.session_state.max_pages_per_query
        _render_status_strip(
            label="Combined view",
            status=_derive_aggregate_status(summary_data),
            fetched=summary_data["total_fetched"],
            target=summary_data["total_requested"],
            pages=summary_data["pages_completed"],
            max_pages=total_max_pages,
            errors=aggregate_errors,
        )
        if show_filtered:
            inner_all, inner_filtered = st.tabs(["All Results", "Shortlisted Results"])
            with inner_all:
                _display_results_table(
                    search_result.items,
                    search_result,
                    title_suffix="(All Results)",
                    show_checkboxes=True,
                    include_query_source=True,
                    key_prefix="combined_all_results",
                )
            with inner_filtered:
                _display_results_table(
                    filtered_result.relevant_videos,
                    search_result,
                    title_suffix="(AI Filtered)",
                    show_checkboxes=False,
                    key_prefix="combined_filtered_results",
                )
                st.info(
                    f"AI filtered {filtered_result.total_processed} videos based on your research context. "
                    f"Found {len(filtered_result.relevant_videos)} relevant videos."
                )
        else:
            _display_results_table(
                search_result.items,
                search_result,
                show_checkboxes=True,
                include_query_source=True,
                key_prefix="combined_all_results_without_filter",
            )
            if st.session_state.ai_filtering_enabled and not st.session_state.research_context.strip():
                st.info(
                    "Add research context above and click 'Filter Videos with AI' to automatically shortlist relevant videos."
                )
            elif st.session_state.ai_filtering_enabled and st.session_state.research_context.strip():
                st.info("Click 'Filter Videos with AI' in the Actions section below to automatically shortlist relevant videos.")

        if show_filtered and search_result.items:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if search_result.prev_page_token:
                    if st.button("Previous Page (All Results)"):
                        with st.spinner("Loading previous page..."):
                            try:
                                search_params = st.session_state.search_filters.copy()
                                search_params.update({
                                    "query": st.session_state.search_query,
                                    "api_key": YOUTUBE_API_KEY,
                                    "page_token": search_result.prev_page_token,
                                })
                                new_result = search_youtube(**search_params)
                                st.session_state.search_results = new_result
                                st.session_state.current_page_token = search_result.prev_page_token
                                st.session_state.filtered_results = None
                                st.session_state.selected_video_ids.clear()
                                st.session_state.selection_update_counter += 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to load previous page: {str(e)}")
            with col3:
                if search_result.next_page_token:
                    if st.button("Next Page (All Results)"):
                        with st.spinner("Loading next page..."):
                            try:
                                search_params = st.session_state.search_filters.copy()
                                search_params.update({
                                    "query": st.session_state.search_query,
                                    "api_key": YOUTUBE_API_KEY,
                                    "page_token": search_result.next_page_token,
                                })
                                new_result = search_youtube(**search_params)
                                st.session_state.search_results = new_result
                                st.session_state.current_page_token = search_result.next_page_token
                                st.session_state.filtered_results = None
                                st.session_state.selected_video_ids.clear()
                                st.session_state.selection_update_counter += 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to load next page: {str(e)}")

        if st.session_state.ai_filtering_enabled and st.session_state.research_context.strip():
            if st.button("Filter Videos with AI", type="secondary", use_container_width=True):
                with st.spinner("AI is evaluating video relevance..."):
                    try:
                        search_results = st.session_state.search_results
                        if search_results and hasattr(search_results, "items") and search_results.items:
                            filter_result = filter_videos_by_relevance(
                                videos=search_results.items,
                                search_query=st.session_state.search_query,
                                research_context=st.session_state.research_context.strip(),
                                model=st.session_state.selected_model,
                                api_key=OPENROUTER_API_KEY,
                            )
                            st.session_state.filtered_results = filter_result
                        else:
                            st.error("No videos available for filtering")
                            filter_result = None
                            st.session_state.filtered_results = None

                        if filter_result and filter_result.success:
                            st.success(
                                f"Filtered {filter_result.total_processed} videos: "
                                f"{len(filter_result.relevant_videos)} relevant, {len(filter_result.filtered_out_videos)} filtered out"
                            )
                            st.rerun()
                        elif filter_result:
                            st.error(f"Filtering failed: {filter_result.error_message}")
                    except Exception as e:
                        st.error(f"AI filtering error: {str(e)}")
                        if "API key" in str(e).lower():
                            st.info("Make sure OPENROUTER_API_KEY is set in your .env file")
            st.divider()

        col1, col2, col3, col4 = st.columns(4)
        search_results = st.session_state.search_results
        if search_results and hasattr(search_results, "items") and search_results.items:
            if st.session_state.selected_video_ids:
                action_videos = [item for item in search_results.items if item.video_id in st.session_state.selected_video_ids]
                action_source = "youtube_search_selected"
                action_label = "Selected"
            else:
                action_videos = search_results.items
                action_source = "youtube_search"
                action_label = "All"
        else:
            action_videos = []
            action_source = "youtube_search"
            action_label = "All"

        if st.session_state.filtered_results and st.session_state.filtered_results.success:
            action_videos = st.session_state.filtered_results.relevant_videos
            action_source = "youtube_search_filtered"
            action_label = "Shortlisted"
            
            # Validate filtered results contain videos from all queries
            if len(st.session_state.planned_queries) > 1:
                filtered_breakdown = _get_query_source_breakdown(action_videos)
                all_queries = set(st.session_state.planned_queries[:st.session_state.planned_queries_to_run])
                filtered_queries = set(filtered_breakdown.keys())
                missing_in_filtered = all_queries - filtered_queries
                if missing_in_filtered:
                    st.info(
                        f"Note: Filtered results contain videos from {len(filtered_queries)} of {len(all_queries)} queries. "
                        f"Some queries may have had no relevant videos after AI filtering."
                    )

        # Show query source breakdown for user feedback
        if action_videos and len(st.session_state.planned_queries) > 1:
            breakdown = _get_query_source_breakdown(action_videos)
            if breakdown:
                query_summary = ", ".join([f"Q{i+1}: {count}" for i, (query, count) in enumerate(sorted(breakdown.items(), key=lambda x: -x[1])[:5])])
                if len(breakdown) > 5:
                    query_summary += f" (+{len(breakdown) - 5} more)"
                st.caption(f"Query distribution: {query_summary}")

        action_key_prefix = "step3_actions"
        with col1:
            if st.button(f"Copy {action_label} URLs", key=f"{action_key_prefix}_copy_urls", use_container_width=True):
                urls = [item.video_url for item in action_videos]
                urls_text = "\n".join(urls)
                st.code(urls_text, language=None)
                st.success(f"Copied {len(urls)} {action_label.lower()} URLs to clipboard (select and copy the code block above)")

        with col2:
            if st.button(f"Copy {action_label} IDs", key=f"{action_key_prefix}_copy_ids", use_container_width=True):
                ids = [item.video_id for item in action_videos]
                ids_text = ",".join(ids)
                st.code(ids_text, language=None)
                st.success(f"Copied {len(ids)} {action_label.lower()} video IDs to clipboard (select and copy the code block above)")

        with col3:
            if st.button(f"Copy {action_label} as JSON", key=f"{action_key_prefix}_copy_json", use_container_width=True):
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
                st.success(f"Copied {len(results_data)} {action_label.lower()} results as JSON to clipboard (select and copy the code block above)")

        with col4:
            if st.button(f"Send {action_label} to Transcript Tool", key=f"{action_key_prefix}_send_transcript", type="primary", use_container_width=True):
                urls = [item.video_url for item in action_videos]
                metadata_list = [video_search_item_to_dict(item) for item in action_videos]
                
                # Validate metadata before storing
                is_valid, errors = validate_metadata_list(metadata_list)
                if not is_valid:
                    st.error(f"Metadata validation failed: {', '.join(errors[:3])}")
                    if len(errors) > 3:
                        st.caption(f"... and {len(errors) - 3} more errors")
                else:
                    # Show query breakdown in success message
                    if len(st.session_state.planned_queries) > 1:
                        breakdown = _get_query_source_breakdown(action_videos)
                        unique_queries = len(breakdown)
                        query_info = f" from {unique_queries} query{'ies' if unique_queries != 1 else ''}"
                    else:
                        query_info = ""
                    
                    st.session_state['transcript_urls'] = urls
                    st.session_state['transcript_metadata'] = metadata_list
                    st.session_state['transcript_source'] = action_source
                    st.success(f"Prepared {len(urls)} {action_label.lower()} videos{query_info} for transcription with rich metadata")
                st.page_link(
                    "pages/02_Bulk_Transcribe.py",
                    label="Go to Transcript Tool",
                    help="Continue to the transcript tool with selected videos"
                )

    for idx, query_tab in enumerate(tabs[1:], start=0):
        query_text = planned_queries[idx]
        run_data = st.session_state.planned_query_runs[idx] if idx < len(st.session_state.planned_query_runs) else {}
        run_errors = run_data.get('errors') if isinstance(run_data, dict) else []
        with query_tab:
            _render_status_strip(
                label=f"Query {idx + 1}",
                status=run_data.get('status', 'queued') if isinstance(run_data, dict) else 'queued',
                fetched=run_data.get('fetched_results', 0) if isinstance(run_data, dict) else 0,
                target=run_data.get('requested_results', st.session_state.max_results_per_page),
                pages=run_data.get('pages_completed', 0) if isinstance(run_data, dict) else 0,
                max_pages=run_data.get('max_pages', st.session_state.max_pages_per_query),
                errors=run_errors,
            )
            if isinstance(run_data, dict):
                _render_cap_notice(run_data)
            focus_target = st.session_state.focused_query_tab
            if focus_target == idx + 1:
                st.info("Highlight requested by progress tracker. Inspect this query tab.")
                st.session_state.focused_query_tab = None
            st.subheader(f"Query {idx + 1} overview")
            st.caption(f"Query text: {query_text}")
            query_items = _filter_results_by_query(search_result.items, query_text)
            query_result = SearchResult(
                items=query_items,
                total_results=len(query_items),
                results_per_page=len(query_items) or st.session_state.max_results_per_page,
                next_page_token=None,
                prev_page_token=None,
            )
            _display_results_table(
                query_items,
                query_result,
                title_suffix=f"(Query {idx + 1})",
                show_checkboxes=True,
                key_prefix=f"query_{idx+1}",
            )
            if run_data.get("status") == "failed":
                st.warning("This query failed during the previous run.")
                if st.button(f"Retry query {idx + 1}", key=f"retry_query_{idx}"):
                    _retry_planned_query(idx)

# Phase 2 Placeholder
st.header("AI Agent Mode (Phase 2 - Coming Soon)")

with st.expander("Future Features", expanded=False):
    st.info("""
    **Phase 2 will enable AI-powered research workflows:**

    **Multiple Query Generation**: AI generates comprehensive search queries for thorough research

    **Bulk Processing**: Automatically fetch transcripts for hundreds of videos

    **Intelligent Selection**: AI ranks and filters videos by relevance before transcription

    **Deep Analysis**: Automated summarization and insights extraction from transcripts

    **Iterative Research**: AI refines searches based on initial findings

    This will transform the tool from manual search to automated research assistant.
    """)

    st.button("Enable AI Agent Mode", disabled=True, help="Available in Phase 2")

# Footer
st.markdown("---")
st.caption("YouTube Search Tool - Phase 1 | Built with YouTube Data API v3")

# Function moved to top of file after imports
