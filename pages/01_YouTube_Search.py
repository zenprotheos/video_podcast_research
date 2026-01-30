"""YouTube Search Tool - Phase 1"""
import json
import os
import time
from datetime import datetime, date, timedelta
from typing import List, Optional

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

from src.bulk_transcribe.utils import try_copy_via_pyperclip
from src.bulk_transcribe.youtube_search import (
    search_youtube,
    VideoSearchItem,
    SearchResult,
    get_search_filters_dict,
    enrich_items_with_metadata,
)
from src.bulk_transcribe.video_filter import filter_videos_by_relevance, FilteringResult
from src.bulk_transcribe.query_planner import infer_single_required_term, plan_search_queries
from src.bulk_transcribe.direct_input import parse_direct_input, create_search_result_from_items, DirectInputResult
from src.bulk_transcribe.metadata_transfer import video_search_item_to_dict, validate_metadata_list


def _format_duration(seconds: Optional[int]) -> str:
    """Format seconds as MM:SS or H:MM:SS."""
    if not seconds:
        return ""
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _format_elapsed_time(seconds: float) -> str:
    """Format elapsed time for stopwatch display.
    
    Under 60s: "23.4s"
    60s+: "2m 15s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"


def _format_count(count: Optional[int]) -> str:
    """Format large numbers as 1.2M, 45K, etc."""
    if count is None:
        return ""
    if count >= 1_000_000:
        return f"{count/1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count/1_000:.1f}K"
    return str(count)


def _copy_to_clipboard(text: str, *, label: str, count: int, language: Optional[str] = None) -> None:
    """
    Copy text to clipboard: try pyperclip first, then attempt browser clipboard,
    then show code block with manual-copy message. Only shows the text block when
    clipboard is unavailable (last fallback).
    """
    if try_copy_via_pyperclip(text):
        st.success(f"Copied {count} {label} to clipboard")
        return
    # Attempt browser clipboard via injected script (runs on next paint)
    escaped = json.dumps(text)
    html = (
        "<script>(function(){ var t = " + escaped + ";"
        " if (navigator.clipboard && navigator.clipboard.writeText) "
        "navigator.clipboard.writeText(t).catch(function(){}); })();</script>"
    )
    st.components.v1.html(html, height=0)
    st.info("Clipboard unavailable — please copy manually from the block below.")
    st.code(text, language=language)


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

    # Use a real tabular component so we get:
    # - headers
    # - horizontal scrolling when content exceeds viewport
    # - configurable column widths (long text gets more space)
    rows = []
    for item in items:
        rows.append(
            {
                "video_id": item.video_id,
                "Select": item.video_id in st.session_state.selected_video_ids,
                "Thumbnail": item.thumbnail_url or "",
                "Title": item.title or "",
                "Channel": item.channel_title or "",
                "Duration": _format_duration(getattr(item, "duration_seconds", None)),
                "Views": _format_count(getattr(item, "view_count", None)),
                "Published": (item.published_at or "")[:10],
                "Description": item.description or "",
                "Watch": item.video_url or "",
                "Queries": ", ".join(getattr(item, "query_sources", []) or []),
            }
        )

    df = pd.DataFrame(rows)

    # Hide columns depending on context
    hidden_cols = ["video_id"]
    if not show_checkboxes:
        hidden_cols.append("Select")
    if not include_query_source:
        hidden_cols.append("Queries")

    edited = st.data_editor(
        df,
        key=f"{prefix}_data_editor",
        hide_index=True,
        height=400,
        use_container_width=False,  # allow horizontal scrolling instead of squishing
        disabled=not show_checkboxes,  # allow checkbox edits only when enabled
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", width="small"),
            "Thumbnail": st.column_config.ImageColumn("Thumb", width="small"),
            "Title": st.column_config.TextColumn("Title", width="medium"),
            "Channel": st.column_config.TextColumn("Channel", width="small"),
            "Duration": st.column_config.TextColumn("Duration", width="small"),
            "Views": st.column_config.TextColumn("Views", width="small"),
            "Published": st.column_config.TextColumn("Published", width="small"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Watch": st.column_config.LinkColumn(
                "Watch",
                display_text="Watch",
                width="small",
            ),
            "Queries": st.column_config.TextColumn("Queries", width="large"),
        },
        column_order=[c for c in df.columns if c not in hidden_cols],
    )

    if show_checkboxes and not edited.empty:
        # Sync selection state from editor
        new_selected = set(edited.loc[edited["Select"] == True, "video_id"].tolist())
        if new_selected != st.session_state.selected_video_ids:
            st.session_state.selected_video_ids = new_selected
            st.session_state.selection_update_counter += 1


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
            published_after = None
            published_before = None
            if st.session_state.published_after_date and st.session_state.published_before_date:
                published_after = _date_to_published_after(st.session_state.published_after_date)
                published_before = _date_to_published_before(st.session_state.published_before_date)

            page_token = None
            for _ in range(st.session_state.max_pages_per_query):
                search_result = search_youtube(
                    query=query_text,
                    api_key=YOUTUBE_API_KEY,
                    max_results=st.session_state.max_results_per_page,
                    order='relevance',
                    type='video',
                    published_after=published_after,
                    published_before=published_before,
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

            enrich_items_with_metadata(
                aggregated_items,
                YOUTUBE_API_KEY,
                st.session_state.video_metadata_cache,
            )
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


def _autofill_research_context():
    """Combine Step 0 data (prompt, notes, required_terms) into research context."""
    parts = []
    if st.session_state.get('query_planner_prompt', '').strip():
        parts.append(st.session_state.query_planner_prompt.strip())
    if st.session_state.get('query_planner_notes', '').strip():
        parts.append(f"Additional guidance: {st.session_state.query_planner_notes.strip()}")
    if st.session_state.get('required_terms', '').strip():
        parts.append(f"Required terms in title/description: {st.session_state.required_terms.strip()}")
    if parts:
        return "\n\n".join(parts)
    return None


def _date_to_published_after(d: date) -> str:
    # YouTube Data API expects RFC3339 timestamps.
    # Use start-of-day UTC for publishedAfter.
    return f"{d.isoformat()}T00:00:00Z"


def _date_to_published_before(d: date) -> str:
    # YouTube Data API expects RFC3339 timestamps.
    # Use end-of-day UTC for publishedBefore.
    return f"{d.isoformat()}T23:59:59Z"


# Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "").strip()
if not YOUTUBE_API_KEY:
    st.error("YouTube Data API key not found. Please set YOUTUBE_DATA_API_KEY in your .env file.")
    st.stop()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
_raw_default = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini").strip()
# Normalize deprecated/wrong default to established default (4o-mini)
if _raw_default == "openai/gpt-5-mini":
    _raw_default = "openai/gpt-4o-mini"
OPENROUTER_DEFAULT_MODEL = _raw_default or "openai/gpt-4o-mini"


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
if 'required_terms' not in st.session_state:
    st.session_state.required_terms = ""
if 'required_terms_pending' not in st.session_state:
    # Used to pre-fill required_terms on next rerun (must be applied before widget instantiation).
    st.session_state.required_terms_pending = None
if 'max_results_per_page' not in st.session_state:
    st.session_state.max_results_per_page = 50
if 'max_pages_per_query' not in st.session_state:
    st.session_state.max_pages_per_query = 1
if 'search_execution_mode' not in st.session_state:
    st.session_state.search_execution_mode = "single"
if 'execution_mode_manually_set' not in st.session_state:
    st.session_state.execution_mode_manually_set = False
if 'planned_query_runs' not in st.session_state:
    st.session_state.planned_query_runs = []
if 'focused_query_tab' not in st.session_state:
    st.session_state.focused_query_tab = None

# Date filter session state
if 'date_filter_mode' not in st.session_state:
    st.session_state.date_filter_mode = "Any time"  # "Any time" | "Preset" | "Manual"
if 'date_preset' not in st.session_state:
    st.session_state.date_preset = "Last 6 months"
if 'published_after_date' not in st.session_state:
    st.session_state.published_after_date = None  # date | None
if 'published_before_date' not in st.session_state:
    st.session_state.published_before_date = None  # date | None
if 'video_metadata_cache' not in st.session_state:
    st.session_state.video_metadata_cache = {}  # cache for videos.list metadata (Dict[str, Dict])

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

    # Apply any pending inferred required term BEFORE the widget is instantiated.
    pending_required_terms = (st.session_state.get("required_terms_pending") or "").strip()
    if pending_required_terms and not (st.session_state.get("required_terms") or "").strip():
        st.session_state["required_terms"] = pending_required_terms
        st.session_state["required_terms_pending"] = None

    st.text_input(
        "Required terms in title and description",
        key="required_terms",
        placeholder="e.g., machine learning, Python, tutorial",
        help="Keywords or phrases that must appear in video titles or descriptions. Separate multiple terms with commas; each will be quoted in search queries. Informs query generation and AI filtering.",
    )

    with st.expander("Query planning settings", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            # Order by reliability: fastest + 0 retries first (from reliability analysis)
            preset_models = [
                "openai/gpt-4o-mini",
                "openai/gpt-4.1-nano",
                "google/gemini-2.5-flash-lite",
                "openai/gpt-5-nano",
                "anthropic/claude-haiku-4.5",
                "meta-llama/llama-3.2-3b-instruct",
            ]
            model_options = preset_models + ["Custom"]
            current_planner_model = (st.session_state.query_planner_model or "").strip()
            if current_planner_model in preset_models:
                planner_model_index = preset_models.index(current_planner_model)
            elif current_planner_model:
                planner_model_index = model_options.index("Custom")
            else:
                planner_model_index = 0
            selected_model_option = st.selectbox(
                "Planner model",
                model_options,
                index=planner_model_index,
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
                value=current_planner_model if current_planner_model not in preset_models else "",
                placeholder="e.g., openai/gpt-5-nano, anthropic/claude-haiku-4.5",
                help="Enter a custom OpenRouter model identifier.",
            )
            query_planner_model = custom_model.strip()

            # Validate custom model input
            if not query_planner_model:
                st.error("Please enter a custom model name when selecting 'Custom'.")
                query_planner_model = OPENROUTER_DEFAULT_MODEL  # Fallback
            elif "/" not in query_planner_model:
                st.error(
                    "Custom model must be in format 'provider/model-name' (e.g., 'openai/gpt-5-nano')."
                )
                query_planner_model = OPENROUTER_DEFAULT_MODEL  # Fallback
            else:
                st.info(f"Using custom planner model: {query_planner_model}")
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
            messages = [{"role": "user", "content": st.session_state.query_planner_prompt.strip()}]
            if st.session_state.query_planner_notes.strip():
                messages.append(
                    {"role": "user", "content": f"Additional guidance: {st.session_state.query_planner_notes.strip()}"}
                )
            required_terms_empty = not (st.session_state.required_terms or "").strip()
            if not required_terms_empty:
                messages.append(
                    {"role": "user", "content": f"Required terms in title/description: {st.session_state.required_terms.strip()}"}
                )

            status_container = st.status("Initializing...", expanded=True)
            progress_messages = []

            def progress_callback(msg: str) -> None:
                progress_messages.append(msg)
                with status_container:
                    for pm in progress_messages:
                        st.text(pm)

            with status_container:
                if required_terms_empty:
                    infer_result = infer_single_required_term(
                        messages=messages,
                        model=st.session_state.query_planner_model,
                        api_key=OPENROUTER_API_KEY,
                        progress_callback=progress_callback,
                    )
                    if not infer_result.success or not infer_result.required_terms:
                        status_container.update(state="complete")
                        st.error(infer_result.error_message or "Could not infer a required term. Try entering one in Step 0.")
                    else:
                        # Can't set st.session_state.required_terms after the widget is created.
                        # Store it as pending and apply it on the next rerun (before widget instantiation).
                        st.session_state["required_terms_pending"] = infer_result.required_terms
                        messages.append(
                            {"role": "user", "content": f"Required terms in title/description: {infer_result.required_terms}"}
                        )
                        result = plan_search_queries(
                            messages=messages,
                            model=st.session_state.query_planner_model,
                            api_key=OPENROUTER_API_KEY,
                            max_queries=st.session_state.query_plan_max_queries,
                            progress_callback=progress_callback,
                        )
                        status_container.update(state="complete")
                        if result.success:
                            new_text = "\n".join(result.queries)
                            st.session_state.planned_queries = result.queries
                            st.session_state.planned_queries_text = new_text
                            st.session_state["planned_queries_text_area"] = new_text
                            st.info("Required terms filled from your research prompt (one conservative term). Edit or clear above.")
                            success_msg = f"Generated {len(result.queries)} queries."
                            if result.timing_info:
                                total_time = sum(result.timing_info.values())
                                success_msg += f" Total time: {total_time:.1f}s"
                            st.success(success_msg)
                            if result.timing_info:
                                with st.expander("Timing breakdown (dev)", expanded=False):
                                    for key, value in result.timing_info.items():
                                        st.text(f"{key}: {value:.2f}s")
                            # Ensure Step 0 required-terms input immediately reflects the inferred value.
                            st.rerun()
                        else:
                            st.error(f"Query planning failed: {result.error_message}")
                else:
                    result = plan_search_queries(
                        messages=messages,
                        model=st.session_state.query_planner_model,
                        api_key=OPENROUTER_API_KEY,
                        max_queries=st.session_state.query_plan_max_queries,
                        progress_callback=progress_callback,
                    )
                    status_container.update(state="complete")
                    if result.success:
                        new_text = "\n".join(result.queries)
                        st.session_state.planned_queries = result.queries
                        st.session_state.planned_queries_text = new_text
                        st.session_state["planned_queries_text_area"] = new_text
                        success_msg = f"Generated {len(result.queries)} queries."
                        if result.timing_info:
                            total_time = sum(result.timing_info.values())
                            success_msg += f" Total time: {total_time:.1f}s"
                            if result.retry_count > 0:
                                success_msg += " (1 retry)"
                        st.success(success_msg)
                        if result.timing_info:
                            with st.expander("Timing breakdown (dev)", expanded=False):
                                for key, value in result.timing_info.items():
                                    st.text(f"{key}: {value:.2f}s")
                                if result.retry_count > 0:
                                    st.warning("Retry was needed - model may not be optimal for this prompt")
                    else:
                        st.error(f"Query planning failed: {result.error_message}")
                        if result.timing_info:
                            with st.expander("Timing breakdown (dev)", expanded=False):
                                for key, value in result.timing_info.items():
                                    st.text(f"{key}: {value:.2f}s")

    if st.session_state.planned_queries:
        st.session_state.planned_queries_to_run = st.number_input(
            "Queries to run",
            min_value=1,
            max_value=len(st.session_state.planned_queries),
            value=min(st.session_state.planned_queries_to_run, len(st.session_state.planned_queries)),
            step=1,
            help="Limit how many planned queries to execute.",
        )

    st.info("💡 Tip: You can freely edit the search queries or add your own list here. One query per line.")
    # When using a widget key, Streamlit persists the value in st.session_state[key].
    # Seed it once from planned_queries_text so the textbox shows existing content.
    if "planned_queries_text_area" not in st.session_state:
        st.session_state["planned_queries_text_area"] = st.session_state.planned_queries_text
    st.text_area(
        "Planned queries (one per line):",
        height=140,
        help="Review and edit the planned queries. One query per line.",
        key="planned_queries_text_area",
    )
    planned_queries_text = st.session_state.get("planned_queries_text_area", "")
    st.session_state.planned_queries_text = planned_queries_text
    # Update planned_queries list from text
    st.session_state.planned_queries = [
        line.strip()
        for line in planned_queries_text.splitlines()
        if line.strip()
    ]

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

            st.divider()
            st.subheader("Date range")
            date_mode = st.radio(
                "Filter videos by publish date:",
                ["Any time", "Rolling preset", "Manual range"],
                index=0
                if st.session_state.date_filter_mode == "Any time"
                else (1 if st.session_state.date_filter_mode == "Preset" else 2),
                horizontal=True,
                help="Limit results to a publish date window. Presets are rolling ranges; manual lets you pick start/end dates.",
            )

            if date_mode == "Any time":
                st.session_state.date_filter_mode = "Any time"
                st.session_state.published_after_date = None
                st.session_state.published_before_date = None
            elif date_mode == "Rolling preset":
                st.session_state.date_filter_mode = "Preset"
                preset = st.selectbox(
                    "Preset",
                    ["Last 3 months", "Last 6 months", "Last 12 months"],
                    index=["Last 3 months", "Last 6 months", "Last 12 months"].index(
                        st.session_state.date_preset
                        if st.session_state.date_preset in ["Last 3 months", "Last 6 months", "Last 12 months"]
                        else "Last 6 months"
                    ),
                    help="Sets a rolling window ending today.",
                )
                st.session_state.date_preset = preset
                months = 6
                if preset == "Last 3 months":
                    months = 3
                elif preset == "Last 12 months":
                    months = 12
                today = date.today()
                # Approximate months as 30-day blocks (simple, predictable UX).
                start = today - timedelta(days=30 * months)
                st.session_state.published_after_date = start
                st.session_state.published_before_date = today

                with st.expander("Preview / adjust", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.date_input(
                            "Start date",
                            value=st.session_state.published_after_date,
                            key="preset_start_date_preview",
                            disabled=True,
                        )
                    with col_b:
                        st.date_input(
                            "End date",
                            value=st.session_state.published_before_date,
                            key="preset_end_date_preview",
                            disabled=True,
                        )
                    st.caption("To tweak these dates, switch to Manual range.")
            else:
                st.session_state.date_filter_mode = "Manual"
                col_a, col_b = st.columns(2)
                with col_a:
                    start_date = st.date_input(
                        "Start date",
                        value=st.session_state.published_after_date or (date.today() - timedelta(days=30 * 6)),
                        help="Inclusive. Will map to publishedAfter.",
                    )
                with col_b:
                    end_date = st.date_input(
                        "End date",
                        value=st.session_state.published_before_date or date.today(),
                        help="Inclusive. Will map to publishedBefore.",
                    )

                if start_date and end_date and start_date > end_date:
                    st.warning("Start date must be on or before end date. Date filter will be ignored until fixed.")
                    st.session_state.published_after_date = None
                    st.session_state.published_before_date = None
                else:
                    st.session_state.published_after_date = start_date
                    st.session_state.published_before_date = end_date

        st.session_state.max_results_per_page = max_results_per_page
        st.session_state.max_pages_per_query = max_pages_per_query

        # Auto-select planned mode if queries exist and mode hasn't been manually set
        planned_queries = st.session_state.get('planned_queries', [])
        has_planned_queries = planned_queries and len(planned_queries) > 0
        
        if (has_planned_queries 
            and not st.session_state.execution_mode_manually_set
            and st.session_state.search_execution_mode == "single"):
            st.session_state.search_execution_mode = "planned"
        
        # If planned queries were deleted, switch back to single mode
        if not has_planned_queries and st.session_state.search_execution_mode == "planned":
            st.session_state.search_execution_mode = "single"
            st.session_state.execution_mode_manually_set = False

        # Radio button for execution mode
        radio_options = ["Single query", "Planned queries"]
        radio_index = 0 if st.session_state.search_execution_mode == "single" else 1
        selected_mode = st.radio(
            "Search execution mode",
            radio_options,
            index=radio_index,
            horizontal=True,
            help="Run a single query or execute the planned queries list.",
        )
        
        # Track if user manually changed the mode
        new_mode = "single" if selected_mode == "Single query" else "planned"
        if new_mode != st.session_state.search_execution_mode:
            st.session_state.execution_mode_manually_set = True
        st.session_state.search_execution_mode = new_mode

        # Conditionally render UI based on mode
        if st.session_state.search_execution_mode == "planned":
            # Planned queries mode: show info and planned search button only
            if has_planned_queries:
                query_count = len(planned_queries)
                st.info(f"Using {query_count} planned {'queries' if query_count != 1 else 'query'} from Step 0. Click below to run them.")
            else:
                st.warning("No planned queries available. Generate queries in Step 0 or switch to single query mode.")
            
            planned_search_button = st.button(
                "Run planned queries",
                type="primary",
                use_container_width=True,
                disabled=not has_planned_queries,
            )
            # Initialize variables for single query mode (not used but maintain state)
            search_query = st.session_state.get('search_query', '')
            search_button = False
        else:
            # Single query mode: show search input and button
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input(
                    "Search Query:",
                    value=st.session_state.get('search_query', ''),
                    placeholder="Enter YouTube search terms...",
                    help="Search for videos on YouTube"
                )
            with col2:
                search_button = st.button("Search YouTube", type="primary", use_container_width=True)
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
            published_after = None
            published_before = None
            if st.session_state.published_after_date and st.session_state.published_before_date:
                published_after = _date_to_published_after(st.session_state.published_after_date)
                published_before = _date_to_published_before(st.session_state.published_before_date)

            # Prepare search parameters
            search_params = {
                'query': search_query.strip(),
                'api_key': YOUTUBE_API_KEY,
                'max_results': st.session_state.max_results_per_page,
                'order': 'relevance',
                'type': 'video',
                'published_after': published_after,
                'published_before': published_before,
            }

            # Execute search
            search_result = search_youtube(**search_params)
            enrich_items_with_metadata(
                search_result.items,
                YOUTUBE_API_KEY,
                st.session_state.video_metadata_cache,
            )

            # Store results in session state
            st.session_state.search_results = search_result
            st.session_state.search_query = search_query
            st.session_state.current_page_token = None
            st.session_state.search_filters = get_search_filters_dict(
                max_results=st.session_state.max_results_per_page,
                published_after=published_after,
                published_before=published_before,
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
                published_after = None
                published_before = None
                if st.session_state.published_after_date and st.session_state.published_before_date:
                    published_after = _date_to_published_after(st.session_state.published_after_date)
                    published_before = _date_to_published_before(st.session_state.published_before_date)

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
                                published_after=published_after,
                                published_before=published_before,
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
                status_text.write("Fetching full metadata...")
                enrich_items_with_metadata(
                    aggregated_items,
                    YOUTUBE_API_KEY,
                    st.session_state.video_metadata_cache,
                )
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
                    max_results=st.session_state.max_results_per_page,
                    published_after=published_after,
                    published_before=published_before,
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

# Advanced search filters removed for simplified flow

# Step 2: Results & Actions (only show when videos are loaded)
if st.session_state.search_results is not None:
    filtered = st.session_state.filtered_results is not None and st.session_state.filtered_results.success
    st.header("Step 2: Results & Actions")

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
                                enrich_items_with_metadata(
                                    new_result.items,
                                    YOUTUBE_API_KEY,
                                    st.session_state.video_metadata_cache,
                                )
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
                                enrich_items_with_metadata(
                                    new_result.items,
                                    YOUTUBE_API_KEY,
                                    st.session_state.video_metadata_cache,
                                )
                                st.session_state.search_results = new_result
                                st.session_state.current_page_token = search_result.next_page_token
                                st.session_state.filtered_results = None
                                st.session_state.selected_video_ids.clear()
                                st.session_state.selection_update_counter += 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to load next page: {str(e)}")

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

# Step 3: AI Research Filter (only show when videos are loaded)
if st.session_state.search_results is not None:
    st.header("Step 3: AI Research Filter (Optional)")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        autofill_button = st.button(
            "Autofill Research Context from Step 0",
            type="secondary",
            use_container_width=True,
            help="Combine research prompt, guidance, and required terms from Step 0"
        )
    with col2:
        if st.session_state.research_context.strip():
            st.success("✓ Research context ready")
        else:
            st.info("Click autofill or enter manually")
    
    if autofill_button:
        autofilled = _autofill_research_context()
        if autofilled:
            st.session_state.research_context = autofilled
            st.success("Research context autofilled from Step 0 data")
            st.rerun()
        else:
            st.warning("No Step 0 data available to autofill")
    
    # Display research context (editable)
    research_context = st.text_area(
        "Research Context/Goal:",
        value=st.session_state.research_context,
        height=100,
        placeholder="Describe your research goal or context...",
        help="This context helps the AI understand what you're researching"
    )
    st.session_state.research_context = research_context
    
    # Model selection
    with st.expander("AI Model Settings", expanded=False):
        # Order by reliability: fastest + 0 retries first (from reliability analysis)
        preset_models = [
            "openai/gpt-4o-mini",
            "openai/gpt-4.1-nano",
            "google/gemini-2.5-flash-lite",
            "openai/gpt-5-nano",
            "anthropic/claude-haiku-4.5",
            "meta-llama/llama-3.2-3b-instruct",
        ]
        model_options = preset_models + ["Custom"]
        col1, col2 = st.columns([3, 1])
        
        with col1:
            current_filter_model = (st.session_state.selected_model or "").strip()
            if current_filter_model in preset_models:
                filter_model_index = preset_models.index(current_filter_model)
            elif current_filter_model:
                filter_model_index = model_options.index("Custom")
            else:
                filter_model_index = 0
            selected_model_option = st.selectbox(
                "AI Model:",
                model_options,
                index=filter_model_index,
                help="Choose the AI model for video relevance filtering. Free models may have limits. OpenAI models are generally reliable. See https://openrouter.ai/models for all available options."
            )
        
        with col2:
            if selected_model_option == "Custom":
                custom_model = st.text_input(
                    "Custom Model:",
                    value=current_filter_model if current_filter_model not in preset_models else "",
                    placeholder="e.g., openai/gpt-5-nano, anthropic/claude-haiku-4.5",
                    help="Enter custom OpenRouter model identifier. Must be in format 'provider/model-name'. Check https://openrouter.ai/models for available options."
                )
                selected_model = custom_model.strip()
                
                # Validate custom model input
                if not selected_model:
                    st.error("Please enter a custom model name when selecting 'Custom'.")
                    selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                elif "/" not in selected_model:
                    st.error("Custom model must be in format 'provider/model-name' (e.g., 'openai/gpt-4').")
                    selected_model = OPENROUTER_DEFAULT_MODEL  # Fallback
                else:
                    st.info(f"Using custom model: {selected_model}")
            else:
                selected_model = selected_model_option
        
        st.session_state.selected_model = selected_model
    
    # Filter button
    if st.button("Filter Videos with AI", type="primary", use_container_width=True, 
                 disabled=not st.session_state.research_context.strip()):
        st.session_state.filter_ai_progress_lines = []
        st.session_state.filter_start_time = time.time()
        st.session_state.filter_elapsed_time = None
        
        # JavaScript-based running timer (updates every 100ms in browser)
        timer_html = """
        <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; 
                    font-size: 14px; color: #31333F; padding: 8px 0;">
            <span style="font-weight: 600;">Elapsed:</span> 
            <span id="running-timer" style="font-weight: 500;">0.0s</span>
        </div>
        <script>
            (function() {
                var startTime = Date.now();
                var timerEl = document.getElementById('running-timer');
                function updateTimer() {
                    var elapsed = (Date.now() - startTime) / 1000;
                    var display;
                    if (elapsed < 60) {
                        display = elapsed.toFixed(1) + 's';
                    } else {
                        var mins = Math.floor(elapsed / 60);
                        var secs = Math.floor(elapsed % 60);
                        display = mins + 'm ' + secs + 's';
                    }
                    if (timerEl) timerEl.textContent = display;
                }
                setInterval(updateTimer, 100);
                updateTimer();
            })();
        </script>
        """
        st.components.v1.html(timer_html, height=40)
        
        live_placeholder = st.empty()
        
        def on_filter_progress(msg: str) -> None:
            elapsed = time.time() - st.session_state.filter_start_time
            elapsed_formatted = _format_elapsed_time(elapsed)
            # Prepend timestamp to each batch message (real Python-measured time)
            timestamped_msg = f"[{elapsed_formatted}] {msg}"
            st.session_state.filter_ai_progress_lines.append(timestamped_msg)
            # Display progress lines below the JS timer
            live_placeholder.caption("\n".join(st.session_state.filter_ai_progress_lines))
        
        with st.spinner("AI is evaluating video relevance..."):
            try:
                search_results = st.session_state.search_results
                if search_results and hasattr(search_results, "items") and search_results.items:
                    req_terms = (st.session_state.get("required_terms") or "").strip() or None
                    filter_result = filter_videos_by_relevance(
                        videos=search_results.items,
                        search_query=st.session_state.search_query,
                        research_context=st.session_state.research_context.strip(),
                        model=st.session_state.selected_model,
                        api_key=OPENROUTER_API_KEY,
                        required_terms=req_terms,
                        progress_callback=on_filter_progress,
                    )
                    st.session_state.filtered_results = filter_result
                    # Store final elapsed time
                    final_elapsed = time.time() - st.session_state.filter_start_time
                    st.session_state.filter_elapsed_time = final_elapsed
                else:
                    st.error("No videos available for filtering")
                    filter_result = None
                    st.session_state.filtered_results = None
                
                if filter_result and filter_result.success:
                    # Build success message with cleanup info if applicable
                    msg = (
                        f"Filtered {filter_result.total_processed} videos: "
                        f"{len(filter_result.relevant_videos)} relevant, {len(filter_result.filtered_out_videos)} filtered out"
                    )
                    if filter_result.cleanup_recovered > 0:
                        msg += f" ({filter_result.cleanup_recovered} recovered in cleanup)"
                    
                    # Check if there are any failed videos (partial success)
                    failed_count = len(filter_result.failed_batch_videos) if filter_result.failed_batch_videos else 0
                    if failed_count > 0:
                        st.warning(
                            f"{msg}. Note: {failed_count} video(s) could not be evaluated after retry."
                        )
                    else:
                        st.success(msg)
                    st.rerun()
                elif filter_result:
                    st.error(f"Filtering failed: {filter_result.error_message}")
            except Exception as e:
                st.error(f"AI filtering error: {str(e)}")
                if "API key" in str(e).lower():
                    st.info("Make sure OPENROUTER_API_KEY is set in your .env file")
    
    # Show filtered results status
    if st.session_state.filtered_results and st.session_state.filtered_results.success:
        filtered_result = st.session_state.filtered_results
        
        # Build status message with cleanup and failure info
        status_msg = (
            f"AI filtered {filtered_result.total_processed} videos based on your research context. "
            f"Found {len(filtered_result.relevant_videos)} relevant videos. "
        )
        if filtered_result.cleanup_recovered > 0:
            status_msg += f"Recovered {filtered_result.cleanup_recovered} in cleanup phase. "
        status_msg += "Shortlisted results are shown in Step 2 above."
        
        failed_count = len(filtered_result.failed_batch_videos) if filtered_result.failed_batch_videos else 0
        if failed_count > 0:
            st.warning(f"{status_msg} Note: {failed_count} video(s) could not be evaluated.")
        else:
            st.info(status_msg)
        # Concise live-update log (collapsed after job done)
        progress_lines = st.session_state.get("filter_ai_progress_lines") or []
        filter_elapsed = st.session_state.get("filter_elapsed_time")
        if progress_lines or filter_elapsed:
            with st.expander("AI filter progress", expanded=False):
                # Show total time at the TOP
                if filter_elapsed:
                    total_time_str = _format_elapsed_time(filter_elapsed)
                    st.caption(f"**Total time: {total_time_str}**")
                    st.caption("")  # Empty line separator
                for line in progress_lines:
                    st.caption(line)
        # Dev console — per-batch logs (title, description, full reason; wrap, scroll, manual height)
        summaries = getattr(filtered_result, "batch_summaries", None)
        if summaries:
            with st.expander("Dev console — batch logs", expanded=False):
                for s in summaries:
                    bid = s.get("batch_id", "?")
                    decisions = s.get("decisions", [])
                    n = len(s.get("video_ids", []))
                    r = sum(1 for d in decisions if d.get("relevant"))
                    st.caption(f"**{bid}**: {n} videos -> {r} relevant, {n - r} out")
                    with st.expander(f"Decisions — {bid}", expanded=False):
                        for d in decisions:
                            vid = d.get("video_id") or ""
                            title = d.get("title") or ""
                            desc = d.get("description") or ""
                            reason = d.get("reason") or ""
                            rel = "In" if d.get("relevant") else "Out"
                            st.markdown(f"**{vid}** | **{rel}**")
                            st.caption("Title")
                            st.text(title)
                            st.caption("Description")
                            st.text_area(
                                "Description",
                                value=desc,
                                height=80,
                                disabled=True,
                                key=f"dev_desc_{bid}_{vid}",
                            )
                            st.caption("Reason (full; wraps; scroll if long)")
                            st.text_area(
                                "Reason",
                                value=reason,
                                height=80,
                                disabled=True,
                                key=f"dev_reason_{bid}_{vid}",
                            )
                            st.divider()
        
        # Dev console — failed batch videos (if any)
        failed_videos = getattr(filtered_result, "failed_batch_videos", None)
        if failed_videos:
            with st.expander(f"Dev console — failed videos ({len(failed_videos)})", expanded=False):
                st.caption("These videos could not be evaluated after cleanup retry:")
                for fv in failed_videos:
                    vid = getattr(fv, "video_id", "?")
                    title = getattr(fv, "title", "") or ""
                    st.markdown(f"**{vid}**: {title[:80]}{'...' if len(title) > 80 else ''}")

# Step 4: Final Actions (only show when videos are loaded)
if st.session_state.search_results is not None:
    st.header("Step 4: Final Actions")
    
    # Determine action source
    search_results = st.session_state.search_results
    if search_results and hasattr(search_results, "items") and search_results.items:
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
        elif st.session_state.selected_video_ids:
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
    
    # Show query source breakdown for user feedback
    if action_videos and len(st.session_state.planned_queries) > 1:
        breakdown = _get_query_source_breakdown(action_videos)
        if breakdown:
            query_summary = ", ".join([f"Q{i+1}: {count}" for i, (query, count) in enumerate(sorted(breakdown.items(), key=lambda x: -x[1])[:5])])
            if len(breakdown) > 5:
                query_summary += f" (+{len(breakdown) - 5} more)"
            st.caption(f"Query distribution: {query_summary}")
    
    st.info(f"Actions will apply to {len(action_videos)} {action_label.lower()} video(s)")
    
    action_key_prefix = "step4_actions"
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(f"Copy {action_label} URLs", key=f"{action_key_prefix}_copy_urls", use_container_width=True):
            urls = [item.video_url for item in action_videos]
            urls_text = "\n".join(urls)
            _copy_to_clipboard(urls_text, label=f"{action_label.lower()} URLs", count=len(urls), language=None)
    
    with col2:
        if st.button(f"Copy {action_label} IDs", key=f"{action_key_prefix}_copy_ids", use_container_width=True):
            ids = [item.video_id for item in action_videos]
            ids_text = ",".join(ids)
            _copy_to_clipboard(ids_text, label="video IDs", count=len(ids), language=None)
    
    with col3:
        if st.button(f"Copy {action_label} as JSON", key=f"{action_key_prefix}_copy_json", use_container_width=True):
            results_data = []
            for item in action_videos:
                results_data.append({
                    "video_id": item.video_id,
                    "title": item.title,
                    "channel_title": item.channel_title,
                    "published_at": item.published_at,
                    "video_url": item.video_url,
                    # Export full description (do not truncate).
                    "description": item.description,
                })
            json_text = json.dumps(results_data, indent=2, ensure_ascii=False)
            _copy_to_clipboard(json_text, label="results as JSON", count=len(results_data), language="json")
    
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
                    query_info = f" from {unique_queries} {'queries' if unique_queries != 1 else 'query'}"
                else:
                    query_info = ""
                
                st.session_state['transcript_urls'] = urls
                st.session_state['transcript_metadata'] = metadata_list
                st.session_state['transcript_source'] = action_source
                st.success(f"Prepared {len(urls)} {action_label.lower()} videos{query_info} for transcription with rich metadata")
            st.page_link(
                "pages/03_Bulk_Transcribe_Proxy.py",
                label="Go to Transcript Tool",
                help="Continue to the transcript tool with selected videos"
            )

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
