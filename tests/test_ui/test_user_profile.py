"""Critical tests for user profile and ticker management."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from finnews.ui.user_profile import (
    UserProfile,
    add_tickers,
    get_all_unique_tickers,
    get_portfolio_tickers,
    load_user_profile,
    remove_tickers,
    save_user_profile,
    validate_ticker,
)


class TestUserProfile:
    """Test UserProfile model."""

    def test_user_profile_initialization(self):
        """Test creating a new user profile."""
        profile = UserProfile(user_id="test_user")

        assert profile.user_id == "test_user"
        assert profile.portfolio_tickers == []
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_user_profile_with_tickers(self):
        """Test creating profile with initial tickers."""
        profile = UserProfile(user_id="test_user", portfolio_tickers=["AAPL", "MSFT"])

        assert profile.portfolio_tickers == ["AAPL", "MSFT"]

    def test_user_profile_to_dict(self):
        """Test converting profile to dictionary."""
        profile = UserProfile(
            user_id="test_user",
            portfolio_tickers=["AAPL"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        data = profile.to_dict()

        assert data["user_id"] == "test_user"
        assert data["portfolio_tickers"] == ["AAPL"]
        assert data["created_at"] == "2024-01-01T00:00:00"
        assert data["updated_at"] == "2024-01-01T00:00:00"

    def test_user_profile_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "user_id": "test_user",
            "portfolio_tickers": ["AAPL", "MSFT"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        profile = UserProfile.from_dict(data)

        assert profile.user_id == "test_user"
        assert profile.portfolio_tickers == ["AAPL", "MSFT"]


class TestValidateTicker:
    """Test ticker validation - critical for preventing scraper failures."""

    def test_valid_simple_ticker(self):
        """Test validation of standard tickers."""
        is_valid, error = validate_ticker("AAPL")
        assert is_valid
        assert error == ""

    def test_valid_hyphenated_ticker(self):
        """Test validation of hyphenated tickers (BRK-A, etc)."""
        is_valid, error = validate_ticker("BRK-A")
        assert is_valid
        assert error == ""

    def test_valid_ticker_normalization(self):
        """Test that tickers are normalized to uppercase."""
        is_valid, error = validate_ticker("aapl")
        assert is_valid

    def test_invalid_empty_ticker(self):
        """Test rejection of empty tickers."""
        is_valid, error = validate_ticker("")
        assert not is_valid
        assert "cannot be empty" in error

    def test_invalid_too_long_ticker(self):
        """Test rejection of tickers longer than 5 characters."""
        is_valid, error = validate_ticker("TOOLONG")
        assert not is_valid
        assert "Invalid ticker format" in error

    def test_invalid_special_characters(self):
        """Test rejection of tickers with invalid characters."""
        is_valid, error = validate_ticker("AAP$L")
        assert not is_valid

    def test_invalid_numbers(self):
        """Test rejection of tickers with numbers."""
        is_valid, error = validate_ticker("AAP1L")
        assert not is_valid

    def test_valid_one_letter_ticker(self):
        """Test that single-letter tickers are valid."""
        is_valid, error = validate_ticker("F")  # Ford
        assert is_valid

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is handled."""
        is_valid, error = validate_ticker("  AAPL  ")
        assert is_valid


