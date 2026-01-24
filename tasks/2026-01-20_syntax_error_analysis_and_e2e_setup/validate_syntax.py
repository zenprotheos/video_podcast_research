#!/usr/bin/env python3
"""
Simple syntax validation script
"""

import ast
import sys
from pathlib import Path

def validate_syntax(file_path):
    """Validate Python syntax using AST parsing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse the AST
        tree = ast.parse(source, file_path)
        print(f"✅ SUCCESS: {file_path} - Syntax is valid")
        return True

    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR in {file_path}:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False

    except Exception as e:
        print(f"❌ OTHER ERROR in {file_path}: {e}")
        return False

if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "pages" / "1_Bulk_Transcribe.py"
    success = validate_syntax(file_path)
    sys.exit(0 if success else 1)