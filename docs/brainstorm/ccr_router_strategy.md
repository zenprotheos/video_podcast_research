# Claude Code Router (CCR) Strategy - OpenRouter-Only Configuration

## Overview
This document captures the strategic model routing configuration for Claude Code Router (CCR), optimized for cost-effective AI-assisted development with fallback tiers for different task complexities.

## Current Status
- **CCR Version**: Installed via `@musistudio/claude-code-router`
- **Config Location**: `~/.claude-code-router/config.json`
- **Port**: 3456 (default)
- **Last Verified**: 2026-01-23 (all 7 models tested OK)

---

## Final Router Configuration (OpenRouter-Only) - VERIFIED

```json
{
  "PORT": 3456,
  "LOG": true,
  "LOG_LEVEL": "info",
  "API_TIMEOUT_MS": 600000,
  "Providers": [
    {
      "name": "openrouter",
      "api_base_url": "https://openrouter.ai/api/v1/chat/completions",
      "api_key": "$OPENROUTER_API_KEY",
      "models": [
        "deepseek/deepseek-v3.2",
        "z-ai/glm-4.7",
        "x-ai/grok-code-fast-1",
        "qwen/qwen3-coder",
        "openai/gpt-5.1-codex-mini",
        "anthropic/claude-sonnet-4.5",
        "google/gemini-2.5-pro"
      ],
      "transformer": {
        "use": ["openrouter"]
      }
    }
  ],
  "Router": {
    "default": "openrouter,deepseek/deepseek-v3.2",
    "background": "openrouter,qwen/qwen3-coder",
    "think": "openrouter,x-ai/grok-code-fast-1",
    "longContext": "openrouter,google/gemini-2.5-pro"
  }
}
```

---

## Verified Model IDs (Tested 2026-01-23)

| Model | OpenRouter ID | Status |
|-------|---------------|--------|
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | OK |
| GLM-4.7 | `z-ai/glm-4.7` | OK |
| Grok Code Fast | `x-ai/grok-code-fast-1` | OK |
| Qwen3 Coder 480B | `qwen/qwen3-coder` | OK |
| GPT-5.1 Codex Mini | `openai/gpt-5.1-codex-mini` | OK |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` | OK |
| Gemini 2.5 Pro | `google/gemini-2.5-pro` | OK |

**Note**: The Qwen model ID is `qwen/qwen3-coder`, NOT `qwen/qwen3-coder-480b-a35b-instruct`.

---

## Strategic Router Design

### Router Mapping

```
Router Type     -> Model                          -> Use Case
---------------------------------------------------------------------------
default         -> deepseek/deepseek-v3.2         -> General dev (80%+ tasks)
background      -> qwen/qwen3-coder               -> Exploration, scaffolding
think           -> x-ai/grok-code-fast-1          -> Multi-step logic, planning
cheapThink      -> deepseek/deepseek-v3.2         -> First-pass reasoning
hardThink       -> anthropic/claude-sonnet-4.5    -> Critical decisions (insurance)
longContext     -> google/gemini-2.5-pro          -> Large file/repo analysis
                -> qwen/qwen3-coder               -> (fallback, 262K context)
