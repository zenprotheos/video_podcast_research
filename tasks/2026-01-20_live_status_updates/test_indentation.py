#!/usr/bin/env python3
"""
Test Indentation Fix

Simple test to verify the IndentationError is resolved.
"""

def test_indentation():
    """Test that the file can be parsed without IndentationError."""
    try:
        with open('../pages/1_Bulk_Transcribe.py', 'r', encoding='utf-8') as f:
            code = f.read()

        # Try to compile to check for syntax errors
        compile(code, '1_Bulk_Transcribe.py', 'exec')
        print("✅ IndentationError FIXED - file compiles successfully")
        return True

    except IndentationError as e:
        print(f"❌ IndentationError still exists: {e}")
        print(f"   Line {e.lineno}: {repr(e.text)}")
        return False

    except SyntaxError as e:
        print(f"❌ Other SyntaxError: {e}")
        return False

    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Indentation Fix")
    print("=" * 40)

    if test_indentation():
        print("\n🎉 SUCCESS: The IndentationError has been resolved!")
        print("   The live status updates should now work correctly.")
    else:
        print("\n❌ FAILURE: Indentation issues remain.")
        print("   Please check the indentation around the for loop.")