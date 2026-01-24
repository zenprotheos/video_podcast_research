# YouTube Search to Bulk Transcribe Metadata Preservation Fix

## Task Overview
**Date:** 2026-01-20
**Status:** Planning Phase
**Priority:** High

## Problem Statement
When transferring filtered and approved videos from the YouTube Search tool to the Bulk Transcribe tool, only YouTube URLs are transferred. All the rich metadata collected during the search (title, description, channel, published date, thumbnails, etc.) is lost, resulting in a degraded user experience where the bulk transcribe tool's map column section cannot display the video details.

## Current Data Flow Issue
1. **YouTube Search Tool** collects comprehensive metadata via `VideoSearchItem` objects containing:
   - video_id, title, description, channel_title, channel_id
   - published_at, thumbnail_url, thumbnail_high_url, video_url
   - raw_data (full API response)

2. **Data Transfer** only sends URLs via `st.session_state['transcript_urls'] = urls`

3. **Bulk Transcribe Tool** receives only URLs and creates minimal spreadsheet structure with:
   - source_type: "youtube"
   - youtube_url: [URL]
   - All other fields: empty

## Expected Behavior
The bulk transcribe tool should receive a complete one-to-one mapping of all metadata from the YouTube search tool, allowing the map column section to display all video details in the table.

## Task Objectives
1. **Analyze** current data structures and transfer mechanisms
2. **Design** metadata preservation solution
3. **Implement** enhanced data transfer between tools
4. **Test** end-to-end metadata flow
5. **Document** changes and validate functionality

## Files to Create
- `progress_tracker_metadata_preservation_fix.md` - Task progress tracking
- `specs_impact_assessment.md` - Specification changes assessment
- `artifacts/complete_architecture_analysis.md` - Current architecture documentation
- `artifacts/data_flow_diagrams.md` - UML diagrams and data flow analysis
- `artifacts/proposed_solution_design.md` - Solution design and implementation plan

## Next Steps
1. Create comprehensive UML diagrams of current architecture
2. Document data structures and transfer points
3. Design metadata preservation mechanism
4. Implement solution