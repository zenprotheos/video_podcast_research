"""
Pytest configuration and fixtures for Bulk Transcribe E2E tests
"""

import pytest
import tempfile
import os
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, patch

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_youtube_urls():
    """Sample YouTube URLs for testing"""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (reliable test video)
        "https://youtu.be/dQw4w9WgXcQ",  # Short form
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Another test video
    ]

@pytest.fixture
def mock_youtube_metadata():
    """Mock YouTube metadata response"""
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Test Video Title",
        "description": "Test video description",
        "duration": "PT3M33S",
        "channel": "Test Channel",
        "upload_date": "2020-01-01",
        "view_count": "1000000"
    }

@pytest.fixture
def mock_transcript_result():
    """Mock transcript result"""
    return {
        "success": True,
        "transcript_text": "This is a test transcript text.",
        "method": "api",
        "error_message": None
    }

@pytest.fixture
def sample_csv_data(sample_youtube_urls):
    """Create sample CSV data for testing"""
    data = {
        "url": sample_youtube_urls,
        "title": ["Video 1", "Video 2", "Video 3"],
        "description": ["Desc 1", "Desc 2", "Desc 3"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_csv_file(test_data_dir, sample_csv_data):
    """Create a temporary CSV file with sample data"""
    csv_path = test_data_dir / "test_videos.csv"
    sample_csv_data.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing"""
    mock_sm = Mock()
    mock_session = Mock()
    mock_session.youtube_dir = Path("/tmp/test_session")
    mock_session.manifest_path = Path("/tmp/test_session/manifest.json")
    mock_sm.create_session.return_value = mock_session
    return mock_sm

@pytest.fixture(autouse=True)
def mock_env_variables():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'YOUTUBE_API_KEY': 'test_api_key_123',
        'OPENAI_API_KEY': 'test_openai_key_123'
    }):
        yield

@pytest.fixture
def mock_streamlit_session_state():
    """Mock Streamlit session state"""
    return {
        'processing_state': {
            'processed_count': 0,
            'failed_count': 0,
            'status_history': []
        }
    }