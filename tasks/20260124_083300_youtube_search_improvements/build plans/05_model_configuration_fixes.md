# Build Plan 5: Model Configuration Fixes

**Status:** Pending  
**Estimated Complexity:** Low  
**Dependencies:** None  
**Related Feedback Items:** #4, #7

## Objective

1. Fix custom model syntax issue (model `openai/gpt-5-nano` fails but should work)
2. Update model presets to prioritize `openai/gpt-5-nano` as default
3. Set `anthropic/claude-haiku-4.5` as second option

## Current Issues

1. **Custom model bug:** Custom models in "filter ai search" don't work, but presets do
2. **Syntax issue:** Model `openai/gpt-5-nano` is a valid working model but fails
3. **Outdated presets:** Default model is `openai/gpt-4o-mini`, should be `openai/gpt-5-nano`
4. **Preset order:** Second option should be `anthropic/claude-haiku-4.5`

## Implementation Tasks

### Task 5.1: Debug Custom Model Syntax Issue
- [ ] Investigate why custom models fail
- [ ] Check model validation logic in `video_filter.py` (Lines ~52-54)
- [ ] Check model format validation in UI (Lines ~944-948 in `01_YouTube_Search.py`)
- [ ] Test with `openai/gpt-5-nano` specifically
- [ ] Check if issue is in:
  - Model format validation (must contain "/")
  - API call format
  - Model name parsing

### Task 5.2: Fix Custom Model Handling
- [ ] Ensure custom model input is properly stripped and validated
- [ ] Fix any syntax/parsing issues
- [ ] Test with various model formats:
  - `openai/gpt-5-nano` ✓ (should work)
  - `anthropic/claude-haiku-4.5` ✓
  - `openai/gpt-4o-mini` ✓
  - Invalid formats should show clear error

### Task 5.3: Update Model Presets
- [ ] Update preset list in Step 0 (query planner):
  - Change order: `openai/gpt-5-nano`, `anthropic/claude-haiku-4.5`, `meta-llama/llama-3.2-3b-instruct`, `Custom`
  - Update default selection logic
- [ ] Update preset list in Step 2 (AI filter):
  - Change order: `openai/gpt-5-nano`, `anthropic/claude-haiku-4.5`, `meta-llama/llama-3.2-3b-instruct`, `Custom`
  - Update default selection logic
- [ ] Update default model in session state initialization

### Task 5.4: Update Default Model Constants
- [ ] Check for `OPENROUTER_DEFAULT_MODEL` constant
- [ ] Update to `openai/gpt-5-nano`
- [ ] Ensure fallback logic uses new default

## Code Locations

**File:** `pages/01_YouTube_Search.py`

- **Step 0 model selection:** Lines ~482-520
- **Step 2 model selection:** Lines ~922-957
- **Custom model validation:** Lines ~940-948

**File:** `src/bulk_transcribe/video_filter.py`

- **Model validation:** Lines ~52-54
- **API call:** Lines ~249-293

**File:** Check for constants file or config

- Look for `OPENROUTER_DEFAULT_MODEL` definition

## Implementation Details

### Model Preset Update
```python
# Step 0 - Query Planner
model_options = [
    "openai/gpt-5-nano",  # New default
    "anthropic/claude-haiku-4.5",  # Second option
    "meta-llama/llama-3.2-3b-instruct",
    "Custom",
]

# Step 2 - AI Filter
model_options = [
    "openai/gpt-5-nano",  # New default
    "anthropic/claude-haiku-4.5",  # Second option
    "meta-llama/llama-3.2-3b-instruct",
    "Custom",
]
```

### Default Model Initialization
```python
# In session state initialization
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "openai/gpt-5-nano"

if 'query_planner_model' not in st.session_state:
    st.session_state.query_planner_model = "openai/gpt-5-nano"
```

### Custom Model Validation Fix
```python
# Check current validation logic
if selected_model_option == "Custom":
    custom_model = st.text_input(...)
    selected_model = custom_model.strip()
    
    # Validation
    if not selected_model:
        st.error("Please enter a custom model name when selecting 'Custom'.")
        selected_model = "openai/gpt-5-nano"  # Fallback
    elif "/" not in selected_model:
        st.error("Custom model must be in format 'provider/model-name' (e.g., 'openai/gpt-5-nano').")
        selected_model = "openai/gpt-5-nano"  # Fallback
    else:
        # Should work - check if there are other validation issues
        st.info(f"Using custom model: {selected_model}")
```

## Testing Checklist

- [ ] Custom model `openai/gpt-5-nano` works in query planner
- [ ] Custom model `openai/gpt-5-nano` works in AI filter
- [ ] Model presets updated in both Step 0 and Step 2
- [ ] Default model is `openai/gpt-5-nano`
- [ ] Second option is `anthropic/claude-haiku-4.5`
- [ ] Invalid model formats show clear errors
- [ ] Fallback to default works correctly
- [ ] No console errors

## Debugging Steps

1. **Test custom model directly:**
   ```python
   # In video_filter.py, test with openai/gpt-5-nano
   test_result = _test_openrouter_connection("openai/gpt-5-nano", api_key)
   ```

2. **Check validation logic:**
   - Is the model name being stripped correctly?
   - Is there extra whitespace?
   - Is the "/" check too strict?

3. **Check API call:**
   - Is the model name passed correctly to OpenRouter?
   - Are there any character encoding issues?

## Success Criteria

- Custom models work correctly (especially `openai/gpt-5-nano`)
- Model presets updated and prioritized correctly
- Default model is `openai/gpt-5-nano`
- Clear error messages for invalid models
- No regressions in existing functionality

## Notes

- `openai/gpt-5-nano` is a real working model - the issue is likely in our validation/code
- Check OpenRouter documentation for exact model name format
- Consider adding model name autocomplete or suggestions
- Test with actual API calls to verify fixes
