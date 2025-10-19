import streamlit as st
import requests

from finnews.common.config import settings
from finnews.ui.session_manager import load_session


def api_base() -> str:
    return f"http://{settings.api_host}:{settings.api_port}"


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
            "user_id": user_id,
            "conversation_id": conversation_id,
        }
        if tickers:
            payload["tickers"] = tickers

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


if __name__ == "__main__":
    run()

