"""Tests for the session manager module."""

from unittest.mock import patch

import pytest

from finnews.ui.session_manager import (
    create_new_conversation,
    get_active_conversation,
    load_session,
    set_active_conversation,
)


class TestSessionManager:
    """Test session manager functions."""

    @pytest.fixture(autouse=True)
    def setup_session_file(self, temp_dir):
        """Setup temporary session file for each test."""
        self.session_file = temp_dir / "chat_sessions" / "sessions.json"
        with patch("finnews.ui.session_manager.SESSION_FILE", str(self.session_file)):
            yield

    def test_load_session_creates_new_for_new_user(self):
        """Test load_session creates new UUID for new user."""
        conversation_id = load_session("new_user")

        assert isinstance(conversation_id, str)
        assert len(conversation_id) == 36  # UUID4 format

    def test_load_session_returns_existing_for_existing_user(self):
        """Test load_session returns same ID for existing user."""
        conv_id_1 = load_session("test_user")
        conv_id_2 = load_session("test_user")

        assert conv_id_1 == conv_id_2

    def test_create_new_conversation(self):
        """Test creating multiple conversations for same user."""
        conv_id_1 = create_new_conversation("user1")
        conv_id_2 = create_new_conversation("user1")

        # Should be different UUIDs
        assert conv_id_1 != conv_id_2

        # Active conversation should be the latest
        assert get_active_conversation("user1") == conv_id_2

    def test_set_and_get_active_conversation(self):
        """Test setting and retrieving active conversation."""
        set_active_conversation("user1", "conv123")
        active = get_active_conversation("user1")

        assert active == "conv123"

    def test_get_active_conversation_returns_none_for_new_user(self):
        """Test get_active_conversation returns None for non-existent user."""
        active = get_active_conversation("nonexistent")

        assert active is None

    def test_multiple_users_isolated(self):
        """Test that different users have isolated sessions."""
        conv1 = load_session("user1")
        conv2 = load_session("user2")

        assert conv1 != conv2
        assert get_active_conversation("user1") == conv1
        assert get_active_conversation("user2") == conv2

    def test_conversation_switching(self):
        """Test switching between conversations."""
        old_conv = load_session("user1")
        new_conv = create_new_conversation("user1")

        assert old_conv != new_conv
        assert get_active_conversation("user1") == new_conv

        # Switch back to old conversation
        set_active_conversation("user1", old_conv)
        assert get_active_conversation("user1") == old_conv
