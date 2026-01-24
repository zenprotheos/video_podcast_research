#!/usr/bin/env python3
"""
Test Error Reporting Accuracy

Ensures that status messages accurately reflect actual errors,
preventing misleading debugging information.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from pages.bulk_transcribe import categorize_error, update_status_safe

def test_error_categorization():
    """Test that errors are categorized accurately."""
    print("Testing Error Categorization Accuracy")
    print("=" * 50)

    test_cases = [
        # (input_error, expected_icon, expected_description_contains)
        ("NameError: status_table_data not defined", "💥", "Code bug"),
        ("Rate limit exceeded", "⏸️", "Rate limited"),
        ("HTTP 429", "⏸️", "Rate limited"),
        ("Insufficient credits", "💰", "Credits exhausted"),
        ("HTTP 402", "💰", "Credits exhausted"),
        ("Unauthorized", "🔐", "API key invalid"),
        ("HTTP 401", "🔐", "API key invalid"),
        ("Request timeout", "⏰", "Request timeout"),
        ("Network error", "🌐", "Network error"),
        ("Video unavailable", "🚫", "Video unavailable"),
        ("Private video", "🔒", "Private video"),
        ("Unknown error xyz", "❌", "Unknown error xyz"),
    ]

    passed = 0
    total = len(test_cases)

    for error_msg, expected_icon, expected_desc in test_cases:
        icon, desc = categorize_error(error_msg)

        icon_correct = icon == expected_icon
        desc_correct = expected_desc in desc

        if icon_correct and desc_correct:
            print(f"✅ '{error_msg[:30]}...' → {icon} {desc}")
            passed += 1
        else:
            print(f"❌ '{error_msg[:30]}...' → {icon} {desc} (expected {expected_icon} + '{expected_desc}')")

    print(f"\nError categorization: {passed}/{total} passed")
    return passed == total

def test_code_error_flag():
    """Test that code errors are marked properly."""
    print("\nTesting Code Error Flag")
    print("=" * 30)

    # Test with code error flag
    icon, desc = categorize_error("Some error", is_code_error=True)
    if icon == "💥" and "Code bug" in desc:
        print("✅ Code error flag works correctly")
        return True
    else:
        print(f"❌ Code error flag failed: {icon} {desc}")
        return False

def test_status_update_safety():
    """Test that status updates don't crash."""
    print("\nTesting Status Update Safety")
    print("=" * 35)

    # Mock status table
    class MockTable:
        def dataframe(self, df):
            pass  # Mock implementation

    mock_table = MockTable()
    status_data = []

    # Test normal update
    test_status = {"Status": "✅ Success", "Error": "None"}
    result = update_status_safe(status_data, test_status, mock_table)

    if result and len(status_data) == 1:
        print("✅ Normal status update works")
        return True
    else:
        print("❌ Normal status update failed")
        return False

def validate_bulk_transcribe_error_handling():
    """Validate that the main file has proper error handling."""
    print("\nValidating Bulk Transcribe Error Handling")
    print("=" * 45)

    with open(os.path.join(os.path.dirname(__file__), '..', '..', 'pages', '1_Bulk_Transcribe.py'), 'r', encoding='utf-8') as f:
        code = f.read()

    checks = [
        ("categorize_error function defined", "def categorize_error" in code),
        ("update_status_safe function defined", "def update_status_safe" in code),
        ("Processing wrapped in try/catch", "try:" in code and "except Exception as processing_error:" in code),
        ("Crash status handling", "processing_crashed = True" in code),
        ("Accurate crash reporting", "Code error:" in code),
    ]

    passed = 0
    for check_name, check_result in checks:
        if check_result:
            print(f"✅ {check_name}")
            passed += 1
        else:
            print(f"❌ {check_name}")

    print(f"\nCode validation: {passed}/{len(checks)} passed")
    return passed == len(checks)

if __name__ == "__main__":
    print("🔍 Error Reporting Accuracy Validation")
    print("=" * 50)

    tests = [
        test_error_categorization,
        test_code_error_flag,
        test_status_update_safety,
        validate_bulk_transcribe_error_handling,
    ]

    passed = 0
    for test_func in tests:
        if test_func():
            passed += 1

    print(f"\n{'='*50}")
    print(f"OVERALL RESULT: {passed}/{len(tests)} test suites passed")

    if passed == len(tests):
        print("🎉 All error reporting tests passed!")
        print("✅ Status messages will now accurately reflect actual errors")
        print("✅ No more misleading 'rate limited' messages for code bugs")
    else:
        print("⚠️ Some tests failed - error reporting may still be misleading")
        print("🔧 Please fix the failing tests before deploying")