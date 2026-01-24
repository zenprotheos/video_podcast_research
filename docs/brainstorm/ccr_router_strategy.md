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
      "api_key": "YOUR_OPENROUTER_API_KEY_HERE",
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
    "background": "openrouter,z-ai/glm-4.7",
    "think": "openrouter,x-ai/grok-code-fast-1",
    "longContext": "openrouter,qwen/qwen3-coder"
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
default         -> deepseek/deepseek-v3.2         -> General dev (80%+ tasks, cheapest)
background      -> z-ai/glm-4.7                   -> Stable step-by-step execution, agent loops
think           -> x-ai/grok-code-fast-1          -> Multi-step logic, planning
cheapThink      -> deepseek/deepseek-v3.2         -> First-pass reasoning (manual)
hardThink       -> anthropic/claude-sonnet-4.5    -> Critical decisions (manual, insurance)
longContext     -> qwen/qwen3-coder               -> Large repo analysis (262K context)
                -> google/gemini-2.5-pro          -> (manual fallback for very large context)
```

### Why This Assignment Works

Based on community feedback and benchmarks:

| Model | Strength | Router Assignment |
|-------|----------|-------------------|
| **DeepSeek V3.2** | Cheapest with good reasoning | `default` - first-shot for 80%+ tasks |
| **GLM-4.7** | Stable execution, agent loops, reliable multi-turn | `background` - step-by-step tasks |
| **Grok Code Fast** | Fast action chaining, good diffs | `think` - planning and logic |
| **Qwen3 Coder** | 262K context, best open-source for large repos | `longContext` - repo-wide analysis |
| **Claude Sonnet 4.5** | Best judgment, lowest chaos | `hardThink` - manual override only |

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

### 2. GLM-4.7 - Stable Execution Stabilizer
**Model**: `z-ai/glm-4.7`

**Characteristics**:
- Strong multi-step execution stability
- Excellent at agent loops and multi-turn handling
- "Thinking before acting" behavior
- ~$0.40/1M input, ~$1.50/1M output (moderate cost)
- ~200K+ context window

**Role**: `background` (PRIMARY)
- Step-by-step task execution
- Exploration and scaffolding tasks
- Reliable multi-turn coding handling
- Better stability than DeepSeek for complex agent workflows

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
- Context up to 262K tokens (extendable to ~1M with Yarn)
- Pricing: $0.22/M input, $0.95/M output (very cost-effective)
- Strong agentic coding focus with function calling support

**Role**: `longContext` (PRIMARY)
- Large codebase analysis and refactoring
- Repo-wide multi-file reasoning
- Best cost/performance ratio for long-context coding tasks
- Cheaper than Gemini for most large context needs

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

## How to Use CCR - Complete Usage Guide

### CLI Commands Reference

| Command | Description |
|---------|-------------|
| `ccr start` | Start the CCR server (runs in background) |
| `ccr stop` | Stop the CCR server |
| `ccr restart` | Restart after config changes |
| `ccr status` | Check if server is running |
| `ccr code` | Launch Claude Code through CCR |
| `ccr model` | Interactive model selector (terminal UI) |
| `ccr ui` | Web-based configuration editor |
| `ccr preset export <name>` | Export current config as preset |
| `ccr preset list` | List saved presets |

### Starting a CCR Session

```powershell
# 1. Ensure CCR is running
ccr status

# 2. If not running, start it
ccr start

