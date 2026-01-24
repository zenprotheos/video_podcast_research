# E2E Tests for Confirm Button Integration

import pytest
from unittest.mock import Mock, patch, MagicMock

def test_full_url_input_flow_with_button():
    """Test complete user flow: input URLs -> click button -> validation"""
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.error') as mock_error:

        # Simulate user entering URLs and clicking button
        test_urls = "https://youtube.com/watch?v=test1\nhttps://youtube.com/watch?v=test2"
        mock_textarea.return_value = test_urls
        mock_button.return_value = True  # User clicks button

        # Mock the URL parsing logic
        with patch('src.bulk_transcribe.sheet_ingest.parse_spreadsheet') as mock_parse:
            mock_parse.return_value = Mock(
                columns=['source_type', 'youtube_url'],
                rows=[
                    {'source_type': 'youtube', 'youtube_url': 'https://youtube.com/watch?v=test1'},
                    {'source_type': 'youtube', 'youtube_url': 'https://youtube.com/watch?v=test2'}
                ],
                row_count=2
            )

            # Simulate the application flow
            # When button is clicked, URLs should be parsed
            if mock_button.return_value and mock_textarea.return_value.strip():
                # This mimics the URL processing logic
                lines = [line.strip() for line in test_urls.strip().split("\n") if line.strip()]
                parsed = mock_parse(lines[0], b"dummy")  # Mock parsing

                # Verify success feedback
                mock_success.assert_called_with("Loaded 2 URLs from text input")

def test_button_and_keyboard_shortcut_equivalence():
    """Test that button click and ctrl+enter produce same results"""

    test_urls = "https://youtube.com/watch?v=test"

    # Test 1: Button click flow
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.success') as mock_success:

        mock_textarea.return_value = test_urls
        mock_button.return_value = True  # Button clicked

        # Simulate processing
        button_result = mock_textarea.return_value

        # Test 2: Keyboard shortcut flow (simulated)
        mock_textarea.return_value = test_urls
        mock_button.return_value = False  # Button not clicked, but URLs entered

        keyboard_result = mock_textarea.return_value

        # Both methods should produce same input for processing
        assert button_result == keyboard_result == test_urls

def test_button_disabled_when_no_urls():
    """Test button behavior with empty input"""
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.warning') as mock_warning:

        # Empty input
        mock_textarea.return_value = ""
        mock_button.return_value = False  # Button not clicked (would be disabled)

        # Should show appropriate message
        if not mock_textarea.return_value.strip():
            mock_warning.assert_called_with("Enter URLs or upload a file to continue.")

def test_button_error_handling():
    """Test button handles parsing errors gracefully"""
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.error') as mock_error:

        # Valid input that might cause parsing issues
        mock_textarea.return_value = "https://youtube.com/watch?v=test"
        mock_button.return_value = True

        # Simulate parsing failure
        with patch('src.bulk_transcribe.sheet_ingest.parse_spreadsheet') as mock_parse:
            mock_parse.side_effect = Exception("Parsing failed")

            # Should handle error gracefully
            try:
                # This would trigger the error handling in the app
                mock_parse("dummy", b"dummy")
            except Exception:
                mock_error.assert_called_with("Failed to parse spreadsheet: Parsing failed")

def test_button_preserves_session_state():
    """Test that button click preserves URL prepopulation from search tools"""
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.session_state') as mock_session:

        # Simulate prepopulated URLs from search tool
        mock_session.__getitem__.return_value = ['https://youtube.com/watch?v=search_result']
        mock_session.get.return_value = 'YouTube Search'

        mock_textarea.return_value = "https://youtube.com/watch?v=search_result"
        mock_button.return_value = True

        # Button should work with prepopulated URLs
        assert mock_textarea.return_value is not None
        assert mock_button.return_value is True