"""User profile management for portfolio tickers."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from finnews.common.config import settings
from finnews.common.io_utils import read_json, write_json

logger = logging.getLogger(__name__)


class UserProfile:
    """Represents a user's profile with portfolio tickers."""

    def __init__(
        self,
        user_id: str,
        portfolio_tickers: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
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


def add_tickers(user_id: str, tickers: List[str]) -> UserProfile:
    """Add tickers to a user's portfolio.

    Args:
        user_id: The user's ID
        tickers: List of ticker symbols to add

    Returns:
        Updated UserProfile
    """
    profile = load_user_profile(user_id)

    # Normalize tickers to uppercase and remove duplicates
    normalized_tickers = [t.strip().upper() for t in tickers if t.strip()]

    # Add only new tickers
    for ticker in normalized_tickers:
        if ticker not in profile.portfolio_tickers:
            profile.portfolio_tickers.append(ticker)
            logger.info(f"Added ticker {ticker} to user {user_id}")

    save_user_profile(profile)
    return profile


def remove_tickers(user_id: str, tickers: List[str]) -> UserProfile:
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


def get_portfolio_tickers(user_id: str) -> List[str]:
    """Get a user's portfolio tickers.

    Args:
        user_id: The user's ID

    Returns:
        List of ticker symbols
    """
    profile = load_user_profile(user_id)
    return profile.portfolio_tickers
