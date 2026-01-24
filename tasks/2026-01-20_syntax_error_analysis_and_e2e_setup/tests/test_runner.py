#!/usr/bin/env python3
"""
Test Runner for Bulk Transcribe E2E Tests
Runs comprehensive test suite with reporting
"""

import subprocess
import sys
from pathlib import Path
import pytest
import json
from datetime import datetime

class TestRunner:
    """Comprehensive test runner for the Bulk Transcribe application"""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent
        self.results = {}

    def run_syntax_validation(self):
        """Run syntax validation on all Python files"""
        print("🔍 Running syntax validation...")

        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip common exclude directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv']]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        syntax_errors = []
        for file_path in python_files:
            try:
                compile(open(file_path, 'r', encoding='utf-8').read(), str(file_path), 'exec')
            except SyntaxError as e:
                syntax_errors.append({
                    'file': str(file_path),
                    'line': e.lineno,
                    'error': e.msg,
                    'text': e.text
                })

        self.results['syntax_validation'] = {
            'total_files': len(python_files),
            'errors': syntax_errors,
            'passed': len(syntax_errors) == 0
        }

        return len(syntax_errors) == 0

    def run_unit_tests(self):
        """Run unit tests"""
        print("🧪 Running unit tests...")

        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                str(self.test_dir),
                '-v',
                '--tb=short',
                '--json-report',
                '--json-report-file=' + str(self.test_dir / 'test_results.json')
            ], capture_output=True, text=True, cwd=self.project_root)

            # Parse results if available
            results_file = self.test_dir / 'test_results.json'
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_data = json.load(f)
                self.results['unit_tests'] = {
                    'passed': test_data.get('passed', 0),
                    'failed': test_data.get('failed', 0),
                    'errors': test_data.get('errors', 0),
                    'duration': test_data.get('duration', 0),
                    'success': result.returncode == 0
                }
            else:
                self.results['unit_tests'] = {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'errors': result.stderr
                }

            return result.returncode == 0

        except Exception as e:
            self.results['unit_tests'] = {
                'success': False,
                'error': str(e)
            }
            return False

    def run_import_tests(self):
        """Test that all modules can be imported"""
        print("📦 Testing module imports...")

        import_errors = []

        # Test core modules
        modules_to_test = [
            'src.bulk_transcribe.session_manager',
            'src.bulk_transcribe.youtube_metadata',
            'src.bulk_transcribe.youtube_transcript',
            'src.bulk_transcribe.transcript_writer',
            'src.bulk_transcribe.sheet_ingest',
            'src.bulk_transcribe.video_filter',
            'src.bulk_transcribe.utils'
        ]

        for module in modules_to_test:
            try:
                __import__(module)
            except Exception as e:
                import_errors.append({
                    'module': module,
                    'error': str(e)
                })

        self.results['import_tests'] = {
            'total_modules': len(modules_to_test),
            'errors': import_errors,
            'passed': len(import_errors) == 0
        }

        return len(import_errors) == 0

    def generate_report(self):
        """Generate comprehensive test report"""
        report = []
        report.append("# Bulk Transcribe Test Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Syntax validation
        syntax = self.results.get('syntax_validation', {})
        report.append("## 🔍 Syntax Validation")
        report.append(f"- Files checked: {syntax.get('total_files', 0)}")
        if syntax.get('errors'):
            report.append(f"- Errors found: {len(syntax['errors'])} ❌")
            for error in syntax['errors']:
                report.append(f"  - {error['file']}:{error['line']} - {error['error']}")
        else:
            report.append("- Status: ✅ PASSED")
        report.append("")

        # Import tests
        imports = self.results.get('import_tests', {})
        report.append("## 📦 Import Tests")
        report.append(f"- Modules tested: {imports.get('total_modules', 0)}")
        if imports.get('errors'):
            report.append(f"- Import errors: {len(imports['errors'])} ❌")
            for error in imports['errors']:
                report.append(f"  - {error['module']}: {error['error']}")
        else:
            report.append("- Status: ✅ PASSED")
        report.append("")

        # Unit tests
        unit = self.results.get('unit_tests', {})
        report.append("## 🧪 Unit Tests")
        if 'passed' in unit:
            report.append(f"- Passed: {unit['passed']}")
            report.append(f"- Failed: {unit['failed']}")
            report.append(f"- Errors: {unit['errors']}")
            report.append(".2f")
            report.append(f"- Status: {'✅ PASSED' if unit.get('success') else '❌ FAILED'}")
        else:
            report.append(f"- Status: {'✅ PASSED' if unit.get('success') else '❌ FAILED'}")
        report.append("")

        # Overall status
        all_passed = all([
            syntax.get('passed', False),
            imports.get('passed', False),
            unit.get('success', False)
        ])

        report.append("## 📊 Overall Status")
        report.append(f"- Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        return "\n".join(report)

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Bulk Transcribe Test Suite")
        print("=" * 50)

        results = []

        # Run all test phases
        results.append(("Syntax Validation", self.run_syntax_validation()))
        results.append(("Import Tests", self.run_import_tests()))
        results.append(("Unit Tests", self.run_unit_tests()))

        print("\n" + "=" * 50)
        print("📋 Test Results Summary:")
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name}: {status}")

        all_passed = all(passed for _, passed in results)
        print(f"\n🏁 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        # Generate and save report
        report = self.generate_report()
        report_file = self.test_dir / "test_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📄 Detailed report saved to: {report_file}")
        return all_passed

if __name__ == "__main__":
    import os
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)