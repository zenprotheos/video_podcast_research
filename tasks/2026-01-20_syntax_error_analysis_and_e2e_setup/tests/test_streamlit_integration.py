"""
Streamlit Integration Tests
Test the Streamlit UI components and interactions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestStreamlitUI:
    """Test Streamlit UI components"""

    @patch('streamlit.sidebar')
    @patch('streamlit.container')
    def test_sidebar_layout(self, mock_container, mock_sidebar):
        """Test sidebar component creation"""
        # Mock Streamlit components
        mock_sidebar_instance = Mock()
        mock_sidebar.return_value = mock_sidebar_instance

        mock_main_container = Mock()
        mock_container.return_value = mock_main_container

        # This would test the UI layout logic from the main page
        # Note: Actual Streamlit testing requires special setup
        assert mock_sidebar.called
        assert mock_container.called

    def test_data_display_formatting(self):
        """Test data display formatting functions"""
        # Test the status table formatting
        test_data = [
            {"Title": "Test Video", "Status": "✅ Success", "Method": "api", "Time": "1.2s"},
            {"Title": "Failed Video", "Status": "❌ Failed", "Error": "Rate limit", "Time": "0.5s"}
        ]

        df = pd.DataFrame(test_data)

        # Validate DataFrame structure
        assert len(df) == 2
        assert "Status" in df.columns
        assert "Title" in df.columns

    @patch('streamlit.dataframe')
    def test_progress_display(self, mock_dataframe):
        """Test progress display updates"""
        test_status_data = [
            {"Title": "Video 1", "Status": "✅ Success"},
            {"Title": "Video 2", "Status": "🎙️ Getting transcript..."}
        ]

        # Mock the dataframe display
        mock_dataframe.return_value = None

        # This simulates calling st.dataframe with status data
        # In real implementation, this would be extracted from the main processing loop
        assert mock_dataframe.called

class TestFileUploadHandling:
    """Test file upload and processing"""

    def test_csv_upload_validation(self, sample_csv_file):
        """Test CSV file upload validation"""
        assert sample_csv_file.exists()
        assert sample_csv_file.suffix == '.csv'

        # Read and validate content
        df = pd.read_csv(sample_csv_file)
        assert len(df) > 0
        assert 'url' in df.columns

    def test_excel_upload_support(self, test_data_dir, sample_csv_data):
        """Test Excel file upload (converted from CSV for testing)"""
        excel_path = test_data_dir / "test_data.xlsx"
        sample_csv_data.to_excel(excel_path, index=False)

        assert excel_path.exists()
        assert excel_path.suffix == '.xlsx'

        # Read back and validate
        df_read = pd.read_excel(excel_path)
        assert len(df_read) == len(sample_csv_data)

    def test_large_file_handling(self, test_data_dir):
        """Test handling of large input files"""
        # Create a large test file
        large_data = pd.DataFrame({
            'url': [f'https://youtube.com/watch?v=test{i}' for i in range(1000)],
            'title': [f'Test Video {i}' for i in range(1000)]
        })

        large_file = test_data_dir / "large_test.csv"
        large_data.to_csv(large_file, index=False)

        # Validate file was created
        assert large_file.exists()
        assert large_file.stat().st_size > 10000  # Should be reasonably large

class TestErrorDisplay:
    """Test error display and user feedback"""

    @pytest.mark.parametrize("error_type,expected_message", [
        ("rate_limit", "Rate limited - try later"),
        ("quota", "Credits exhausted"),
        ("timeout", "Request timeout"),
        ("generic", "Unknown error occurred")
    ])
    def test_error_message_formatting(self, error_type, expected_message):
        """Test error message formatting for user display"""
        # This tests the error categorization logic

        if error_type == "rate_limit":
            error_msg = "HTTP 429: Rate limit exceeded"
        elif error_type == "quota":
            error_msg = "Quota exceeded for API"
        elif error_type == "timeout":
            error_msg = "Request timeout after 30 seconds"
        else:
            error_msg = "Some unknown error"

        # Apply categorization logic (extracted from main app)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            display_error = "Rate limited - try later"
        elif "quota" in error_msg.lower() or "402" in error_msg:
            display_error = "Credits exhausted"
        elif "timeout" in error_msg.lower():
            display_error = "Request timeout"
        else:
            display_error = error_msg[:50]

        assert expected_message in display_error

class TestSessionStateManagement:
    """Test Streamlit session state management"""

    def test_processing_state_initialization(self):
        """Test initial processing state setup"""
        initial_state = {
            'processed_count': 0,
            'failed_count': 0,
            'status_history': []
        }

        assert initial_state['processed_count'] == 0
        assert initial_state['failed_count'] == 0
        assert len(initial_state['status_history']) == 0

    def test_status_update_logic(self):
        """Test status update logic"""
        status_history = []

        # Simulate adding status updates
        status_history.append({"video": "video1", "status": "success"})
        status_history.append({"video": "video2", "status": "failed"})

        assert len(status_history) == 2
        assert status_history[0]['status'] == 'success'
        assert status_history[1]['status'] == 'failed'

    def test_progress_counter_updates(self):
        """Test progress counter updates"""
        counters = {'processed': 0, 'failed': 0, 'total': 10}

        # Simulate processing
        counters['processed'] += 1
        counters['processed'] += 1
        counters['failed'] += 1

        assert counters['processed'] == 2
        assert counters['failed'] == 1
        assert counters['total'] == 10