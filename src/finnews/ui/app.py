import os
import sys
import time
from datetime import datetime
from streamlit.web import cli as stcli
import streamlit as st
import requests

from finnews.common.config import settings
from finnews.ui.session_manager import load_session, create_new_conversation, set_active_conversation
from finnews.ui.conversation_history import (
    load_user_conversations,
    add_message,
    get_conversation_messages,
    delete_conversation
)
from finnews.ui.user_profile import (
    load_user_profile,
    add_tickers as add_tickers_to_profile,
    remove_tickers as remove_tickers_from_profile
)


def api_base() -> str:
    return f"http://{settings.API_HOST}:{settings.API_PORT}"


def format_time_ago(iso_timestamp: str) -> str:
    """Format an ISO timestamp as 'X time ago'.

    Args:
        iso_timestamp: ISO format timestamp string

    Returns:
        Human-readable time ago string
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        diff = now - dt

        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    except (ValueError, TypeError, AttributeError):
        return "unknown"


def render_portfolio_section(user_id: str):
    """Render the portfolio ticker management section.

    Args:
        user_id: The user's ID
    """
    st.subheader("📊 My Portfolio Tickers")

    # Load user profile
    profile = load_user_profile(user_id)

    # Get ticker metadata
    if profile.portfolio_tickers:
        with st.spinner("Loading ticker metadata..."):
            try:
                response = requests.post(
                    f"{api_base()}/scrape/tickers/metadata",
                    json={"tickers": profile.portfolio_tickers},
                    timeout=5
                )
                if response.status_code == 200:
                    metadata = response.json().get("metadata", [])
                    metadata_dict = {item["ticker"]: item for item in metadata}
                else:
                    metadata_dict = {}
            except requests.RequestException:
                metadata_dict = {}

        # Display current tickers
        for ticker in profile.portfolio_tickers:
            col1, col2, col3 = st.columns([3, 4, 1])

            with col1:
                st.markdown(f"**{ticker}**")

            with col2:
                # Show last scraped info
                if ticker in metadata_dict:
                    meta = metadata_dict[ticker]
                    if meta.get("never_scraped"):
                        st.caption("Never scraped")
                    else:
                        last_scraped = meta.get("last_scraped")
                        if last_scraped:
                            time_ago = format_time_ago(last_scraped)
                            st.caption(f"Scraped {time_ago}")

            with col3:
                # Remove button
                if st.button("✖", key=f"remove_{ticker}"):
                    remove_tickers_from_profile(user_id, [ticker])
                    st.rerun()
    else:
        st.info("No tickers in portfolio yet. Add some below!")

    # Add ticker input
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input(
            "Add ticker",
            placeholder="AAPL",
            key="new_ticker_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("➕ Add", use_container_width=True):
            if new_ticker:
                cleaned_ticker = new_ticker.strip().upper()
                if cleaned_ticker:
                    add_tickers_to_profile(user_id, [cleaned_ticker])
                    st.rerun()


def render_scraping_section(user_id: str):
    """Render the scraping controls section.

    Args:
        user_id: The user's ID
    """
    st.subheader("🔄 Scraping Controls")

    # Check scrape status
    try:
        status_response = requests.get(f"{api_base()}/scrape/status", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            scrape_status = status_data.get("status", "idle")
            pipeline_stage = status_data.get("pipeline_stage", "idle")
            stage_message = status_data.get("stage_message", "Ready")
            started_at = status_data.get("started_at")
            completed = status_data.get("completed", 0)
            total = status_data.get("total", 0)
            articles_found = status_data.get("articles_found", 0)
            time_elapsed = status_data.get("time_elapsed_seconds", 0)
        else:
            scrape_status = "idle"
            pipeline_stage = "idle"
            stage_message = "Ready"
            started_at = None
            completed = 0
            total = 0
            articles_found = 0
            time_elapsed = 0
    except requests.RequestException as e:
        # API is unavailable or request failed - default to idle state
        scrape_status = "idle"
        pipeline_stage = "idle"
        stage_message = "Ready"
        started_at = None
        completed = 0
        total = 0
        articles_found = 0
        time_elapsed = 0

    if scrape_status == "running":
        # Show progress with pipeline stage info
        # Choose icon based on stage
        if pipeline_stage == "scraping":
            icon = "🔄"
        elif pipeline_stage in ["chunking", "chunking_complete"]:
            icon = "⚙️"
        elif pipeline_stage == "embedding":
            icon = "🧠"
        else:
            icon = "🔄"

        st.info(f"{icon} {stage_message}")

        # Show progress bar for scraping stage
        if pipeline_stage == "scraping" and total > 0:
            progress = completed / total
            st.progress(progress)
            st.caption(
                f"Progress: {completed}/{total} tickers • {articles_found} articles • "
                f"{int(time_elapsed)}s elapsed"
            )
        # Show indeterminate progress for post-processing stages
        elif pipeline_stage in ["chunking", "chunking_complete", "embedding"]:
            st.progress(0.5)  # Show half-filled progress bar
            st.caption(f"Processing... • {int(time_elapsed)}s total elapsed")
        else:
            st.caption("Initializing...")

        # Auto-refresh every 3 seconds
        time.sleep(3)
        st.rerun()

    elif scrape_status == "completed" or pipeline_stage == "completed":
        # Show completion message
        st.success("✅ Pipeline complete! Articles ready for querying")
        # Reset status after showing message
        try:
            requests.post(f"{api_base()}/scrape/reset", timeout=5)
        except Exception:
            pass  # Silently fail - status will be reset on next UI load if needed

    else:
        # Show scrape button
        profile = load_user_profile(user_id)
        if not profile.portfolio_tickers:
            st.warning("Add tickers to your portfolio first!")
        else:
            if st.button("🔄 Scrape Now", use_container_width=True):
                try:
                    response = requests.post(
                        f"{api_base()}/scrape/start",
                        json={"user_id": user_id},
                        timeout=10
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "started":
                            st.success(f"Started scraping {len(result.get('tickers', []))} tickers!")
                            time.sleep(1)
                            st.rerun()
                        elif result.get("status") == "already_running":
                            st.warning("A scraping job is already in progress")
                    else:
                        st.error(f"Failed to start scraping: {response.text}")
                except Exception as e:
                    st.error(f"Error starting scrape: {e}")


def render_sidebar(user_id: str, current_conversation_id: str):
    """Render the sidebar with conversation history."""
    with st.sidebar:
        # Portfolio ticker management
        render_portfolio_section(user_id)

        st.divider()

        # Scraping controls
        render_scraping_section(user_id)

        st.divider()

        # Chat history
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

    # Chat input
    user_question = st.chat_input("Ask about financial news...")

    if user_question:
        # Add user message to conversation
        add_message(user_id, conversation_id, "user", user_question)

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_question)

        # Prepare API request (portfolio tickers are auto-loaded in API)
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


def main() -> None:
    script = os.path.abspath(__file__)
    args = [
        "streamlit", "run", script,
        "--server.port", str(settings.STREAMLIT_PORT),
        "--server.headless", "true",
    ]
    sys.argv = args
    sys.exit(stcli.main())


if __name__ == "__main__":
    run()
