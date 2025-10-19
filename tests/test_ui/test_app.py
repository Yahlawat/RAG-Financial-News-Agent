"""Tests for the Streamlit app module."""
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from finnews.ui.app import api_base, run


class TestApiBase:
    """Test the api_base function."""

    @patch('finnews.ui.app.settings')
    def test_api_base_default(self, mock_settings):
        """Test api_base with default settings."""
        mock_settings.api_host = "127.0.0.1"
        mock_settings.api_port = 8000
        
        result = api_base()
        
        assert result == "http://127.0.0.1:8000"

    @patch('finnews.ui.app.settings')
    def test_api_base_custom(self, mock_settings):
        """Test api_base with custom settings."""
        mock_settings.api_host = "0.0.0.0"
        mock_settings.api_port = 9000
        
        result = api_base()
        
        assert result == "http://0.0.0.0:9000"

    @patch('finnews.ui.app.settings')
    def test_api_base_different_host(self, mock_settings):
        """Test api_base with different host."""
        mock_settings.api_host = "localhost"
        mock_settings.api_port = 8080
        
        result = api_base()
        
        assert result == "http://localhost:8080"


class TestRunFunction:
    """Test the run function."""

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_successful_request(self, mock_post, mock_load_session, mock_st):
        """Test successful API request."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": [
                {
                    "title": "Test Source",
                    "url": "https://example.com",
                    "published_date": "2024-01-01"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify streamlit components were called
            mock_st.title.assert_called_once_with("FinNews Assistant")
            mock_st.text_input.assert_called()
            mock_st.button.assert_called_once_with("Send")
            
            # Verify API request was made
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['json']['question'] == "test question"
            assert call_args[1]['json']['user_id'] == "test_user"
            assert call_args[1]['json']['conversation_id'] == "test_conv_id"
            
            # Verify response was displayed
            mock_st.subheader.assert_called()
            mock_st.write.assert_called()

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_with_tickers(self, mock_post, mock_load_session, mock_st):
        """Test API request with tickers filter."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.side_effect = ["test_user", "What is the news?", "AAPL, MSFT"]
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer about AAPL and MSFT",
            "sources": []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify API request included tickers
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['json']['tickers'] == ["AAPL", "MSFT"]

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_api_error(self, mock_post, mock_load_session, mock_st):
        """Test handling of API error."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API error
        mock_post.side_effect = Exception("API request failed")
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify error was displayed
            mock_st.error.assert_called_once()
            assert "API request failed" in mock_st.error.call_args[0][0]

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    def test_run_no_message(self, mock_load_session, mock_st):
        """Test behavior when no message is provided."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Should not make API request
            with patch('finnews.ui.app.requests.post') as mock_post:
                mock_post.assert_not_called()

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_button_not_clicked(self, mock_post, mock_load_session, mock_st):
        """Test behavior when button is not clicked."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = False  # Button not clicked
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Should not make API request
            mock_post.assert_not_called()

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_with_sources(self, mock_post, mock_load_session, mock_st):
        """Test display of sources in response."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response with sources
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": [
                {
                    "title": "Source 1",
                    "url": "https://example.com/1",
                    "published_date": "2024-01-01"
                },
                {
                    "title": "Source 2",
                    "url": "https://example.com/2",
                    "published_date": "2024-01-02"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify sources were displayed
            assert mock_st.subheader.call_count >= 2  # Answer + Sources
            assert mock_st.markdown.call_count == 2  # Two sources

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_without_sources(self, mock_post, mock_load_session, mock_st):
        """Test response without sources."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.return_value = "test_user"
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response without sources
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify only answer was displayed
            assert mock_st.subheader.call_count == 1  # Only Answer
            mock_st.markdown.assert_not_called()  # No sources

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_empty_tickers(self, mock_post, mock_load_session, mock_st):
        """Test behavior with empty tickers input."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.side_effect = ["test_user", "What is the news?", ""]  # Empty tickers
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify API request was made without tickers
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert 'tickers' not in call_args[1]['json']

    @patch('finnews.ui.app.st')
    @patch('finnews.ui.app.load_session')
    @patch('finnews.ui.app.requests.post')
    def test_run_whitespace_tickers(self, mock_post, mock_load_session, mock_st):
        """Test behavior with whitespace-only tickers input."""
        # Mock streamlit components
        mock_st.title.return_value = None
        mock_st.text_input.side_effect = ["test_user", "What is the news?", "   "]  # Whitespace only
        mock_st.button.return_value = True
        mock_st.subheader.return_value = None
        mock_st.write.return_value = None
        mock_st.markdown.return_value = None
        mock_st.error.return_value = None
        
        # Mock session manager
        mock_load_session.return_value = "test_conv_id"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Test answer",
            "sources": []
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Mock settings
        with patch('finnews.ui.app.settings') as mock_settings:
            mock_settings.api_host = "127.0.0.1"
            mock_settings.api_port = 8000
            
            # Call the function
            run()
            
            # Verify API request was made without tickers
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert 'tickers' not in call_args[1]['json']