# 3. Launch Claude Code through CCR
ccr code
```

All requests now route through CCR based on your config.

---

### Dynamic Model Switching (Mid-Session)

Switch models on-the-fly without restarting:

```
/model openrouter,anthropic/claude-sonnet-4.5
```

**Format**: `/model provider,model-id`

**Examples for our config**:
```
/model openrouter,deepseek/deepseek-v3.2      # Switch to cheap default
/model openrouter,z-ai/glm-4.7                # Switch to stable GLM
/model openrouter,x-ai/grok-code-fast-1       # Switch to fast Grok
/model openrouter,qwen/qwen3-coder            # Switch to long-context Qwen
/model openrouter,anthropic/claude-sonnet-4.5 # Switch to Claude (insurance)
/model openrouter,google/gemini-2.5-pro       # Switch to Gemini
/model openrouter,openai/gpt-5.1-codex-mini   # Switch to Codex Mini
```

**When to manually switch**:
- Task is failing repeatedly -> switch to Claude Sonnet 4.5
- Need extreme context (>262K) -> switch to Gemini 2.5 Pro
- Complex planning task -> switch to Codex Mini or Grok

---

### Automatic Router Triggers

CCR automatically routes based on task context:

| Router Type | Triggers Automatically When... | Assigned Model |
|-------------|-------------------------------|----------------|
| `default` | Most general requests | DeepSeek V3.2 |
| `background` | File operations, exploration, scaffolding | GLM-4.7 |
| `think` | Plan mode, complex reasoning, multi-step logic | Grok Code Fast |
| `longContext` | Context exceeds `longContextThreshold` (default 60K tokens) | Qwen3 Coder |

**Note**: `longContextThreshold` can be configured in config.json:
```json
"Router": {
  "longContextThreshold": 60000
}
```

---

### Subagent Routing (Advanced)

Route specific subagent tasks to designated models by adding a tag at the **beginning** of the subagent prompt:

```
<CCR-SUBAGENT-MODEL>openrouter,anthropic/claude-sonnet-4.5</CCR-SUBAGENT-MODEL>
Please analyze this code for security vulnerabilities...
```

**Use cases**:
- Route code review subagents to Claude for best judgment
- Route exploration subagents to cheap models
- Route critical analysis to premium models

---

### Practical Prompting Tips

#### 1. Let CCR Handle Routing (Default Behavior)
Just prompt normally - CCR routes automatically:
```
"Fix the bug in the authentication module"
-> Routes to: default (DeepSeek V3.2)
```

#### 2. Trigger Think Mode for Complex Tasks
Use plan mode or ask for reasoning:
```
"Let's think through the architecture for this feature step by step"
-> Routes to: think (Grok Code Fast)
```

#### 3. Force Premium Model for Critical Work
Switch manually when stakes are high:
```
/model openrouter,anthropic/claude-sonnet-4.5
"Review this security-critical code and identify any vulnerabilities"
```

#### 4. Large Codebase Analysis
For repo-wide tasks (auto-triggers longContext):
```
"Analyze the entire src/ directory and suggest refactoring opportunities"
-> Routes to: longContext (Qwen3 Coder) if context > 60K tokens
```

---

### Common Workflows

#### Workflow 1: Cost-Optimized Development
```
1. Start with default (DeepSeek V3.2) for initial work
2. Let CCR auto-route background tasks to GLM-4.7
3. Only switch to Claude when stuck or for critical decisions
```

#### Workflow 2: Large Repo Refactoring
```
1. CCR auto-routes to Qwen3 Coder for long context
2. If context exceeds Qwen's limits, manually switch to Gemini:
   /model openrouter,google/gemini-2.5-pro
```

#### Workflow 3: Debugging Session
```
1. Start with default model
2. If debugging is complex, switch to think model:
   /model openrouter,x-ai/grok-code-fast-1
3. If still failing, escalate to Claude:
   /model openrouter,anthropic/claude-sonnet-4.5
```

#### Workflow 4: Code Review
```
1. For non-critical review: use default
2. For security-critical review:
   /model openrouter,anthropic/claude-sonnet-4.5
   "Review this code for security issues"
```

---

### Troubleshooting

| Issue | Solution |
|-------|----------|
| CCR not starting | Check `ccr status`, ensure port 3456 is free |
| Model not found | Verify model ID on OpenRouter, run test script |
| Slow responses | Check if using expensive model, switch to cheaper |
| Config changes not applied | Run `ccr restart` |
| API errors | Check OpenRouter API key in config.json, verify balance |
| Context too long | CCR should auto-route to longContext model |
| **401 "No cookie auth credentials"** | API key not being passed - see fix below |

#### Fix: 401 Authentication Errors

**Symptom**: `Error from provider(openrouter,model: 401): {"error":{"message":"No cookie auth credentials found"}}`

**Root Cause**: The `$OPENROUTER_API_KEY` environment variable interpolation in config.json only works if the variable is set in the **system environment** where CCR runs, NOT in project `.env` files.

**Solution** (choose one):
1. **Hardcode the API key** (recommended for reliability):
   ```json
   "api_key": "sk-or-v1-your-actual-key-here"
   ```
2. **Set system environment variable**:
   ```powershell
   [Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-...", "User")
   ```
   Then restart CCR: `ccr restart`

**Verification**:
```powershell
python.exe temp/test_openrouter_direct.py
```

**Logs location**: `~/.claude-code-router/logs/`

**Test models**: `python.exe temp/test_ccr_models.py`

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
| 2026-01-23 | Updated router: GLM-4.7 -> background, Qwen3 -> longContext (based on community research) |
| 2026-01-23 | Added comprehensive "How to Use CCR" guide with commands, prompting tips, workflows |
| 2026-01-24 | Fixed 401 auth error: env var interpolation requires system env, not project .env. Added troubleshooting section. |
