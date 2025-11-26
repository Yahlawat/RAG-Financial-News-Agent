"""Tests for the Streamlit app module."""

from unittest.mock import patch

from finnews.ui.app import api_base, format_time_ago


class TestApiBase:
    """Test the api_base utility function."""

    @patch("finnews.ui.app.settings")
    def test_api_base_default(self, mock_settings):
        """Test api_base returns correct URL format."""
        mock_settings.API_HOST = "127.0.0.1"
        mock_settings.API_PORT = 8000

        result = api_base()

        assert result == "http://127.0.0.1:8000"

    @patch("finnews.ui.app.settings")
    def test_api_base_custom_port(self, mock_settings):
        """Test api_base with custom port."""
        mock_settings.API_HOST = "localhost"
        mock_settings.API_PORT = 9000

        result = api_base()

        assert result == "http://localhost:9000"


class TestFormatTimeAgo:
    """Test the format_time_ago utility function."""

    def test_just_now(self):
        """Test time less than 60 seconds."""
        from datetime import datetime

        timestamp = datetime.now()
        result = format_time_ago(timestamp.isoformat())

        assert result == "just now"

    def test_minutes_ago(self):
        """Test time in minutes."""
        from datetime import datetime, timedelta

        timestamp = datetime.now() - timedelta(minutes=5)
        result = format_time_ago(timestamp.isoformat())

        assert "5 minutes ago" == result

    def test_hours_ago(self):
        """Test time in hours."""
        from datetime import datetime, timedelta

        timestamp = datetime.now() - timedelta(hours=3)
        result = format_time_ago(timestamp.isoformat())

        assert "3 hours ago" == result

    def test_days_ago(self):
        """Test time in days."""
        from datetime import datetime, timedelta

        timestamp = datetime.now() - timedelta(days=2)
        result = format_time_ago(timestamp.isoformat())

        assert "2 days ago" == result

    def test_invalid_timestamp(self):
        """Test invalid timestamp returns 'unknown'."""
        result = format_time_ago("invalid")

        assert result == "unknown"


# Note: We don't test the full Streamlit UI with mocks because:
# 1. Streamlit's rendering logic is tested by Streamlit itself
# 2. Mocking st.* components is brittle and provides little value
# 3. The UI is best tested manually or with end-to-end tests
#
# Instead, we focus on testing utility functions and business logic.
