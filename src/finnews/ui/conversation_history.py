import json
from datetime import datetime, timezone
from pathlib import Path

from finnews.common.config import settings

CONVERSATIONS_DIR = settings.CHAT_SESSIONS_FILE.parent / "conversations"


def _ensure_conversations_dir():
    """Ensure conversations directory exists."""
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _get_conversation_file(user_id: str) -> Path:
    """Get the path to a user's conversation history file."""
    return CONVERSATIONS_DIR / f"{user_id}_conversations.json"


def load_user_conversations(user_id: str = None) -> list[dict]:
    """
    Load all conversations for a user.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)

    Returns:
        List of conversation dictionaries
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    _ensure_conversations_dir()
    conv_file = _get_conversation_file(user_id)

    if not conv_file.exists():
        return []

    try:
        with open(conv_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("conversations", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_user_conversations(user_id: str = None, conversations: list[dict] = None):
    """
    Save all conversations for a user.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversations: List of conversation dicts to save
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    _ensure_conversations_dir()
    conv_file = _get_conversation_file(user_id)

    try:
        with open(conv_file, "w", encoding="utf-8") as f:
            json.dump({"conversations": conversations}, f, indent=2, ensure_ascii=False)
    except IOError as e:
        import logging

        logging.warning(f"Failed to save conversations for user {user_id}: {e}")


def get_conversation(user_id: str = None, conversation_id: str = None) -> dict | None:
    """
    Get a specific conversation by ID.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversation_id: Conversation ID

    Returns:
        Conversation dict or None if not found
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    conversations = load_user_conversations(user_id)
    for conv in conversations:
        if conv.get("conversation_id") == conversation_id:
            return conv
    return None


def create_conversation(user_id: str = None, conversation_id: str = None) -> dict:
    """
    Create a new empty conversation.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversation_id: Conversation ID

    Returns:
        Newly created conversation dict
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    now = datetime.now(timezone.utc).isoformat()
    new_conv = {
        "conversation_id": conversation_id,
        "title": "New Chat",
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }

    conversations = load_user_conversations(user_id)
    conversations.append(new_conv)
    save_user_conversations(user_id, conversations)

    return new_conv


def add_message(
    user_id: str = None,
    conversation_id: str = None,
    role: str = None,
    content: str = None,
    sources: list[dict] | None = None,
):
    """
    Add a message to a conversation.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversation_id: Conversation identifier
        role: 'user' or 'assistant'
        content: Message content
        sources: Optional list of source documents (for assistant messages)
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    conversations = load_user_conversations(user_id)

    # Find the conversation
    conv_index = None
    for i, conv in enumerate(conversations):
        if conv.get("conversation_id") == conversation_id:
            conv_index = i
            break

    # Create conversation if it doesn't exist
    if conv_index is None:
        create_conversation(user_id, conversation_id)
        conversations = load_user_conversations(user_id)
        conv_index = len(conversations) - 1

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if sources:
        message["sources"] = sources

    conversations[conv_index]["messages"].append(message)
    conversations[conv_index]["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Auto-generate title from first user message
    if conversations[conv_index]["title"] == "New Chat" and role == "user":
        title = content[:50].strip()
        if len(content) > 50:
            title += "..."
        conversations[conv_index]["title"] = title

    save_user_conversations(user_id, conversations)


def delete_conversation(user_id: str = None, conversation_id: str = None):
    """
    Delete a conversation.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversation_id: Conversation ID to delete
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    conversations = load_user_conversations(user_id)
    conversations = [c for c in conversations if c.get("conversation_id") != conversation_id]
    save_user_conversations(user_id, conversations)


def get_conversation_messages(user_id: str = None, conversation_id: str = None) -> list[dict]:
    """
    Get all messages from a conversation.

    Args:
        user_id: User ID (defaults to DEFAULT_USER_ID)
        conversation_id: Conversation ID

    Returns:
        List of message dicts
    """
    if user_id is None:
        user_id = settings.DEFAULT_USER_ID

    conv = get_conversation(user_id, conversation_id)
    if conv:
        return conv.get("messages", [])
    return []
