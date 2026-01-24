# Python Import Standards & Best Practices

## Overview
This document defines the import organization standards for the Bulk Transcribe project, ensuring consistency, preventing scoping issues, and improving code maintainability.

## Core Principles

### 1. Module-Level vs Function-Level Imports

#### **Module-Level Imports** (Preferred)
Use for frequently-used, lightweight dependencies that are needed throughout the module:

```python
# ✅ GOOD: Module-level imports
import os
import sys
from typing import Optional, List, Dict
import requests
import pandas as pd

from .utils import format_text
from .config import settings
```

#### **Function-Level Imports** (Limited Use)
Use only for:
- Heavy libraries loaded on-demand
- Optional dependencies
- Platform-specific imports
- Libraries that may not be available in all environments

```python
# ✅ ACCEPTABLE: Function-level imports
def process_large_dataset(data):
    # Heavy library loaded only when needed
    import pandas as pd
    import numpy as np
    # ... process data
```

### 2. Import Ordering & Grouping

#### **Standard Order** (PEP 8 Compliant)

```python
# 1. Standard library imports
import os
import sys
from typing import Optional, List, Dict
from pathlib import Path

# 2. Third-party imports
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# 3. Local/project imports
from .utils import format_text
from .config import settings
from ..common.helpers import validate_input
```

#### **Grouping Rules**
- **One import per line** (except for specific exceptions)
- **Blank line** between import groups
- **Alphabetical order** within each group
- **Relative imports** for local modules

### 3. Import Patterns to Avoid

#### **❌ Anti-Patterns**

```python
# ❌ Wildcard imports
from module import *

# ❌ Multiple imports on one line
import os, sys, json

# ❌ Inconsistent ordering
import pandas as pd
import os  # stdlib after third-party

# ❌ Deep relative imports in complex hierarchies
from ../../../../very/deep/module import something
```

#### **✅ Correct Patterns**

```python
# ✅ Explicit imports
from module import ClassName, function_name

# ✅ One import per line
import os
import sys
import json

# ✅ Consistent ordering
import os
import sys
import pandas as pd

# ✅ Shallow relative imports
from .utils import helper
from ..common import shared_function
```

## Specific Guidelines for Bulk Transcribe

### Core Dependencies (Module-Level)

```python
# Always import at module level in these files:
import os
import sys
from typing import Optional, List, Dict, Tuple
import requests
import time
import json
from pathlib import Path
```

### File-Specific Standards

#### `youtube_transcript.py`
```python
# Module-level imports
import os
import time
from typing import Optional
import requests

# Third-party imports
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Local imports
from .youtube_metadata import fetch_youtube_metadata
```

#### `video_filter.py`
```python
# Module-level imports
import os
import re
from typing import List, Optional, Tuple
import requests
```

#### UI Files (Streamlit pages)
```python
# Module-level imports
import os
from typing import Optional, Dict
import pandas as pd
import streamlit as st

# Local imports
from src.bulk_transcribe.session_manager import SessionManager
from src.bulk_transcribe.sheet_ingest import parse_spreadsheet
```

## Implementation Strategy

### Phase 1: Analysis & Planning
1. **Audit current imports** across all Python files
2. **Identify inconsistencies** and scoping issues
3. **Categorize imports** by usage patterns
4. **Create migration plan** for problematic imports

### Phase 2: Refactoring
1. **Start with core modules** (`youtube_transcript.py`, `video_filter.py`)
2. **Move appropriate imports** to module level
3. **Update import ordering** to follow standards
4. **Test after each change** to ensure functionality

### Phase 3: Validation
1. **Run scoping analyzer** to verify no issues
2. **Test all functionality** after changes
3. **Update documentation** with new patterns
4. **Create examples** for future development

## Tools & Automation

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black", "--check-only", "--diff"]

  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3
```

### Static Analysis
```ini
# .flake8 or setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .venv, __pycache__, .git
```

## Common Issues & Solutions

### Issue: Scoping Problems
```python
# ❌ PROBLEMATIC
def outer_function():
    import requests  # Only available here

    def inner_function():
        response = requests.get(url)  # NameError!

# ✅ SOLUTION
import requests  # Module level

def outer_function():
    def inner_function():
        response = requests.get(url)  # Works!
```

### Issue: Heavy Imports
```python
# ✅ SOLUTION: Lazy loading for heavy libraries
def process_data():
    import pandas as pd  # Loaded only when needed
    # ... use pandas
```

### Issue: Circular Imports
```python
# ✅ SOLUTION: Move shared imports to separate module
# shared_deps.py
import requests
import json

# module_a.py
from .shared_deps import requests, json

# module_b.py
from .shared_deps import requests, json
```

## Migration Checklist

- [ ] Audit all Python files for import patterns
- [ ] Identify files needing import refactoring
- [ ] Create backup branch before changes
- [ ] Test each file after import changes
- [ ] Run full test suite after migration
- [ ] Update documentation and examples
- [ ] Train team on new standards

## Benefits

### Maintainability
- **Consistent patterns** across codebase
- **Easier code reviews** with standard formats
- **Reduced cognitive load** for developers

### Reliability
- **Prevents scoping issues** that cause runtime errors
- **Clearer dependencies** for each module
- **Easier debugging** with organized imports

### Performance
- **Lazy loading** for heavy libraries when appropriate
- **Reduced import time** for frequently used modules
- **Better module loading** efficiency

### Developer Experience
- **Automated formatting** with pre-commit hooks
- **Clear standards** reduce decision fatigue
- **Consistent tooling** across team members