class TestLoadAndSaveProfile:
    """Test profile persistence."""

    @patch("finnews.ui.user_profile.settings")
    def test_load_user_profile_new_user(self, mock_settings):
        """Test loading profile for new user creates empty profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)

            profile = load_user_profile("new_user")

            assert profile.user_id == "new_user"
            assert profile.portfolio_tickers == []

    @patch("finnews.ui.user_profile.settings")
    def test_save_and_load_profile(self, mock_settings):
        """Test saving and loading profile round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)

            # Create and save profile
            profile = UserProfile(user_id="test_user", portfolio_tickers=["AAPL", "MSFT"])
            save_user_profile(profile)

            # Load it back
            loaded_profile = load_user_profile("test_user")

            assert loaded_profile.user_id == "test_user"
            assert loaded_profile.portfolio_tickers == ["AAPL", "MSFT"]

    @patch("finnews.ui.user_profile.settings")
    def test_save_profile_updates_timestamp(self, mock_settings):
        """Test that saving profile updates the updated_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)

            profile = UserProfile(user_id="test_user", updated_at="2024-01-01T00:00:00")

            save_user_profile(profile)

            # Timestamp should be updated
            assert profile.updated_at != "2024-01-01T00:00:00"


class TestAddTickers:
    """Test adding tickers to user portfolio - critical for scraper triggering."""

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.scrape_new_tickers")
    def test_add_valid_tickers(self, mock_scrape, mock_settings):
        """Test adding valid tickers to portfolio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False  # Disable scraping trigger

            profile, added, errors = add_tickers("test_user", ["AAPL", "MSFT"])

            assert "AAPL" in profile.portfolio_tickers
            assert "MSFT" in profile.portfolio_tickers
            assert added == ["AAPL", "MSFT"]
            assert errors == []

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.scrape_new_tickers")
    def test_add_tickers_normalization(self, mock_scrape, mock_settings):
        """Test that tickers are normalized to uppercase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            profile, added, errors = add_tickers("test_user", ["aapl", "msft"])

            assert "AAPL" in profile.portfolio_tickers
            assert "MSFT" in profile.portfolio_tickers

    @patch("finnews.ui.user_profile.settings")
    def test_add_duplicate_tickers(self, mock_settings):
        """Test that duplicate tickers are not added."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            # Add initial tickers
            profile, added, errors = add_tickers("test_user", ["AAPL"])
            assert added == ["AAPL"]

            # Try to add same ticker again
            profile, added, errors = add_tickers("test_user", ["AAPL"])
            assert added == []  # Not added again
            assert len(profile.portfolio_tickers) == 1

    @patch("finnews.ui.user_profile.settings")
    def test_add_invalid_tickers_validation(self, mock_settings):
        """Test that invalid tickers are rejected with error messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            profile, added, errors = add_tickers("test_user", ["AAPL", "INVALID123", "MSFT"])

            # Valid tickers should be added
            assert "AAPL" in profile.portfolio_tickers
            assert "MSFT" in profile.portfolio_tickers

            # Invalid ticker should not be added
            assert "INVALID123" not in profile.portfolio_tickers

            # Should have validation error
            assert len(errors) == 1
            assert "INVALID123" in errors[0]

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.scrape_new_tickers")
    def test_add_tickers_triggers_scraping(self, mock_scrape, mock_settings):
        """Test that adding new tickers triggers scraping when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = True  # Enable scraping trigger

            # Need to import after patching
            with patch("finnews.ui.user_profile.scrape_new_tickers") as mock_scrape_func:
                profile, added, errors = add_tickers("test_user", ["AAPL", "MSFT"])

                # Should trigger scraping for new tickers
                mock_scrape_func.assert_called_once_with(["AAPL", "MSFT"])

    @patch("finnews.ui.user_profile.settings")
    def test_add_tickers_no_scraping_when_disabled(self, mock_settings):
        """Test that scraping is not triggered when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            with patch("finnews.ui.user_profile.scrape_new_tickers") as mock_scrape:
                profile, added, errors = add_tickers("test_user", ["AAPL"])

                # Should NOT trigger scraping
                mock_scrape.assert_not_called()


class TestRemoveTickers:
    """Test removing tickers from portfolio."""

    @patch("finnews.ui.user_profile.settings")
    def test_remove_existing_tickers(self, mock_settings):
        """Test removing tickers that exist in portfolio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            # Add tickers first
            add_tickers("test_user", ["AAPL", "MSFT", "GOOGL"])

            # Remove some tickers
            profile = remove_tickers("test_user", ["AAPL", "MSFT"])

            assert "AAPL" not in profile.portfolio_tickers
            assert "MSFT" not in profile.portfolio_tickers
            assert "GOOGL" in profile.portfolio_tickers

    @patch("finnews.ui.user_profile.settings")
    def test_remove_nonexistent_tickers(self, mock_settings):
        """Test removing tickers that don't exist (should not error)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            # Add one ticker
            add_tickers("test_user", ["AAPL"])

            # Try to remove ticker that doesn't exist
            profile = remove_tickers("test_user", ["MSFT"])

            # Should not error, original ticker still there
            assert "AAPL" in profile.portfolio_tickers


class TestGetPortfolioTickers:
    """Test retrieving user's tickers."""

    @patch("finnews.ui.user_profile.settings")
    def test_get_portfolio_tickers(self, mock_settings):
        """Test getting user's portfolio tickers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            # Add tickers
            add_tickers("test_user", ["AAPL", "MSFT"])

            # Get tickers
            tickers = get_portfolio_tickers("test_user")

            assert tickers == ["AAPL", "MSFT"]

    @patch("finnews.ui.user_profile.settings")
    def test_get_portfolio_tickers_new_user(self, mock_settings):
        """Test getting tickers for new user returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.USER_PROFILES_DIR = Path(tmpdir)

            tickers = get_portfolio_tickers("new_user")

            assert tickers == []


class TestGetAllUniqueTickers:
    """Test aggregating tickers across all users - critical for scraper."""

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_multiple_users(self, mock_dir, mock_settings):
        """Test aggregating tickers from multiple users."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_settings.USER_PROFILES_DIR = tmpdir_path
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []

            mock_settings.SCRAPE_ON_NEW_TICKER = False

            # Temporarily patch USER_PROFILES_DIR
            with patch("finnews.ui.user_profile.USER_PROFILES_DIR", tmpdir_path):
                # Add tickers for multiple users
                add_tickers("user1", ["AAPL", "MSFT"])
                add_tickers("user2", ["MSFT", "GOOGL"])  # MSFT is duplicate
                add_tickers("user3", ["TSLA"])

                # Get all unique tickers
                all_tickers = get_all_unique_tickers()

                # Should be sorted and unique
                assert all_tickers == ["AAPL", "GOOGL", "MSFT", "TSLA"]

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_empty(self, mock_dir, mock_settings):
        """Test getting tickers when no users exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_settings.USER_PROFILES_DIR = tmpdir_path

            with patch("finnews.ui.user_profile.USER_PROFILES_DIR", tmpdir_path):
                all_tickers = get_all_unique_tickers()
                assert all_tickers == []

    @patch("finnews.ui.user_profile.settings")
    @patch("finnews.ui.user_profile.USER_PROFILES_DIR")
    def test_get_all_unique_tickers_case_normalization(self, mock_dir, mock_settings):
        """Test that tickers are normalized to uppercase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            mock_settings.USER_PROFILES_DIR = tmpdir_path
            mock_settings.SCRAPE_ON_NEW_TICKER = False

            with patch("finnews.ui.user_profile.USER_PROFILES_DIR", tmpdir_path):
                # Add lowercase tickers
                add_tickers("user1", ["aapl"])

                all_tickers = get_all_unique_tickers()

                # Should be uppercase
                assert all_tickers == ["AAPL"]
