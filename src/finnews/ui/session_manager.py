import json
import os
import uuid
from finnews.common.config import settings

SESSION_FILE = settings.chat_sessions


def load_session(user_id: str) -> str:
    """Return existing conversation_id for a user or create a new one."""
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
        return data[user_id]

    conversation_id = str(uuid.uuid4())
    data[user_id] = conversation_id
    
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
    except IOError:
        # If we can't write to file, still return the conversation ID
        pass
    
    return conversation_id


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
