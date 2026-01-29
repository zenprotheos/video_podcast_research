"""
Model Reliability Analysis Test

Runs each model 3 times to determine success rates and identify root causes of failures.
Analyzes whether failures are due to token limits or prose responses.
"""

import os
import time
from typing import Dict, List, Tuple

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
    """Load .env for local runs."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass


def _analyze_failure_type(result, raw_response: str) -> str:
    """Determine if failure is token-related or prose-related."""
    if not raw_response:
        return "empty_response"
    
    # Check for token truncation indicators
    if len(raw_response) > 1400:  # Close to 1500 token limit
        return "likely_token_limit"
    
    # Check if it's prose (not JSON)
    raw_lower = raw_response.lower()
    if raw_response.strip().startswith("i ") or raw_response.strip().startswith("the "):
        return "prose_response"
    if "looking to" in raw_lower or "i can" in raw_lower or "we should" in raw_lower:
        return "prose_response"
    if not raw_response.strip().startswith("[") and not raw_response.strip().startswith("```"):
        return "prose_response"
    
    # Check if it's markdown-wrapped JSON (acceptable but indicates model didn't follow instructions)
    if "```" in raw_response:
        return "markdown_wrapped"
    
    return "unknown"


@pytest.mark.integration
def test_model_reliability_analysis() -> None:
    """
    Run each model 3 times and analyze success rates and failure types.
    
    Set OPENROUTER_RUN_MODEL_TESTS=1 and OPENROUTER_API_KEY to enable.
    """
    if os.getenv("OPENROUTER_RUN_MODEL_TESTS") != "1":
        pytest.skip("Set OPENROUTER_RUN_MODEL_TESTS=1 to enable")
    
    _load_env_if_available()
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    results: Dict[str, List[Tuple[bool, str, float, int]]] = {}  # model -> [(success, error_type, duration, retry_count)]
    
    print("\n" + "="*80)
    print("MODEL RELIABILITY ANALYSIS")
    print("="*80)
    print(f"Testing {len(MODELS_TO_TEST)} models, 3 runs each")
    print(f"Research prompt: {RESEARCH_PROMPT[:60]}...")
    print("="*80 + "\n")
    
    for model in MODELS_TO_TEST:
        print(f"\nTesting: {model}")
        print("-" * 80)
        model_results = []
        
        for run in range(1, 4):
            print(f"  Run {run}/3...", end=" ", flush=True)
            start_time = time.time()
            
            result = plan_search_queries(
                messages=[{"role": "user", "content": RESEARCH_PROMPT}],
                model=model,
                api_key=api_key,
                max_queries=5,
            )
            
            duration = time.time() - start_time
            success = result.success
            
            if success:
                error_type = "success"
                print(f"PASS ({duration:.1f}s, {len(result.queries)} queries, {result.retry_count} retries)")
            else:
                failure_type = _analyze_failure_type(result, result.raw_response or "")
                error_type = failure_type
                raw_preview = (result.raw_response or "")[:100].replace("\n", " ")
                print(f"FAIL ({duration:.1f}s) - {failure_type}")
                print(f"    Error: {result.error_message}")
                print(f"    Raw preview: {raw_preview}...")
            
            model_results.append((success, error_type, duration, result.retry_count))
            time.sleep(1)  # Brief pause between runs
        
        results[model] = model_results
    
    # Analysis summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    for model, model_results in results.items():
        successes = sum(1 for s, _, _, _ in model_results if s)
        success_rate = (successes / len(model_results)) * 100
        avg_duration = sum(d for _, _, d, _ in model_results) / len(model_results)
        total_retries = sum(r for _, _, _, r in model_results)
        
        print(f"\n{model}:")
        print(f"  Success rate: {success_rate:.0f}% ({successes}/3)")
        print(f"  Avg duration: {avg_duration:.1f}s")
        print(f"  Total retries: {total_retries}")
        
        if success_rate == 100:
            print(f"  RECOMMENDED: 100% success rate")
        elif success_rate >= 66:
            print(f"  CAUTION: {success_rate:.0f}% success rate - may need prompt tuning")
        else:
            print(f"  NOT RECOMMENDED: {success_rate:.0f}% success rate")
        
        # Failure type breakdown
        failure_types = {}
        for _, error_type, _, _ in model_results:
            if error_type != "success":
                failure_types[error_type] = failure_types.get(error_type, 0) + 1
        
        if failure_types:
            print(f"  Failure types:")
            for ft, count in failure_types.items():
                print(f"    - {ft}: {count}x")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    recommended = [m for m, res in results.items() if all(s for s, _, _, _ in res)]
    if recommended:
        print(f"\nModels with 100% success rate (use these):")
        for m in recommended:
            print(f"  - {m}")
    else:
        print("\nNo models achieved 100% success rate. Consider prompt improvements.")
    
    problematic = [m for m, res in results.items() if not any(s for s, _, _, _ in res)]
    if problematic:
        print(f"\nModels with 0% success rate (avoid these):")
        for m in problematic:
            print(f"  - {m}")
    
    # Root cause analysis
    print("\n" + "="*80)
    print("ROOT CAUSE ANALYSIS")
    print("="*80)
    
    prose_failures = sum(
        1 for res_list in results.values()
        for _, error_type, _, _ in res_list
        if error_type == "prose_response"
    )
    token_failures = sum(
        1 for res_list in results.values()
        for _, error_type, _, _ in res_list
        if error_type == "likely_token_limit"
    )
    markdown_failures = sum(
        1 for res_list in results.values()
        for _, error_type, _, _ in res_list
        if error_type == "markdown_wrapped"
    )
    
    print(f"\nFailure breakdown:")
    print(f"  Prose responses (prompt/model issue): {prose_failures}")
    print(f"  Token limit issues: {token_failures}")
    print(f"  Markdown-wrapped (minor): {markdown_failures}")
    
    if prose_failures > token_failures:
        print("\n⚠ PRIMARY ISSUE: Prose responses (prompt or model capability)")
        print("  → Focus on prompt improvements or use more capable models")
    elif token_failures > prose_failures:
        print("\n⚠ PRIMARY ISSUE: Token limits")
        print("  → Consider reducing max_queries or increasing token budget")
    else:
        print("\nMixed failure types - both prompt and token limits may need attention")
    
    print("\n" + "="*80)
