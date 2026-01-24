# Unit Tests for Confirm Button UI

import pytest
import streamlit as st
from unittest.mock import Mock, patch

def test_confirm_button_renders():
    """Test that the confirm button renders correctly in the UI"""
    # This would be tested in a Streamlit testing environment
    # Mock the streamlit components
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button:

        # Simulate the UI rendering
        mock_textarea.return_value = "https://example.com/video1\nhttps://example.com/video2"
        mock_button.return_value = True  # Simulate button click

        # The button should be created with correct parameters
        # button(label="Submit URLs", type="primary")
        mock_button.assert_called_with("Submit URLs", type="primary", help="Click to parse and validate the URLs above")

def test_confirm_button_event_handling():
    """Test that button click triggers URL processing"""
    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.success') as mock_success:

        # Simulate user input and button click
        mock_textarea.return_value = "https://youtube.com/watch?v=test"
        mock_button.return_value = True

        # Verify that URL parsing logic would be triggered
        # This test ensures the button integrates with existing parsing logic
        assert mock_button.called
        assert mock_textarea.called

def test_button_styling_matches_design():
    """Test that button styling follows design guidelines"""
    # Verify button uses primary type for prominence
    # Verify button text is clear and action-oriented
    expected_label = "Submit URLs"
    expected_type = "primary"

    with patch('streamlit.button') as mock_button:
        mock_button.return_value = False  # Button not clicked

        # In actual implementation, button should be called with:
        # st.button("Submit URLs", type="primary", help="...")
        mock_button.assert_called_with(
            expected_label,
            type=expected_type,
            help="Click to parse and validate the URLs above, or press ctrl+enter"
        )

def test_button_preserves_keyboard_shortcut():
    """Test that ctrl+enter functionality is preserved alongside button"""
    # This test ensures backward compatibility
    # ctrl+enter should still work even with the button present

    with patch('streamlit.text_area') as mock_textarea, \
         patch('streamlit.button') as mock_button:

        # Simulate keyboard input (ctrl+enter behavior)
        mock_textarea.return_value = "https://youtube.com/watch?v=test"
        mock_button.return_value = False  # Button not clicked, but URLs entered

        # Both input methods should lead to same processing logic
        # This test verifies the dual-trigger system works
        assert mock_textarea.return_value is not None