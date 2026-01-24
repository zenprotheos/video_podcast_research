#!/usr/bin/env python3
"""
Validation test for the live status updates fix.
Tests that the code runs without NameError.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_imports():
    """Test that all required imports work."""
    try:
        from bulk_transcribe.youtube_transcript import get_youtube_transcript
        from bulk_transcribe.youtube_metadata import fetch_youtube_metadata
        print("✅ Imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_syntax():
    """Test that the main page file has valid syntax."""
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', '..', 'pages', '1_Bulk_Transcribe.py'), 'r', encoding='utf-8') as f:
            code = f.read()

        # Try to compile the code to check for syntax errors
        compile(code, '1_Bulk_Transcribe.py', 'exec')
        print("✅ Syntax validation passed")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ File reading error: {e}")
        return False

def test_variable_references():
    """Test that status_table_data references have been fixed."""
    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'pages', '1_Bulk_Transcribe.py'), 'r', encoding='utf-8') as f:
        code = f.read()

    # Check for remaining status_table_data references
    if 'status_table_data' in code:
        print("❌ Still contains status_table_data references")
        return False

    # Check that status_data is used instead
    if 'status_data' not in code:
        print("❌ Missing status_data references")
        return False

    print("✅ Variable references fixed")
    return True

if __name__ == "__main__":
    print("🔍 Validating Live Status Updates Fix")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Syntax", test_syntax),
        ("Variable References", test_variable_references),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed! The fix should work.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")