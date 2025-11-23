<<<<<<< HEAD
import os
import sys
=======
import os, sys
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
from streamlit.web import cli as stcli
import streamlit as st
import requests

from finnews.common.config import settings
<<<<<<< HEAD
from finnews.ui.session_manager import load_session, create_new_conversation, set_active_conversation
from finnews.ui.conversation_history import (
    load_user_conversations,
    add_message,
    get_conversation_messages,
    delete_conversation
)
=======
from finnews.ui.session_manager import load_session
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d


def api_base() -> str:
    return f"http://{settings.api_host}:{settings.api_port}"


<<<<<<< HEAD
def render_sidebar(user_id: str, current_conversation_id: str):
    """Render the sidebar with conversation history."""
    with st.sidebar:
        st.title("💬 Chat History")

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            new_conv_id = create_new_conversation(user_id)
            st.rerun()

        st.divider()

        # Load and display conversations
        conversations = load_user_conversations(user_id)

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
                        type="primary" if is_active else "secondary"
                    ):
                        set_active_conversation(user_id, conv_id)
                        st.rerun()

                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"del_{conv_id}"):
                        delete_conversation(user_id, conv_id)
                        # If deleting active conversation, create a new one
                        if conv_id == current_conversation_id:
                            create_new_conversation(user_id)
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
        initial_sidebar_state="expanded"
    )

    st.title("📈 FinNews Assistant")
    st.caption("AI-powered financial news analysis using RAG")

    # User ID input (could be replaced with auth later)
    user_id = st.text_input("👤 User ID", value="demo", key="user_id_input")

    if not user_id:
        st.warning("Please enter a User ID to continue.")
        return

    # Load or create active conversation
    conversation_id = load_session(user_id)

    # Render sidebar with conversation history
    render_sidebar(user_id, conversation_id)

    # Load conversation messages
    messages = get_conversation_messages(user_id, conversation_id)

    # Display conversation history
    if messages:
        render_chat_messages(messages)
    else:
        st.info("👋 Start a new conversation! Ask me anything about financial news.")

    # Ticker input (optional filter)
    with st.expander("⚙️ Advanced Options"):
        tickers_input = st.text_input(
            "Filter by Tickers (optional, comma-separated)",
            placeholder="AAPL, TSLA, MSFT"
        )

    # Chat input
    user_question = st.chat_input("Ask about financial news...")

    if user_question:
        # Add user message to conversation
        add_message(user_id, conversation_id, "user", user_question)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_question)

        # Prepare API request
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()] if tickers_input else None
        payload = {
            "question": user_question,
=======
def run():
    st.title("FinNews Assistant")

    user_id = st.text_input("User ID", value="demo")
    conversation_id = load_session(user_id)

    msg = st.text_input("Ask something about the news:")
    tickers_input = st.text_input("Tickers (optional, comma-separated)")

    if st.button("Send") and msg:
        tickers = [t.strip() for t in tickers_input.split(",") if t.strip()] if tickers_input else None
        payload = {
            "question": msg,
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
            "user_id": user_id,
            "conversation_id": conversation_id,
        }
        if tickers:
            payload["tickers"] = tickers

<<<<<<< HEAD
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
                    add_message(user_id, conversation_id, "assistant", answer, sources)

                except requests.ConnectionError:
                    error_msg = f"❌ Cannot connect to API server at {api_base()}. Please ensure the API server is running with `finnews-api`."
                    st.error(error_msg)
                except requests.Timeout:
                    error_msg = "⏱️ Request timed out. The API server may be overloaded or processing a large query."
                    st.error(error_msg)
                except requests.HTTPError as e:
                    error_msg = f"❌ API returned an error: {e.response.status_code} - {e.response.text}"
                    st.error(error_msg)
                except requests.RequestException as e:
                    error_msg = f"❌ API request failed: {e}"
                    st.error(error_msg)


=======
        try:
            r = requests.post(f"{api_base()}/chat", json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            st.subheader("Answer")
            st.write(data.get("answer", "<no answer>"))

            sources = data.get("sources", [])
            if sources:
                st.subheader("Sources")
                for s in sources:
                    st.markdown(f"- [{s.get('title','source')}]({s.get('url','#')}) ({s.get('published_date','')})")
        except requests.RequestException as e:
            st.error(f"API request failed: {e}")
            
>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
def main() -> None:
    script = os.path.abspath(__file__)
    args = [
        "streamlit", "run", script,
        "--server.port", str(settings.streamlit_port),
        "--server.headless", "true",
    ]
    sys.argv = args
    sys.exit(stcli.main())

<<<<<<< HEAD

if __name__ == "__main__":
    run()
=======
if __name__ == "__main__":
    run()

>>>>>>> 7af5a402772857b0c388489419e38a01f18be89d
