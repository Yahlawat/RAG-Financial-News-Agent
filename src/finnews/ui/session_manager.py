import json
import os
import uuid
from finnews.common.config import settings

SESSION_FILE = settings.chat_sessions


def load_session(user_id: str) -> str:
    """Return existing conversation_id for a user or create a new one."""
    os.makedirs(os.path.dirname(str(SESSION_FILE)), exist_ok=True)
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    if user_id in data:
        return data[user_id]

    conversation_id = str(uuid.uuid4())
    data[user_id] = conversation_id
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)
    return conversation_id


def save_session(user_id: str, conversation_id: str) -> None:
    """Persist conversation_id for a user."""
    os.makedirs(os.path.dirname(str(SESSION_FILE)), exist_ok=True)
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    data[user_id] = conversation_id
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)
