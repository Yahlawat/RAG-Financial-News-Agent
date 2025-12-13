import logging
import os
import sys

import requests
import streamlit as st
from streamlit.web import cli as stcli

from finnews.common.config import settings
from finnews.common.logging import setup_logging
from finnews.ui.conversation_history import (
    add_message,
    delete_conversation,
    get_conversation_messages,
    load_user_conversations,
)
from finnews.ui.session_manager import (
    create_new_conversation,
    load_session,
    set_active_conversation,
)


def api_base() -> str:
    return f"http://{settings.API_HOST}:{settings.API_PORT}"


def render_sidebar(current_conversation_id: str):
    """Render the sidebar with conversation history."""
    with st.sidebar:
        st.title("💬 Chat History")

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            create_new_conversation()
            st.rerun()

        st.divider()

        # Load and display conversations
        conversations = load_user_conversations()

        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        if not conversations:
            st.info("No conversations yet. Start chatting!")
        else:
            for conv in conversations:
                conv_id = conv.get("conversation_id")
                title = conv.get("title", "Untitled")
                is_active = conv_id == current_conversation_id

                # Create a container for each conversation
                col1, col2 = st.columns([4, 1])

                with col1:
                    # Highlight active conversation
                    if st.button(
                        f"{'📌 ' if is_active else ''}{title}",
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        set_active_conversation(conversation_id=conv_id)
                        st.rerun()

                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"del_{conv_id}"):
                        delete_conversation(conversation_id=conv_id)
                        # If deleting active conversation, create a new one
                        if conv_id == current_conversation_id:
                            create_new_conversation()
                        st.rerun()


def render_chat_messages(messages):
    """Render chat message history."""
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        sources = msg.get("sources", [])

        with st.chat_message(role):
            st.markdown(content)

            # Show sources for assistant messages
            if role == "assistant" and sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        title = source.get("title", "Source")
                        url = source.get("url", "#")
                        date = source.get("published_date", "")
                        st.markdown(f"- [{title}]({url}) ({date})")


def run():
    st.set_page_config(
        page_title="FinNews Assistant",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📈 FinNews Assistant")
    st.caption("AI-powered financial news analysis using RAG")

    # Use default user
    user_id = settings.DEFAULT_USER_ID

    # Load or create active conversation
    conversation_id = load_session()

    # Render sidebar with conversation history
    render_sidebar(conversation_id)

    # Load conversation messages
    messages = get_conversation_messages(conversation_id=conversation_id)

    # Display conversation history
    if messages:
        render_chat_messages(messages)
    else:
        st.info("👋 Start a new conversation! Ask me anything about financial news.")

    # Chat input
    user_question = st.chat_input("Ask about financial news...")

    if user_question:
        # Add user message to conversation
        add_message(conversation_id=conversation_id, role="user", content=user_question)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_question)

        # Prepare API request
        payload = {
            "question": user_question,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }

        # Call API and display response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    r = requests.post(f"{api_base()}/chat", json=payload, timeout=60)
                    r.raise_for_status()
                    data = r.json()

                    answer = data.get("answer", "<no answer>")
                    sources = data.get("sources", [])

                    st.markdown(answer)

                    # Show sources
                    if sources:
                        with st.expander("📚 Sources"):
                            for s in sources:
                                st.markdown(
                                    f"- [{s.get('title', 'source')}]({s.get('url', '#')}) "
                                    f"({s.get('published_date', '')})"
                                )

                    # Save assistant response to conversation
                    add_message(
                        conversation_id=conversation_id, role="assistant", content=answer, sources=sources
                    )

                except requests.ConnectionError:
                    error_msg = f"❌ Cannot connect to API server at {api_base()}. Please ensure the API server is running with `finnews-api`."
                    st.error(error_msg)
                except requests.Timeout:
                    error_msg = "⏱️ Request timed out. The API server may be overloaded or processing a large query."
                    st.error(error_msg)
                except requests.HTTPError as e:
                    error_msg = (
                        f"❌ API returned an error: {e.response.status_code} - {e.response.text}"
                    )
                    st.error(error_msg)
                except requests.RequestException as e:
                    error_msg = f"❌ API request failed: {e}"
                    st.error(error_msg)


def main() -> None:
    # Setup logging for UI component (console disabled for Streamlit)
    setup_logging(component="ui", level=logging.INFO, console=False)

    script = os.path.abspath(__file__)
    args = [
        "streamlit",
        "run",
        script,
        "--server.port",
        str(settings.STREAMLIT_PORT),
        "--server.headless",
        "true",
    ]
    sys.argv = args
    sys.exit(stcli.main())


if __name__ == "__main__":
    run()
