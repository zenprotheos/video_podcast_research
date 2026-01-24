#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Script
Analyzes all Python files for syntax, structure, and potential issues
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict

class CodeAnalyzer:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.results = {
            'syntax_errors': [],
            'files_analyzed': 0,
            'total_lines': 0,
            'imports': defaultdict(int),
            'functions': [],
            'classes': [],
            'try_blocks': [],
            'complexity_warnings': []
        }

    def analyze_file(self, file_path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            self.results['files_analyzed'] += 1
            self.results['total_lines'] += len(lines)

            # Syntax validation
            try:
                tree = ast.parse(content, str(file_path))
            except SyntaxError as e:
                self.results['syntax_errors'].append({
                    'file': str(file_path),
                    'line': e.lineno,
                    'error': e.msg,
                    'text': e.text
                })
                return

            # Analyze AST
            self._analyze_ast(tree, file_path)

            # Analyze imports
            self._analyze_imports(content, file_path)

            # Check for complexity issues
            self._check_complexity(content, file_path, lines)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _analyze_ast(self, tree, file_path):
        """Analyze AST nodes"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.results['functions'].append({
                    'file': str(file_path),
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args)
                })
            elif isinstance(node, ast.ClassDef):
                self.results['classes'].append({
                    'file': str(file_path),
                    'name': node.name,
                    'line': node.lineno
                })
            elif isinstance(node, ast.Try):
                self.results['try_blocks'].append({
                    'file': str(file_path),
                    'line': node.lineno,
                    'handlers': len(node.handlers)
                })

    def _analyze_imports(self, content, file_path):
        """Analyze import statements"""
        import_lines = re.findall(r'^(?:from\s+\S+\s+import|import\s+\S+)', content, re.MULTILINE)
        for line in import_lines:
            self.results['imports'][line.strip()] += 1

    def _check_complexity(self, content, file_path, lines):
        """Check for potential complexity issues"""
        # Long functions (>50 lines)
        in_function = False
        func_start = 0
        func_name = ""

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('def '):
                if in_function:
                    func_length = i - func_start
                    if func_length > 50:
                        self.results['complexity_warnings'].append({
                            'type': 'long_function',
                            'file': str(file_path),
                            'name': func_name,
                            'lines': func_length,
                            'start': func_start,
                            'end': i
                        })
                in_function = True
                func_start = i
                # Extract function name
                match = re.match(r'def\s+(\w+)', line.strip())
                if match:
                    func_name = match.group(1)
            elif line.strip() == '' and in_function:
                # End of function (empty line after)
                func_length = i - func_start
                if func_length > 50:
                    self.results['complexity_warnings'].append({
                        'type': 'long_function',
                        'file': str(file_path),
                        'name': func_name,
                        'lines': func_length,
                        'start': func_start,
                        'end': i
                    })
                in_function = False

    def analyze_directory(self):
        """Analyze all Python files in directory"""
        for root, dirs, files in os.walk(self.root_path):
            # Skip common exclude directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv']]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    self.analyze_file(file_path)

    def generate_report(self):
        """Generate analysis report"""
        report = []
        report.append("# Codebase Analysis Report")
        report.append(f"Files analyzed: {self.results['files_analyzed']}")
        report.append(f"Total lines: {self.results['total_lines']}")
        report.append("")

        # Syntax errors
        if self.results['syntax_errors']:
            report.append("## 🚨 Syntax Errors")
            for error in self.results['syntax_errors']:
                report.append(f"- **{error['file']}** line {error['line']}: {error['error']}")
                report.append(f"  `{error['text'].strip()}`")
            report.append("")
        else:
            report.append("## ✅ No Syntax Errors Found")
            report.append("")

        # Complexity warnings
        if self.results['complexity_warnings']:
            report.append("## ⚠️ Complexity Warnings")
            for warning in self.results['complexity_warnings']:
                report.append(f"- **{warning['type']}**: `{warning['name']}` in {warning['file']} ({warning['lines']} lines)")
            report.append("")

        # Structure summary
        report.append("## 📊 Code Structure")
        report.append(f"- Functions: {len(self.results['functions'])}")
        report.append(f"- Classes: {len(self.results['classes'])}")
        report.append(f"- Try blocks: {len(self.results['try_blocks'])}")
        report.append("")

        # Top imports
        if self.results['imports']:
            report.append("## 📦 Most Used Imports")
            sorted_imports = sorted(self.results['imports'].items(), key=lambda x: x[1], reverse=True)[:10]
            for imp, count in sorted_imports:
                report.append(f"- `{imp}` ({count} times)")
            report.append("")

        return "\n".join(report)

def main():
    analyzer = CodeAnalyzer(".")
    analyzer.analyze_directory()
    report = analyzer.generate_report()

    with open("tasks/2026-01-20_syntax_error_analysis_and_e2e_setup/analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("Analysis complete. Report saved to analysis_report.md")

if __name__ == "__main__":
    main()