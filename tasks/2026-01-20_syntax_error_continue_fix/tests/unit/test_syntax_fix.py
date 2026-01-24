#!/usr/bin/env python3
"""
Unit test to verify the syntax error fix for continue statement
"""
import unittest
import ast
import os

class TestSyntaxFix(unittest.TestCase):
    """Test that the syntax error has been fixed"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        self.fixed_file = os.path.join(self.project_root, 'pages', '1_Bulk_Transcribe.py')

    def test_file_exists(self):
        """Test that the file exists"""
        self.assertTrue(os.path.exists(self.fixed_file), f"File not found: {self.fixed_file}")

    def test_syntax_valid(self):
        """Test that the file has valid Python syntax"""
        with open(self.fixed_file, 'r', encoding='utf-8') as f:
            code = f.read()

        # This will raise SyntaxError if syntax is invalid
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.fail(f"Syntax error in {self.fixed_file}: {e}")

    def test_continue_statements_exist(self):
        """Test that continue statements exist in the expected locations"""
        with open(self.fixed_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check that continue statements exist on the expected lines
        continue_lines = []
        for i, line in enumerate(lines, 1):
            if 'continue' in line.strip():
                continue_lines.append(i)

        # Should have continue statements (we know there are 2)
        self.assertGreaterEqual(len(continue_lines), 2, f"Expected at least 2 continue statements, found {len(continue_lines)}")

        # Verify they're in the expected line range (around 238 and 247)
        self.assertTrue(any(235 <= line <= 245 for line in continue_lines), "Continue statement not found near line 238")
        self.assertTrue(any(245 <= line <= 250 for line in continue_lines), "Continue statement not found near line 247")

if __name__ == '__main__':
    unittest.main()