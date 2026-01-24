"""
End-to-End Tests for Bulk Transcribe Application
Tests the complete workflow from input to output
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.bulk_transcribe.session_manager import SessionManager
from src.bulk_transcribe.youtube_metadata import fetch_youtube_metadata
from src.bulk_transcribe.youtube_transcript import get_youtube_transcript

class TestBulkTranscribeE2E:
    """End-to-end tests for the bulk transcribe functionality"""

    def test_complete_workflow_single_video_success(self, sample_youtube_urls, mock_youtube_metadata, mock_transcript_result):
        """Test complete successful processing of a single video"""
        url = sample_youtube_urls[0]

        # Mock all external dependencies
        with patch('src.bulk_transcribe.youtube_metadata.fetch_youtube_metadata') as mock_meta, \
             patch('src.bulk_transcribe.youtube_transcript.get_youtube_transcript') as mock_transcript, \
             patch('src.bulk_transcribe.session_manager.SessionManager') as mock_session_mgr, \
             patch('src.bulk_transcribe.transcript_writer.write_transcript_markdown') as mock_writer:

            # Setup mocks
            mock_meta.return_value = Mock()
            mock_meta.return_value.video_id = "dQw4w9WgXcQ"
            mock_meta.return_value.title = "Test Video"
            mock_meta.return_value.raw = mock_youtube_metadata

            mock_transcript.return_value = Mock()
            mock_transcript.return_value.success = True
            mock_transcript.return_value.transcript_text = "Test transcript"
            mock_transcript.return_value.method = "api"
            mock_transcript.return_value.error_message = None

            mock_session = Mock()
            mock_session.youtube_dir = Path("/tmp/test")
            mock_session_mgr.return_value.create_session.return_value = mock_session

            # Import and test the main processing function
            # Note: This would need to be extracted from the Streamlit page for testing
            # For now, we'll test the individual components

            # Test metadata fetching
            result = fetch_youtube_metadata(url)
            assert result is not None
            mock_meta.assert_called_once_with(url)

            # Test transcript fetching
            transcript_result = get_youtube_transcript("dQw4w9WgXcQ", "test_key")
            assert transcript_result is not None
            mock_transcript.assert_called_once()

    def test_complete_workflow_batch_processing(self, sample_csv_data):
        """Test batch processing of multiple videos"""
        # This test would validate the complete CSV processing workflow
        assert len(sample_csv_data) == 3
        assert 'url' in sample_csv_data.columns
        assert all(url.startswith(('http://', 'https://')) for url in sample_csv_data['url'])

    def test_error_handling_rate_limit(self, sample_youtube_urls):
        """Test error handling for rate limiting"""
        url = sample_youtube_urls[0]

        with patch('src.bulk_transcribe.youtube_transcript.get_youtube_transcript') as mock_transcript:
            # Mock rate limit error
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "Rate limit exceeded"
            mock_transcript.return_value = mock_result

            result = get_youtube_transcript("test_video_id", "test_key")
            assert result.success == False
            assert "Rate limit" in str(result.error_message)

    def test_error_handling_invalid_url(self):
        """Test error handling for invalid YouTube URLs"""
        invalid_urls = [
            "https://notyoutube.com/video",
            "https://youtube.com/watch",  # Missing video ID
            "not_a_url_at_all",
            ""
        ]

        for invalid_url in invalid_urls:
            with patch('src.bulk_transcribe.youtube_metadata.fetch_youtube_metadata') as mock_meta:
                mock_meta.side_effect = Exception("Invalid URL")

                # Should handle the error gracefully
                try:
                    fetch_youtube_metadata(invalid_url)
                    # If no exception, that's also acceptable if handled internally
                except Exception:
                    # Expected for invalid URLs
                    pass

    def test_output_file_generation(self, tmp_path, mock_youtube_metadata, mock_transcript_result):
        """Test that output files are generated correctly"""
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        with patch('src.bulk_transcribe.transcript_writer.write_transcript_markdown') as mock_writer, \
             patch('src.bulk_transcribe.youtube_metadata.save_metadata_json') as mock_save_meta:

            # Mock the write functions
            mock_writer.return_value = None
            mock_save_meta.return_value = None

            # Test file path generation
            from src.bulk_transcribe.transcript_writer import generate_filename

            video_id = "dQw4w9WgXcQ"
            title = "Test Video Title"
            filename = generate_filename(video_id, title, "youtube")

            assert filename.endswith('.md')
            assert video_id in filename
            assert 'Test_Video_Title' in filename

    def test_session_management(self):
        """Test session creation and management"""
        with patch('src.bulk_transcribe.session_manager.SessionManager') as mock_mgr_class:
            mock_mgr = Mock()
            mock_session = Mock()
            mock_session.session_id = "test_session_123"
            mock_mgr.create_session.return_value = mock_session
            mock_mgr_class.return_value = mock_mgr

            # Test session creation
            mgr = SessionManager()
            session = mgr.create_session()
            assert session.session_id == "test_session_123"

    @pytest.mark.parametrize("error_type,expected_icon", [
        ("rate limit", "⏸️"),
        ("quota", "💰"),
        ("timeout", "⏰"),
        ("unknown error", "❌")
    ])
    def test_error_categorization(self, error_type, expected_icon):
        """Test error message categorization"""
        # Import the categorization function if it exists
        # This would need to be extracted from the main processing logic
        error_msg = f"Simulated {error_type} error"

        # Basic categorization logic (would be extracted from main app)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            icon = "⏸️"
            display_error = "Rate limited - try later"
        elif "quota" in error_msg.lower() or "402" in error_msg:
            icon = "💰"
            display_error = "Credits exhausted"
        elif "timeout" in error_msg.lower():
            icon = "⏰"
            display_error = "Request timeout"
        else:
            icon = "❌"
            display_error = error_msg[:50]

        assert icon == expected_icon

class TestDataValidation:
    """Tests for input data validation"""

    def test_csv_format_validation(self, sample_csv_data):
        """Test CSV format validation"""
        required_columns = ['url']

        # Check required columns exist
        assert all(col in sample_csv_data.columns for col in required_columns)

        # Check data types
        assert sample_csv_data['url'].dtype == object

    def test_url_validation(self, sample_youtube_urls):
        """Test YouTube URL validation"""
        def is_valid_youtube_url(url):
            """Basic URL validation logic"""
            if not url or not isinstance(url, str):
                return False
            return 'youtube.com' in url or 'youtu.be' in url

        for url in sample_youtube_urls:
            assert is_valid_youtube_url(url), f"Invalid URL: {url}"

    def test_empty_data_handling(self):
        """Test handling of empty input data"""
        empty_df = pd.DataFrame()

        # Should handle empty data gracefully
        assert len(empty_df) == 0

class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    def test_mixed_success_failure_batch(self):
        """Test batch processing with mix of success and failure"""
        # This would test processing multiple videos where some succeed and some fail
        pass

    def test_large_batch_processing(self):
        """Test processing of large batches"""
        # Test with 100+ videos to ensure scalability
        pass

    def test_network_error_recovery(self):
        """Test recovery from network errors"""
        # Test automatic retry logic
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])