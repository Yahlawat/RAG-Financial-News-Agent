import logging
import uuid
from typing import Optional
from finnews.common.config import settings
from finnews.common.io_utils import read_json, write_json, ensure_file_dir

SESSION_FILE = str(settings.CHAT_SESSIONS_FILE)
logger = logging.getLogger(__name__)


def _read_session_data() -> dict:
    """Read session data from file with error handling."""
    ensure_file_dir(SESSION_FILE)
    return read_json(SESSION_FILE)


def _write_session_data(data: dict) -> None:
    """Write session data to file with error handling."""
    write_json(SESSION_FILE, data, indent=2)


def load_session(user_id: str) -> str:
    """Return the active conversation_id for a user or create a new one."""
    data = _read_session_data()

    if user_id in data:
        return data[user_id]

    conversation_id = str(uuid.uuid4())
    data[user_id] = conversation_id
    _write_session_data(data)

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
    data = _read_session_data()
    data[user_id] = conversation_id
    _write_session_data(data)


def get_active_conversation(user_id: str) -> Optional[str]:
    """Get the currently active conversation_id for a user.

    Returns:
        conversation_id or None if no active conversation
    """
    data = _read_session_data()
    if user_id in data:
        return data[user_id]
    return None
