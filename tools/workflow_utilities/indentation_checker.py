#!/usr/bin/env python3
"""
Indentation Checker - Programmatic detection of Python indentation issues

This tool provides multiple methods to detect indentation problems before runtime.
"""

import os
import sys
import ast
import py_compile
import re
from typing import List, Tuple, Optional


class IndentationChecker:
    """Comprehensive indentation validation for Python files."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.lines = []

    def load_file(self) -> bool:
        """Load file content and split into lines."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.lines = self.content.splitlines()
            return True
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False

    def check_py_compile(self) -> Tuple[bool, str]:
        """Use py_compile to detect syntax errors including indentation."""
        try:
            py_compile.compile(self.file_path, doraise=True)
            return True, "✅ Syntax validation passed"
        except py_compile.PyCompileError as e:
            return False, f"❌ PyCompileError: {e}"
        except IndentationError as e:
            return False, f"❌ IndentationError: {e}"
        except SyntaxError as e:
            return False, f"❌ SyntaxError: {e}"
        except Exception as e:
            return False, f"❌ Unexpected error: {e}"

    def check_ast_parse(self) -> Tuple[bool, str]:
        """Use AST parsing to detect syntax errors."""
        try:
            ast.parse(self.content, self.file_path)
            return True, "✅ AST parsing passed"
        except IndentationError as e:
            return False, f"❌ IndentationError: {e}"
        except SyntaxError as e:
            return False, f"❌ SyntaxError: {e}"
        except Exception as e:
            return False, f"❌ AST parsing failed: {e}"

    def check_import_test(self) -> Tuple[bool, str]:
        """Test if file can be imported (module-level validation)."""
        # Get module name from file path
        file_name = os.path.basename(self.file_path)
        if not file_name.endswith('.py'):
            return False, "❌ Not a Python file"

        module_name = file_name[:-3]  # Remove .py extension

        # Add current directory to path temporarily
        current_dir = os.path.dirname(os.path.abspath(self.file_path))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        try:
            # Remove from cache if already imported
            if module_name in sys.modules:
                del sys.modules[module_name]

            __import__(module_name)
            return True, f"✅ Import test passed for {module_name}"
        except IndentationError as e:
            return False, f"❌ IndentationError on import: {e}"
        except SyntaxError as e:
            return False, f"❌ SyntaxError on import: {e}"
        except Exception as e:
            return False, f"⚠️ Import failed (may be expected): {e}"
        finally:
            # Clean up path
            if current_dir in sys.path:
                sys.path.remove(current_dir)

    def analyze_indentation_patterns(self) -> List[str]:
        """Analyze indentation patterns for inconsistencies."""
        issues = []

        for i, line in enumerate(self.lines, 1):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Count leading spaces
            leading_spaces = len(line) - len(line.lstrip())

            # Check for mixed tabs and spaces
            if '\t' in line[:leading_spaces]:
                issues.append(f"Line {i}: Mixed tabs and spaces in indentation")

            # Check for unusual indentation (not multiple of 4)
            if leading_spaces > 0 and leading_spaces % 4 != 0:
                issues.append(f"Line {i}: Indentation not multiple of 4 spaces ({leading_spaces} spaces)")

        return issues

    def check_control_flow_indentation(self) -> List[str]:
        """Check for missing indentation after control flow statements."""
        issues = []
        control_flow_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'def', 'class']

        i = 0
        while i < len(self.lines) - 1:  # -1 to avoid index error
            line = self.lines[i].strip()

            # Check if this line ends with a control flow keyword followed by colon
            for keyword in control_flow_keywords:
                if line.startswith(keyword + ' ') and line.endswith(':'):
                    # Check next non-empty line
                    next_line_idx = i + 1
                    while next_line_idx < len(self.lines):
                        next_line = self.lines[next_line_idx]
                        next_stripped = next_line.strip()

                        if next_stripped and not next_stripped.startswith('#'):
                            # This should be indented more than the control flow line
                            current_indent = len(self.lines[i]) - len(self.lines[i].lstrip())
                            next_indent = len(next_line) - len(next_line.lstrip())

                            if next_indent <= current_indent:
                                issues.append(f"Line {next_line_idx + 1}: Missing indentation after '{keyword}' statement")
                            break

                        next_line_idx += 1
                    break

            i += 1

        return issues

    def run_all_checks(self) -> dict:
        """Run all indentation and syntax checks."""
        if not self.load_file():
            return {"error": "Could not load file"}

        results = {
            "file": self.file_path,
            "checks": {},
            "issues": []
        }

        # Run validation checks
        checks = [
            ("py_compile", self.check_py_compile),
            ("ast_parse", self.check_ast_parse),
            ("import_test", self.check_import_test),
        ]

        all_passed = True
        for check_name, check_func in checks:
            passed, message = check_func()
            results["checks"][check_name] = {
                "passed": passed,
                "message": message
            }
            if not passed:
                all_passed = False

        # Run analysis checks
        pattern_issues = self.analyze_indentation_patterns()
        control_flow_issues = self.check_control_flow_indentation()

        results["issues"] = pattern_issues + control_flow_issues
        results["all_passed"] = all_passed and len(results["issues"]) == 0

        return results


def main():
    """Main function for command-line usage."""
    if len(sys.argv) != 2:
        print("Usage: python indentation_checker.py <python_file>")
        print("\nThis tool provides multiple programmatic ways to check Python indentation:")
        print("1. py_compile - Built-in Python syntax checker")
        print("2. AST parsing - Abstract syntax tree validation")
        print("3. Import testing - Module-level validation")
        print("4. Pattern analysis - Indentation consistency checks")
        print("5. Control flow analysis - Missing indentation detection")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    checker = IndentationChecker(file_path)
    results = checker.run_all_checks()

    print(f"🔍 Indentation Check Results for: {results['file']}")
    print("=" * 60)

    # Show check results
    for check_name, check_result in results["checks"].items():
        status = "✅ PASS" if check_result["passed"] else "❌ FAIL"
        print(f"{status} {check_name}: {check_result['message']}")

    print()

    # Show issues
    if results["issues"]:
        print("🚨 INDENTATION ISSUES FOUND:")
        for issue in results["issues"]:
            print(f"  • {issue}")
    else:
        print("✅ No indentation issues detected")

    print()
    print(f"🎯 OVERALL RESULT: {'✅ ALL CHECKS PASSED' if results['all_passed'] else '❌ ISSUES FOUND'}")

    # Exit with appropriate code
    sys.exit(0 if results["all_passed"] else 1)


if __name__ == "__main__":
    main()