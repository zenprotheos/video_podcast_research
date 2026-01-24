#!/usr/bin/env python3
"""
Syntax Analysis Script for Bulk Transcribe App
Analyzes indentation and try/except block structure
"""

import ast
import re
from pathlib import Path

def analyze_file_structure(file_path):
    """Analyze the structure of a Python file, focusing on indentation and try/except blocks"""

    print(f"Analyzing file: {file_path}")
    print("=" * 60)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find try/except blocks
        try_blocks = []
        except_blocks = []
        finally_blocks = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('try:'):
                indent_level = len(line) - len(line.lstrip())
                try_blocks.append((i, indent_level, stripped))
            elif stripped.startswith('except'):
                indent_level = len(line) - len(line.lstrip())
                except_blocks.append((i, indent_level, stripped))
            elif stripped.startswith('finally:'):
                indent_level = len(line) - len(line.lstrip())
                finally_blocks.append((i, indent_level, stripped))

        print("TRY BLOCKS FOUND:")
        for line_num, indent, code in try_blocks:
            print(f"  Line {line_num}: {'  ' * (indent//4)}{code}")

        print("\nEXCEPT BLOCKS FOUND:")
        for line_num, indent, code in except_blocks:
            print(f"  Line {line_num}: {'  ' * (indent//4)}{code}")

        print("\nFINALLY BLOCKS FOUND:")
        for line_num, indent, code in finally_blocks:
            print(f"  Line {line_num}: {'  ' * (indent//4)}{code}")

        # Check for mismatched blocks
        print("\nANALYSIS:")
        if len(try_blocks) != len(except_blocks) + len(finally_blocks):
            print(f"❌ MISMATCH: {len(try_blocks)} try blocks vs {len(except_blocks) + len(finally_blocks)} except/finally blocks")

        # Check indentation consistency
        print("\nINDENTATION ANALYSIS AROUND LINE 522:")
        for i in range(max(1, 522-10), min(len(lines), 522+10)):
            line = lines[i-1]
            indent = len(line) - len(line.lstrip())
            marker = ">>> " if i == 522 else "    "
            print(f"{marker}Line {i:3d} ({indent:2d}): {line.rstrip()}")

        # Try to parse the AST
        print("\nAST PARSING:")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, file_path)
            print("✅ AST parsing successful - no syntax errors detected")
        except SyntaxError as e:
            print(f"❌ AST parsing failed: {e}")
            print(f"   Line {e.lineno}: {e.text}")

    except Exception as e:
        print(f"Error analyzing file: {e}")

if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "pages" / "1_Bulk_Transcribe.py"
    analyze_file_structure(file_path)