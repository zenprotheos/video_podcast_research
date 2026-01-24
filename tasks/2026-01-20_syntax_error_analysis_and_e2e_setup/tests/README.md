# Bulk Transcribe E2E Testing Framework

This directory contains comprehensive end-to-end tests for the Bulk Transcribe application.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_e2e_bulk_transcribe.py # Core E2E workflow tests
├── test_streamlit_integration.py # Streamlit UI integration tests
├── test_runner.py              # Comprehensive test runner script
└── README.md                   # This file
```

## Test Categories

### 1. End-to-End Tests (`test_e2e_bulk_transcribe.py`)
- **Complete workflow testing**: Single video processing
- **Batch processing**: Multiple videos with mixed success/failure
- **Error handling**: Rate limits, invalid URLs, network issues
- **Output validation**: File generation and formatting
- **Session management**: Session creation and cleanup

### 2. Streamlit Integration Tests (`test_streamlit_integration.py`)
- **UI component testing**: Sidebar, containers, data display
- **File upload handling**: CSV/Excel validation and processing
- **Progress display**: Status updates and progress tracking
- **Error display**: User-friendly error message formatting
- **Session state management**: State persistence and updates

### 3. Validation Tests (`test_runner.py`)
- **Syntax validation**: All Python files compile correctly
- **Import testing**: All modules can be imported without errors
- **Unit test execution**: Automated pytest execution with reporting

## Running Tests

### Option 1: Comprehensive Test Runner (Recommended)
```bash
cd tasks/2026-01-20_syntax_error_analysis_and_e2e_setup
python tests/test_runner.py
```

This runs:
- Syntax validation on all Python files
- Import tests for all modules
- Complete unit test suite
- Generates detailed report (`tests/test_report.md`)

### Option 2: Individual Test Files
```bash
# Run specific test file
pytest tests/test_e2e_bulk_transcribe.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test class/method
pytest tests/test_streamlit_integration.py::TestErrorDisplay::test_error_message_formatting -v
```

### Option 3: Validation Only
```bash
# Syntax check only
python -c "import ast; [ast.parse(open(f).read()) for f in ['pages/1_Bulk_Transcribe.py', 'app.py'] if f.endswith('.py')]"

# Import check only
python -c "import src.bulk_transcribe.session_manager; print('✅ Imports OK')"
```

## Test Fixtures

### Data Fixtures
- `sample_youtube_urls`: Valid YouTube URLs for testing
- `mock_youtube_metadata`: Mock metadata responses
- `mock_transcript_result`: Mock transcript API responses
- `sample_csv_data`: Sample CSV data as DataFrame
- `sample_csv_file`: Temporary CSV file for upload testing

### Mock Fixtures
- `mock_session_manager`: Mocked session management
- `mock_streamlit_session_state`: Mock Streamlit session state
- `mock_env_variables`: Environment variable mocking

## Test Coverage Areas

### ✅ Implemented
- [x] Syntax validation
- [x] Import testing
- [x] Core E2E workflows
- [x] Error handling scenarios
- [x] File upload processing
- [x] Session state management
- [x] Progress tracking
- [x] Output file generation

### 🚧 Future Enhancements
- [ ] Streamlit UI visual testing
- [ ] Performance/load testing
- [ ] Cross-browser compatibility
- [ ] API integration testing
- [ ] Database persistence testing

## Mock Strategy

The tests use comprehensive mocking to:
- **Isolate units**: Test individual components without external dependencies
- **Control scenarios**: Simulate various success/failure conditions
- **Speed up execution**: Avoid slow network calls and API rate limits
- **Ensure reliability**: Tests don't depend on external service availability

### Key Mocked Components
- YouTube API calls (metadata and transcript fetching)
- File system operations
- Streamlit UI components
- Session management
- External service integrations

## Error Simulation

Tests simulate various error conditions:
- **Rate limiting**: HTTP 429 responses
- **API quota exceeded**: Authentication/credit errors
- **Network timeouts**: Connection failures
- **Invalid URLs**: Malformed YouTube URLs
- **File system errors**: Permission/write failures
- **Corrupted data**: Invalid CSV/Excel formats

## Continuous Integration

### GitHub Actions Setup (Recommended)
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt
    - run: pip install pytest pytest-cov
    - run: python tests/test_runner.py
```

### Pre-commit Hooks
```bash
# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: syntax-check
        name: Python Syntax Check
        entry: python -m py_compile
        language: system
        files: \.py$
      - id: test-suite
        name: Run Test Suite
        entry: python tests/test_runner.py
        language: system
        pass_filenames: false
```

## Test Results and Reporting

### Automatic Reports
- **Test Report**: `tests/test_report.md` - Detailed results summary
- **Coverage Report**: `htmlcov/` - Code coverage visualization
- **JSON Results**: `tests/test_results.json` - Machine-readable results

### Report Contents
- Syntax validation status
- Import test results
- Unit test pass/fail counts
- Error details and stack traces
- Performance metrics
- Coverage percentages

## Debugging Failed Tests

### Common Issues
1. **Import Errors**: Check Python path and module structure
2. **Mock Failures**: Verify mock setup and assertions
3. **Environment Variables**: Ensure test environment variables are set
4. **File Permissions**: Check read/write permissions for test directories

### Debug Commands
```bash
# Run with detailed output
pytest tests/ -v -s --tb=long

# Run specific failing test
pytest tests/test_e2e_bulk_transcribe.py::TestBulkTranscribeE2E::test_complete_workflow_single_video_success -v -s

# Debug imports
python -c "import sys; sys.path.append('.'); import src.bulk_transcribe.session_manager"
```

## Maintenance

### Adding New Tests
1. **Identify test category**: E2E, integration, or unit
2. **Create test file**: Follow naming convention `test_*.py`
3. **Add fixtures**: Use existing fixtures or add new ones in `conftest.py`
4. **Mock dependencies**: Ensure external calls are properly mocked
5. **Update README**: Document new test coverage

### Updating Test Data
- **Sample URLs**: Use reliable, long-lived YouTube videos
- **Mock responses**: Keep consistent with real API responses
- **Test files**: Use small, representative datasets

## Performance Considerations

### Test Execution Time
- **Unit tests**: < 30 seconds
- **Integration tests**: < 2 minutes
- **Full suite**: < 5 minutes

### Resource Usage
- **Memory**: Minimal (mostly mocked operations)
- **Disk**: Temporary files cleaned up automatically
- **Network**: No external calls (all mocked)

## Troubleshooting

### Test Environment Setup
```bash
# Ensure virtual environment is active
source .venv/Scripts/activate  # Windows
source .venv/bin/activate     # Linux/Mac

# Install test dependencies
pip install pytest pytest-mock pytest-cov

# Run setup validation
python -c "import pytest; print('✅ Pytest available')"
```

### Common Error Resolution
- **ModuleNotFoundError**: Check Python path and imports
- **Fixture errors**: Verify fixture definitions in `conftest.py`
- **Mock assertion errors**: Check mock setup and call patterns
- **Streamlit import errors**: Install streamlit in test environment