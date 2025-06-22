import requests
import streamlit as st
import sys
import os
import uuid

from session_manager import load_session, save_session

import csv

FALLBACK_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "NVDA",
    "META",
    "NFLX",
    "JPM",
    "BRK.B",
]


def load_tickers_from_csv(path: str = "data/tickers/tickers.csv", column: str = "ticker_symbol"):
    """Load a list of tickers from a CSV file.

    Falls back to ``FALLBACK_TICKERS`` if the file is missing or unreadable.
    """
    if not os.path.exists(path):
        return FALLBACK_TICKERS

    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            # choose provided column or first available
            col = column if column in reader.fieldnames else reader.fieldnames[0]
            tickers = [row.get(col, "").strip().upper() for row in reader]
            tickers = [t for t in tickers if t]
            return tickers if tickers else FALLBACK_TICKERS
    except Exception as e:
        st.warning(f"Failed to read {path}: {e}")
        return FALLBACK_TICKERS


TICKERS = load_tickers_from_csv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag_pipeline.retriever import get_full_chat_history, load_vectorstore

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
    st.session_state["conversation_id"] = load_session(user_id)

if "chat_store" not in st.session_state:
    try:
        st.session_state["chat_store"] = load_vectorstore("data/chat_memory")
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
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Optional Reset Button
if st.button("🔄 Reset Conversation"):
    new_id = str(uuid.uuid4())
    st.session_state["conversation_id"] = new_id
    st.session_state["chat_history"] = []
    save_session(user_id, new_id)
    st.rerun()

# ──────────────────────────────
# USER INPUT
# ──────────────────────────────
selected_tickers = st.multiselect(
    "Filter by ticker(s)", options=TICKERS, key="tickers_select"
)

question = st.chat_input("Ask a question")

if question:
    tickers = [t.strip().upper() for t in selected_tickers] if selected_tickers else None
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

        # Display assistant answer with sources
        with st.chat_message("assistant"):
            st.markdown(data.get("answer", ""))
            if data.get("sources"):
                st.markdown("**Sources**")
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