```

---

## Model Role Assignments

### 1. DeepSeek V3.2 - Cheap Serious Thinker
**Model**: `deepseek/deepseek-v3.2`

**Characteristics**:
- Very low output cost (~$0.38/M tokens)
- Explicit agentic + tool-use training
- Reasoning toggle support
- Community perception: "cheap but surprisingly deep"

**Role**: `default`, `cheapThink`
- First-pass multi-step reasoning
- General development tasks
- Replaces deprecated free models

---

### 2. GLM-4.7 - Cheap Execution Stabilizer
**Model**: `z-ai/glm-4.7`

**Characteristics**:
- Strong multi-step execution stability
- Good at agent loops
- Cheap enough to retry without stress

**Role**: `default` (fallback), `background`
- Step-by-step task execution after planning
- Better long-term substitute than flash-only or free models

---

### 3. Grok Code Fast - Fast Multi-Logic Workhorse
**Model**: `x-ai/grok-code-fast-1`

**Characteristics**:
- Strong at chaining actions
- Good diff discipline
- Cheap relative to Codex / Claude

**Role**: `default` (fallback), `think`
- Multi-step logic tasks
- Code generation and refactoring

---

### 4. GPT-5.1 Codex Mini - Clean Codex Replacement
**Model**: `openai/gpt-5.1-codex-mini`

**Characteristics**:
- Better than older Codex
- Cheaper than flagship GPT-5 / Claude
- Very good at structured planning

**Role**: `think` (secondary to Grok)
- Never use as default
- Structured planning tasks

---

### 5. Qwen3-Coder 480B - Big Cheap Repo Brain
**Model**: `qwen/qwen3-coder`

**Characteristics**:
- Massive MoE code model (480B total, 35B active)
- Excellent for repo-wide reasoning
- Context up to 262K tokens
- Pricing: $0.22/M input, $0.95/M output

**Role**: `background`, `longContext`
- Exploration and scaffolding
- Large codebase analysis
- Best cost/performance long-context coder

---

### 6. Claude Sonnet 4.5 - Pure Insurance
**Model**: `anthropic/claude-sonnet-4.5`

**Characteristics**:
- Best judgment
- Lowest chaos
- Highest cost

**Role**: `hardThink` only
- Last-resort correctness
- Critical architectural decisions

---

### 7. Gemini 2.5 Pro - Long Context Champion
**Model**: `google/gemini-2.5-pro`

**Characteristics**:
- Massive context window
- Good at large file analysis
- Strong reasoning capabilities

**Role**: `longContext`
- Large repository analysis
- Multi-file refactoring

---

## Implicit Speed Tiers

The routing configuration implicitly encodes speed/cost tiers:

| Tier | Speed | Cost | Models |
|------|-------|------|--------|
| Fast/Cheap | High | Low | DeepSeek V3.2, GLM-4.7 |
| Medium (Main) | Medium | Medium | Grok Code Fast, Codex Mini |
| Slow/Deliberate | Low | High | Claude Sonnet 4.5 |

---

## CCR Router Types Explained

| Router Type | Purpose | When Used |
|-------------|---------|-----------|
| `default` | General coding tasks | Most requests |
| `background` | Background/scaffolding tasks | Exploration, file operations |
| `think` | Reasoning-heavy tasks | Plan mode, complex logic |
| `longContext` | Large context handling | Files > 60K tokens |
| `webSearch` | Web-enabled queries | API documentation research |
| `image` | Image-related tasks | Visual content handling |

---

## Setup Instructions

### 1. Prerequisites
- OpenRouter API key in `.env` file as `OPENROUTER_API_KEY`
- CCR installed: `npm install -g @musistudio/claude-code-router`

### 2. Configure CCR
The config file is at: `~/.claude-code-router/config.json`

### 3. Start CCR
```powershell
ccr start
ccr status  # Verify running
```

### 4. Test Configuration
```powershell
# Run the test script
python.exe temp/test_ccr_models.py
```

### 5. Switch Models Dynamically
Within Claude Code session:
```
/model openrouter,anthropic/claude-sonnet-4.5
```

---

## Verification Checklist

- [x] OpenRouter API key set in .env
- [x] All model IDs verified against OpenRouter (2026-01-23)
- [x] CCR server starts without errors
- [x] `ccr status` shows "Running"
- [x] All 7 models respond successfully
- [ ] Model switching works via `/model` command (to test in live session)

---

## Cost Optimization Notes

1. **Default to cheap models**: DeepSeek V3.2 handles 80%+ of tasks
2. **Reserve Claude for critical decisions**: Only use `hardThink` when needed
3. **Use Qwen for exploration**: Cheap long-context exploration before committing
4. **Grok for iteration**: Fast feedback loops during development

---

## Test Script Location

A test script is available at: `temp/test_ccr_models.py`

Run with:
```powershell
python.exe temp/test_ccr_models.py
```

---

## Related Documentation

- CCR GitHub: https://github.com/musistudio/claude-code-router
- OpenRouter Models: https://openrouter.ai/models
- CCR Configuration Examples: See CCR repo `config.example.json`

---

## Revision History

| Date | Change |
|------|--------|
| 2026-01-23 | Initial strategy documentation |
| 2026-01-23 | Verified all 7 model IDs, corrected Qwen to `qwen/qwen3-coder` |
