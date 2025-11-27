"""User profile management for portfolio tickers."""

import logging
import re
from datetime import datetime

from finnews.common.config import settings
from finnews.common.io_utils import read_json, write_json

logger = logging.getLogger(__name__)

# Directory reference for external use
USER_PROFILES_DIR = settings.USER_PROFILES_DIR


class UserProfile:
    """Represents a user's profile with portfolio tickers."""

    def __init__(
        self,
        user_id: str,
        portfolio_tickers: list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.user_id = user_id
        self.portfolio_tickers = portfolio_tickers or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "portfolio_tickers": self.portfolio_tickers,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create profile from dictionary."""
        return cls(
            user_id=data.get("user_id", ""),
            portfolio_tickers=data.get("portfolio_tickers", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


def get_user_profile_path(user_id: str) -> str:
    """Get the file path for a user's profile.

    Args:
        user_id: The user's ID

    Returns:
        Absolute path to the user's profile JSON file
    """
    return str(settings.USER_PROFILES_DIR / f"{user_id}_profile.json")


def load_user_profile(user_id: str) -> UserProfile:
    """Load a user's profile from disk.

    If the profile doesn't exist, creates a new one.

    Args:
        user_id: The user's ID

    Returns:
        UserProfile object
    """
    profile_path = get_user_profile_path(user_id)
    data = read_json(profile_path)

    if data:
        logger.info(f"Loaded profile for user: {user_id}")
        return UserProfile.from_dict(data)
    else:
        logger.info(f"Creating new profile for user: {user_id}")
        return UserProfile(user_id=user_id)


def save_user_profile(profile: UserProfile) -> None:
    """Save a user's profile to disk.

    Args:
        profile: The UserProfile to save
    """
    profile.updated_at = datetime.now().isoformat()
    profile_path = get_user_profile_path(profile.user_id)
    write_json(profile_path, profile.to_dict())
    logger.info(f"Saved profile for user: {profile.user_id}")


def validate_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate a ticker symbol.

    Args:
        ticker: Ticker symbol to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string
    """
    if not ticker:
        return False, "Ticker cannot be empty"

    # Normalize to uppercase
    ticker = ticker.strip().upper()

    # Pattern: 1-5 uppercase letters, optional hyphen followed by 1-2 letters
    # Examples: AAPL, BRK-A, RUMBW
    pattern = r"^[A-Z]{1,5}(-[A-Z]{1,2})?$"

    if not re.match(pattern, ticker):
        return False, f"Invalid ticker format: '{ticker}'. Must be 1-5 uppercase letters, optionally followed by hyphen and 1-2 letters"

    return True, ""


def get_all_unique_tickers() -> list[str]:
    """
    Get all unique tickers from all user portfolios.

    Returns:
        List of unique ticker symbols (uppercase, sorted)
    """
    tickers = set()

    try:
        if not USER_PROFILES_DIR.exists():
            logger.warning("User profiles directory does not exist: %s", USER_PROFILES_DIR)
            return []

        # Load all user profile files
        for profile_file in USER_PROFILES_DIR.glob("*_profile.json"):
            try:
                data = read_json(str(profile_file))
                if data:
                    portfolio_tickers = data.get("portfolio_tickers", [])
                    tickers.update(t.strip().upper() for t in portfolio_tickers if t.strip())

            except Exception as e:
                logger.error("Failed to load profile %s: %s", profile_file, e)
                continue

        ticker_list = sorted(list(tickers))
        logger.info("Aggregated %d unique tickers from all user portfolios", len(ticker_list))
        return ticker_list

    except Exception as e:
        logger.exception("Failed to aggregate tickers: %s", e)
        return []


def add_tickers(
    user_id: str, tickers: list[str], trigger_scrape: bool = True
) -> tuple[UserProfile, list[str], list[str]]:
    """Add tickers to a user's portfolio with validation.

    Args:
        user_id: The user's ID
        tickers: List of ticker symbols to add
        trigger_scrape: Whether to trigger on-demand scraping for new tickers

    Returns:
        Tuple of (updated_profile, newly_added_tickers, validation_errors)
    """
    profile = load_user_profile(user_id)

    newly_added = []
    validation_errors = []

    # Process each ticker
    for ticker in tickers:
        ticker = ticker.strip()
        if not ticker:
            continue

        # Validate ticker format
        is_valid, error_msg = validate_ticker(ticker)
        if not is_valid:
            validation_errors.append(error_msg)
            continue

        # Normalize to uppercase
        ticker = ticker.upper()

        # Add only new tickers
        if ticker not in profile.portfolio_tickers:
            profile.portfolio_tickers.append(ticker)
            newly_added.append(ticker)
            logger.info(f"Added ticker {ticker} to user {user_id}")

    # Save profile if any tickers were added
    if newly_added:
        save_user_profile(profile)

        # Trigger on-demand scraping for new tickers
        if trigger_scrape and settings.SCRAPE_ON_NEW_TICKER:
            try:
                from finnews.scraper.scheduler import scrape_new_tickers

                scrape_new_tickers(newly_added)
                logger.info(f"Triggered scraping for new tickers: {newly_added}")
            except Exception as e:
                logger.error(f"Failed to trigger scraping for new tickers: {e}")

    return profile, newly_added, validation_errors


def remove_tickers(user_id: str, tickers: list[str]) -> UserProfile:
    """Remove tickers from a user's portfolio.

    Args:
        user_id: The user's ID
        tickers: List of ticker symbols to remove

    Returns:
        Updated UserProfile
    """
    profile = load_user_profile(user_id)

    # Normalize tickers to uppercase
    normalized_tickers = [t.strip().upper() for t in tickers if t.strip()]

    # Remove tickers
    for ticker in normalized_tickers:
        if ticker in profile.portfolio_tickers:
            profile.portfolio_tickers.remove(ticker)
            logger.info(f"Removed ticker {ticker} from user {user_id}")

    save_user_profile(profile)
    return profile


def get_portfolio_tickers(user_id: str) -> list[str]:
    """Get a user's portfolio tickers.

    Args:
        user_id: The user's ID

    Returns:
        List of ticker symbols
    """
    profile = load_user_profile(user_id)
    return profile.portfolio_tickers
