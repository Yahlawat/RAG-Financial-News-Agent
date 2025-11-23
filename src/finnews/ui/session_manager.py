import json
import os
import uuid
from typing import Optional
from finnews.common.config import settings

SESSION_FILE = settings.chat_sessions


def load_session(user_id: str) -> str:
    """Return the active conversation_id for a user or create a new one."""
    os.makedirs(os.path.dirname(str(SESSION_FILE)), exist_ok=True)

    data = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, start fresh
            data = {}

    if user_id in data:
        session_value = data[user_id]
        # Handle both old format (dict) and new format (string)
        if isinstance(session_value, dict):
            return session_value.get("conversation_id", str(uuid.uuid4()))
        return session_value

    conversation_id = str(uuid.uuid4())
    data[user_id] = conversation_id

    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except IOError:
        # If we can't write to file, still return the conversation ID
        pass

    return conversation_id


def create_new_conversation(user_id: str) -> str:
    """Create a new conversation for a user and set it as active.

    Returns:
        New conversation_id
    """
    conversation_id = str(uuid.uuid4())
    set_active_conversation(user_id, conversation_id)
    return conversation_id


def set_active_conversation(user_id: str, conversation_id: str) -> None:
    """Set the active conversation for a user."""
    os.makedirs(os.path.dirname(str(SESSION_FILE)), exist_ok=True)

    data = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}

    data[user_id] = conversation_id

    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except IOError:
        import logging
        logging.warning(f"Failed to set active conversation for user {user_id}")


def get_active_conversation(user_id: str) -> Optional[str]:
    """Get the currently active conversation_id for a user.

    Returns:
        conversation_id or None if no active conversation
    """
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                if user_id in data:
                    session_value = data[user_id]
                    if isinstance(session_value, dict):
                        return session_value.get("conversation_id")
                    return session_value
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_session(user_id: str, conversation_id: str) -> None:
    """Persist conversation_id for a user."""
    os.makedirs(os.path.dirname(str(SESSION_FILE)), exist_ok=True)
    
    data = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, start fresh
            data = {}

    data[user_id] = conversation_id
    
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except IOError:
        # If we can't write to file, log the error but don't crash
        import logging
        logging.warning(f"Failed to save session for user {user_id}")
