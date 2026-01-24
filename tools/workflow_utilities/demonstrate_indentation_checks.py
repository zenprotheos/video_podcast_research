#!/usr/bin/env python3
"""
Demonstration of programmatic indentation checking methods
"""

import ast
import py_compile
import os

def demonstrate_py_compile_check():
    """Demonstrate py_compile syntax checking."""
    print("🔧 Method 1: py_compile syntax validation")
    print("-" * 40)

    try:
        # This will catch IndentationError and other syntax issues
        py_compile.compile('pages/1_Bulk_Transcribe.py', doraise=True)
        print("✅ No syntax errors detected")
    except IndentationError as e:
        print(f"❌ IndentationError detected: {e}")
    except SyntaxError as e:
        print(f"❌ SyntaxError detected: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

def demonstrate_ast_parsing():
    """Demonstrate AST parsing for syntax validation."""
    print("\n🔧 Method 2: AST parsing validation")
    print("-" * 40)

    try:
        with open('pages/1_Bulk_Transcribe.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST - this catches syntax errors including indentation
        ast.parse(content, 'pages/1_Bulk_Transcribe.py')
        print("✅ AST parsing successful - no syntax errors")
    except IndentationError as e:
        print(f"❌ IndentationError in AST: {e}")
    except SyntaxError as e:
        print(f"❌ SyntaxError in AST: {e}")
    except Exception as e:
        print(f"❌ AST parsing failed: {e}")

def demonstrate_import_test():
    """Demonstrate import testing for module validation."""
    print("\n🔧 Method 3: Import testing")
    print("-" * 40)

    # This would test if the module can be imported without syntax errors
    print("Note: Import testing would be done like this:")
    print("python -c \"import sys; sys.path.insert(0, 'pages'); import bulk_transcribe_page\"")
    print("(Renaming would be needed for proper import)")

def demonstrate_pattern_analysis():
    """Demonstrate basic indentation pattern analysis."""
    print("\n🔧 Method 4: Pattern analysis")
    print("-" * 40)

    try:
        with open('pages/1_Bulk_Transcribe.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        issues = []
        for i, line in enumerate(lines, 1):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check indentation
            leading_spaces = len(line) - len(line.lstrip())

            # Check for tabs (should use spaces)
            if '\t' in line[:leading_spaces]:
                issues.append(f"Line {i}: Contains tabs instead of spaces")

            # Check for non-multiple of 4 spaces
            if leading_spaces > 0 and leading_spaces % 4 != 0:
                issues.append(f"Line {i}: {leading_spaces} spaces (should be multiple of 4)")

        if issues:
            print("❌ Indentation pattern issues found:")
            for issue in issues[:5]:  # Show first 5
                print(f"  • {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
        else:
            print("✅ No obvious indentation pattern issues")

    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")

def main():
    """Run all demonstrations."""
    print("🔍 PROGRAMMATIC INDENTATION CHECKING METHODS")
    print("=" * 60)
    print("These methods can detect indentation issues before runtime:")
    print()

    # Change to project root
    os.chdir('..')

    demonstrate_py_compile_check()
    demonstrate_ast_parsing()
    demonstrate_import_test()
    demonstrate_pattern_analysis()

    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS:")
    print("• Run py_compile check after any structural code changes")
    print("• Use AST parsing for deeper syntax validation")
    print("• Implement pre-commit hooks with these checks")
    print("• Add these to CI/CD pipelines for automated validation")

if __name__ == "__main__":
    main()