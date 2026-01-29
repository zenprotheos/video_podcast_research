import os
from typing import Any, Dict

import pytest

from src.bulk_transcribe.query_planner import plan_search_queries


RESEARCH_PROMPT = (
    "research current marketing strategies for B2B SaaS companies that are working today "
    "(late 2025 to 2026), preferring more reputable sources and experts in the field. "
    "We should have a diverse topics covering all the core areas of marketing e2e."
)


MODELS_TO_TEST = [
    "openai/gpt-5-nano",
    "openai/gpt-oss-20b",
    "openai/gpt-4o-mini",
    "openai/gpt-oss-120b",
    "openai/gpt-4.1-nano",
    "google/gemini-2.5-flash-lite",
]


def _load_env_if_available() -> None:
    """Load .env for local runs (no-op if unavailable)."""
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv()


class _FakeResponse:
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Dict[str, Any]:
        return self._json_data


def test_plan_search_queries_parses_json_array(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '["b2b saas positioning strategy","b2b saas demand gen 2026"]'
                        }
                    }
                ]
            }
        )

    import src.bulk_transcribe.query_planner as qp

    monkeypatch.setattr(qp.requests, "post", fake_post)

    result = plan_search_queries(
        messages=[{"role": "user", "content": RESEARCH_PROMPT}],
        model="openai/gpt-4o-mini",
        api_key="test_key",
        max_queries=5,
    )
    assert result.success is True
    assert len(result.queries) >= 1


def test_plan_search_queries_empty_content_returns_helpful_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse({"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]})

    import src.bulk_transcribe.query_planner as qp

    monkeypatch.setattr(qp.requests, "post", fake_post)

    result = plan_search_queries(
        messages=[{"role": "user", "content": RESEARCH_PROMPT}],
        model="openai/gpt-4o-mini",
        api_key="test_key",
        max_queries=5,
    )
    assert result.success is False
    assert "Empty response from OpenRouter API" in (result.error_message or "")
    assert "finish_reason" in (result.error_message or "")


def test_plan_search_queries_retries_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "I'm looking to craft some specific queries. First focuses on Gartner..."
                        }
                    }
                ]
            }
        ),
        _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '["b2b saas marketing strategy 2026","b2b saas demand gen 2025 2026","b2b saas lifecycle marketing playbook"]'
                        }
                    }
                ]
            }
        ),
    ]

    def fake_post(*args: Any, **kwargs: Any) -> _FakeResponse:
        return responses.pop(0)

    import src.bulk_transcribe.query_planner as qp

    monkeypatch.setattr(qp.requests, "post", fake_post)

    result = plan_search_queries(
        messages=[{"role": "user", "content": RESEARCH_PROMPT}],
        model="openai/gpt-4o-mini",
        api_key="test_key",
        max_queries=5,
    )
    assert result.success is True
    assert len(result.queries) >= 2


@pytest.mark.integration
@pytest.mark.parametrize("model", MODELS_TO_TEST)
def test_openrouter_model_generates_queries_integration(model: str) -> None:
    """
    Real OpenRouter integration test.

    Enable by setting:
      - OPENROUTER_API_KEY
      - OPENROUTER_RUN_MODEL_TESTS=1
    """
    if os.getenv("OPENROUTER_RUN_MODEL_TESTS") != "1":
        pytest.skip("Set OPENROUTER_RUN_MODEL_TESTS=1 to enable real OpenRouter calls")

    _load_env_if_available()
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    result = plan_search_queries(
        messages=[{"role": "user", "content": RESEARCH_PROMPT}],
        model=model,
        api_key=api_key,
        max_queries=5,
    )
    assert result.success is True, f"{model} failed: {result.error_message}"
    assert len(result.queries) >= 2, f"{model} returned too few queries: {result.queries}"

