# Import Analysis Report - Bulk Transcribe Project

## Current Import Patterns Assessment

### Overall Assessment: MODERATE - Needs Standardization

The codebase has inconsistent import patterns with some good practices but several areas needing improvement. Most files follow basic PEP 8 ordering, but there are opportunities for better organization and consistency.

## File-by-File Analysis

### ✅ GOOD: Well-Organized Files

#### `src/bulk_transcribe/video_filter.py`
```python
# GOOD: Module-level imports properly organized
import os
import re
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

import requests

from .youtube_search import VideoSearchItem
```
**Status**: Excellent - follows standards perfectly

#### `src/bulk_transcribe/youtube_search.py`
```python
# GOOD: Clean separation of import groups
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
```
**Status**: Good - proper grouping and ordering

### ⚠️ NEEDS IMPROVEMENT: Minor Issues

#### `src/bulk_transcribe/youtube_transcript.py`
```python
# CURRENT:
import os
from dataclasses import dataclass
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata

# NEEDS: Add commonly used imports
# import requests  # Used in multiple functions
# import time      # Used in multiple functions
```

**Issues**:
- Missing `requests` and `time` at module level (currently in functions)
- Should add these to prevent future scoping issues

#### `pages/1_Bulk_Transcribe.py`
```python
# CURRENT: Good overall structure but could be cleaner
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Local imports with multi-line format (acceptable)
from src.bulk_transcribe.sheet_ingest import (
    ColumnMapping,
    ParsedSheet,
    normalize_rows,
    parse_spreadsheet,
    resolve_column_mapping,
    validate_normalized_rows,
)
from src.bulk_transcribe.session_manager import SessionConfig, SessionManager
```

**Status**: Good - minor improvements possible

### 📊 Import Usage Statistics

#### Most Frequently Used Imports Across Files:
1. `os` - 8 files
2. `typing` imports - 8 files
3. `dataclasses` - 5 files
4. `requests` - 3 files (but inconsistent placement)
5. `json` - 3 files
6. `time` - 2 files (inconsistent placement)

#### Import Pattern Distribution:
- **Module-level only**: 4 files (50%)
- **Mixed (some function-level)**: 3 files (37.5%)
- **Needs improvement**: 1 file (12.5%)

## Recommended Changes

### Phase 1 Priority: Core Module Standardization

#### 1. `src/bulk_transcribe/youtube_transcript.py`
**Add to module level:**
```python
# Add after existing imports
import requests
import time
import json
```

**Remove from functions:**
- `import requests` from `try_deapi_transcription()`
- `import time` from `try_deapi_transcription()`
- `import requests` from `_try_deapi_transcription_once()`

#### 2. Verify Other Files
- `video_filter.py` ✅ Already correct
- `youtube_search.py` ✅ Already correct
- `youtube_metadata.py` ✅ Simple, correct
- `session_manager.py` ✅ Correct
- `transcript_writer.py` ✅ Correct
- `sheet_ingest.py` ✅ Correct
- `utils.py` ✅ Correct
- `direct_input.py` ✅ Correct

### Phase 2: Import Ordering Standardization

#### Ensure consistent grouping across all files:
```python
# 1. Standard library
import os
import sys
import json
import time
from typing import Optional, List, Dict

# 2. Third-party
import requests
import pandas as pd
import streamlit as st

# 3. Local imports
from .utils import helper
from ..common import shared
```

## Implementation Plan

### Step 1: Core Module Updates
1. Update `youtube_transcript.py` with module-level imports
2. Test functionality remains intact
3. Run scoping analyzer to verify no issues

### Step 2: Import Ordering
1. Review all files for consistent ordering
2. Apply standard grouping where needed
3. Run automated formatting tools

### Step 3: Documentation
1. Update import standards document with examples
2. Add file-specific guidelines
3. Create migration checklist

## Risk Assessment

### Low Risk Changes:
- Adding imports to module level (what we already do)
- Reordering existing imports
- Adding blank lines between groups

### Medium Risk Changes:
- Removing function-level imports (need to verify no conflicts)
- Large-scale import reorganization

### Testing Strategy:
1. **Unit tests** for each modified file
2. **Integration tests** for import-dependent functionality
3. **Full application test** after changes
4. **Scoping analyzer** validation

## Success Metrics

### Before Changes:
- ❌ Inconsistent import patterns
- ❌ Potential for scoping issues
- ❌ Mixed module/function-level imports

### After Changes:
- ✅ 100% consistent import patterns
- ✅ All frequently-used imports at module level
- ✅ Clear separation of import groups
- ✅ Zero detectable scoping issues

## Timeline

- **Analysis**: Complete ✅
- **Core Changes**: 30-45 minutes
- **Testing**: 30-45 minutes
- **Documentation**: 15-20 minutes
- **Total**: ~2 hours

## Next Steps

1. Implement changes to `youtube_transcript.py`
2. Test functionality
3. Run scoping analyzer
4. Update documentation
5. Move to Phase 2 (code quality infrastructure)