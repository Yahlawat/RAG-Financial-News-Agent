import uuid
import requests
import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag_pipeline.retriever import get_full_chat_history, load_vectorstore


@st.cache_resource
def get_chat_store() -> "Chroma":
    """Load the chat memory vector store only once."""
    return load_vectorstore("data/chat_memory")

API_URL = "http://localhost:8000/chat"

st.set_page_config(
    page_title="Financial News QA",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("Financial News Question Answering")
st.markdown("""
Ask questions about financial news and get AI-powered answers based on the latest news articles.
The system uses RAG (Retrieval Augmented Generation) to provide accurate and up-to-date information.
""")

# ──────────────────────────────
# USER LOGIN
# ──────────────────────────────
user_id = st.text_input("Enter your username:", key="user_id")
if not user_id:
    st.stop()

# ──────────────────────────────
# SESSION STATE SETUP
# ──────────────────────────────
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

if "chat_store" not in st.session_state:
    try:
        st.session_state["chat_store"] = get_chat_store()
    except Exception as e:
        st.error(f"Failed to load chat vectorstore: {e}")
        st.stop()

chat_store = st.session_state["chat_store"]
conversation_id = st.session_state["conversation_id"]

# Initialize chat history only once per new user or session
if "chat_history" not in st.session_state:
    try:
        docs = get_full_chat_history(chat_store, conversation_id, user_id)
        if docs:
            st.session_state["chat_history"] = [
                {"role": doc.metadata.get("role", "assistant"), "content": doc.page_content}
                for doc in docs
            ]
        else:
            st.session_state["chat_history"] = []
    except Exception as e:
        st.warning(f"No previous chat found or failed to load history: {e}")
        st.session_state["chat_history"] = []

# ──────────────────────────────
# CHAT HISTORY DISPLAY
# ──────────────────────────────
if st.session_state["chat_history"]:
    st.write("### 🗨️ Chat History")
    for msg in st.session_state["chat_history"]:
        speaker = "You" if msg["role"] == "user" else "Assistant"
        st.markdown(f"**{speaker}:** {msg['content']}")

# Optional Reset Button
if st.button("🔄 Reset Conversation"):
    st.session_state["conversation_id"] = str(uuid.uuid4())
    st.session_state["chat_history"] = []
    st.rerun()

# ──────────────────────────────
# USER INPUT
# ──────────────────────────────
question = st.text_input("Ask a question")
tickers_raw = st.text_input("Tickers (comma-separated)")

if st.button("Submit"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        tickers = [t.strip().upper() for t in tickers_raw.split(',') if t.strip()] if tickers_raw else None
        payload = {
            "question": question,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "target_tickers": tickers,
        }

        try:
            r = requests.post(API_URL, json=payload)
            r.raise_for_status()
            data = r.json()

            # Append to chat state
            st.session_state["chat_history"].append({"role": "user", "content": question})
            st.session_state["chat_history"].append({"role": "assistant", "content": data.get("answer", "")})

            # Display
            st.markdown(f"**Assistant:** {data.get('answer', '')}")
            if data.get("sources"):
                st.write("### Sources")
                for src in data["sources"]:
                    title = src.get("title", "source")
                    url = src.get("url", "")
                    date = src.get("published_date", "")
                    if url:
                        st.markdown(f"- [{title}]({url}) ({date})")
                    else:
                        st.markdown(f"- {title} ({date})")

        except Exception as e:
            st.error(f"Error contacting API: {e}")
