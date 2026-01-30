"""
E2E-style tests for AI filter prompt flexibility and query planner quoted phrases.

- Filter: required_terms param is threaded to user prompt; when set, prompt includes
  "Required terms (must appear..."; when empty, prompt does not.
- Query planner: when messages include "Required terms in title/description", returned
  queries may contain quoted phrases; when not, no requirement for quotes.

Uses mocks for OpenRouter/API so tests are fast and deterministic.
"""

import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.bulk_transcribe.video_filter import filter_videos_by_relevance
from src.bulk_transcribe.query_planner import infer_single_required_term, plan_search_queries
from src.bulk_transcribe.youtube_search import VideoSearchItem


def _make_video_item(
    video_id: str = "abc123",
    title: str = "Test Video",
    description: str = "Test description",
) -> VideoSearchItem:
    """Build a minimal VideoSearchItem for tests."""
    return VideoSearchItem(
        video_id=video_id,
        title=title,
        description=description,
        channel_title="Channel",
        channel_id="ch1",
        published_at="2025-01-01",
        thumbnail_url="https://example.com/t.jpg",
        thumbnail_high_url="https://example.com/th.jpg",
        video_url="https://www.youtube.com/watch?v=abc123",
        raw_data={},
    )


class _FakeResponse:
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return self._json_data


def test_filter_user_prompt_includes_required_terms_when_set() -> None:
    """When required_terms is set, the user prompt sent to the API includes Required terms line."""
    import src.bulk_transcribe.video_filter as vf

    captured_payload: List[Dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        payload = kwargs.get("json", {})
        msgs = payload.get("messages", [])
        if len(msgs) == 1:
            return _FakeResponse({"choices": [{"message": {"content": "OK"}}]})
        if len(msgs) >= 2:
            captured_payload.append(payload)
        decisions = [{"video_id": "abc123", "relevant": True, "reason": "On topic"}]
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps({"decisions": decisions})}}]
        })

    with patch.object(vf.requests, "post", side_effect=fake_post):
        videos = [_make_video_item()]
        result = filter_videos_by_relevance(
            videos=videos,
            search_query="SaaS marketing",
            research_context="B2B SaaS marketing strategies",
            model="openai/gpt-4o-mini",
            api_key="test_key",
            required_terms="SaaS companies",
        )
    assert result.success
    assert len(captured_payload) >= 1
    messages = captured_payload[0].get("messages", [])
    user_content = next((m["content"] for m in messages if m.get("role") == "user"), "")
    assert "Required terms (must appear or be clearly reflected" in user_content
    assert "SaaS companies" in user_content


def test_filter_user_prompt_omits_required_terms_when_empty() -> None:
    """When required_terms is None or empty, the user prompt does not include Required terms line."""
    import src.bulk_transcribe.video_filter as vf

    captured_payload: List[Dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        payload = kwargs.get("json", {})
        msgs = payload.get("messages", [])
        if len(msgs) == 1:
            return _FakeResponse({"choices": [{"message": {"content": "OK"}}]})
        if len(msgs) >= 2:
            captured_payload.append(payload)
        decisions = [{"video_id": "abc123", "relevant": True, "reason": "On topic"}]
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps({"decisions": decisions})}}]
        })

    with patch.object(vf.requests, "post", side_effect=fake_post):
        videos = [_make_video_item()]
        result = filter_videos_by_relevance(
            videos=videos,
            search_query="SaaS marketing",
            research_context="B2B SaaS marketing",
            model="openai/gpt-4o-mini",
            api_key="test_key",
            required_terms=None,
        )
    assert result.success
    assert len(captured_payload) >= 1
    user_content = next(
        (m["content"] for m in captured_payload[0].get("messages", []) if m.get("role") == "user"),
        "",
    )
    assert "Required terms (must appear or be clearly reflected" not in user_content


def test_filter_system_prompt_includes_flexibility_wording() -> None:
    """System prompt includes conceptual breadth / exclude only when off-topic wording."""
    import src.bulk_transcribe.video_filter as vf

    captured_payload: List[Dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> _FakeResponse:
        payload = kwargs.get("json", {})
        msgs = payload.get("messages", [])
        if len(msgs) == 1:
            return _FakeResponse({"choices": [{"message": {"content": "OK"}}]})
        if len(msgs) >= 2:
            captured_payload.append(payload)
        decisions = [{"video_id": "abc123", "relevant": True, "reason": "On topic"}]
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps({"decisions": decisions})}}]
        })

    with patch.object(vf.requests, "post", side_effect=fake_post):
        videos = [_make_video_item()]
        filter_videos_by_relevance(
            videos=videos,
            search_query="q",
            research_context="ctx",
            model="openai/gpt-4o-mini",
            api_key="test_key",
        )
    assert len(captured_payload) >= 1
    sys_content = next(
        (m["content"] for m in captured_payload[0].get("messages", []) if m.get("role") == "system"),
        "",
    )
    assert "reasonable breadth" in sys_content or "different terminology" in sys_content
    assert "Exclude only when content is clearly off-topic" in sys_content


