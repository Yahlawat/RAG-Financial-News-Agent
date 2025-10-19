"""Tests for the session manager module."""
import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from finnews.ui.session_manager import load_session, save_session


class TestLoadSession:
    """Test the load_session function."""

    def test_load_session_new_user(self):
        """Test loading session for a new user."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                # File doesn't exist initially
                user_id = "new_user"
                conversation_id = load_session(user_id)
                
                # Should return a valid UUID
                assert isinstance(conversation_id, str)
                assert len(conversation_id) == 36  # UUID length
                
                # Verify UUID is valid
                uuid.UUID(conversation_id)
                
                # Verify file was created and contains the session
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == conversation_id

    def test_load_session_existing_user(self):
        """Test loading session for an existing user."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Create existing session file
            existing_conversation_id = str(uuid.uuid4())
            with open(temp_file.name, 'w') as f:
                json.dump({"existing_user": existing_conversation_id}, f)
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "existing_user"
                conversation_id = load_session(user_id)
                
                # Should return a new UUID for new user
                assert conversation_id != existing_conversation_id
                assert isinstance(conversation_id, str)
                
                # Verify file contains both users
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data["existing_user"] == existing_conversation_id
                    assert data[user_id] == conversation_id

    def test_load_session_existing_user_returns_existing_id(self):
        """Test that existing user gets their existing conversation ID."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Create existing session file
            existing_conversation_id = str(uuid.uuid4())
            with open(temp_file.name, 'w') as f:
                json.dump({"existing_user": existing_conversation_id}, f)
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "existing_user"
                conversation_id = load_session(user_id)
                
                # Should return the existing conversation ID
                assert conversation_id == existing_conversation_id

    def test_load_session_invalid_json(self):
        """Test loading session with invalid JSON in file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Write invalid JSON
            with open(temp_file.name, 'w') as f:
                f.write("invalid json")
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                conversation_id = load_session(user_id)
                
                # Should create new session despite invalid JSON
                assert isinstance(conversation_id, str)
                assert len(conversation_id) == 36

    def test_load_session_empty_file(self):
        """Test loading session with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Create empty file
            with open(temp_file.name, 'w') as f:
                f.write("")
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                conversation_id = load_session(user_id)
                
                # Should create new session
                assert isinstance(conversation_id, str)
                assert len(conversation_id) == 36

    def test_load_session_directory_creation(self):
        """Test that load_session creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "nonexistent" / "sessions.json"
            
            with patch('finnews.ui.session_manager.SESSION_FILE', str(session_file)):
                user_id = "test_user"
                conversation_id = load_session(user_id)
                
                # Should create directory and file
                assert session_file.exists()
                assert isinstance(conversation_id, str)

    def test_load_session_multiple_users(self):
        """Test loading sessions for multiple users."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                # Load sessions for multiple users
                user1_id = "user1"
                user2_id = "user2"
                
                conv1_id = load_session(user1_id)
                conv2_id = load_session(user2_id)
                
                # Should be different conversation IDs
                assert conv1_id != conv2_id
                
                # Verify both are in the file
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user1_id] == conv1_id
                    assert data[user2_id] == conv2_id


class TestSaveSession:
    """Test the save_session function."""

    def test_save_session_new_user(self):
        """Test saving session for a new user."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "new_user"
                conversation_id = str(uuid.uuid4())
                
                save_session(user_id, conversation_id)
                
                # Verify session was saved
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == conversation_id

    def test_save_session_existing_user(self):
        """Test saving session for an existing user (updates existing)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Create existing session file
            old_conversation_id = str(uuid.uuid4())
            with open(temp_file.name, 'w') as f:
                json.dump({"existing_user": old_conversation_id}, f)
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "existing_user"
                new_conversation_id = str(uuid.uuid4())
                
                save_session(user_id, new_conversation_id)
                
                # Verify session was updated
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == new_conversation_id
                    assert data[user_id] != old_conversation_id

    def test_save_session_invalid_json(self):
        """Test saving session with invalid JSON in existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Write invalid JSON
            with open(temp_file.name, 'w') as f:
                f.write("invalid json")
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                conversation_id = str(uuid.uuid4())
                
                save_session(user_id, conversation_id)
                
                # Should create new session despite invalid JSON
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == conversation_id

    def test_save_session_empty_file(self):
        """Test saving session with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            # Create empty file
            with open(temp_file.name, 'w') as f:
                f.write("")
            
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                conversation_id = str(uuid.uuid4())
                
                save_session(user_id, conversation_id)
                
                # Should save session
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == conversation_id

    def test_save_session_directory_creation(self):
        """Test that save_session creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "nonexistent" / "sessions.json"
            
            with patch('finnews.ui.session_manager.SESSION_FILE', str(session_file)):
                user_id = "test_user"
                conversation_id = str(uuid.uuid4())
                
                save_session(user_id, conversation_id)
                
                # Should create directory and file
                assert session_file.exists()
                
                # Verify session was saved
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == conversation_id

    def test_save_session_multiple_users(self):
        """Test saving sessions for multiple users."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                # Save sessions for multiple users
                user1_id = "user1"
                user2_id = "user2"
                conv1_id = str(uuid.uuid4())
                conv2_id = str(uuid.uuid4())
                
                save_session(user1_id, conv1_id)
                save_session(user2_id, conv2_id)
                
                # Verify both sessions are saved
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user1_id] == conv1_id
                    assert data[user2_id] == conv2_id

    def test_save_session_overwrite_existing(self):
        """Test that save_session overwrites existing conversation ID."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                old_conversation_id = str(uuid.uuid4())
                new_conversation_id = str(uuid.uuid4())
                
                # Save first session
                save_session(user_id, old_conversation_id)
                
                # Save new session (should overwrite)
                save_session(user_id, new_conversation_id)
                
                # Verify only the new session is saved
                with open(temp_file.name, 'r') as f:
                    data = json.load(f)
                    assert data[user_id] == new_conversation_id
                    assert data[user_id] != old_conversation_id


class TestSessionManagerIntegration:
    """Integration tests for session manager functions."""

    def test_load_then_save_session(self):
        """Test loading a session and then saving a new one."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                user_id = "test_user"
                
                # Load initial session
                initial_conv_id = load_session(user_id)
                
                # Save new session
                new_conv_id = str(uuid.uuid4())
                save_session(user_id, new_conv_id)
                
                # Load session again - should get the new one
                loaded_conv_id = load_session(user_id)
                
                assert loaded_conv_id == new_conv_id
                assert loaded_conv_id != initial_conv_id

    def test_multiple_users_persistence(self):
        """Test that multiple users' sessions persist correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            with patch('finnews.ui.session_manager.SESSION_FILE', temp_file.name):
                # Create sessions for multiple users
                user1_id = "user1"
                user2_id = "user2"
                
                conv1_id = load_session(user1_id)
                conv2_id = load_session(user2_id)
                
                # Save new sessions
                new_conv1_id = str(uuid.uuid4())
                new_conv2_id = str(uuid.uuid4())
                
                save_session(user1_id, new_conv1_id)
                save_session(user2_id, new_conv2_id)
                
                # Load sessions again
                loaded_conv1_id = load_session(user1_id)
                loaded_conv2_id = load_session(user2_id)
                
                assert loaded_conv1_id == new_conv1_id
                assert loaded_conv2_id == new_conv2_id