def test_planner_with_required_terms_in_messages_accepts_quoted_queries() -> None:
    """When messages include Required terms, planner returns queries; quoted phrases are accepted."""
    import src.bulk_transcribe.query_planner as qp

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        queries_with_quotes = [
            '"SaaS companies" marketing strategies 2025',
            'B2B "SaaS companies" growth',
        ]
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps(queries_with_quotes)}}]
        })

    with patch.object(qp.requests, "post", side_effect=fake_post):
        result = plan_search_queries(
            messages=[
                {"role": "user", "content": "B2B SaaS marketing"},
                {"role": "user", "content": "Required terms in title/description: SaaS companies"},
            ],
            model="openai/gpt-4o-mini",
            api_key="test_key",
            max_queries=5,
        )
    assert result.success
    assert len(result.queries) >= 1
    assert any('"' in q for q in result.queries), "Expected at least one query with quoted phrase"


def test_planner_without_required_terms_accepts_plain_queries() -> None:
    """When messages do not include Required terms, plain queries (no quotes) are valid."""
    import src.bulk_transcribe.query_planner as qp

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        plain = ['b2b saas marketing 2025', 'saas demand gen strategies']
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps(plain)}}]
        })

    with patch.object(qp.requests, "post", side_effect=fake_post):
        result = plan_search_queries(
            messages=[{"role": "user", "content": "B2B SaaS marketing"}],
            model="openai/gpt-4o-mini",
            api_key="test_key",
            max_queries=5,
        )
    assert result.success
    assert len(result.queries) >= 1


def test_infer_single_required_term_returns_one_conservative_term() -> None:
    """infer_single_required_term returns one term (1-3 words); comma-separated response is trimmed to first term."""
    import src.bulk_transcribe.query_planner as qp

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        payload = json.dumps({"required_terms": "B2B SaaS"})
        return _FakeResponse({"choices": [{"message": {"content": payload}}]})

    with patch.object(qp.requests, "post", side_effect=fake_post):
        result = infer_single_required_term(
            messages=[{"role": "user", "content": "B2B SaaS marketing strategies"}],
            model="openai/gpt-4o-mini",
            api_key="test_key",
        )
    assert result.success
    assert result.required_terms is not None
    assert result.required_terms == "B2B SaaS"
    assert "," not in result.required_terms
    assert len(result.required_terms.split()) <= 3


def test_infer_single_required_term_takes_first_segment_if_comma_returned() -> None:
    """If model returns comma-separated value, we take first segment and enforce 1-3 words."""
    import src.bulk_transcribe.query_planner as qp

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        payload = json.dumps({"required_terms": "SaaS, B2B SaaS, marketing"})
        return _FakeResponse({"choices": [{"message": {"content": payload}}]})

    with patch.object(qp.requests, "post", side_effect=fake_post):
        result = infer_single_required_term(
            messages=[{"role": "user", "content": "SaaS marketing"}],
            model="openai/gpt-4o-mini",
            api_key="test_key",
        )
    assert result.success
    assert result.required_terms is not None
    assert result.required_terms == "SaaS"


def test_planner_comma_separated_required_terms_accepts_multiple_quoted_phrases() -> None:
    """When messages include comma-separated required terms, planner accepts queries with multiple quoted phrases."""
    import src.bulk_transcribe.query_planner as qp

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        queries_with_multiple_quotes = [
            '"SaaS companies" "B2B SaaS" marketing strategies 2025',
            '"B2B SaaS" growth "SaaS companies"',
        ]
        return _FakeResponse({
            "choices": [{"message": {"content": json.dumps(queries_with_multiple_quotes)}}]
        })

    with patch.object(qp.requests, "post", side_effect=fake_post):
        result = plan_search_queries(
            messages=[
                {"role": "user", "content": "B2B SaaS marketing"},
                {"role": "user", "content": "Required terms in title/description: SaaS companies, B2B SaaS"},
            ],
            model="openai/gpt-4o-mini",
            api_key="test_key",
            max_queries=5,
        )
    assert result.success
    assert len(result.queries) >= 1
    quote_count = sum(q.count('"') for q in result.queries)
    assert quote_count >= 2, "Expected at least two quoted phrases (multiple terms)"
